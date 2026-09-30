from app.logging_config import scrub_event
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd_and_payment_card() -> None:
    out = scrub_text("CCCD 012345678901; card 4111 1111 1111 1111")
    assert "012345678901" not in out
    assert "4111 1111 1111 1111" not in out
    assert "REDACTED_CCCD" in out
    assert "REDACTED_CREDIT_CARD" in out


def test_log_processor_scrubs_context_and_nested_payload() -> None:
    event = {
        "session_id": "student@example.invalid",
        "payload": {
            "details": ["Call 0901234567", {"identity": "012345678901"}],
        },
    }

    scrubbed = scrub_event(None, "info", event)

    assert scrubbed["session_id"] == "[REDACTED_EMAIL]"
    assert scrubbed["payload"]["details"] == [
        "Call [REDACTED_PHONE_VN]",
        {"identity": "[REDACTED_CCCD]"},
    ]
