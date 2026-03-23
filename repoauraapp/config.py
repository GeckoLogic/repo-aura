import os
from dotenv import load_dotenv

load_dotenv()


def _parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [r.strip() for r in value.split(",") if r.strip()]


DATABASE_URL: str = os.environ["DATABASE_URL"]
GITHUB_TOKEN: str | None = os.environ.get("GH_TOKEN")
GITHUB_USERNAME: str | None = os.environ.get("GH_USERNAME")
DASHBOARD_PASSWORD: str = os.environ.get("DASHBOARD_PASSWORD", "")

EXCLUDED_REPOS: list[str] = _parse_list(os.environ.get("EXCLUDED_REPOS"))
HIDDEN_REPOS: list[str] = _parse_list(os.environ.get("HIDDEN_REPOS"))

COLLECTION_INTERVAL_HOURS: int = int(os.environ.get("COLLECTION_INTERVAL_HOURS", "6"))
