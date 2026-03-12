from __future__ import annotations

import threading
from typing import Any

import httpx
from authlib.jose import JsonWebToken, JWTClaims
from fastapi import Depends, HTTPException, Security
from fastapi.security import (
    APIKeyHeader,
    HTTPBasic,
    HTTPBearer,
    HTTPBasicCredentials,
    HTTPAuthorizationCredentials,
)
from shared.logging import get_logger

from config import auth_config

_http_basic = HTTPBasic()
_http_bearer = HTTPBearer(auto_error=False)

logger = get_logger(__name__)

# Authlib: JWT with asymmetric algorithms only (RFC 8725 §2.1)
_JWT_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
_jwt_decoder = JsonWebToken(_JWT_ALGORITHMS)

# Cache JWKS per issuer (thread-safe for gunicorn workers)
_jwks_lock = threading.Lock()
_jwks_cache: dict[str, dict[str, Any]] = {}


def _get_jwks_uri(issuer_url: str) -> str:
    """Fetch OpenID discovery and return jwks_uri."""
    url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("Failed to fetch OIDC discovery from %s: %s", url, e)
        raise HTTPException(
            status_code=503,
            detail="OAuth2 issuer discovery unavailable",
        ) from e
    jwks_uri = data.get("jwks_uri")
    if not jwks_uri:
        raise HTTPException(
            status_code=503,
            detail="OAuth2 issuer has no jwks_uri",
        )
    return jwks_uri


def _get_jwks(issuer_url: str) -> dict[str, Any]:
    """Get or create a cached JWKS dict for the issuer (OIDC discovery + JWKS fetch)."""
    issuer_key = issuer_url.rstrip("/")
    with _jwks_lock:
        if issuer_key not in _jwks_cache:
            jwks_uri = _get_jwks_uri(issuer_url)
            try:
                with httpx.Client(timeout=10.0) as client:
                    r = client.get(jwks_uri)
                    r.raise_for_status()
                    _jwks_cache[issuer_key] = r.json()
            except Exception as e:
                logger.warning("Failed to fetch JWKS from %s: %s", jwks_uri, e)
                raise HTTPException(
                    status_code=503,
                    detail="OAuth2 JWKS unavailable",
                ) from e
        return _jwks_cache[issuer_key]


def validate_auth_config() -> None:
    """Raise at startup if auth is enabled but required credentials are missing."""
    if not auth_config or auth_config.type is None:
        return
    if auth_config.type == "basic":
        if not auth_config.username or not auth_config.password:
            raise ValueError("AUTH_TYPE=basic requires AUTH_USERNAME and AUTH_PASSWORD")
    elif auth_config.type == "api_key":
        if not auth_config.api_key:
            raise ValueError("AUTH_TYPE=api_key requires AUTH_API_KEY")
    elif auth_config.type == "oauth2":
        has_issuer = bool(
            auth_config.oauth2_issuer_url and auth_config.oauth2_issuer_url.strip()
        )
        has_static = bool(auth_config.oauth2_bearer_token)
        if not has_issuer and not has_static:
            raise ValueError(
                "AUTH_TYPE=oauth2 requires AUTH_OAUTH2_ISSUER_URL (JWT validation) "
                "or AUTH_OAUTH2_BEARER_TOKEN (static token)"
            )


_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _verify_basic(
    credentials: HTTPBasicCredentials = Depends(_http_basic),
) -> HTTPBasicCredentials:
    if (
        credentials.username != auth_config.username
        or credentials.password != auth_config.password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials


def _verify_api_key(key: str | None = Security(_api_key_header)) -> str:
    if not key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if key != auth_config.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


def _verify_oauth2(
    creds: HTTPAuthorizationCredentials | None = Security(_http_bearer),
) -> str:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Bearer token")
    token = creds.credentials

    issuer_url = (auth_config.oauth2_issuer_url or "").strip()
    if issuer_url:
        # Allow comma-separated issuers (e.g. keycloak:8080 and localhost:8080 when port-forwarding)
        allowed_issuers = [
            u.strip().rstrip("/") for u in issuer_url.split(",") if u.strip()
        ]
        primary_issuer_url = allowed_issuers[0] if allowed_issuers else ""
        if not primary_issuer_url:
            raise HTTPException(status_code=401, detail="Invalid Bearer token")
        # Authlib: JWT validation via OIDC discovery + JWKS, then claims (iss, exp, aud)
        claims_options: dict[str, Any] = {
            "iss": {"essential": True, "values": allowed_issuers},
            "exp": {"essential": True},
        }
        if auth_config.oauth2_audience:
            claims_options["aud"] = {
                "essential": True,
                "values": [auth_config.oauth2_audience],
            }
        try:
            jwks = _get_jwks(primary_issuer_url)
            claims = _jwt_decoder.decode(
                token,
                key=jwks,
                claims_cls=JWTClaims,
                claims_options=claims_options,
            )
            claims.validate()
        except Exception as e:
            logger.debug("OAuth2 JWT validation failed: %s", e)
            raise HTTPException(
                status_code=401, detail="Invalid or expired Bearer token"
            )
        return token
    # Fallback: static token comparison (legacy)
    if auth_config.oauth2_bearer_token and token == auth_config.oauth2_bearer_token:
        return token
    raise HTTPException(status_code=401, detail="Invalid Bearer token")


def get_auth_dependencies() -> list:
    """FastAPI dependencies for the configured auth type (basic, api_key, oauth2, or none)."""
    if not auth_config or auth_config.type is None:
        return []
    if auth_config.type == "basic":
        return [Depends(_verify_basic)]
    if auth_config.type == "api_key":
        return [Depends(_verify_api_key)]
    if auth_config.type == "oauth2":
        return [Depends(_verify_oauth2)]
    return []
