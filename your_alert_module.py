from bs4 import BeautifulSoup

# Your tracked horses (lowercase for normalization)
tracked_horses = {
    "velocity", "air force red", "silversmith",
    "la ville lumiere", "julia street", "toodles",
    "cultural", "ariri", "needlepoint", "diver",
    "speed shopper", "auntie"
}

def normalize_row_text(raw):
    """
    Collapse whitespace and lowercase everything
    to produce a stable key.
    """
    return " ".join(raw.lower().split())

def check_site_once(html, seen_entries):
    """
    Parse the provided HTML string once,
    return a list of new cache keys (alerts)
    and update seen_entries.
    """
    soup = BeautifulSoup(html, "html.parser")
    new_alerts = []

    for row in soup.find_all("tr"):
        raw = row.get_text(separator="|").strip()
        norm = normalize_row_text(raw)

        for horse in tracked_horses:
            if horse in norm:
                cache_key = f"{horse}::{norm}"
                print(f"[DEBUG] Checking: {cache_key[:50]}...")
                if cache_key not in seen_entries:
                    print(f"[DEBUG] New alert for {horse}")
                    seen_entries.add(cache_key)
                    new_alerts.append(cache_key)
                else:
                    print(f"[DEBUG] Already seen: {horse}")
    return new_alerts
