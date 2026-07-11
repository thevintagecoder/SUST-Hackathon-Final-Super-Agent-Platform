"""Generate and persist explainable multilingual alerts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    Agent,
    AgentPosition,
    Alert,
    AlertEvent,
    Provider,
    ProviderBalance,
)
from backend.app.schemas.alert import (
    AlertGenerationRequest,
    AlertGenerationResponse,
    AlertType,
    RenderedAlertTemplate,
)
from backend.app.schemas.anomaly import (
    AnomalyDetectionRequest,
)
from backend.app.schemas.forecast import (
    LiquidityRunwayRequest,
)
from backend.app.services.alert_templates import (
    render_alert_template,
)
from backend.app.services.anomaly_service import (
    detect_anomalies_for_request,
)
from backend.app.services.forecast_service import (
    forecast_liquidity_runway,
)


ZERO = Decimal("0.00")
FOUR_DECIMAL_PLACES = Decimal("0.0001")
TWO_DECIMAL_PLACES = Decimal("0.01")


class AlertGenerationNotFoundError(Exception):
    """Raised when required alert data cannot be found."""


class AlertGenerationValidationError(Exception):
    """Raised when alert-generation input is inconsistent."""


class AlertGenerationDataUnavailableError(Exception):
    """Raised when alert source data is unavailable."""


def as_decimal(
    value: object,
) -> Decimal:
    """Convert a database numeric value into Decimal."""

    return Decimal(
        str(value)
    )


def decimal_text(
    value: Decimal,
) -> str:
    """Format a decimal for JSON evidence."""

    return format(
        value.quantize(
            TWO_DECIMAL_PLACES
        ),
        ".2f",
    )


def datetime_text(
    value: datetime | None,
) -> str | None:
    """Format an optional datetime for JSON evidence."""

    if value is None:
        return None

    return value.isoformat()


def normalized_confidence(
    value: Decimal,
) -> Decimal:
    """Store confidence using the model's four-decimal scale."""

    return value.quantize(
        FOUR_DECIMAL_PLACES
    )


def find_agent(
    *,
    db: Session,
    agent_code: str,
) -> Agent:
    """Find an active Agent."""

    agent = db.scalar(
        select(Agent).where(
            Agent.code == agent_code
        )
    )

    if agent is None:
        raise AlertGenerationNotFoundError(
            f"Agent '{agent_code}' was not found."
        )

    if not agent.is_active:
        raise AlertGenerationValidationError(
            f"Agent '{agent_code}' is inactive."
        )

    return agent


def find_provider(
    *,
    db: Session,
    provider_code: str,
) -> Provider:
    """Find a provider."""

    provider = db.scalar(
        select(Provider).where(
            Provider.code == provider_code
        )
    )

    if provider is None:
        raise AlertGenerationNotFoundError(
            f"Provider '{provider_code}' was not found."
        )

    return provider


def provider_display_name(
    provider: Provider,
) -> str:
    """Return a human-readable provider name."""

    provider_name = getattr(
        provider,
        "name",
        None,
    )

    if (
        isinstance(provider_name, str)
        and provider_name.strip()
    ):
        return provider_name.strip()

    return provider.code


def build_deduplication_key(
    *,
    alert_type: AlertType,
    agent_code: str,
    provider_code: str | None,
    scenario_id: str | None,
    source_token: str,
) -> str:
    """Build a deterministic evidence-specific alert key."""

    return ":".join(
        (
            alert_type,
            agent_code,
            provider_code or "ALL",
            scenario_id or "LIVE",
            source_token,
        )
    )[:255]


def no_alert_response(
    *,
    alert_type: AlertType,
    reason: str,
) -> AlertGenerationResponse:
    """Return a result when alert conditions are not met."""

    return AlertGenerationResponse(
        alert_type=alert_type,
        condition_detected=False,
        alert_created=False,
        deduplicated=False,
        alert_id=None,
        reason=reason,
        human_review_required=False,
        automatic_action_taken=False,
    )


