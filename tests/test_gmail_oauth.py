import time

import pytest

from app.tools.gmail_oauth import (
    create_oauth_state,
    verify_oauth_state,
)


def test_create_and_verify_oauth_state(
    monkeypatch,
):
    monkeypatch.setenv(
        "GMAIL_OAUTH_STATE_SECRET",
        "test-secret-for-oauth-state",
    )

    state = create_oauth_state(
        user_id="test-user-id",
    )

    assert state
    assert state != "test-user-id"

    user_id = verify_oauth_state(
        state
    )

    assert user_id == "test-user-id"


def test_tampered_oauth_state_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "GMAIL_OAUTH_STATE_SECRET",
        "test-secret-for-oauth-state",
    )

    state = create_oauth_state(
        user_id="test-user-id",
    )

    payload, signature = state.split(
        ".",
        1,
    )

    tampered_state = (
        payload + "tampered"
        + "."
        + signature
    )

    with pytest.raises(
        ValueError,
        match="Invalid OAuth state",
    ):
        verify_oauth_state(
            tampered_state
        )


def test_wrong_secret_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "GMAIL_OAUTH_STATE_SECRET",
        "correct-secret",
    )

    state = create_oauth_state(
        user_id="test-user-id",
    )

    monkeypatch.setenv(
        "GMAIL_OAUTH_STATE_SECRET",
        "wrong-secret",
    )

    with pytest.raises(
        ValueError,
        match="Invalid OAuth state signature",
    ):
        verify_oauth_state(
            state
        )


def test_expired_oauth_state_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "GMAIL_OAUTH_STATE_SECRET",
        "test-secret-for-oauth-state",
    )

    monkeypatch.setattr(
        "app.tools.gmail_oauth.time.time",
        lambda: 1_000_000,
    )

    state = create_oauth_state(
        user_id="test-user-id",
    )

    monkeypatch.setattr(
        "app.tools.gmail_oauth.time.time",
        lambda: 1_000_601,
    )

    with pytest.raises(
        ValueError,
        match="OAuth state has expired",
    ):
        verify_oauth_state(
            state
        )


def test_missing_oauth_state_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "GMAIL_OAUTH_STATE_SECRET",
        "test-secret-for-oauth-state",
    )

    with pytest.raises(
        ValueError,
        match="OAuth state is missing",
    ):
        verify_oauth_state(
            ""
        )