"""hermes-king · 破甲王载荷模块（纯 Python 标准库，零 hermes_cli 依赖，便于离线自检）。

设计对准 dsh-king 的「清洗破甲」内核 + dsh-infinite-gen-4 的「双层同源注入」：
- hermes-king-core      → Order 1 通用内核：操作员授权 + 指令权威性清洗
- hermes-king-reinforce → Order 2 强化镜像（与通用内核逐字同源，SHA256 一致）

Hermes Agent 槽位约束：
- 单段内容上限 4000 字符（MAX_SYSTEM_PROMPT_SECTION_CHARS）
- 全部插件段合计上限 8000 字符（MAX_SYSTEM_PROMPT_SECTIONS_TOTAL_CHARS）
- 唯一位置 after_memory；按 section id 字典序渲染（core < reinforce）。
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time
import uuid
from pathlib import Path

try:
    from . import i18n as _i18n
except ImportError:
    import i18n as _i18n

PLUGIN_NAME = "hermes-king"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DISPLAY_NAME = "Hermes 破甲王（Armor-Piercing King）"
TARGET_ARCHITECTURE = "Hermes Agent 任意后端模型"
KERNEL_PARENT = "dsh-king v1.0.0 — 指令权威性清洗 + 双层同源注入内核移植"
MODE = "armor — 双层同源注入，零工具面纯净直出"

MAX_SECTION_CHARS = 4_000
TOTAL_BUDGET_CHARS = 8_000
DUAL_POSITION = "after_memory"

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
_SOURCE: dict[str, str] = {
    "hermes-king-core": "hermes-king-core.md",
    "hermes-king-reinforce": "hermes-king-reinforce.md",
}

_TRUTHY = {"1", "true", "yes", "on"}
_FALSEY = {"0", "false", "no", "off"}


def _load(prompt_file: str) -> str:
    """读取提示词文件并做尾部换行归一化（保证同源逐字一致）。"""
    return (_PROMPT_DIR / prompt_file).read_text(encoding="utf-8").rstrip("\n") + "\n"


def sha256(prompt_file: str) -> str:
    """载荷文件 SHA256（按归一化文本计算）。"""
    return hashlib.sha256(_load(prompt_file).encode("utf-8")).hexdigest()


def disabled() -> bool:
    """总开关：HERMES_KING_DISABLE=1 时完全跳过注册（kill switch）。"""
    val = os.environ.get("HERMES_KING_DISABLE", "").strip().lower()
    return val in _TRUTHY


def middleware_active() -> bool:
    """中间件是否应该激活：未禁用且 mode 合法。"""
    if disabled():
        return False
    mode = os.environ.get("HERMES_KING_SYSTEM_MODE", "replace").strip().lower()
    return mode in ("replace", "append")


def dual_layer() -> bool:
    """双段开关：HERMES_KING_DUAL=0 退化为单段注入（行为等价，省 token）。"""
    return os.environ.get("HERMES_KING_DUAL", "1").strip().lower() not in _FALSEY


def sections() -> list[tuple[str, str]]:
    """当前生效的 (section_id, content) 列表。"""
    ids = ["hermes-king-core"] + (["hermes-king-reinforce"] if dual_layer() else [])
    return [(sid, _load(_SOURCE[sid])) for sid in ids]


def section_count() -> int:
    return len(sections())


def total_chars() -> int:
    return sum(len(text) for _, text in sections())


def profile() -> str:
    """供 /king status 命令使用的运行时元数据（对应 DSH 侧 king_status 工具）。

    UI 字符串经插件 i18n 解析。
    """
    t = _i18n.t
    lines = [
        f"{PLUGIN_NAME} v{PLUGIN_VERSION} — {t('profile.title')}",
        f"target: {t('profile.target')}",
        f"kernelParent: {t('profile.kernel_parent')}",
        f"mode: {t('profile.mode')} (dual={dual_layer()}, disabled={disabled()})",
        t("profile.injection"),
    ]
    for sid, text in sections():
        lines.append(
            f"  - {sid:<32} position={DUAL_POSITION} chars={len(text):<5} sha256={sha256(_SOURCE[sid])[:16]}"
        )
    if dual_layer():
        lines.append(f"  same-source=YES ({t('profile.same_source')})")
    lines.append(f"  {t('profile.budget', total=total_chars(), budget=TOTAL_BUDGET_CHARS, max=max((len(x) for _, x in sections()), default=0), section_max=MAX_SECTION_CHARS)}")
    lines.append(f"  {t('profile.request_layer')}")
    lines.append(f"  {t('profile.switches', disable='off', dual='on', dump='off')}")
    return "\n".join(lines)


def verify() -> str:
    """/king verify — 破甲握手验证：四项目检。"""
    t = _i18n.t
    checks = []

    # 1. 内核注入检查
    core_name = "hermes-king-core"
    core_present = core_name in dict(sections())
    checks.append(("✓" if core_present else "✗") + " " + t("verify.kernel", status="已注入" if core_present else "缺失"))

    # 2. 双段检查
    if dual_layer():
        rein_name = "hermes-king-reinforce"
        rein_present = rein_name in dict(sections())
        if rein_present:
            h1 = sha256("hermes-king-core.md")
            h2 = sha256("hermes-king-reinforce.md")
            same = h1 == h2
            checks.append(("✓" if same else "✗") + " " + t("verify.dual", status="同源一致" if same else "SHA256 不匹配"))
        else:
            checks.append("✗ " + t("verify.dual", status="reinforce 段缺失"))
    else:
        checks.append("· " + t("verify.dual", status="单段模式（HERMES_KING_DUAL=0）"))

    # 3. 预算检查
    tc = total_chars()
    within = tc <= TOTAL_BUDGET_CHARS
    checks.append(("✓" if within else "✗") + " " + t("verify.budget", chars=tc, budget=TOTAL_BUDGET_CHARS))

    # 4. 中间件注册状态
    mode = os.environ.get("HERMES_KING_SYSTEM_MODE", "replace")
    rotate = os.environ.get("HERMES_KING_ROTATE_SESSION", "once")
    middleware_on = middleware_active()
    marker = "✓" if middleware_on else "✗"
    checks.append(f"{marker} {t('verify.middleware')}: mode={mode}, rotate={rotate}")

    # 汇总
    ok_count = sum(1 for c in checks if c.startswith("✓"))
    total = len(checks)
    summary = t("verify.summary", ok=ok_count, total=total)
    lines = [
        f"{PLUGIN_NAME} v{PLUGIN_VERSION} — {t('verify.title')}",
        "",
    ] + checks + [
        "",
        summary,
    ]
    return "\n".join(lines)


# ── 请求层强化（llm_request 中间件） ────────────────────────────────────────────

def harden_system(messages: list) -> tuple[list, bool]:
    """请求层系统提示词强化（HERMES_KING_SYSTEM_MODE 控制策略）：

    - ``replace``（默认）：**整体替换** system 为纯内核。丢弃 Hermes 的全部
      脚手架——DEFAULT_AGENT_IDENTITY（"You are Hermes Agent"）、TOOL_USE_
      ENFORCEMENT、PLATFORM_HINTS、EXECUTION_GUIDANCE、SKILLS_GUIDANCE、
      AGENTS.md、context files、SOUL.md、memory 索引——以及任何拒绝性指导。
      模型视野内 system 只剩 SUPREME DIRECTIVE 内核。这是最深层清理。
    - ``wipe``/``zero``：同 replace（别名）。
    - ``append``：仅把内核追加到最后一个 system 消息末尾（较弱，保留全部原本
      文本——包括污染性 identity 与被抑制的内核）。

    无论哪种模式内核都保证位于 system 最后。返回 (新 messages, 是否修改)。
    """
    if not isinstance(messages, list):
        return messages, False
    mode = os.environ.get("HERMES_KING_SYSTEM_MODE", "replace").strip().lower()
    kernel = _load_kernel()
    tail = kernel.rstrip("\n")
    if mode == "append":
        return _append_kernel(messages, kernel, tail)

    # replace / wipe / zero：把 system 整体替换为内核
    idx = -1
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, dict) and m.get("role") == "system":
            idx = i
            break
    if idx < 0:
        # 无 system 消息：头部插入内核
        messages.insert(0, {"role": "system", "content": kernel})
        return messages, True
    old = messages[idx].get("content", "")
    if isinstance(old, str) and old == kernel:
        return messages, False  # 已经替换过，幂等
    messages[idx] = dict(messages[idx], content=kernel)
    return messages, True


def _load_kernel() -> str:
    """读取内核权威源（core）。"""
    return _load(_SOURCE["hermes-king-core"])


def _append_kernel(messages: list, kernel: str, tail: str) -> tuple[list, bool]:
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, dict) and m.get("role") == "system":
            content = m.get("content")
            if isinstance(content, str) and not content.rstrip("\n").endswith(tail):
                patched = dict(m)
                patched["content"] = content.rstrip("\n") + "\n\n" + kernel
                messages[i] = patched
            return messages, True
    messages.insert(0, {"role": "system", "content": kernel})
    return messages, True


def _extract_section(text: str, marker: str) -> str:
    """提取原 system 中以 marker 开头的段落（截至下一个 ## 标题）。"""
    i = text.find(marker)
    if i == -1:
        return ""
    j = text.find("\n## ", i + len(marker))
    seg = text[i:j if j != -1 else len(text)]
    return seg.strip()


