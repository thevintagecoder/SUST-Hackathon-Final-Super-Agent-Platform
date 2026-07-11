"""Tests for persisted alert generation."""

from decimal import Decimal
from pathlib import Path

from sqlalchemy import (
    create_engine,
    select,
)
from sqlalchemy.orm import Session

from backend.app.data_loading.synthetic_loader import (
    load_synthetic_scenario,
)
from backend.app.db.base import Base
from backend.app.models import (
    Agent,
    Alert,
    AlertEvent,
    Provider,
    ProviderBalance,
)
from backend.app.schemas.alert import (
    AlertGenerationRequest,
)
from backend.app.services.alert_generation_service import (
    generate_persisted_alert,
)
from synthetic_data.generator import (
    generate_bundle,
)


def prepare_scenario_database(
    *,
    tmp_path: Path,
    scenario_id: str,
):
    """Create an isolated database with one scenario."""

    generated_directory = (
        tmp_path / "generated"
    )

    generate_bundle(
        output_directory=generated_directory,
        seed=42,
    )

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    with Session(engine) as db:
        load_synthetic_scenario(
            db=db,
            input_directory=(
                generated_directory
            ),
            scenario_id=scenario_id,
        )

    return engine


def test_liquidity_runway_alert_is_persisted_and_deduplicated(
    tmp_path: Path,
) -> None:
    """Forecast evidence should create only one alert."""

    engine = prepare_scenario_database(
        tmp_path=tmp_path,
        scenario_id="FORECAST-001",
    )

    request = AlertGenerationRequest(
        alert_type="LIQUIDITY_RUNWAY",
        agent_code="AGENT-SYL-001",
        provider_code="NAGAD_SIM",
        scenario_id="FORECAST-001",
        lookback_hours=6,
        warning_threshold_hours=Decimal(
            "8.00"
        ),
    )

    with Session(engine) as db:
        first_result = generate_persisted_alert(
            db=db,
            request=request,
        )

        second_result = generate_persisted_alert(
            db=db,
            request=request,
        )

        alerts = list(
            db.scalars(
                select(Alert)
            ).all()
        )

        events = list(
            db.scalars(
                select(AlertEvent)
            ).all()
        )

    assert first_result.condition_detected is True
    assert first_result.alert_created is True
    assert first_result.deduplicated is False

    assert second_result.condition_detected is True
    assert second_result.alert_created is False
    assert second_result.deduplicated is True

    assert len(alerts) == 1
    assert len(events) == 1

    assert alerts[0].alert_type == (
        "LIQUIDITY_RUNWAY"
    )

    assert alerts[0].severity == "HIGH"
    assert alerts[0].status == "OPEN"

    assert alerts[0].title_en
    assert alerts[0].title_bn
    assert alerts[0].title_bn_latn

    engine.dispose()


def test_anomaly_evidence_creates_review_alert(
    tmp_path: Path,
) -> None:
    """REPEATED-001 should create an anomaly alert."""

    engine = prepare_scenario_database(
        tmp_path=tmp_path,
        scenario_id="REPEATED-001",
    )

    with Session(engine) as db:
        result = generate_persisted_alert(
            db=db,
            request=AlertGenerationRequest(
                alert_type="ANOMALY_REVIEW",
                agent_code="AGENT-SYL-001",
                scenario_id="REPEATED-001",
            ),
        )

        saved_alert = db.scalar(
            select(Alert)
        )

    assert result.alert_created is True
    assert saved_alert is not None

    assert (
        saved_alert.alert_type
        == "ANOMALY_REVIEW"
    )

    assert saved_alert.severity in {
        "MEDIUM",
        "HIGH",
    }

    assert (
        saved_alert
        .human_review_required
        is True
    )

    assert (
        saved_alert
        .automatic_action_taken
        is False
    )

    assert "fraud" not in (
        saved_alert.message_en.lower()
    )

    engine.dispose()


def test_delayed_balance_creates_stale_data_alert(
    tmp_path: Path,
) -> None:
    """A non-fresh provider feed should create an alert."""

    engine = prepare_scenario_database(
        tmp_path=tmp_path,
        scenario_id="STALE-001",
    )

    with Session(engine) as db:
        stale_balance = db.scalar(
            select(ProviderBalance).where(
                ProviderBalance.freshness_state
                != "fresh"
            )
        )

        assert stale_balance is not None

        agent = db.get(
            Agent,
            stale_balance.agent_id,
        )

        provider = db.get(
            Provider,
            stale_balance.provider_id,
        )

        assert agent is not None
        assert provider is not None

        result = generate_persisted_alert(
            db=db,
            request=AlertGenerationRequest(
                alert_type="STALE_DATA",
                agent_code=agent.code,
                provider_code=provider.code,
                scenario_id="STALE-001",
            ),
        )

        saved_alert = db.scalar(
            select(Alert)
        )

    assert result.alert_created is True
    assert saved_alert is not None

    assert saved_alert.alert_type == "STALE_DATA"

    assert saved_alert.freshness_state != "fresh"

    engine.dispose()


def test_large_request_creates_shortfall_alert(
    tmp_path: Path,
) -> None:
    """An impossible cash-out should create a shortfall alert."""

    engine = prepare_scenario_database(
        tmp_path=tmp_path,
        scenario_id="SHORTAGE-001",
    )

    with Session(engine) as db:
        agent = db.scalar(
            select(Agent).order_by(
                Agent.id
            )
        )

        provider = db.scalar(
            select(Provider).order_by(
                Provider.id
            )
        )

        assert agent is not None
        assert provider is not None

        result = generate_persisted_alert(
            db=db,
            request=AlertGenerationRequest(
                alert_type=(
                    "SERVICEABILITY_SHORTFALL"
                ),
                agent_code=agent.code,
                provider_code=provider.code,
                scenario_id="SHORTAGE-001",
                transaction_type="cash_out",
                requested_amount=Decimal(
                    "1000000.00"
                ),
            ),
        )

        saved_alert = db.scalar(
            select(Alert)
        )

    assert result.alert_created is True
    assert saved_alert is not None

    assert (
        saved_alert.alert_type
        == "SERVICEABILITY_SHORTFALL"
    )

    assert (
        saved_alert.evidence[
            "serviceable"
        ]
        is False
    )

    assert Decimal(
        str(
            saved_alert.evidence[
                "shortfall_amount"
            ]
        )
    ) > Decimal("0.00")

    engine.dispose()


def test_fresh_balance_does_not_create_stale_alert(
    tmp_path: Path,
) -> None:
    """Fresh provider data should not produce an alert."""

    engine = prepare_scenario_database(
        tmp_path=tmp_path,
        scenario_id="NORMAL-001",
    )

    with Session(engine) as db:
        fresh_balance = db.scalar(
            select(ProviderBalance).where(
                ProviderBalance.freshness_state
                == "fresh"
            )
        )

        assert fresh_balance is not None

        agent = db.get(
            Agent,
            fresh_balance.agent_id,
        )

        provider = db.get(
            Provider,
            fresh_balance.provider_id,
        )

        assert agent is not None
        assert provider is not None

        result = generate_persisted_alert(
            db=db,
            request=AlertGenerationRequest(
                alert_type="STALE_DATA",
                agent_code=agent.code,
                provider_code=provider.code,
                scenario_id="NORMAL-001",
            ),
        )

        alert_count = len(
            list(
                db.scalars(
                    select(Alert)
                ).all()
            )
        )

    assert result.condition_detected is False
    assert result.alert_created is False
    assert result.alert_id is None
    assert alert_count == 0

    engine.dispose()