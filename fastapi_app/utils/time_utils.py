from datetime import datetime, timezone


def get_utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
