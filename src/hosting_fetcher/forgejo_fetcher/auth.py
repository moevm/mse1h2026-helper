import requests
from typing import Optional
from urllib.parse import urlparse
from pyforgejo import PyforgejoApi


def login(pr_url: str, token: str | None = None) -> PyforgejoApi:
    parsed = urlparse(pr_url)

    base_url = f"{parsed.scheme}://{parsed.netloc}/api/v1" 

    return PyforgejoApi(
        base_url=base_url,
        api_key=token,
    )