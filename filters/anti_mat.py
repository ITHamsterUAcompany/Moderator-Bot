import re
from typing import Dict, List

from aiogram.filters import BaseFilter
from aiogram.types import Message
from fuzzywuzzy import fuzz

from config import settings
from constants import letters_rest_table, special_symbols_map


def build_inverse_map(table: Dict[str, List[str]]) -> Dict[str, str]:
    inverse_map: Dict[str, str] = {}
    for cyrillic_char, variants in table.items():
        for variant in variants:
            inverse_map[variant] = cyrillic_char
        inverse_map[cyrillic_char] = cyrillic_char
    for k, v in special_symbols_map.items():
        inverse_map[k] = v
    return inverse_map


INVERSE_MAP = build_inverse_map(letters_rest_table)
REPLACEMENTS = sorted(INVERSE_MAP.items(), key=lambda kv: -len(kv[0]))


def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.lower()
    for pattern, repl in REPLACEMENTS:
        if pattern and pattern in normalized:
            normalized = normalized.replace(pattern, repl)
    normalized = re.sub(r"[^а-яєіїґ0-9\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def load_bad_words(path: str = settings.BAD_WORDS_FILE) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        raw = []
    normalized = [normalize_text(w) for w in raw if w]
    return [w for w in normalized if w]


BAD_WORDS = load_bad_words()
FUZZY_THRESHOLD = settings.BAD_FUZZY_THRESHOLD


def text_contains_bad(norm_text: str) -> bool:
    if not norm_text:
        return False
    for bad in BAD_WORDS:
        if bad and bad in norm_text:
            return True
    if settings.ANTI_MAT_USE_FUZZY:
        for bad in BAD_WORDS:
            if not bad:
                continue
            if fuzz.partial_ratio(norm_text, bad) >= FUZZY_THRESHOLD:
                return True
    tokens = norm_text.split()
    if settings.ANTI_MAT_USE_FUZZY:
        for token in tokens:
            for bad in BAD_WORDS:
                if fuzz.partial_ratio(token, bad) >= FUZZY_THRESHOLD:
                    return True
    joined = norm_text.replace(" ", "")
    if settings.ANTI_MAT_USE_FUZZY:
        for bad in BAD_WORDS:
            L = len(bad)
            if L == 0 or L > len(joined):
                continue
            for i in range(0, len(joined) - L + 1):
                window = joined[i : i + L + 1]
                if fuzz.partial_ratio(window, bad) >= FUZZY_THRESHOLD:
                    return True
    return False


class AntiMat(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        text = message.text or message.caption or ""
        if not text:
            return False
        norm = normalize_text(text)
        return text_contains_bad(norm)

