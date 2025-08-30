import os
import json
import tempfile
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def get_youtube_service():
    """
    Initializes and returns the YouTube API service client.
    Uses environment variables for credentials and scopes.
    """
    # YouTube API settings
    service_name = os.getenv("YOUTUBE_API_SERVICE_NAME", "youtube")
    api_version = os.getenv("YOUTUBE_API_VERSION", "v3")
    scopes = json.loads(os.getenv("YOUTUBE_SCOPES", '["https://www.googleapis.com/auth/youtube.force-ssl"]'))

    # Get client secret JSON from env
    client_secret_json = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
    if not client_secret_json:
        raise ValueError("YOUTUBE_CLIENT_SECRET_JSON not set in environment variables")

    # Write JSON to temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write(client_secret_json)
        credentials_file_path = f.name

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file_path, scopes)
    credentials = flow.run_local_server(port=0)

    # Build YouTube service
    youtube = build(service_name, api_version, credentials=credentials)
    return youtube
