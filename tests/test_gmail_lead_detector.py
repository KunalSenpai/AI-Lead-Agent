from app.services.gmail_lead_detector import (
    is_potential_lead
)


def test_real_sales_enquiry_is_detected():

    email = {
        "email": "priya@techflow.com",
        "subject": "Interested in automating lead qualification",
        "body": (
            "We receive 300 enquiries every month "
            "and would like to discuss automation."
        ),
    }

    assert is_potential_lead(email) is True


def test_delivery_failure_is_ignored():

    email = {
        "email": "mailer-daemon@googlemail.com",
        "subject": "Delivery Status Notification (Failure)",
        "body": "Address not found.",
    }

    assert is_potential_lead(email) is False


def test_own_email_is_ignored():

    email = {
        "email": "kunalsenpai69@gmail.com",
        "subject": "Interested in automation",
        "body": "Let's discuss your sales solution.",
    }

    assert is_potential_lead(email) is False


def test_generic_email_is_ignored():

    email = {
        "email": "person@example.com",
        "subject": "Hello",
        "body": "Hope you're having a good day.",
    }

    assert is_potential_lead(email) is False


def test_promotional_email_is_ignored():

    email = {
        "email": "support@zendrop.com",
        "subject": "Last chance to join the Build Your Store Challenge!",
        "body": (
            "I'm kicking things off in 41 minutes. "
            "Join the challenge. It's free."
        ),
    }

    assert is_potential_lead(email) is False

def test_promotion_email_is_ignored():

    email = {
        "email": "jared@zendrop.com",
        "subject": "Summer Promo",
        "body": (
            "Upgrade to Zendrop Plus annual today "
            "and get a custom AI-built store."
        ),
    }

    assert is_potential_lead(email) is False