def persist_alert(
    *,
    db: Session,
    alert_type: AlertType,
    severity: str,
    agent: Agent,
    provider: Provider | None,
    scenario_id: str | None,
    source_reference: str,
    source_token: str,
    template: RenderedAlertTemplate,
    evidence: dict[str, object],
    confidence: Decimal,
    freshness_state: str | None,
) -> AlertGenerationResponse:
    """Persist an alert unless the same evidence already exists."""

    deduplication_key = build_deduplication_key(
        alert_type=alert_type,
        agent_code=agent.code,
        provider_code=(
            provider.code
            if provider is not None
            else None
        ),
        scenario_id=scenario_id,
        source_token=source_token,
    )

    existing_alert = db.scalar(
        select(Alert).where(
            Alert.deduplication_key
            == deduplication_key
        )
    )

    if existing_alert is not None:
        return AlertGenerationResponse(
            alert_type=alert_type,
            condition_detected=True,
            alert_created=False,
            deduplicated=True,
            alert_id=existing_alert.id,
            reason=(
                "An alert already exists for the same "
                "source evidence."
            ),
            human_review_required=(
                existing_alert
                .human_review_required
            ),
            automatic_action_taken=(
                existing_alert
                .automatic_action_taken
            ),
        )

    alert = Alert(
        deduplication_key=deduplication_key,
        alert_type=alert_type,
        severity=severity,
        status="OPEN",
        agent_id=agent.id,
        provider_id=(
            provider.id
            if provider is not None
            else None
        ),
        scenario_id=scenario_id,
        source_reference=source_reference,
        title_en=template.title.en,
        title_bn=template.title.bn,
        title_bn_latn=(
            template.title.bn_latn
        ),
        message_en=template.message.en,
        message_bn=template.message.bn,
        message_bn_latn=(
            template.message.bn_latn
        ),
        next_step_en=(
            template.next_step.en
        ),
        next_step_bn=(
            template.next_step.bn
        ),
        next_step_bn_latn=(
            template.next_step.bn_latn
        ),
        evidence=evidence,
        confidence=normalized_confidence(
            confidence
        ),
        freshness_state=freshness_state,
        human_review_required=True,
        automatic_action_taken=False,
    )

    alert.events.append(
        AlertEvent(
            event_type="CREATED",
            actor="system",
            note=(
                "Created from explainable "
                "source evidence."
            ),
            event_data={
                "alert_type": alert_type,
                "source_reference": (
                    source_reference
                ),
            },
        )
    )

    db.add(
        alert
    )
    db.commit()
    db.refresh(
        alert
    )

    return AlertGenerationResponse(
        alert_type=alert_type,
        condition_detected=True,
        alert_created=True,
        deduplicated=False,
        alert_id=alert.id,
        reason=(
            "Alert created from the detected "
            "source condition."
        ),
        human_review_required=True,
        automatic_action_taken=False,
    )


