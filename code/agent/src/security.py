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


def validate_auth_config() -> None:
    """Raise at startup if auth is enabled but required credentials are missing."""

    logger.info(f"Validating auth config: {auth_config}")

    if not auth_config or auth_config.type is None:
        logger.info("No auth config found")
        return
    if auth_config.type == "basic":
        logger.info("Basic auth config found")
        if not auth_config.username or not auth_config.password:
            logger.warning("USERNAME and PASSWORD are not set")
            raise ValueError("AUTH_TYPE=basic requires USERNAME and PASSWORD to be set")
        logger.info("Basic auth config is valid")
    elif auth_config.type == "api_key":
        logger.info("API key auth config found")
        if not auth_config.api_key:
            raise ValueError("AUTH_TYPE=api_key requires AUTH_API_KEY")
    elif auth_config.type == "oauth2":
        logger.info("OAuth2 auth config found")
        if not auth_config.oauth2_bearer_token:
            raise ValueError(
                "AUTH_TYPE=oauth2 requires AUTH_OAUTH2_BEARER_TOKEN (expected Bearer token)"
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
    if creds.credentials != auth_config.oauth2_bearer_token:
        raise HTTPException(status_code=401, detail="Invalid Bearer token")
    return creds.credentials


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
