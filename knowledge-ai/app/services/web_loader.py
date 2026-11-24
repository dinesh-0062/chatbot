import hashlib
import os
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.services.url_validator import UnsafeURLException, validate_public_http_url


class WebLoadError(Exception):
    pass


class WebLoader:
    def __init__(self):
        self.timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
        self.max_bytes = int(float(os.getenv("MAX_URL_CONTENT_SIZE_MB", "5")) * 1024 * 1024)

    def _validate_redirect_chain(self, response: httpx.Response) -> str:
        current = str(response.url)
        validate_public_http_url(current)
        for redirect in response.history:
            validate_public_http_url(str(redirect.url))
        return current

    def load(self, url: str) -> dict:
        original_url = validate_public_http_url(url)
        robots_url = f"{urlparse(original_url).scheme}://{urlparse(original_url).netloc}/robots.txt"

        try:
            with httpx.Client(follow_redirects=True, timeout=self.timeout, headers={"User-Agent": "KnowledgeAI/1.0"}) as client:
                robots = client.get(robots_url)
                if robots.status_code == 200:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(robots.text.splitlines())
                    if not parser.can_fetch("KnowledgeAI", original_url):
                        raise WebLoadError("This website disallows automated access in robots.txt.")

                response = client.get(original_url)
        except httpx.HTTPError as exc:
            raise WebLoadError("The website could not be reached.") from exc

        if response.status_code >= 400:
            raise WebLoadError(f"The website returned HTTP status {response.status_code}.")

        canonical_url = self._validate_redirect_chain(response)
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise WebLoadError("The URL does not return supported HTML content.")
        if len(response.content) > self.max_bytes:
            raise WebLoadError("The page exceeds the configured content size limit.")

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title_tag = soup.find("title")
        h1 = soup.find("h1")
        title = (title_tag.get_text(" ", strip=True) if title_tag else "") or (
            h1.get_text(" ", strip=True) if h1 else "Web Documentation"
        )

        canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
        if canonical_tag and canonical_tag.get("href"):
            candidate = urljoin(canonical_url, canonical_tag["href"])
            canonical_url = validate_public_http_url(candidate)

        main = soup.find("main") or soup.find("article") or soup.find("div", role="main") or soup.body or soup
        text = "\n".join(
            line.strip()
            for line in main.get_text("\n", strip=True).splitlines()
            if line.strip()
        )
        text = "\n".join(dict.fromkeys(text.splitlines()))
        if len(text.strip()) < 100:
            raise WebLoadError("No readable page content was found.")

        return {
            "original_url": original_url,
            "canonical_url": canonical_url,
            "title": title[:255],
            "text": text,
            "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
