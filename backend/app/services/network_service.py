"""Business logic for Agent-to-Agent liquidity support discovery."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    Agent,
    AgentPosition,
    Provider,
    ProviderBalance,
)
from backend.app.schemas.liquidity import (
    ServiceabilityRequest,
)
from backend.app.schemas.network import (
    NetworkSupportRequest,
    NetworkSupportResponse,
    SupportCandidateResponse,
)
from backend.app.services.liquidity_service import (
    LiquidityDataUnavailableError,
    ServiceabilityNotFoundError,
    check_serviceability,
)


ZERO = Decimal("0.00")

PROVIDER_FLOAT_SAFETY_RESERVE = Decimal(
    "40000.00"
)
PHYSICAL_CASH_SAFETY_RESERVE = Decimal(
    "40000.00"
)

EARTH_RADIUS_KM = 6371.0088


class NetworkDataUnavailableError(Exception):
    """Raised when network-support data cannot be evaluated."""


def calculate_distance_km(
    first_latitude: Decimal | None,
    first_longitude: Decimal | None,
    second_latitude: Decimal | None,
    second_longitude: Decimal | None,
) -> Decimal | None:
    """Calculate approximate distance using the Haversine formula."""

    coordinates = (
        first_latitude,
        first_longitude,
        second_latitude,
        second_longitude,
    )

    if any(value is None for value in coordinates):
        return None

    first_latitude_radians = radians(
        float(first_latitude)
    )
    first_longitude_radians = radians(
        float(first_longitude)
    )
    second_latitude_radians = radians(
        float(second_latitude)
    )
    second_longitude_radians = radians(
        float(second_longitude)
    )

    latitude_difference = (
        second_latitude_radians
        - first_latitude_radians
    )
    longitude_difference = (
        second_longitude_radians
        - first_longitude_radians
    )

    haversine_value = (
        sin(latitude_difference / 2) ** 2
        + cos(first_latitude_radians)
        * cos(second_latitude_radians)
        * sin(longitude_difference / 2) ** 2
    )

    angular_distance = 2 * asin(
        sqrt(haversine_value)
    )

    distance = EARTH_RADIUS_KM * angular_distance

    return Decimal(
        str(round(distance, 2))
    )


def confidence_for_freshness(
    freshness_state: str,
) -> Decimal:
    """Return a transparent confidence value for feed freshness."""

    confidence_by_state = {
        "fresh": Decimal("0.95"),
        "delayed": Decimal("0.55"),
        "conflicting": Decimal("0.25"),
        "missing": Decimal("0.10"),
    }

    return confidence_by_state.get(
        freshness_state,
        Decimal("0.20"),
    )


def supportable_capacity(
    resource_balance: Decimal,
    safety_reserve: Decimal,
) -> Decimal:
    """Calculate liquidity that may be considered above reserve."""

    return max(
        resource_balance - safety_reserve,
        ZERO,
    )


def candidate_status(
    *,
    can_cover_shortfall: bool,
    freshness_state: str,
) -> str:
    """Classify whether a candidate should be recommended."""

    if not can_cover_shortfall:
        return "INSUFFICIENT_CAPACITY"

    if freshness_state != "fresh":
        return "REQUIRES_CONFIRMATION"

    return "RECOMMENDED"


def candidate_priority(
    candidate: SupportCandidateResponse,
) -> tuple[int, Decimal, Decimal]:
    """Return a stable ranking key for network candidates."""

    priority_by_status = {
        "RECOMMENDED": 0,
        "REQUIRES_CONFIRMATION": 1,
        "INSUFFICIENT_CAPACITY": 2,
    }

    distance = (
        candidate.distance_km
        if candidate.distance_km is not None
        else Decimal("999999.00")
    )

    return (
        priority_by_status[
            candidate.recommendation_status
        ],
        distance,
        -candidate.supportable_capacity,
    )


def build_candidate(
    *,
    agent: Agent,
    requesting_agent: Agent,
    resource_balance: Decimal,
    safety_reserve: Decimal,
    freshness_state: str,
    last_updated_at: datetime,
    shortfall: Decimal,
    max_distance_km: Decimal,
    transaction_type: str,
) -> SupportCandidateResponse | None:
    """Build one ranked support candidate."""

    distance_km = calculate_distance_km(
        requesting_agent.latitude,
        requesting_agent.longitude,
        agent.latitude,
        agent.longitude,
    )

    if (
        distance_km is not None
        and distance_km > max_distance_km
    ):
        return None

    available_capacity = supportable_capacity(
        resource_balance=resource_balance,
        safety_reserve=safety_reserve,
    )

    if available_capacity <= ZERO:
        return None

    can_cover_shortfall = (
        available_capacity >= shortfall
    )

    recommendation_status = candidate_status(
        can_cover_shortfall=can_cover_shortfall,
        freshness_state=freshness_state,
    )

    if transaction_type == "cash_in":
        recommended_mode = (
            "customer_referral_or_float_support_request"
        )
    else:
        recommended_mode = (
            "customer_referral_or_cash_support_request"
        )

    if recommendation_status == "RECOMMENDED":
        explanation = (
            "This Agent reports enough capacity above its "
            "safety reserve, and the relevant data is fresh."
        )

    elif (
        recommendation_status
        == "REQUIRES_CONFIRMATION"
    ):
        explanation = (
            "This Agent reports enough capacity, but the data "
            "is not fresh. Availability must be confirmed "
            "before making a referral or support request."
        )

    else:
        explanation = (
            "This Agent has some capacity above its safety "
            "reserve, but not enough to cover the full shortfall."
        )

    return SupportCandidateResponse(
        agent_code=agent.code,
        name=agent.name,
        area=agent.area,
        distance_km=distance_km,
        resource_balance=resource_balance,
        safety_reserve=safety_reserve,
        supportable_capacity=available_capacity,
        can_cover_shortfall=can_cover_shortfall,
        freshness_state=freshness_state,
        last_updated_at=last_updated_at,
        confidence=confidence_for_freshness(
            freshness_state
        ),
        recommendation_status=(
            recommendation_status
        ),
        recommended_mode=recommended_mode,
        explanation=explanation,
    )


def find_cash_in_candidates(
    *,
    db: Session,
    requesting_agent: Agent,
    provider: Provider,
    shortfall: Decimal,
    max_distance_km: Decimal,
) -> list[SupportCandidateResponse]:
    """Find Agents with provider-specific electronic capacity."""

    rows = db.execute(
        select(
            Agent,
            ProviderBalance,
        )
        .join(
            ProviderBalance,
            ProviderBalance.agent_id == Agent.id,
        )
        .where(
            Agent.id != requesting_agent.id,
            Agent.is_active.is_(True),
            ProviderBalance.provider_id
            == provider.id,
        )
    ).all()

    candidates: list[
        SupportCandidateResponse
    ] = []

    for agent, balance in rows:
        candidate = build_candidate(
            agent=agent,
            requesting_agent=requesting_agent,
            resource_balance=Decimal(
                balance.electronic_balance
            ),
            safety_reserve=(
                PROVIDER_FLOAT_SAFETY_RESERVE
            ),
            freshness_state=(
                balance.freshness_state
            ),
            last_updated_at=(
                balance.last_update_at
            ),
            shortfall=shortfall,
            max_distance_km=max_distance_km,
            transaction_type="cash_in",
        )

        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(
        key=candidate_priority
    )

    return candidates


def find_cash_out_candidates(
    *,
    db: Session,
    requesting_agent: Agent,
    shortfall: Decimal,
    max_distance_km: Decimal,
) -> list[SupportCandidateResponse]:
    """Find Agents with physical-cash capacity."""

    rows = db.execute(
        select(
            Agent,
            AgentPosition,
        )
        .join(
            AgentPosition,
            AgentPosition.agent_id == Agent.id,
        )
        .where(
            Agent.id != requesting_agent.id,
            Agent.is_active.is_(True),
        )
    ).all()

    candidates: list[
        SupportCandidateResponse
    ] = []

    for agent, position in rows:
        candidate = build_candidate(
            agent=agent,
            requesting_agent=requesting_agent,
            resource_balance=Decimal(
                position.shared_cash
            ),
            safety_reserve=(
                PHYSICAL_CASH_SAFETY_RESERVE
            ),
            freshness_state="fresh",
            last_updated_at=position.as_of,
            shortfall=shortfall,
            max_distance_km=max_distance_km,
            transaction_type="cash_out",
        )

        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(
        key=candidate_priority
    )

    return candidates


def determine_network_status(
    *,
    local_serviceable: bool,
    candidates: list[SupportCandidateResponse],
) -> str:
    """Classify the overall network-support result."""

    if local_serviceable:
        return "LOCAL_SERVICEABLE"

    if any(
        candidate.recommendation_status
        == "RECOMMENDED"
        for candidate in candidates
    ):
        return "NETWORK_SUPPORT_AVAILABLE"

    if any(
        candidate.recommendation_status
        == "REQUIRES_CONFIRMATION"
        for candidate in candidates
    ):
        return "CONFIRMATION_REQUIRED"

    return "NO_SUPPORT_FOUND"


def build_recommended_action(
    *,
    status: str,
) -> str:
    """Return a safe operational recommendation."""

    actions = {
        "LOCAL_SERVICEABLE": (
            "The requesting Agent appears able to serve the "
            "transaction locally. Confirm balances before acting."
        ),
        "NETWORK_SUPPORT_AVAILABLE": (
            "Review the recommended candidate and obtain human "
            "confirmation before referring the customer or "
            "creating a liquidity-support request."
        ),
        "CONFIRMATION_REQUIRED": (
            "A potentially capable Agent was found, but its data "
            "is not fresh. Confirm availability before taking action."
        ),
        "NO_SUPPORT_FOUND": (
            "No nearby Agent has confirmed capacity above its "
            "safety reserve. Escalate to Operations, a Super Agent, "
            "or an authorized provider coordinator."
        ),
    }

    return actions[status]


def find_network_support(
    db: Session,
    request: NetworkSupportRequest,
) -> NetworkSupportResponse:
    """Find nearby Agents that may support an unserviceable request."""

    requesting_agent = db.scalar(
        select(Agent).where(
            Agent.code
            == request.requesting_agent_code
        )
    )

    if requesting_agent is None:
        raise ServiceabilityNotFoundError(
            "Requesting Agent "
            f"'{request.requesting_agent_code}' "
            "was not found."
        )

    if not requesting_agent.is_active:
        raise NetworkDataUnavailableError(
            "The requesting Agent is inactive."
        )

    provider = db.scalar(
        select(Provider).where(
            Provider.code == request.provider_code
        )
    )

    if provider is None:
        raise ServiceabilityNotFoundError(
            f"Provider '{request.provider_code}' "
            "was not found."
        )

    local_result = check_serviceability(
        db=db,
        request=ServiceabilityRequest(
            agent_code=(
                request.requesting_agent_code
            ),
            provider_code=request.provider_code,
            transaction_type=(
                request.transaction_type
            ),
            amount=request.amount,
        ),
    )

    if request.transaction_type == "cash_in":
        safety_reserve = (
            PROVIDER_FLOAT_SAFETY_RESERVE
        )
    else:
        safety_reserve = (
            PHYSICAL_CASH_SAFETY_RESERVE
        )

    candidates: list[
        SupportCandidateResponse
    ] = []

    if not local_result.serviceable:
        if request.transaction_type == "cash_in":
            candidates = find_cash_in_candidates(
                db=db,
                requesting_agent=(
                    requesting_agent
                ),
                provider=provider,
                shortfall=local_result.shortfall,
                max_distance_km=(
                    request.max_distance_km
                ),
            )
        else:
            candidates = find_cash_out_candidates(
                db=db,
                requesting_agent=(
                    requesting_agent
                ),
                shortfall=local_result.shortfall,
                max_distance_km=(
                    request.max_distance_km
                ),
            )

    status = determine_network_status(
        local_serviceable=(
            local_result.serviceable
        ),
        candidates=candidates,
    )

    explanation = (
        "Candidates are ranked using the correct liquidity "
        "resource, capacity above a safety reserve, feed "
        "freshness, and approximate distance. Results are "
        "recommendations only and do not transfer money."
    )

    return NetworkSupportResponse(
        status=status,
        requesting_agent_code=(
            requesting_agent.code
        ),
        provider_code=provider.code,
        transaction_type=(
            request.transaction_type
        ),
        requested_amount=request.amount,
        local_available_amount=(
            local_result.available_amount
        ),
        shortfall=local_result.shortfall,
        required_resource=(
            local_result.required_resource
        ),
        safety_reserve=safety_reserve,
        local_serviceable=(
            local_result.serviceable
        ),
        candidates=candidates,
        explanation=explanation,
        recommended_action=(
            build_recommended_action(
                status=status
            )
        ),
        human_confirmation_required=True,
    )