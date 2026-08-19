import base64
import hashlib
import hmac
import json
import os
import secrets
import time


OAUTH_STATE_TTL_SECONDS = 600


def _get_oauth_state_secret() -> bytes:
    secret = os.getenv(
        "GMAIL_OAUTH_STATE_SECRET"
    )

    if not secret:
        raise RuntimeError(
            "GMAIL_OAUTH_STATE_SECRET is not configured"
        )

    return secret.encode("utf-8")


def create_oauth_state(
    user_id: str,
) -> str:
    """
    Create a short-lived, signed OAuth state value.

    The state contains the application user ID,
    an expiration timestamp, and a random nonce.
    """

    payload = {
        "user_id": user_id,
        "expires_at": int(
            time.time()
        ) + OAUTH_STATE_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(32),
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    encoded_payload = (
        base64.urlsafe_b64encode(
            payload_bytes
        )
        .decode("ascii")
        .rstrip("=")
    )

    signature = hmac.new(
        _get_oauth_state_secret(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()

    encoded_signature = (
        base64.urlsafe_b64encode(
            signature
        )
        .decode("ascii")
        .rstrip("=")
    )

    return (
        f"{encoded_payload}.{encoded_signature}"
    )


def verify_oauth_state(
    state: str,
) -> str:
    """
    Validate an OAuth state and return the
    authenticated application user ID.

    Raises ValueError when the state is invalid,
    tampered with, or expired.
    """

    if not state:
        raise ValueError(
            "OAuth state is missing"
        )

    try:
        encoded_payload, encoded_signature = (
            state.split(".", 1)
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid OAuth state"
        ) from exc

    expected_signature = hmac.new(
        _get_oauth_state_secret(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()

    try:
        supplied_signature = (
            base64.urlsafe_b64decode(
                encoded_signature
                + "="
                * (
                    -len(encoded_signature)
                    % 4
                )
            )
        )
    except Exception as exc:
        raise ValueError(
            "Invalid OAuth state signature"
        ) from exc

    if not hmac.compare_digest(
        supplied_signature,
        expected_signature,
    ):
        raise ValueError(
            "Invalid OAuth state signature"
        )

    try:
        payload_bytes = (
            base64.urlsafe_b64decode(
                encoded_payload
                + "="
                * (
                    -len(encoded_payload)
                    % 4
                )
            )
        )

        payload = json.loads(
            payload_bytes.decode("utf-8")
        )

    except Exception as exc:
        raise ValueError(
            "Invalid OAuth state payload"
        ) from exc

    user_id = payload.get(
        "user_id"
    )

    expires_at = payload.get(
        "expires_at"
    )

    nonce = payload.get(
        "nonce"
    )

    if not user_id:
        raise ValueError(
            "OAuth state does not contain a user ID"
        )

    if not isinstance(
        expires_at,
        int,
    ):
        raise ValueError(
            "OAuth state expiration is invalid"
        )

    if not nonce:
        raise ValueError(
            "OAuth state nonce is missing"
        )

    if time.time() > expires_at:
        raise ValueError(
            "OAuth state has expired"
        )

    return str(user_id)