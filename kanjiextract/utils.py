import json
import os
import urllib.parse
from pathlib import Path
from typing import Iterable
import shutil
import time

from pydantic import BaseModel, Field

DATA_FILE_PATH = Path(__file__).parent / "data.json"


class IgnoreConfigJson(BaseModel):
    ignore_list: str = Field(default="")
    path: str = Field(exclude=True)

    class Config:
        validate_assignment = True

    def add_to_ignore_list(self, kanji: str | Iterable[str]) -> int:
        ignore_set = set(self.ignore_list)
        len_before = len(self.ignore_list)
        for k in kanji:
            if is_kanji(k) and k not in ignore_set:
                ignore_set.add(k)
        self.ignore_list = "".join(ignore_set)
        return len(self.ignore_list) - len_before

    def remove_from_ignore_list(self, kanji: str | Iterable[str]) -> int:
        ignore_set = set(self.ignore_list)
        len_before = len(self.ignore_list)
        for k in kanji:
            if is_kanji(k) and k in ignore_set:
                ignore_set.remove(k)
        self.ignore_list = "".join(ignore_set)
        return len(self.ignore_list) - len_before

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.dict(), f, indent=4, ensure_ascii=False)


class InternalConfigJson(IgnoreConfigJson):
    external_ignored_file_path: str | None = Field(default=None)


def normalize_path(path: str | Path) -> Path:
    filepath = Path(path)
    if not filepath.is_absolute():
        filepath = Path(os.getcwd()) / filepath
    return filepath.resolve()


def get_internal_config() -> InternalConfigJson:
    try:
        with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
            config = InternalConfigJson(**json.load(f), path=str(DATA_FILE_PATH))
    except FileNotFoundError:
        config = InternalConfigJson(path=str(DATA_FILE_PATH))
        config.save()

    return config


def get_external_config() -> IgnoreConfigJson | None:
    internal_config = get_internal_config()
    external_config_path = internal_config.external_ignored_file_path
    if external_config_path is None:
        return None
    try:
        with open(external_config_path, "r", encoding="utf-8") as f:
            config = IgnoreConfigJson(**json.load(f), path=str(external_config_path))
    except json.decoder.JSONDecodeError:
        p = Path(external_config_path)
        new_name = p.parent / (str(p.name)+f".backup-{int(time.time())}.json")
        config = IgnoreConfigJson(path=str(external_config_path))
        config.save()
    except FileNotFoundError:
        p = Path(get_internal_config().external_ignored_file_path)
        if not p.parent.exists():
            FileNotFoundError(f"Directory for external config ('{p.parent}') does not exist!")
        config = IgnoreConfigJson(path=str(external_config_path))
        config.save()
    return config


def _get_actual_kanji_ignore_list_config() -> IgnoreConfigJson:
    internal_config = get_internal_config()
    if internal_config.external_ignored_file_path is None:
        return internal_config
    return get_external_config()


def set_ignored_file_path(path: str | Path | None, merge: bool) -> Path:
    if path is not None:
        p = normalize_path(path)
        if p.is_dir():
            p = p / "kanjiextract_data.json"
        if not p.parent.exists():
            raise FileNotFoundError(f"Directory '{p.parent}' does not exist!")
        p = str(p)
    else:
        p = None

    conf = get_internal_config()
    conf.external_ignored_file_path = p
    conf.save()

    if merge:
        if p is not None:
            ext_config = get_external_config()
            ext_config.ignore_list = "".join(set(ext_config.ignore_list) | set(conf.ignore_list))
            ext_config.save()
        else:
            print("External config is None, unable to merge it with internal!")

    return Path(conf.external_ignored_file_path)


def find_all_kanji(text: str, ignore: Iterable[str] | None = None) -> tuple[str, str]:
    ignored = set()
    if ignore is None:
        ignore = []
    kanji = []
    for symbol in text:
        if is_kanji(symbol) and symbol not in kanji:
            if symbol in ignore:
                ignored.add(symbol)
                continue
            kanji.append(symbol)
    return "".join(kanji), "".join(ignored)


def is_kanji(char: str) -> bool:
    u = ord(char)
    return 19968 < u < 40895


def generate_jisho_links(kanji: Iterable[str] | str) -> list[str]:
    if isinstance(kanji, str):
        k = "".join([kanji for kanji in kanji])
    else:
        k = [kanji for kanji in kanji]

    links = []

    n = 10
    chunks = [k[i:i + n] for i in range(0, len(k), n)]

    for chunk in chunks:
        line = "".join(chunk)
        links.append(f"https://jisho.org/search/{urllib.parse.quote(f'{line}#kanji')}")

    return links


def extract(path: Path | str, use_ignore_list: bool):
    filepath = normalize_path(path)
    ignore = []
    if use_ignore_list:
        ignore = get_ignored_kanji()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            kanji, ignored = find_all_kanji(f.read(), ignore)
    except UnicodeDecodeError:
        print(f"Unable to read file {filepath}. Is it a text file?")
        return

    print(f"Found {len(kanji)} kanji ({len(ignored)} ignored, "
          f"{len(kanji) + len(ignored)} total):")
    print(" ".join(kanji))
    print()
    print(f"jisho.org links:")
    for link in generate_jisho_links(kanji):
        print(link)
        print()


def get_ignored_kanji() -> set[str]:
    internal_config = get_internal_config()
    if internal_config.external_ignored_file_path is None:
        return set(internal_config.ignore_list)
    return set(get_external_config().ignore_list)


def add_ignored_kanji(kanji: str | Iterable[str]) -> int:
    config = _get_actual_kanji_ignore_list_config()
    count = config.add_to_ignore_list(kanji)
    config.save()
    return count


def set_ignored_kanji(kanji: str | Iterable[str]) -> (str, str):
    config = _get_actual_kanji_ignore_list_config()
    old = config.ignore_list
    config.ignore_list, _ = find_all_kanji(kanji)
    config.save()
    return old, config.ignore_list


def remove_ignored_kanji(kanji: str | set[str]) -> int:
    config = _get_actual_kanji_ignore_list_config()
    count = config.remove_from_ignore_list(kanji)
    config.save()
    return count
