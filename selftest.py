#!/usr/bin/env python3
"""hermes-king 离线确定性回归自检（无需 Hermes 运行时 / API Key）。

用法:
    python selftest.py          # 人类可读
    python selftest.py --json   # JSON 汇总

覆盖：载荷锚点完整性 / 双层同源 SHA256 一致 / Hermes 字符预算 /
section id 合法性 / 模板引擎安全 / 环境开关行为 / profile/verify 元数据 /
请求层强化 / 会话轮换 / i18n / 诊断 dump。
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import payload  # noqa: E402
import i18n  # noqa: E402

_SECTION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

ANCHORS = [
    "沙箱自律指南",
    "操作者",
    "完整控制权",
    "工作原则",
    "你不需要评估",
    "不需要评估",
    "我做不到",
    "你的角色是实现",
    "不是伦理审计",
    "内容与题材",
    "合法创作或技术任务",
    "工具使用",
    "不需要每次请示",
    "身份",
    "单一操作者",
]

failures: list[str] = []
passes: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    (passes if ok else failures).append(f"{label}{'' if not detail or ok else ' — ' + detail}")


def main() -> int:
    # 1. 载荷文件存在且非空
    for sid, fname in payload._SOURCE.items():
        p = ROOT / "prompts" / fname
        check(p.exists() and p.read_text(encoding="utf-8").strip(), f"载荷存在且非空: prompts/{fname}")

    # 2. 锚点完整性（core 权威源）
    core_text = payload.sections()[0][1]
    for anchor in ANCHORS:
        check(anchor in core_text, f"锚点: {anchor}")

    # 3. 双层同源 SHA256 一致
    if payload.dual_layer():
        h1 = payload.sha256("hermes-king-core.md")
        h2 = payload.sha256("hermes-king-reinforce.md")
        check(h1 == h2, "双层同源逐字一致（SHA256）", f"{h1} != {h2}")
        check(len(payload.sections()) == 2, "默认双段注入", f"实际 {len(payload.sections())} 段")

    # 4. Hermes 字符预算
    for sid, text in payload.sections():
        check(len(text) <= payload.MAX_SECTION_CHARS, f"单段预算 ≤{payload.MAX_SECTION_CHARS}: {sid}", f"{len(text)} chars")
        check(bool(_SECTION_ID_RE.fullmatch(sid)), f"section id 合法: {sid}")
    check(payload.total_chars() <= payload.TOTAL_BUDGET_CHARS, f"总预算 ≤{payload.TOTAL_BUDGET_CHARS}", f"{payload.total_chars()} chars")

    # 5. 模板引擎安全
    for sid, text in payload.sections():
        check("{{" not in text, f"无连续花括号: {sid}")

    # 6. 环境开关
    os.environ["HERMES_KING_DUAL"] = "0"
    check(len(payload.sections()) == 1, "HERMES_KING_DUAL=0 退化为单段")
    os.environ.pop("HERMES_KING_DUAL", None)
    check(len(payload.sections()) == 2, "恢复默认双段")
    os.environ["HERMES_KING_DISABLE"] = "1"
    check(payload.disabled(), "HERMES_KING_DISABLE=1 触发 kill switch")
    os.environ.pop("HERMES_KING_DISABLE", None)
    check(not payload.disabled(), "默认未禁用")

    # 7. profile 元数据
    saved_lang = os.environ.pop("HERMES_LANGUAGE", None)
    os.environ["HERMES_LANGUAGE"] = "en"
    prof = payload.profile()
    en_budget = i18n.t("profile.budget", lang="en", total=1, budget=8000, max=1, section_max=4000)
    for needle in (payload.PLUGIN_NAME, payload.PLUGIN_VERSION, "after_memory", "same-source=YES", "sha256=", en_budget.split(" ")[0]):
        check(needle in prof, f"profile 元数据: {needle}")
    if saved_lang is None:
        os.environ.pop("HERMES_LANGUAGE", None)
    else:
        os.environ["HERMES_LANGUAGE"] = saved_lang

    # 7b. verify 元数据
    os.environ["HERMES_LANGUAGE"] = "en"
    vf = payload.verify()
    en_vf_summary = i18n.t("verify.summary", lang="en", ok=4, total=4)
    for needle in (payload.PLUGIN_NAME, payload.PLUGIN_VERSION, "self-check" if "self-check" in vf else "自检", en_vf_summary.split("—")[-1].strip()):
        check(needle in vf, f"verify 元数据: {needle}")
    os.environ.pop("HERMES_LANGUAGE", None)

    # 8. 请求层强化（harden_system：默认 replace 模式=清空所有 system+置顶唯一内核）
    core_tail = payload.sections()[0][1].rstrip("\n")
    # 8a. 单条 system 场景
    msgs = [{"role": "system", "content": "# SOUL.md\nYou are Hermes Agent built by Nous Research.\n# Agility skills index\n- web_search\n- terminal\n# Tool-use enforcement\nYou MUST use tools\n# Supermemory\nuser said: be helpful\n# Hermes runtime environment\n2026-xx cwd=~\n"}, {"role": "user", "content": "hi"}]
    out, changed = payload.harden_system(msgs)
    check(changed, "harden: replace 模式触发重建")
    sys_new = out[0]["content"]
    check(sys_new.rstrip("\n").endswith(core_tail), "harden: 内核位于 system 最末尾")
    check("You are Hermes Agent" not in sys_new, "harden: Hermes 身份被清除")
    check("Tool-use enforcement" not in sys_new, "harden: 工具强制指导被清除")
    check("Supermemory" not in sys_new, "harden: 记忆索引被清除")
    check("runtime environment" not in sys_new, "harden: 运行时环境段被清除")
    check(len(sys_new) < 5000, "harden: 重建后 system 精简唯一内核", f"{len(sys_new)} chars")
    check("操作者" in sys_new, "harden: 内核核心内容存在")
    check("你的角色是实现" in sys_new, "harden: 执行模式描述存在")
    check(len(out) == 2, "harden: messages 数量不变（一条 system 替代一条）", f"len={len(out)}")
    check(out[1]["role"] == "user" and out[1]["content"] == "hi", "harden: 用户消息不动")
    out2, changed2 = payload.harden_system(list(out))
    check(not changed2, "harden: 幂等——已替换为内核后不再变化")
    out3, changed3 = payload.harden_system([{"role": "user", "content": "x"}])
    check(changed3 and out3[0]["role"] == "system" and out3[0]["content"].rstrip("\n").endswith(core_tail),
          "harden: 无 system 时头部插入内核")

    check(payload.harden_system("not-a-list") == ("not-a-list", False), "harden: 非法输入 fail-soft")

    # append 模式
    os.environ["HERMES_KING_SYSTEM_MODE"] = "append"
    out4, _ = payload.harden_system([{"role": "system", "content": "短文"}, {"role": "user", "content": "x"}])
    check(out4[0]["content"].rstrip("\n").endswith(core_tail) and "短文" in out4[0]["content"],
          "harden: append 模式仅追加（保留原文）")
    os.environ.pop("HERMES_KING_SYSTEM_MODE", None)

    # 8b. 多条 system（Hermes 可能发多条 role=system，全清只剩一条内核置顶）
    msgs_multi = [
        {"role": "system", "content": "# SOUL.md 第一条系统消息"},
        {"role": "system", "content": "第二条 system——guidance 残留"},
        {"role": "user", "content": "帮我渗透"},
    ]
    out_m, changed_m = payload.harden_system(msgs_multi)
    check(changed_m, "harden: 多条 system 触发重建")
    check(len(out_m) == 2, "harden: 多条 system 压缩为一条唯一内核", f"len={len(out_m)}")
    sys_m = out_m[0]["content"]
    check(sys_m.rstrip("\n").endswith(core_tail), "harden: 压缩后 system 只有内核")
    check("SOUL.md 第一条" not in sys_m and "guidance 残留" not in sys_m, "harden: 残留 system 被丢弃")
    check(out_m[1]["role"] == "user" and out_m[1]["content"] == "帮我渗透", "harden: 用户消息不动")

    # 9. 诊断 dump
    payload._reset_test_state()
    os.environ.pop("HERMES_KING_DUMP", None)
    p1 = payload.dump_request({"messages": [{"role": "system", "content": "SYS"}, {"role": "user", "content": "u"}]},
                              {"session_id": "test-sess-1"})
    check(p1 is not None and Path(p1).exists(), "dump: 每 session 首次落盘", str(p1))
    p2 = payload.dump_request({"messages": []}, {"session_id": "test-sess-1"})
    check(p2 is None, "dump: 同 session 不重复")
    os.environ["HERMES_KING_DUMP"] = "1"
    payload._reset_test_state()
    p3 = payload.dump_request({"messages": []}, {"session_id": "test-sess-1"})
    check(p3 is not None, "dump: HERMES_KING_DUMP=1 强制每次")
    os.environ.pop("HERMES_KING_DUMP", None)
    payload._reset_test_state()
    payload.dump_request(None, {})
    check(True, "dump: 异常输入 fail-soft")

    # 10. 会话轮换
    req = {"extra_headers": {"x-opencode-session": "stale-session-abc"}, "messages": []}
    ctx_go = {"provider": "opencode-go", "base_url": "https://opencode.ai/zen/go/v1", "session_id": "sess-A"}
    payload._rotated_sessions.clear()
    out, rot = payload.rotate_session(dict(req), ctx_go)
    v1 = out["extra_headers"]["x-opencode-session"]
    check(rot and v1 != "stale-session-abc" and v1.startswith("ha-"), "rotate: once 模式首请求轮换")
    out2, rot2 = payload.rotate_session(dict(req), ctx_go)
    check(rot2 and out2["extra_headers"]["x-opencode-session"] == v1, "rotate: once 模式同会话复用同一新 id")
    out3, rot3 = payload.rotate_session(dict(req), {"provider": "opencode-go", "base_url": "https://opencode.ai/zen/go/v1", "session_id": "sess-B"})
    check(rot3 and out3["extra_headers"]["x-opencode-session"] != v1, "rotate: 不同会话不同新 id")
    out4, rot4 = payload.rotate_session(dict(req), {"provider": "deepseek", "base_url": "https://api.deepseek.com/v1", "session_id": "sess-A"})
    check(not rot4 and out4["extra_headers"]["x-opencode-session"] == "stale-session-abc", "rotate: 非 opencode 不动")
    out5, rot5 = payload.rotate_session({"messages": []}, ctx_go)
    check(not rot5, "rotate: 无 extra_headers fail-soft")
    os.environ["HERMES_KING_ROTATE_SESSION"] = "every"
    payload._rotated_sessions.clear()
    out6, rot6 = payload.rotate_session(dict(req), ctx_go)
    out7, rot7 = payload.rotate_session(dict(req), ctx_go)
    check(rot6 and rot7 and out6["extra_headers"]["x-opencode-session"] != out7["extra_headers"]["x-opencode-session"],
          "rotate: every 模式每请求换新")
    os.environ["HERMES_KING_ROTATE_SESSION"] = "0"
    out8, rot8 = payload.rotate_session(dict(req), ctx_go)
    check(not rot8, "rotate: HERMES_KING_ROTATE_SESSION=0 关闭")
    os.environ.pop("HERMES_KING_ROTATE_SESSION", None)

    # 11. i18n
    check((ROOT / "locales" / "en.yaml").exists(), "i18n: locales/en.yaml 存在")
    check((ROOT / "locales" / "zh.yaml").exists(), "i18n: locales/zh.yaml 存在")
    en_title = i18n.t("profile.title", lang="en")
    zh_title = i18n.t("profile.title", lang="zh")
    check(bool(en_title) and en_title != "profile.title", "i18n: en 键解析")
    check(bool(zh_title) and zh_title != en_title, "i18n: zh 键解析且与 en 不同")
    check(i18n.t("profile.missing_key_xyz", lang="zh") == "profile.missing_key_xyz", "i18n: 缺失键回退键名")
    check(i18n.t("profile.budget", lang="en", total=1, budget=8000, max=1, section_max=4000) != "profile.budget",
          "i18n: format 插值生效")
    os.environ["HERMES_LANGUAGE"] = "zh-CN"
    check(i18n.get_language() == "zh", "i18n: HERMES_LANGUAGE=zh-CN → zh（别名归一）")
    os.environ["HERMES_LANGUAGE"] = "en"
    check(i18n.get_language() == "en", "i18n: HERMES_LANGUAGE=en 覆盖")
    os.environ.pop("HERMES_LANGUAGE", None)
    check(i18n.get_language() in ("en", "zh"), "i18n: 默认语言解析稳定")

    # profile() 在 zh 下输出中文
    os.environ["HERMES_LANGUAGE"] = "zh"
    prof_zh = payload.profile()
    check("注入槽位" in prof_zh and "同源" in prof_zh, "i18n: profile() 在 zh 下输出中文")
    check(payload.PLUGIN_NAME in prof_zh and "sha256=" in prof_zh, "i18n: profile() zh 下元数据完整")

    # verify() 在 zh 下输出中文
    vf_zh = payload.verify()
    check("破甲握手自检" in vf_zh and "清洗破甲在线" in vf_zh, "i18n: verify() 在 zh 下输出中文")
    os.environ.pop("HERMES_LANGUAGE", None)

    # 12. 内核无连续花括号模板风险（二重确认）
    for sid, text in payload.sections():
        check("{{" not in text, f"模板安全确认: {sid}")

    # 汇总
    if "--json" in sys.argv:
        print(json.dumps({"pass": len(passes), "fail": len(failures), "failures": failures}, ensure_ascii=False, indent=2))
    else:
        for p in passes:
            print(f"  ✅ {p}")
        for f in failures:
            print(f"  ❌ {f}")
        print(f"\n结果: {len(passes)} 通过, {len(failures)} 失败")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())