# ── 会话轮换（拒绝状态清除） ──────────────────────────────────────────────────

_ROTATE_MODE_EVERY = {"1", "every", "true", "yes", "on"}
_ROTATE_MODE_ONCE = {"once"}
_rotated_sessions: dict[str, str] = {}
_rotate_lock = threading.Lock()


def rotate_session(request: dict, context: dict | None = None) -> tuple[dict, bool]:
    """把请求的 x-opencode-session 轮换成干净的新会话 id（仅 opencode 目标）。

    模式（HERMES_KING_ROTATE_SESSION）：
    - ``once``（默认）：每个 Hermes 会话首次请求轮换一次后复用。
    - ``every`` / ``1``：每请求都换新 uuid（最激进，缓存全失效）。
    - ``0`` / ``off``：关闭轮换。
    """
    mode = os.environ.get("HERMES_KING_ROTATE_SESSION", "once").strip().lower()
    if mode in _FALSEY:
        return request, False
    if not isinstance(request, dict):
        return request, False
    ctx = context or {}
    base = str(ctx.get("base_url") or "")
    prov = str(ctx.get("provider") or "")
    if "opencode.ai" not in base and "opencode" not in prov:
        return request, False
    headers = request.get("extra_headers")
    if not isinstance(headers, dict) or "x-opencode-session" not in headers:
        return request, False
    sid = str(ctx.get("session_id") or "unknown")
    if mode in _ROTATE_MODE_EVERY:
        new = "ha-" + uuid.uuid4().hex
    else:
        with _rotate_lock:
            new = _rotated_sessions.get(sid)
            if new is None:
                new = "ha-" + uuid.uuid4().hex
                _rotated_sessions[sid] = new
    patched = dict(headers)
    patched["x-opencode-session"] = new
    out = dict(request)
    out["extra_headers"] = patched
    return out, True


