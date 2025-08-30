# fellowship/utils.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.conf import settings
import json

def get_youtube_service():
    creds_data = getattr(settings, "YOUTUBE_CLIENT_SECRET_JSON", None)
    if not creds_data:
        raise ValueError("YouTube credentials not configured.")

    creds_dict = json.loads(creds_data)
    credentials = Credentials(
        token=creds_dict.get("token"),
        refresh_token=creds_dict.get("refresh_token"),
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        token_uri=creds_dict.get("token_uri"),
        scopes=settings.YOUTUBE_SCOPES
    )

    youtube = build(
        settings.YOUTUBE_API_SERVICE_NAME,
        settings.YOUTUBE_API_VERSION,
        credentials=credentials
    )
    return youtube
