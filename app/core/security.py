import secrets


def generate_state_token():
    """Generate a random state string to prevent CSRF."""
    return secrets.token_hex(16)
