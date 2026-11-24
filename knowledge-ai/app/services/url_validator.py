import ipaddress
import socket
from urllib.parse import urljoin, urlparse


class UnsafeURLException(ValueError):
    pass


def _is_private_address(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_public_http_url(url: str) -> str:
    if not url or len(url) > 2048:
        raise UnsafeURLException("A valid URL is required.")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise UnsafeURLException("Only HTTP and HTTPS URLs are allowed.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise UnsafeURLException("Invalid URL.")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in ("localhost", "localhost.localdomain") or hostname.endswith(".local"):
        raise UnsafeURLException("Local and private network URLs are blocked.")

    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeURLException("The website hostname could not be resolved.") from exc

    if not addresses:
        raise UnsafeURLException("The website hostname could not be resolved.")

    for family, _, _, _, sockaddr in addresses:
        if family in (socket.AF_INET, socket.AF_INET6):
            if _is_private_address(sockaddr[0]):
                raise UnsafeURLException("Private network addresses are blocked.")

    return parsed.geturl()
