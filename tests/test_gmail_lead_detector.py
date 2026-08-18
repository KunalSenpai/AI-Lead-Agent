from app.services.gmail_lead_detector import (
    is_potential_lead,
)


# =========================================================
# Helper
# =========================================================

def make_email(
    email="john@example.com",
    subject="",
    body="",
):
    return {
        "email": email,
        "subject": subject,
        "body": body,
    }


# =========================================================
# Real lead cases
# =========================================================

def test_real_sales_enquiry_is_detected():

    email = make_email(
        email="john@acme.com",
        subject="Interested in your services",
        body=(
            "We are looking for a solution to automate "
            "our sales workflow. Could we schedule a demo?"
        ),
    )

    assert is_potential_lead(email) is True


def test_pricing_enquiry_is_detected():

    email = make_email(
        email="buyer@company.com",
        subject="Pricing enquiry",
        body=(
            "We are interested in your solution and "
            "would like to know your pricing."
        ),
    )

    assert is_potential_lead(email) is True


def test_demo_request_is_detected():

    email = make_email(
        email="prospect@company.com",
        subject="Request for a demo",
        body=(
            "We would like to schedule a demo and "
            "discuss how your solution could help our team."
        ),
    )

    assert is_potential_lead(email) is True


def test_business_automation_problem_is_detected():

    email = make_email(
        email="ceo@company.com",
        subject="Looking for a solution",
        body=(
            "We are looking for a solution to automate "
            "our lead qualification and sales workflow."
        ),
    )

    assert is_potential_lead(email) is True


def test_quote_request_is_detected():

    email = make_email(
        email="buyer@company.com",
        subject="Request for quotation",
        body=(
            "Could you provide a quote for your services "
            "for our company?"
        ),
    )

    assert is_potential_lead(email) is True


# =========================================================
# Verification / security emails
# =========================================================

def test_email_verification_is_not_a_lead():

    email = make_email(
        email="accounts@example.com",
        subject="Verify your email address",
        body=(
            "Please click the verification link "
            "to confirm your email address."
        ),
    )

    assert is_potential_lead(email) is False


def test_account_verification_is_not_a_lead():

    email = make_email(
        email="accounts@example.com",
        subject="Verify your account",
        body=(
            "Please verify your account to continue "
            "using the service."
        ),
    )

    assert is_potential_lead(email) is False


def test_verification_code_is_not_a_lead():

    email = make_email(
        email="security@example.com",
        subject="Your verification code",
        body=(
            "Your verification code is 123456."
        ),
    )

    assert is_potential_lead(email) is False


def test_otp_email_is_not_a_lead():

    email = make_email(
        email="security@example.com",
        subject="Your one-time password",
        body=(
            "Your one-time password is 123456."
        ),
    )

    assert is_potential_lead(email) is False


def test_password_reset_is_not_a_lead():

    email = make_email(
        email="security@example.com",
        subject="Reset your password",
        body=(
            "Click the link below to reset your password."
        ),
    )

    assert is_potential_lead(email) is False


def test_security_alert_is_not_a_lead():

    email = make_email(
        email="security@example.com",
        subject="Security alert",
        body=(
            "We detected a new sign-in attempt "
            "on your account."
        ),
    )

    assert is_potential_lead(email) is False


# =========================================================
# Transactional emails
# =========================================================

def test_receipt_is_not_a_lead():

    email = make_email(
        email="billing@example.com",
        subject="Your receipt",
        body=(
            "Thank you for your purchase. "
            "Your receipt is attached."
        ),
    )

    assert is_potential_lead(email) is False


def test_payment_confirmation_is_not_a_lead():

    email = make_email(
        email="billing@example.com",
        subject="Payment confirmation",
        body=(
            "Your payment has been received successfully."
        ),
    )

    assert is_potential_lead(email) is False


def test_order_confirmation_is_not_a_lead():

    email = make_email(
        email="orders@example.com",
        subject="Order confirmation",
        body=(
            "Your order has been confirmed and "
            "will be processed shortly."
        ),
    )

    assert is_potential_lead(email) is False


def test_invoice_is_not_a_lead():

    email = make_email(
        email="billing@example.com",
        subject="Invoice #12345",
        body=(
            "Your invoice for this month's subscription "
            "is now available."
        ),
    )

    assert is_potential_lead(email) is False


# =========================================================
# Marketing emails
# =========================================================

def test_newsletter_is_not_a_lead():

    email = make_email(
        email="newsletter@example.com",
        subject="Our monthly newsletter",
        body=(
            "Here are our latest updates. "
            "Unsubscribe at any time."
        ),
    )

    assert is_potential_lead(email) is False


def test_promotional_email_is_not_a_lead():

    email = make_email(
        email="marketing@example.com",
        subject="Special offer",
        body=(
            "Get 50% off today. "
            "Limited time offer. "
            "Unsubscribe here."
        ),
    )

    assert is_potential_lead(email) is False


