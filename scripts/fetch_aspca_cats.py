import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


SOURCE_URL = "https://www.aspca.org/pet-care/animal-poison-control/cats-plant-list"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "aspca_cats_plants.json"


class AspcaCatsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.section = None
        self.in_h2 = False
        self.h2_text = []
        self.in_anchor = False
        self.anchor_text = []
        self.anchor_href = ""
        self.current = None
        self.records = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "h2":
            self._flush_current()
            self.in_h2 = True
            self.h2_text = []
            return

        if tag == "a" and self.section:
            href = attrs_dict.get("href", "")
            if "/toxic-and-non-toxic-plants/" not in href:
                return
            self._flush_current()
            self.in_anchor = True
            self.anchor_text = []
            self.anchor_href = urljoin(SOURCE_URL, href)

    def handle_endtag(self, tag):
        if tag == "h2" and self.in_h2:
            heading = clean_text(" ".join(self.h2_text))
            if heading == "Plants Toxic to Cats":
                self.section = "toxic"
            elif heading == "Plants Non-Toxic to Cats":
                self.section = "safe"
            else:
                self.section = None
            self.in_h2 = False
            self.h2_text = []
            return

        if tag == "a" and self.in_anchor:
            name = clean_text(" ".join(self.anchor_text))
            if name:
                self.current = {
                    "common_name_en": name,
                    "source_url": self.anchor_href,
                    "raw_details": "",
                    "cat_toxicity": self.section,
                }
            self.in_anchor = False
            self.anchor_text = []
            self.anchor_href = ""

    def handle_data(self, data):
        if self.in_h2:
            self.h2_text.append(data)
        elif self.in_anchor:
            self.anchor_text.append(data)
        elif self.current is not None:
            self.current["raw_details"] += data

    def close(self):
        super().close()
        self._flush_current()

    def _flush_current(self):
        if not self.current:
            return
        record = parse_record(self.current)
        if record:
            self.records.append(record)
        self.current = None


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def split_aliases(value):
    value = clean_text(value)
    if not value:
        return []
    value = re.sub(r"^(many,\s+including:|including:)\s*", "", value, flags=re.I)
    return [clean_text(item) for item in value.split(",") if clean_text(item)]


def parse_record(record):
    details = clean_text(record.get("raw_details", ""))
    match = re.match(
        r"^\((.*?)\)\s*\|\s*Scientific Names:\s*(.*?)\s*\|\s*Family:\s*(.*)$",
        details,
        flags=re.I,
    )
    if not match:
        return None

    aliases, scientific_name, family = match.groups()
    common_name = clean_text(record["common_name_en"])
    source_url = record["source_url"]
    slug = source_url.rstrip("/").split("/")[-1]

    return {
        "id": f"aspca-{slug}",
        "source": "ASPCA",
        "source_list_url": SOURCE_URL,
        "source_url": source_url,
        "common_name_en": common_name,
        "aliases_en": split_aliases(aliases),
        "scientific_name": clean_text(scientific_name),
        "family": clean_text(family),
        "cat_toxicity": record["cat_toxicity"],
    }


def fetch_html():
    request = Request(
        SOURCE_URL,
        headers={
            "User-Agent": "catna-data-fetcher/1.0 (+https://github.com/)",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def main():
    html = fetch_html()
    parser = AspcaCatsParser()
    parser.feed(html)
    parser.close()

    data = {
        "metadata": {
            "source": "ASPCA Toxic and Non-Toxic Plant List — Cats",
            "source_url": SOURCE_URL,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(parser.records),
            "note": "For search cache only. Verify important safety decisions with ASPCA or a veterinarian.",
        },
        "plants": parser.records,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    toxic_count = sum(1 for item in parser.records if item["cat_toxicity"] == "toxic")
    safe_count = sum(1 for item in parser.records if item["cat_toxicity"] == "safe")
    print(f"saved {len(parser.records)} records to {OUTPUT_PATH}")
    print(f"toxic={toxic_count}, safe={safe_count}")


if __name__ == "__main__":
    main()
