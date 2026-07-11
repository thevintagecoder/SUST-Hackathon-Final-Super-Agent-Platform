"""Responsible multilingual templates for explainable alerts."""

from decimal import Decimal

from backend.app.schemas.alert import (
    AlertType,
    LocalizedAlertText,
    RenderedAlertTemplate,
)


TWO_DECIMAL_PLACES = Decimal("0.01")

BANGLA_DIGITS = str.maketrans(
    "0123456789",
    "০১২৩৪৫৬৭৮৯",
)


class AlertTemplateError(ValueError):
    """Raised when required alert-template data is missing."""


def format_decimal(
    value: Decimal,
) -> str:
    """Format a decimal value using two decimal places."""

    return format(
        value.quantize(
            TWO_DECIMAL_PLACES
        ),
        ".2f",
    )


def to_bangla_digits(
    value: str,
) -> str:
    """Convert Latin digits to Bangla digits."""

    return value.translate(
        BANGLA_DIGITS
    )


def require_text(
    *,
    value: str | None,
    field_name: str,
    alert_type: AlertType,
) -> str:
    """Return required non-empty template text."""

    if (
        value is None
        or not value.strip()
    ):
        raise AlertTemplateError(
            f"{field_name} is required for "
            f"{alert_type} alerts."
        )

    return value.strip()


def require_decimal(
    *,
    value: Decimal | None,
    field_name: str,
    alert_type: AlertType,
) -> Decimal:
    """Return a required nonnegative decimal value."""

    if value is None:
        raise AlertTemplateError(
            f"{field_name} is required for "
            f"{alert_type} alerts."
        )

    if value < Decimal("0.00"):
        raise AlertTemplateError(
            f"{field_name} cannot be negative."
        )

    return value


def build_liquidity_runway_template(
    *,
    provider_name: str | None,
    runway_hours: Decimal | None,
) -> RenderedAlertTemplate:
    """Build a provider-float runway warning."""

    alert_type: AlertType = (
        "LIQUIDITY_RUNWAY"
    )

    provider = require_text(
        value=provider_name,
        field_name="provider_name",
        alert_type=alert_type,
    )

    runway = require_decimal(
        value=runway_hours,
        field_name="runway_hours",
        alert_type=alert_type,
    )

    runway_text = format_decimal(
        runway
    )

    bangla_runway_text = (
        to_bangla_digits(
            runway_text
        )
    )

    return RenderedAlertTemplate(
        alert_type=alert_type,
        title=LocalizedAlertText(
            en=(
                f"{provider} float may become "
                "insufficient soon"
            ),
            bn=(
                f"{provider} ফ্লোট শীঘ্রই "
                "অপর্যাপ্ত হতে পারে"
            ),
            bn_latn=(
                f"{provider} float shighroi "
                "oporjapto hote pare"
            ),
        ),
        message=LocalizedAlertText(
            en=(
                "Recent activity indicates approximately "
                f"{runway_text} hours of runway before the "
                "prototype safety threshold may be reached."
            ),
            bn=(
                "সাম্প্রতিক কার্যক্রম অনুযায়ী প্রোটোটাইপ "
                "নিরাপত্তা সীমায় পৌঁছানোর আগে আনুমানিক "
                f"{bangla_runway_text} ঘণ্টা সময় থাকতে পারে।"
            ),
            bn_latn=(
                "Shamprotik activity onujayi prototype "
                "safety threshold-e pouchhanor age "
                f"anumaanik {runway_text} ghonta "
                "shomoy thakte pare."
            ),
        ),
        next_step=LocalizedAlertText(
            en=(
                "Review the current balance and consider "
                "a human-approved support request."
            ),
            bn=(
                "বর্তমান ব্যালেন্স পর্যালোচনা করুন এবং "
                "মানব-অনুমোদিত সহায়তা অনুরোধ বিবেচনা করুন।"
            ),
            bn_latn=(
                "Bortoman balance review korun ebong "
                "human-approved support request "
                "bichar korun."
            ),
        ),
    )


def build_anomaly_review_template() -> (
    RenderedAlertTemplate
):
    """Build a responsible unusual-activity alert."""

    return RenderedAlertTemplate(
        alert_type="ANOMALY_REVIEW",
        title=LocalizedAlertText(
            en=(
                "Unusual transaction pattern "
                "requires review"
            ),
            bn=(
                "অস্বাভাবিক লেনদেনের ধরন "
                "পর্যালোচনা প্রয়োজন"
            ),
            bn_latn=(
                "Oshabhabik transaction pattern "
                "review proyojon"
            ),
        ),
        message=LocalizedAlertText(
            en=(
                "Repeated or near-identical transaction "
                "amounts, increased transaction velocity, "
                "or both were observed. The pattern may "
                "have a legitimate explanation."
            ),
            bn=(
                "একই বা কাছাকাছি পরিমাণের একাধিক লেনদেন, "
                "লেনদেনের গতি বৃদ্ধি, অথবা উভয়ই দেখা গেছে। "
                "এই ধরনের কার্যক্রমের বৈধ ব্যাখ্যা থাকতে পারে।"
            ),
            bn_latn=(
                "Eki ba kachakachi amount-er ekadhik "
                "transaction, transaction velocity briddhi, "
                "othoba ubhoyi dekha geche. Ei pattern-er "
                "boidho byakkha thakte pare."
            ),
        ),
        next_step=LocalizedAlertText(
            en=(
                "Ask the assigned operations owner to "
                "review the transactions, verify data "
                "freshness, and record an explanation."
            ),
            bn=(
                "দায়িত্বপ্রাপ্ত অপারেশনস কর্মকর্তাকে "
                "লেনদেন পর্যালোচনা, তথ্যের সতেজতা যাচাই "
                "এবং একটি ব্যাখ্যা নথিভুক্ত করতে বলুন।"
            ),
            bn_latn=(
                "Assigned operations owner-ke transaction "
                "review, data freshness verify, ebong "
                "ekti byakkha record korte bolun."
            ),
        ),
    )