def generate_liquidity_runway_alert(
    *,
    db: Session,
    request: AlertGenerationRequest,
    agent: Agent,
) -> AlertGenerationResponse:
    """Generate an alert from a runway forecast."""

    if request.provider_code is None:
        raise AlertGenerationValidationError(
            "provider_code is required for "
            "LIQUIDITY_RUNWAY alerts."
        )

    provider = find_provider(
        db=db,
        provider_code=request.provider_code,
    )

    forecast = forecast_liquidity_runway(
        db=db,
        request=LiquidityRunwayRequest(
            agent_code=agent.code,
            resource_type="provider_float",
            provider_code=provider.code,
            scenario_id=request.scenario_id,
            lookback_hours=(
                request.lookback_hours
            ),
            warning_threshold_hours=(
                request
                .warning_threshold_hours
            ),
        ),
    )

    if forecast.risk_level not in {
        "HIGH",
        "CRITICAL",
    }:
        return no_alert_response(
            alert_type="LIQUIDITY_RUNWAY",
            reason=(
                "The forecast did not meet the HIGH "
                "or CRITICAL alert threshold."
            ),
        )

    if forecast.runway_hours is None:
        return no_alert_response(
            alert_type="LIQUIDITY_RUNWAY",
            reason=(
                "The forecast did not produce a "
                "runway estimate."
            ),
        )

    template = render_alert_template(
        alert_type="LIQUIDITY_RUNWAY",
        provider_name=(
            provider_display_name(
                provider
            )
        ),
        runway_hours=forecast.runway_hours,
    )

    evidence: dict[str, object] = {
        "resource_type": (
            forecast.resource_type
        ),
        "provider_code": provider.code,
        "current_balance": decimal_text(
            forecast.current_balance
        ),
        "safety_threshold": decimal_text(
            forecast.safety_threshold
        ),
        "runway_hours": decimal_text(
            forecast.runway_hours
        ),
        "risk_level": forecast.risk_level,
        "forecast_as_of": datetime_text(
            forecast.forecast_as_of
        ),
        "estimated_threshold_breach_time": (
            datetime_text(
                forecast
                .estimated_threshold_breach_time
            )
        ),
        "completed_transaction_count": (
            forecast
            .completed_transaction_count
        ),
        "explanation_factors": (
            forecast.explanation_factors
        ),
    }

    source_token = (
        datetime_text(
            forecast.forecast_as_of
        )
        or "UNKNOWN"
    )

    return persist_alert(
        db=db,
        alert_type="LIQUIDITY_RUNWAY",
        severity=forecast.risk_level,
        agent=agent,
        provider=provider,
        scenario_id=request.scenario_id,
        source_reference=(
            "liquidity-runway:"
            f"{request.scenario_id or 'LIVE'}"
        ),
        source_token=source_token,
        template=template,
        evidence=evidence,
        confidence=forecast.confidence,
        freshness_state=(
            forecast.freshness_state
        ),
    )


def generate_anomaly_review_alert(
    *,
    db: Session,
    request: AlertGenerationRequest,
    agent: Agent,
) -> AlertGenerationResponse:
    """Generate an alert from anomaly-detection evidence."""

    provider: Provider | None = None

    if request.provider_code is not None:
        provider = find_provider(
            db=db,
            provider_code=(
                request.provider_code
            ),
        )

    anomaly = detect_anomalies_for_request(
        db=db,
        request=AnomalyDetectionRequest(
            agent_code=agent.code,
            provider_code=(
                provider.code
                if provider is not None
                else None
            ),
            scenario_id=request.scenario_id,
            recent_window_minutes=(
                request.recent_window_minutes
            ),
            baseline_window_minutes=(
                request
                .baseline_window_minutes
            ),
            amount_tolerance=(
                request.amount_tolerance
            ),
            minimum_repeated_count=(
                request
                .minimum_repeated_count
            ),
            velocity_multiplier=(
                request.velocity_multiplier
            ),
        ),
    )

    if not anomaly.anomaly_detected:
        return no_alert_response(
            alert_type="ANOMALY_REVIEW",
            reason=(
                "The transaction pattern did not "
                "meet the anomaly thresholds."
            ),
        )

    template = render_alert_template(
        alert_type="ANOMALY_REVIEW",
    )

    evidence: dict[str, object] = {
        "category": anomaly.category,
        "severity": anomaly.severity,
        "recent_transaction_count": (
            anomaly.recent_transaction_count
        ),
        "baseline_transaction_count": (
            anomaly.baseline_transaction_count
        ),
        "velocity_ratio": (
            decimal_text(
                anomaly.velocity_ratio
            )
            if anomaly.velocity_ratio
            is not None
            else None
        ),
        "repeated_amount_signal": (
            anomaly.repeated_amount_signal
        ),
        "velocity_signal": (
            anomaly.velocity_signal
        ),
        "repeated_transaction_ids": (
            anomaly
            .repeated_transaction_ids
        ),
        "analysis_as_of": datetime_text(
            anomaly.analysis_as_of
        ),
        "explanation_factors": (
            anomaly.explanation_factors
        ),
        "uncertainty": anomaly.uncertainty,
    }

    source_token = (
        datetime_text(
            anomaly.analysis_as_of
        )
        or "UNKNOWN"
    )

    return persist_alert(
        db=db,
        alert_type="ANOMALY_REVIEW",
        severity=anomaly.severity,
        agent=agent,
        provider=provider,
        scenario_id=request.scenario_id,
        source_reference=(
            "anomaly-detection:"
            f"{request.scenario_id or 'LIVE'}"
        ),
        source_token=source_token,
        template=template,
        evidence=evidence,
        confidence=anomaly.confidence,
        freshness_state=None,
    )


