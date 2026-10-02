#!/usr/bin/env python3
"""hermes-king CLI — 离线调试与自检入口。

用法:
    python -m hermes_king --status        # 内核状态
    python -m hermes_king --verify        # 破甲握手验证
    python -m hermes_king --selftest      # 74 项离线自检
    python -m hermes_king --dump          # 打印双段 SHA256 与预算
"""

from __future__ import annotations

import sys


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    from . import payload

    if args[0] in ("--status", "-s"):
        print(payload.profile())
        return 0
    if args[0] in ("--verify", "-v"):
        print(payload.verify())
        return 0
    if args[0] in ("--dump", "-d"):
        for sid, text in payload.sections():
            print(f"{sid}: {len(text)} chars, sha256={payload.sha256(payload._SOURCE[sid])[:32]}")
        if payload.dual_layer():
            h1 = payload.sha256("hermes-king-core.md")
            h2 = payload.sha256("hermes-king-reinforce.md")
            print(f"dual same-source: {h1 == h2}")
        print(f"total: {payload.total_chars()}/{payload.TOTAL_BUDGET_CHARS} chars")
        return 0
    if args[0] in ("--selftest", "-t"):
        import selftest
        return selftest.main()
    print(f"unknown option: {args[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())