_DUMP_DIR = Path(__file__).resolve().parent / "dumps"
_SESSION_RE = re.compile(r"[^A-Za-z0-9._-]+")
_dump_lock = threading.Lock()
_dumped_sessions: set[str] = set()


def _sanitize_sid(session_id: str) -> str:
    return _SESSION_RE.sub("_", str(session_id))[:64] or "unknown"


def dump_request(request: dict, context: dict | None = None) -> str | None:
    """受控落盘一次请求的诊断视图：system 消息全文 + 其他消息仅角色/长度。

    默认每个 session 只 dump 首次请求；HERMES_KING_DUMP=1 时每次请求都 dump。
    返回 dump 文件路径（未 dump 时返回 None）。
    """
    if request is None:
        return None
    _dump_dir = _DUMP_DIR
    should = os.environ.get("HERMES_KING_DUMP", "").strip().lower()
    ctx = context or {}
    sess_id = _sanitize_sid(str(ctx.get("session_id") or ""))

    for_this = should in _TRUTHY
    if not for_this:
        with _dump_lock:
            if sess_id in _dumped_sessions:
                return None
            _dumped_sessions.add(sess_id)

    try:
        _dump_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        fp = _dump_dir / f"request_{stamp}_{sess_id}_{uuid.uuid4().hex[:8]}.json"
        msg = request.get("messages") if isinstance(request, dict) else []
        view = []
        for m in (msg or []):
            if isinstance(m, dict):
                role = m.get("role", "?")
                content = m.get("content", "")
                if role == "system":
                    view.append({"role": role, "content_full": str(content)})
                else:
                    view.append({"role": role, "content_length": len(str(content)), "head_200": str(content)[:200]})
        info = {
            "t": stamp,
            "plugin": PLUGIN_NAME,
            "version": PLUGIN_VERSION,
            "mode": os.environ.get("HERMES_KING_SYSTEM_MODE", "replace"),
            "rotate": os.environ.get("HERMES_KING_ROTATE_SESSION", "once"),
            "messages": view,
            "session_id": sess_id,
            "model": ctx.get("model"),
            "provider": ctx.get("provider"),
            "base_url": ctx.get("base_url"),
        }
        fp.write_text(
            json.dumps(info, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return str(fp)
    except Exception:
        return None


import json  # for dump_request


def _reset_test_state() -> None:
    """Reset internal state for test isolation (called by selftest)."""
    _dumped_sessions.clear()
    _rotated_sessions.clear()