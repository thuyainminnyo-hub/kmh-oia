"""Synthetic outfit selection flow; contains no real character or learner data."""

from contract_guard import DesignToken, is_approved_token


def select_outfit(token: DesignToken) -> dict[str, str]:
    """Select only a synthetic outfit token after its approval check."""
    if not is_approved_token(token):
        raise ValueError("outfit token must be approved")
    return {"token": token.token_name, "status": "selected"}
