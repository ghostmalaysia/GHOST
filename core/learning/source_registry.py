from urllib.parse import urlparse

SOURCES = [
    {
        "id": "arxiv",
        "name": "arXiv",
        "domain": "arxiv.org",
        "categories": ["ai", "machine_learning", "research"],
        "type": "research_repository",
        "trust_level": "research",
    },
    {
        "id": "mit",
        "name": "MIT",
        "domain": "mit.edu",
        "categories": ["ai", "computer_science", "technology"],
        "type": "university",
        "trust_level": "academic",
    },
    {
        "id": "stanford",
        "name": "Stanford University",
        "domain": "stanford.edu",
        "categories": ["ai", "computer_science"],
        "type": "university",
        "trust_level": "academic",
    },
    {
        "id": "python",
        "name": "Python Documentation",
        "domain": "docs.python.org",
        "categories": ["programming", "python"],
        "type": "official_documentation",
        "trust_level": "official",
    },
    {
        "id": "github",
        "name": "GitHub Documentation",
        "domain": "docs.github.com",
        "categories": ["programming", "software"],
        "type": "official_documentation",
        "trust_level": "official",
    },
    {
        "id": "ubuntu",
        "name": "Ubuntu Documentation",
        "domain": "documentation.ubuntu.com",
        "categories": ["linux", "server"],
        "type": "official_documentation",
        "trust_level": "official",
    },
    {
        "id": "kernel",
        "name": "Linux Kernel",
        "domain": "kernel.org",
        "categories": ["linux", "operating_system"],
        "type": "official_project",
        "trust_level": "official",
    },
    {
        "id": "kali",
        "name": "Kali Linux",
        "domain": "kali.org",
        "categories": ["linux", "cybersecurity"],
        "type": "official_documentation",
        "trust_level": "official",
    },
    {
        "id": "owasp",
        "name": "OWASP",
        "domain": "owasp.org",
        "categories": ["cybersecurity", "web_security"],
        "type": "security_organization",
        "trust_level": "established",
    },
    {
        "id": "nist",
        "name": "NIST",
        "domain": "nist.gov",
        "categories": ["cybersecurity", "standards"],
        "type": "government_research",
        "trust_level": "authoritative",
    },
    {
        "id": "rfc",
        "name": "RFC Editor",
        "domain": "rfc-editor.org",
        "categories": ["networking", "internet_standards"],
        "type": "standards",
        "trust_level": "authoritative",
    },
    {
        "id": "postgresql",
        "name": "PostgreSQL",
        "domain": "postgresql.org",
        "categories": ["database", "server"],
        "type": "official_documentation",
        "trust_level": "official",
    },
    {
        "id": "docker",
        "name": "Docker Documentation",
        "domain": "docs.docker.com",
        "categories": ["server", "containers"],
        "type": "official_documentation",
        "trust_level": "official",
    },
]


def list_sources(category=None):
    if category is None:
        return SOURCES.copy()

    category = category.lower()

    return [
        source for source in SOURCES
        if category in source["categories"]
    ]


def find_source(url):
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return None

        hostname = hostname.lower()

        for source in SOURCES:
            domain = source["domain"].lower()

            if hostname == domain or hostname.endswith("." + domain):
                return source

    except Exception:
        return None

    return None


if __name__ == "__main__":
    print("GHOST SOURCE REGISTRY")
    print("Jumlah sumber:", len(SOURCES))

    for source in SOURCES:
        print(
            source["name"],
            "|",
            source["domain"],
            "|",
            source["trust_level"]
        )
