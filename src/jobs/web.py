"""Web request utilities with retry logic."""

from tenacity import retry, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def fetch_with_retry(page, url: str, timeout: int = 15000) -> str:
    """Fetch a page with retry logic."""
    resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    if resp.status != 200:
        raise Exception(f"HTTP {resp.status}")
    return page.content()