def build_stale_data_template(
    *,
    provider_name: str | None,
) -> RenderedAlertTemplate:
    """Build a delayed provider-feed warning."""

    alert_type: AlertType = "STALE_DATA"

    provider = require_text(
        value=provider_name,
        field_name="provider_name",
        alert_type=alert_type,
    )

    return RenderedAlertTemplate(
        alert_type=alert_type,
        title=LocalizedAlertText(
            en=(
                f"{provider} balance data is delayed"
            ),
            bn=(
                f"{provider} ব্যালেন্স তথ্য বিলম্বিত"
            ),
            bn_latn=(
                f"{provider} balance data delayed"
            ),
        ),
        message=LocalizedAlertText(
            en=(
                "The latest provider balance update is "
                "delayed. Current serviceability and "
                "available capacity may be uncertain."
            ),
            bn=(
                "সর্বশেষ প্রোভাইডার ব্যালেন্স তথ্য বিলম্বিত। "
                "বর্তমান সেবা সক্ষমতা এবং প্রাপ্য ধারণক্ষমতা "
                "অনিশ্চিত হতে পারে।"
            ),
            bn_latn=(
                "Shorboshesh provider balance update "
                "delayed. Bortoman serviceability ebong "
                "available capacity onishchit hote pare."
            ),
        ),
        next_step=LocalizedAlertText(
            en=(
                "Verify the provider feed before making "
                "a liquidity or support decision."
            ),
            bn=(
                "লিকুইডিটি বা সহায়তার সিদ্ধান্ত নেওয়ার "
                "আগে প্রোভাইডার তথ্য যাচাই করুন।"
            ),
            bn_latn=(
                "Liquidity ba support decision neyar age "
                "provider feed verify korun."
            ),
        ),
    )


def build_serviceability_shortfall_template(
    *,
    resource_name: str | None,
    shortfall_amount: Decimal | None,
) -> RenderedAlertTemplate:
    """Build a resource-shortfall warning."""

    alert_type: AlertType = (
        "SERVICEABILITY_SHORTFALL"
    )

    resource = require_text(
        value=resource_name,
        field_name="resource_name",
        alert_type=alert_type,
    )

    shortfall = require_decimal(
        value=shortfall_amount,
        field_name="shortfall_amount",
        alert_type=alert_type,
    )

    shortfall_text = format_decimal(
        shortfall
    )

    bangla_shortfall_text = (
        to_bangla_digits(
            shortfall_text
        )
    )

    return RenderedAlertTemplate(
        alert_type=alert_type,
        title=LocalizedAlertText(
            en=(
                f"{resource} is insufficient "
                "for the requested transaction"
            ),
            bn=(
                f"অনুরোধকৃত লেনদেনের জন্য "
                f"{resource} অপর্যাপ্ত"
            ),
            bn_latn=(
                f"Requested transaction-er jonno "
                f"{resource} oporjapto"
            ),
        ),
        message=LocalizedAlertText(
            en=(
                "The estimated resource shortfall is "
                f"৳{shortfall_text}. The transaction "
                "cannot currently be confirmed as "
                "serviceable."
            ),
            bn=(
                "আনুমানিক সম্পদ ঘাটতি "
                f"৳{bangla_shortfall_text}। লেনদেনটি "
                "বর্তমানে সম্পন্ন করা সম্ভব বলে নিশ্চিত "
                "করা যাচ্ছে না।"
            ),
            bn_latn=(
                "Anumaanik resource shortfall "
                f"৳{shortfall_text}. Transaction-ti "
                "bortomane serviceable bole confirm "
                "kora jacche na."
            ),
        ),
        next_step=LocalizedAlertText(
            en=(
                "Review nearby support options or refer "
                "the customer through a human-approved "
                "coordination process."
            ),
            bn=(
                "মানব-অনুমোদিত সমন্বয় প্রক্রিয়ার মাধ্যমে "
                "নিকটবর্তী সহায়তার বিকল্প পর্যালোচনা করুন "
                "অথবা গ্রাহককে অন্য এজেন্টের কাছে পাঠান।"
            ),
            bn_latn=(
                "Human-approved coordination process-er "
                "madhyome nearby support option review "
                "korun othoba customer-ke onno Agent-er "
                "kache refer korun."
            ),
        ),
    )


def render_alert_template(
    *,
    alert_type: AlertType,
    provider_name: str | None = None,
    runway_hours: Decimal | None = None,
    resource_name: str | None = None,
    shortfall_amount: Decimal | None = None,
) -> RenderedAlertTemplate:
    """Render one alert in all supported languages."""

    if alert_type == "LIQUIDITY_RUNWAY":
        return build_liquidity_runway_template(
            provider_name=provider_name,
            runway_hours=runway_hours,
        )

    if alert_type == "ANOMALY_REVIEW":
        return build_anomaly_review_template()

    if alert_type == "STALE_DATA":
        return build_stale_data_template(
            provider_name=provider_name,
        )

    if (
        alert_type
        == "SERVICEABILITY_SHORTFALL"
    ):
        return (
            build_serviceability_shortfall_template(
                resource_name=resource_name,
                shortfall_amount=shortfall_amount,
            )
        )

    raise AlertTemplateError(
        f"Unsupported alert type: {alert_type}."
    )