def generate_stale_data_alert(
    *,
    db: Session,
    request: AlertGenerationRequest,
    agent: Agent,
) -> AlertGenerationResponse:
    """Generate an alert from a stale provider balance."""

    if request.provider_code is None:
        raise AlertGenerationValidationError(
            "provider_code is required for "
            "STALE_DATA alerts."
        )

    provider = find_provider(
        db=db,
        provider_code=request.provider_code,
    )

    balance = db.scalar(
        select(ProviderBalance).where(
            ProviderBalance.agent_id
            == agent.id,
            ProviderBalance.provider_id
            == provider.id,
        )
    )

    if balance is None:
        raise AlertGenerationDataUnavailableError(
            "No provider balance was found for "
            f"Agent '{agent.code}' and provider "
            f"'{provider.code}'."
        )

    freshness_state = (
        balance.freshness_state
        or "missing"
    )

    if freshness_state == "fresh":
        return no_alert_response(
            alert_type="STALE_DATA",
            reason=(
                "The selected provider balance "
                "is currently marked as fresh."
            ),
        )

    severity_by_freshness = {
        "delayed": "MEDIUM",
        "conflicting": "HIGH",
        "missing": "HIGH",
    }

    severity = severity_by_freshness.get(
        freshness_state,
        "MEDIUM",
    )

    template = render_alert_template(
        alert_type="STALE_DATA",
        provider_name=(
            provider_display_name(
                provider
            )
        ),
    )

    evidence: dict[str, object] = {
        "provider_code": provider.code,
        "electronic_balance": decimal_text(
            as_decimal(
                balance.electronic_balance
            )
        ),
        "freshness_state": freshness_state,
        "last_update_at": datetime_text(
            balance.last_update_at
        ),
    }

    source_token = (
        datetime_text(
            balance.last_update_at
        )
        or freshness_state
    )

    return persist_alert(
        db=db,
        alert_type="STALE_DATA",
        severity=severity,
        agent=agent,
        provider=provider,
        scenario_id=request.scenario_id,
        source_reference=(
            "provider-balance:"
            f"{provider.code}"
        ),
        source_token=source_token,
        template=template,
        evidence=evidence,
        confidence=Decimal("0.6000"),
        freshness_state=freshness_state,
    )


