"""Business logic for real-time transaction serviceability."""

from decimal import Decimal

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
    ServiceabilityResponse,
)


ZERO = Decimal("0.00")


class ServiceabilityNotFoundError(Exception):
    """Raised when a requested Agent or provider does not exist."""


class LiquidityDataUnavailableError(Exception):
    """Raised when the required liquidity position is unavailable."""


def determine_status(
    available_amount: Decimal,
    requested_amount: Decimal,
) -> tuple[bool, str]:
    """Classify whether the full transaction can be served."""

    if available_amount >= requested_amount:
        return True, "SERVICEABLE"

    if available_amount > ZERO:
        return False, "PARTIALLY_SERVICEABLE"

    return False, "NOT_SERVICEABLE"


def build_cash_in_recommendations(
    provider_code: str,
    serviceable: bool,
) -> list[str]:
    """Return safe recommendations for a cash-in request."""

    if serviceable:
        return [
            (
                "The requested provider has enough electronic "
                "float for the full transaction."
            ),
            (
                "Confirm the current balance before completing "
                "the transaction."
            ),
        ]

    return [
        "Do not accept the full transaction yet.",
        (
            f"Request an authorized {provider_code} electronic-"
            "float replenishment."
        ),
        (
            "Consider referring the customer to another authorized "
            "Agent with confirmed capacity."
        ),
        (
            "A partial transaction should only be considered when "
            "permitted and accepted by the customer."
        ),
    ]


def build_cash_out_recommendations(
    serviceable: bool,
) -> list[str]:
    """Return safe recommendations for a cash-out request."""

    if serviceable:
        return [
            (
                "The Agent currently has enough physical cash "
                "for the full transaction."
            ),
            (
                "Confirm the physical cash position before "
                "completing the transaction."
            ),
        ]

    return [
        "Do not accept the full cash-out request yet.",
        (
            "Request an authorized physical-cash replenishment "
            "or escalate to the responsible coordinator."
        ),
        (
            "Consider referring the customer to another authorized "
            "Agent with confirmed physical-cash capacity."
        ),
        (
            "A partial transaction should only be considered when "
            "permitted and accepted by the customer."
        ),
    ]


def check_serviceability(
    db: Session,
    request: ServiceabilityRequest,
) -> ServiceabilityResponse:
    """Check whether one Agent can serve a customer request."""

    agent = db.scalar(
        select(Agent).where(
            Agent.code == request.agent_code
        )
    )

    if agent is None:
        raise ServiceabilityNotFoundError(
            f"Agent '{request.agent_code}' was not found."
        )

    provider = db.scalar(
        select(Provider).where(
            Provider.code == request.provider_code
        )
    )

    if provider is None:
        raise ServiceabilityNotFoundError(
            f"Provider '{request.provider_code}' was not found."
        )

    if request.transaction_type == "cash_in":
        balance = db.scalar(
            select(ProviderBalance).where(
                ProviderBalance.agent_id == agent.id,
                ProviderBalance.provider_id == provider.id,
            )
        )

        if balance is None:
            raise LiquidityDataUnavailableError(
                "The requested provider balance is unavailable "
                "for this Agent."
            )

        available_amount = Decimal(
            balance.electronic_balance
        )
        required_resource = (
            f"{provider.code} electronic float"
        )

        serviceable, status = determine_status(
            available_amount=available_amount,
            requested_amount=request.amount,
        )

        explanation = (
            "A cash-in transaction consumes electronic float "
            f"from the requested provider, {provider.code}. "
            "Balances from other providers cannot be substituted."
        )

        recommended_actions = (
            build_cash_in_recommendations(
                provider_code=provider.code,
                serviceable=serviceable,
            )
        )

    else:
        position = db.scalar(
            select(AgentPosition).where(
                AgentPosition.agent_id == agent.id
            )
        )

        if position is None:
            raise LiquidityDataUnavailableError(
                "The shared physical-cash position is unavailable "
                "for this Agent."
            )

        available_amount = Decimal(
            position.shared_cash
        )
        required_resource = "shared physical cash"

        serviceable, status = determine_status(
            available_amount=available_amount,
            requested_amount=request.amount,
        )

        explanation = (
            "A cash-out transaction requires physical cash. "
            "The customer's electronic transfer may increase the "
            "Agent's provider balance, but it does not replace the "
            "physical notes required for the customer."
        )

        recommended_actions = (
            build_cash_out_recommendations(
                serviceable=serviceable,
            )
        )

    shortfall = max(
        request.amount - available_amount,
        ZERO,
    )

    return ServiceabilityResponse(
        serviceable=serviceable,
        status=status,
        agent_code=agent.code,
        provider_code=provider.code,
        transaction_type=request.transaction_type,
        requested_amount=request.amount,
        available_amount=available_amount,
        shortfall=shortfall,
        required_resource=required_resource,
        explanation=explanation,
        recommended_actions=recommended_actions,
        human_confirmation_required=True,
    )