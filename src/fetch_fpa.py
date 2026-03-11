"""Scrape FPA weekly-prices page, download PDFs, parse urea prices."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup

# Mimic browser to reduce 403 risk
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


@dataclass
class FPAFetcher:
    weekly_index_url: str
    raw_subdir: str
    product_keywords: list[str]
    max_reports: int = 80

    def discover_pdf_links(self) -> list[str]:
        r = requests.get(self.weekly_index_url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        links = []
        base = "https://fpa.da.gov.ph"
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if ".pdf" not in href.lower():
                continue
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = base + href
            elif href.startswith("wp-content") or (not href.startswith("http") and "fpa.da.gov.ph" not in href):
                href = base + "/" + href.lstrip("/")
            if not href.startswith("http") or "fpa.da.gov.ph" not in href:
                continue
            links.append(href)

        deduped = []
        seen = set()
        for link in links:
            if link not in seen:
                seen.add(link)
                deduped.append(link)
        return deduped[: self.max_reports]

    def download_pdfs(self, links: list[str]) -> list[Path]:
        Path(self.raw_subdir).mkdir(parents=True, exist_ok=True)
        paths = []
        for i, link in enumerate(links, start=1):
            filename = Path(link.split("?")[0]).name or f"fpa_{i}.pdf"
            outpath = Path(self.raw_subdir) / filename
            if not outpath.exists():
                try:
                    r = requests.get(link, headers=HEADERS, timeout=120)
                    r.raise_for_status()
                    outpath.write_bytes(r.content)
                except requests.RequestException as e:
                    print(f"  Skipping {filename}: {e}")
                    continue
            paths.append(outpath)
        return paths

    def parse_urea_prices(self, pdf_paths: list[Path]) -> pd.DataFrame:
        rows = []

        for pdf_path in pdf_paths:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text = "\n".join((page.extract_text() or "") for page in pdf.pages[:3])

                date_match = re.search(r"([A-Z][a-z]+ \d{1,2},? \d{4})", text)
                report_date = pd.to_datetime(date_match.group(1), errors="coerce") if date_match else pd.NaT

                for keyword in self.product_keywords:
                    if keyword.lower() in text.lower():
                        rows.append({
                            "source_file": pdf_path.name,
                            "report_date": report_date,
                            "product_keyword_found": keyword,
                            "raw_text_excerpt": text[:4000],
                        })
            except Exception:
                continue

        return pd.DataFrame(rows)
