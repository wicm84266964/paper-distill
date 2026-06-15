from __future__ import annotations

import re


DEFAULT_TARGET_LANGUAGE = "Chinese"


def normalize_target_language(value: str | None) -> str:
    if value is None:
        return DEFAULT_TARGET_LANGUAGE
    normalized = " ".join(value.strip().split())
    if not normalized:
        return DEFAULT_TARGET_LANGUAGE

    folded = normalized.casefold()
    if folded in {"zh", "zh-cn", "cn", "chinese", "mandarin", "中文", "汉语"}:
        return "Chinese"
    if folded in {"en", "en-us", "en-gb", "english", "英文", "英语"}:
        return "English"
    if folded in {
        "source",
        "source-language",
        "source language",
        "same as source",
        "same-as-source",
        "original",
        "原文",
        "原文语言",
    }:
        return "source language"
    return normalized


def target_language_instruction(target_language: str) -> str:
    normalized = normalize_target_language(target_language)
    if normalized == "source language":
        return "Write generated dataset fields in the source paper's primary language."
    return f"Write generated dataset fields in {normalized}."


def target_language_version_key(target_language: str) -> str:
    normalized = normalize_target_language(target_language)
    key = re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")
    return key or "custom"
