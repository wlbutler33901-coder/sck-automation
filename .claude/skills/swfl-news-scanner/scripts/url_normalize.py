"""
URL normalizer for the SWFL News Scanner.

Article URLs are the natural dedupe key for the Development News Articles table.
Different ingestion paths (search results, RSS, direct links, syndicated feeds)
will surface the same article with different tracking parameters, casing, or
trailing slashes. Normalize before dedupe checks.

Usage:
    from url_normalize import normalize_url, urls_match

    key = normalize_url("https://www.News-Press.com/article/123?utm_source=rss&fbclid=abc")
    # -> "https://www.news-press.com/article/123"

    urls_match("https://www.bo.com/x", "https://www.bo.com/x/?utm_campaign=a")
    # -> True
"""

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# Tracking params to strip - common analytics/share params, never material to article identity.
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_brand", "utm_social", "utm_social-type",
    "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "yclid", "twclid",
    "_ga", "_gl", "ref", "ref_src", "ref_url", "share", "shared",
    "amp", "_amp",
}


def normalize_url(url: str) -> str:
    """Canonicalize an article URL for dedupe matching.

    - Lowercase scheme + host
    - Strip tracking params (UTM, fbclid, etc.)
    - Strip trailing slash from path
    - Drop fragment (anchor)
    - Leave path case alone (some CMS paths are case-sensitive)
    """
    if not url:
        return ""

    parsed = urlparse(url.strip())

    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    # Strip leading "www." for consistency - many sites serve both with/without.
    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = parsed.path.rstrip("/")

    # Filter query string
    if parsed.query:
        kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if k.lower() not in TRACKING_PARAMS]
        query = urlencode(kept)
    else:
        query = ""

    # Drop fragment entirely (never material for article identity)
    return urlunparse((scheme, netloc, path, "", query, ""))


def urls_match(url_a: str, url_b: str) -> bool:
    """Return True iff the two URLs normalize to the same canonical form
    and both normalize to a non-empty string. Empty/empty does NOT match -
    we don't want missing URLs to falsely dedupe against each other."""
    a = normalize_url(url_a)
    b = normalize_url(url_b)
    return bool(a) and a == b


if __name__ == "__main__":
    # Smoke tests
    cases = [
        # Tracking param strip
        ("https://www.businessobserverfl.com/news/2026/may/17/x/?utm_source=rss",
         "https://businessobserverfl.com/news/2026/may/17/x"),
        # www + trailing slash + uppercase host
        ("https://WWW.News-Press.com/article/123/",
         "https://news-press.com/article/123"),
        # Fragment drop
        ("https://gulfshorebusiness.com/article#section-2",
         "https://gulfshorebusiness.com/article"),
        # Multiple trackers
        ("https://naplesnews.com/x?utm_campaign=daily&fbclid=abc&id=42",
         "https://naplesnews.com/x?id=42"),
        # New SWFL source: www + trailing slash
        ("https://www.yourobserver.com/news/east-county/business/",
         "https://yourobserver.com/news/east-county/business"),
    ]

    print("Normalization tests:")
    all_pass = True
    for input_url, expected in cases:
        actual = normalize_url(input_url)
        ok = actual == expected
        all_pass = all_pass and ok
        marker = "✓" if ok else "✗"
        print(f"  {marker} {input_url}")
        print(f"     expected: {expected}")
        print(f"     actual:   {actual}")

    print(f"\nMatch tests:")
    match_cases = [
        ("https://www.bo.com/x", "https://bo.com/x/?utm_campaign=a", True),
        ("https://news-press.com/a", "https://news-press.com/b", False),
        ("", "https://news-press.com/a", False),
        ("", "", False),
    ]
    for a, b, expected in match_cases:
        actual = urls_match(a, b)
        ok = actual == expected
        all_pass = all_pass and ok
        marker = "✓" if ok else "✗"
        print(f"  {marker} match({a!r}, {b!r}) -> {actual} (expected {expected})")

    print(f"\n{'All passed.' if all_pass else 'FAILURES - fix before shipping.'}")
