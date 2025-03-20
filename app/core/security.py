import base64
import hashlib
import secrets


def generate_state_token():
    """Generate a random state string to prevent CSRF."""
    return secrets.token_hex(16)


def generate_code_verifier():
    """Generate a random string for PKCE code verifier."""
    buffer = secrets.token_bytes(32)
    # Convert to base64url format (removing padding '=' characters)
    return base64.urlsafe_b64encode(buffer).rstrip(b"=").decode()


def generate_code_challenge(verifier):
    """Generate a code challenge (SHA-256 hash of the verifier) for PKCE."""
    hash_value = hashlib.sha256(verifier.encode()).digest()
    # Convert to base64url format (removing padding '=' characters)
    return base64.urlsafe_b64encode(hash_value).rstrip(b"=").decode()
