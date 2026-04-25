from typing import Optional, Union
from datetime import datetime
from urllib.parse import urlparse


def safe_str(value: Optional[str], default: str = '') -> str:
    return value if value is not None else default


def parse_datetime(value: Optional[Union[str, datetime]]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return datetime.fromisoformat(value.split('+')[0].split('Z')[0])
    return None


def detect_hosting(pr_url: str) -> str:
    parsed = urlparse(pr_url)
    if parsed.netloc == 'github.com' or parsed.netloc.endswith('.github.com'):
        return 'github'
    return 'forgejo'