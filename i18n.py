# i18n.py — hermes-king plugin localization.
# Language resolution: HERMES_LANGUAGE > display.language > en.
# Keys fall back: current lang -> en -> key name.

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml

    _YAML_OK = True
except ImportError:
    _YAML_OK = False

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"

_LANG_ALIAS = {
    "zh-cn": "zh",
    "zh-tw": "zh",
    "zh-hans": "zh",
    "zh-hant": "zh",
    "zh-hk": "zh",
    "zh": "zh",
    "zho": "zh",
    "cmn": "zh",
    "chinese": "zh",
}

_CACHED: dict[str, dict] = {}


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    """Flatten nested YAML dict to dotted keys, values coerced to str."""
    out: dict[str, str] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        elif isinstance(v, (str, int, float, bool)):
            out[key] = str(v)
    return out


def _load_lang(lang: str) -> dict[str, str]:
    if lang in _CACHED:
        return _CACHED[lang]
    data: dict[str, str] = {}
    fp = _LOCALES_DIR / f"{lang}.yaml"
    if _YAML_OK and fp.exists():
        with open(fp, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if isinstance(raw, dict):
            data = _flatten(raw)
    elif fp.exists():
        # fallback plain parser: only flat "key: value" lines
        for line in fp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip().strip("'\"")
    _CACHED[lang] = data
    return data


def get_language() -> str:
    """Return current language code (en/zh)."""
    from_env = os.environ.get("HERMES_LANGUAGE", "").strip()
    if from_env:
        norm = from_env.replace("_", "-").lower()
        if norm in _LANG_ALIAS:
            return _LANG_ALIAS[norm]
        base = norm.split("-")[0]
        if base in _LANG_ALIAS:
            return _LANG_ALIAS[base]
        return "en"
    try:
        from hermes_constants import load_display_config

        cfg = load_display_config() or {}
        dl = str(cfg.get("language", "")).strip().lower()
        if dl:
            norm = dl.replace("_", "-").lower()
            if norm in _LANG_ALIAS:
                return _LANG_ALIAS[norm]
            base = norm.split("-")[0]
            if base in _LANG_ALIAS:
                return _LANG_ALIAS[base]
    except Exception:
        pass
    return "en"


def t(key: str, lang: str | None = None, **fmt) -> str:
    """Look up a dotted key; format with {fmt} placeholders; fall back to en then key."""
    lang = lang or get_language()
    d = _load_lang(lang)
    val = d.get(key)
    if val is None and lang != "en":
        val = _load_lang("en").get(key)
    if val is None:
        return key
    try:
        return val.format(**fmt)
    except (KeyError, IndexError, ValueError):
        # An unformatted {foo} in the string with missing fmt is safer to
        # return raw than to crash.
        return val