def test_discount_email_is_not_a_lead():

    email = make_email(
        email="offers@example.com",
        subject="Exclusive discount",
        body=(
            "Save 30% today with our exclusive offer."
        ),
    )

    assert is_potential_lead(email) is False


# =========================================================
# Automated senders
# =========================================================

def test_no_reply_sender_is_not_a_lead():

    email = make_email(
        email="no-reply@example.com",
        subject="Interested in our services",
        body=(
            "Please review the information "
            "in your account."
        ),
    )

    assert is_potential_lead(email) is False


def test_noreply_sender_is_not_a_lead():

    email = make_email(
        email="noreply@example.com",
        subject="Pricing information",
        body=(
            "This is an automated notification "
            "about your account."
        ),
    )

    assert is_potential_lead(email) is False


def test_notifications_sender_is_not_a_lead():

    email = make_email(
        email="notifications@example.com",
        subject="Your account update",
        body=(
            "This is an automated notification."
        ),
    )

    assert is_potential_lead(email) is False


# =========================================================
# Ignored sender domains
# =========================================================

def test_google_sender_is_not_a_lead():

    email = make_email(
        email="someone@google.com",
        subject="Interested in your services",
        body=(
            "We would like to discuss your solution."
        ),
    )

    assert is_potential_lead(email) is False


def test_googlemail_sender_is_not_a_lead():

    email = make_email(
        email="someone@googlemail.com",
        subject="Pricing enquiry",
        body=(
            "We would like to learn more."
        ),
    )

    assert is_potential_lead(email) is False


# =========================================================
# Own email
# =========================================================

def test_own_email_is_not_a_lead(monkeypatch):

    monkeypatch.setenv(
        "GMAIL_USER_EMAIL",
        "me@example.com",
    )

    # Reloading the module is normally unnecessary if the
    # existing test suite already configures this value.
    # This test simply verifies the expected data shape.
    email = make_email(
        email="me@example.com",
        subject="Interested in your services",
        body=(
            "I would like to discuss your solution."
        ),
    )

    # The module reads GMAIL_USER_EMAIL at import time.
    # Therefore this assertion is only valid if the test
    # environment already has the same configured address.
    #
    # If your existing test suite handles this differently,
    # keep that existing own-email test instead.
    from app.services import gmail_lead_detector

    original = gmail_lead_detector.GMAIL_USER_EMAIL

    try:

        gmail_lead_detector.GMAIL_USER_EMAIL = (
            "me@example.com"
        )

        assert is_potential_lead(email) is False

    finally:

        gmail_lead_detector.GMAIL_USER_EMAIL = original


# =========================================================
# Empty / invalid emails
# =========================================================

def test_missing_sender_is_not_a_lead():

    email = make_email(
        email="",
        subject="Interested in your services",
        body="We would like a demo.",
    )

    assert is_potential_lead(email) is False


def test_missing_email_field_is_not_a_lead():

    email = {
        "subject": "Interested in your services",
        "body": "We would like a demo.",
    }

    assert is_potential_lead(email) is False


def test_empty_email_is_not_a_lead():

    email = make_email(
        email="prospect@example.com",
        subject="",
        body="",
    )

    assert is_potential_lead(email) is False


# =========================================================
# Weak keyword protection
# =========================================================

def test_services_alone_is_not_a_lead():

    email = make_email(
        email="person@example.com",
        subject="Services",
        body=(
            "Here is some information about "
            "our services."
        ),
    )

    assert is_potential_lead(email) is False


def test_solution_alone_is_not_a_lead():

    email = make_email(
        email="person@example.com",
        subject="Our solution",
        body=(
            "Please find information about "
            "our solution."
        ),
    )

    assert is_potential_lead(email) is False


def test_sales_alone_is_not_a_lead():

    email = make_email(
        email="person@example.com",
        subject="Sales update",
        body=(
            "Here is the latest sales information."
        ),
    )

    assert is_potential_lead(email) is False


# =========================================================
# Mixed cases
# =========================================================

def test_real_lead_with_generic_keywords_and_business_context():

    email = make_email(
        email="founder@startup.com",
        subject="Looking for sales automation",
        body=(
            "We have a 30-person sales team and "
            "receive hundreds of enquiries every month. "
            "We are interested in your services and "
            "would like to discuss pricing."
        ),
    )

    assert is_potential_lead(email) is True


def test_marketing_email_with_lead_keyword_is_not_a_lead():

    email = make_email(
        email="marketing@example.com",
        subject="Special offer on our services",
        body=(
            "Get our services at a 50% discount. "
            "Limited time offer. Unsubscribe here."
        ),
    )

    assert is_potential_lead(email) is False


def test_verification_email_with_lead_keyword_is_not_a_lead():

    email = make_email(
        email="security@example.com",
        subject="Verify your account",
        body=(
            "Please verify your account to access "
            "our services."
        ),
    )

    assert is_potential_lead(email) is False