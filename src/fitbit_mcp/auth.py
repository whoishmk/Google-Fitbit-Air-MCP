import os
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from mcp.server.mcpserver.exceptions import ToolError

SCOPES = [
    f"https://www.googleapis.com/auth/googlehealth.{area}.readonly"
    for area in (
        "activity_and_fitness",
        "health_metrics_and_measurements",
        "sleep",
        "nutrition",
        "ecg",
        "irn",
        "settings",
    )
]
TOKEN_PATH = Path.home() / ".config" / "fitbit-mcp" / "token.json"
SIGN_IN_HINT = "Run: uv run fitbit-mcp auth"


def sign_in():
    flow = InstalledAppFlow.from_client_secrets_file(
        os.environ["FITBIT_MCP_CLIENT_SECRETS"], SCOPES
    )
    credentials = flow.run_local_server(port=0, prompt="consent")
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.touch(mode=0o600)
    TOKEN_PATH.write_text(credentials.to_json())
    print(f"Saved token to {TOKEN_PATH}")


def authorized_session():
    if not TOKEN_PATH.exists():
        raise ToolError(f"Not signed in. {SIGN_IN_HINT}")
    return AuthorizedSession(Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES))