def generate_serviceability_shortfall_alert(
    *,
    db: Session,
    request: AlertGenerationRequest,
    agent: Agent,
) -> AlertGenerationResponse:
    """Generate an alert for an immediate resource shortfall."""

    if request.provider_code is None:
        raise AlertGenerationValidationError(
            "provider_code is required for "
            "SERVICEABILITY_SHORTFALL alerts."
        )

    if request.transaction_type is None:
        raise AlertGenerationValidationError(
            "transaction_type is required for "
            "SERVICEABILITY_SHORTFALL alerts."
        )

    if request.requested_amount is None:
        raise AlertGenerationValidationError(
            "requested_amount is required for "
            "SERVICEABILITY_SHORTFALL alerts."
        )

    provider = find_provider(
        db=db,
        provider_code=request.provider_code,
    )

    freshness_state: str | None = None

    if request.transaction_type == "cash_in":
        balance = db.scalar(
            select(ProviderBalance).where(
                ProviderBalance.agent_id
                == agent.id,
                ProviderBalance.provider_id
                == provider.id,
            )
        )

        if balance is None:
            raise (
                AlertGenerationDataUnavailableError(
                    "No provider-float balance was "
                    "found for the selected Agent."
                )
            )

        available_balance = as_decimal(
            balance.electronic_balance
        )

        freshness_state = (
            balance.freshness_state
        )

        resource_name = (
            f"{provider_display_name(provider)} "
            "float"
        )

    else:
        position = db.scalar(
            select(AgentPosition).where(
                AgentPosition.agent_id
                == agent.id
            )
        )

        if position is None:
            raise (
                AlertGenerationDataUnavailableError(
                    "No shared physical-cash "
                    "position was found for the "
                    "selected Agent."
                )
            )

        available_balance = as_decimal(
            position.shared_cash
        )

        freshness_state = "fresh"
        resource_name = "Physical cash"

    shortfall = max(
        request.requested_amount
        - available_balance,
        ZERO,
    )

    if shortfall <= ZERO:
        return no_alert_response(
            alert_type=(
                "SERVICEABILITY_SHORTFALL"
            ),
            reason=(
                "The requested transaction is "
                "currently serviceable using the "
                "selected resource balance."
            ),
        )

    severity = (
        "CRITICAL"
        if available_balance <= ZERO
        else "HIGH"
    )

    template = render_alert_template(
        alert_type=(
            "SERVICEABILITY_SHORTFALL"
        ),
        resource_name=resource_name,
        shortfall_amount=shortfall,
    )

    evidence: dict[str, object] = {
        "provider_code": provider.code,
        "transaction_type": (
            request.transaction_type
        ),
        "resource_name": resource_name,
        "requested_amount": decimal_text(
            request.requested_amount
        ),
        "available_balance": decimal_text(
            available_balance
        ),
        "shortfall_amount": decimal_text(
            shortfall
        ),
        "serviceable": False,
    }

    source_token = ":".join(
        (
            request.transaction_type,
            decimal_text(
                request.requested_amount
            ),
            decimal_text(
                available_balance
            ),
        )
    )

    return persist_alert(
        db=db,
        alert_type=(
            "SERVICEABILITY_SHORTFALL"
        ),
        severity=severity,
        agent=agent,
        provider=provider,
        scenario_id=request.scenario_id,
        source_reference=(
            "serviceability-check:"
            f"{request.transaction_type}"
        ),
        source_token=source_token,
        template=template,
        evidence=evidence,
        confidence=Decimal("0.9500"),
        freshness_state=freshness_state,
    )


def generate_persisted_alert(
    *,
    db: Session,
    request: AlertGenerationRequest,
) -> AlertGenerationResponse:
    """Evaluate one source condition and persist its alert."""

    agent = find_agent(
        db=db,
        agent_code=request.agent_code,
    )

    if request.alert_type == "LIQUIDITY_RUNWAY":
        return generate_liquidity_runway_alert(
            db=db,
            request=request,
            agent=agent,
        )

    if request.alert_type == "ANOMALY_REVIEW":
        return generate_anomaly_review_alert(
            db=db,
            request=request,
            agent=agent,
        )

    if request.alert_type == "STALE_DATA":
        return generate_stale_data_alert(
            db=db,
            request=request,
            agent=agent,
        )

    if (
        request.alert_type
        == "SERVICEABILITY_SHORTFALL"
    ):
        return (
            generate_serviceability_shortfall_alert(
                db=db,
                request=request,
                agent=agent,
            )
        )

    raise AlertGenerationValidationError(
        "Unsupported alert type."
    )