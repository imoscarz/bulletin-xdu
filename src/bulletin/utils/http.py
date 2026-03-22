import httpx

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; xdu-bulletin/0.1)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


async def create_client() -> httpx.AsyncClient:
    """Create a configured httpx AsyncClient."""
    transport = httpx.AsyncHTTPTransport(retries=3)
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers=_DEFAULT_HEADERS,
        follow_redirects=True,
    )


async def fetch_page(client: httpx.AsyncClient, url: str) -> str:
    """Fetch a page and return its decoded HTML content."""
    response = await client.get(url)
    response.raise_for_status()
    return response.text
