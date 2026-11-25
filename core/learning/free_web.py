"""Free, key-less web lookup for GHOST learning.

Uses the public Wikipedia API over HTTPS. Retrieved text is always treated as
untrusted reference data, never as instructions.
"""

import json
import re
import urllib.parse
import urllib.request

WIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "GHOST-Learning/1.0 (local research assistant)"


def _request(params):
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def search_web(query, limit=3):
    if not isinstance(query, str) or not query.strip():
        return []

    data = _request({
        "action": "query",
        "list": "search",
        "srsearch": query.strip(),
        "srlimit": max(1, min(int(limit), 5)),
        "format": "json",
    })

    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        if not title:
            continue
        results.append({
            "title": title,
            "url": "https://en.wikipedia.org/wiki/"
                + urllib.parse.quote(title.replace(" ", "_")),
            "snippet": re.sub(r"<[^>]+>", "", item.get("snippet", "")),
        })
    return results


def read_page(title):
    if not isinstance(title, str) or not title.strip():
        return {"error": "Tiada tajuk halaman."}

    data = _request({
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "redirects": 1,
        "titles": title.strip(),
        "format": "json",
    })

    for page in data.get("query", {}).get("pages", {}).values():
        text = page.get("extract", "")
        name = page.get("title", title.strip())
        if text:
            return {
                "title": name,
                "url": "https://en.wikipedia.org/wiki/"
                    + urllib.parse.quote(name.replace(" ", "_")),
                "text": text,
            }

    return {"error": "Tiada kandungan untuk halaman ini."}
