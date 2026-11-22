import re


def clean_content(content):
    if not content:
        return ""

    cleaned = []

    remove_phrases = [
        "Log in",
        "Subscribe",
        "Join IBM at AWS re:Invent",
        "Discover how we deliver AI speed",
    ]

    for line in content.splitlines():
        line = line.strip()

        if not line:
            continue

        if any(phrase.lower() in line.lower()
               for phrase in remove_phrases):
            continue

        # Buang baris yang hanya mengandungi pautan menu
        if re.fullmatch(r'[\*\-\s]*\[[^\]]+\]\([^)]+\)', line):
            continue

        # Bersihkan format pautan Markdown tetapi kekalkan teks
        line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)

        if line:
            cleaned.append(line)

    return "\n\n".join(cleaned)


if __name__ == "__main__":
    print("GHOST CONTENT CLEANER")
    print("Modul berjaya dimuatkan.")
