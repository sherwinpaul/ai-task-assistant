"""One-time script to complete Google OAuth and generate token.json."""
from src.mcp.google_mcp_server import get_google_credentials

creds = get_google_credentials()
print("Google OAuth token saved successfully!")
print(f"Token valid: {creds.valid}")
