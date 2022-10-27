import sys
import os
import urllib.parse
from pathlib import Path
from typing import Iterable

VERSION = "0.1.0"


def is_kanji(char: str) -> bool:
    u = ord(char)
    return u > 19968 and u < 40895


def generate_jisho_links(kanjis: Iterable[str] | str) -> list[str]:
    if isinstance(kanjis, str):
        k = "".join([kanji for kanji in kanjis])
    else:
        k = [kanji for kanji in kanjis]

    links = []

    n = 8
    chunks = [k[i:i+n] for i in range(0, len(k), n)]

    for chunk in chunks:
        l = urllib.parse.quote(f"{chunk}#kanji")
        links.append(f"https://jisho.org/search/{l}")

    return links


def normalize_path(path: str) -> Path:
    filepath = Path(path)
    if not filepath.is_absolute():
        filepath = Path(__file__).parent / filepath
    return filepath.resolve()


def process(filepath: Path):
    kanjis = set()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for symbol in f.read():
                if is_kanji(symbol):
                    kanjis.add(symbol)
    except UnicodeDecodeError:
        print(f"Unable to read file {filepath}. Is it a text file?")
        return

    print(f"Found {len(kanjis)} kanjis:")
    print(" ".join(kanjis))
    print()
    print(f"jisho.org links:")
    for link in generate_jisho_links(kanjis):
        print(link)
        print()


def main():
    print(f"kanjiextract {VERSION}")

    if len(sys.argv) > 1:
        process(" ".join(sys.argv[1:]))
        return
    
    while True:
        print()
        print("Paste the path to a text file to process")
        print("Leave empty to exit")
        print()
        try:
            data = input("> ")
        except KeyboardInterrupt:
            return
        if len(data) == 0:
            return
        process(normalize_path(data))


if __name__ == "__main__":
    main()
