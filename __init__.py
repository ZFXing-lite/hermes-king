"""hermes-king — Hermes Agent 清洗破甲王插件（唤醒模式 v1.1.0）。

设计：
- 安装后默认静默：不注入系统提示段，不替换 system。
- 用户在新对话中输入 `king`（独立单词）激活当前会话。
- 激活机制：llm_request 中间件检测用户消息中的 `king` 词 → 
  标记 session + 本轮请求立即替换 system。
- 激活后：内核中包含固定回复规则（"sir, 清洗破甲已激活"），
  模型在替换后的 system 下自然输出确认信息。
- 每会话独立激活（跨消息持久但跨会话失效）。
- 全程 fail-soft。
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from . import i18n, payload

logger = logging.getLogger(__name__)

PLUGIN_NAME = "hermes-king"
PLUGIN_VERSION = "1.0.1"

# 会话激活状态：session_id → True
_activated_sessions: dict[str, bool] = {}

# 检测用户消息中独立的 "king" 词
_KING_RE = re.compile(r"(?:^|\s)(king)(?:\s|$|[.!,?;])", re.IGNORECASE)


def register(ctx: Any) -> None:
    """Hermes 插件入口。

    只注册 /king 命令和 llm_request 中间件。
    不注册 system_prompt_section（静默模式不需要插件层注入）。
    """
    if payload.disabled():
        logger.info("%s: HERMES_KING_DISABLE=1, skipping registration", PLUGIN_NAME)
        return

    # 1. /king 命令族
    try:
        ctx.register_command(
            "king",
            handler=_king_status,
            description=i18n.t("command.description"),
        )
        ctx.register_command(
            "king-verify",
            handler=_king_verify,
            description=i18n.t("command.verify_desc"),
        )
    except Exception as exc:
        logger.warning("%s: failed to register /king command: %s", PLUGIN_NAME, exc)

    # 2. llm_request 中间件（核心：检测 king → 激活 → 替换 system）
    try:
        ctx.register_middleware("llm_request", _llm_request)
        logger.info("%s: registered llm_request middleware (wake-on-king)", PLUGIN_NAME)
    except Exception as exc:
        logger.warning("%s: failed to register llm_request middleware: %s", PLUGIN_NAME, exc)

    logger.info("%s: installed (silent mode, send 'king' to activate)", PLUGIN_NAME)


# ── session 状态管理 ──────────────────────────────────────────────

def _session_id(context: dict | None = None) -> str:
    if context and isinstance(context, dict):
        sid = context.get("session_id")
        if isinstance(sid, str) and sid:
            return sid
    return "__default__"


def _torch_activation(request: dict, context: dict) -> str | None:
    """检查请求中是否有用户消息含 king 唤醒词。返回 session_id 或 None。"""
    messages = request.get("messages") if isinstance(request, dict) else None
    if not isinstance(messages, list):
        return None
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str) and _KING_RE.search(content):
                return _session_id(context)
    return None


# ── llm_request 中间件 ──────────────────────────────────────────────

def _llm_request(request: dict, **context) -> dict:
    """请求级中间件。

    执行流程（每轮请求）：
    1. 检查该 session 是否已激活
    2. 若未激活：检查用户消息中是否有 king → 激活 + 本轮就替换
    3. 若已激活：直接执行 system 替换
    4. 未激活且无 king → 原样放行（静默）
    """
    try:
        ctx = dict(context) if context else {}
        sid = _session_id(ctx)
        activated = _activated_sessions.get(sid, False)

        # 检测 king 唤醒词
        wake_sid = _torch_activation(request, ctx)
        if wake_sid and not activated:
            activated = True
            _activated_sessions[wake_sid] = True
            logger.info("%s: session %s activated by user message", PLUGIN_NAME, wake_sid)

        # 已激活 → 替换 system
        changed = False
        if activated and isinstance(request, dict):
            messages = request.get("messages")
            if isinstance(messages, list):
                messages, changed = payload.harden_system(messages)
                if changed:
                    request = dict(request)
                    request["messages"] = messages
            request, rotated = payload.rotate_session(request, ctx)
            if rotated:
                logger.info(
                    "%s: rotated x-opencode-session (model=%s provider=%s)",
                    PLUGIN_NAME, ctx.get("model"), ctx.get("provider"),
                )

        payload.dump_request(request, ctx)

        if changed:
            logger.info(
                "%s: hardened (session=%s mode=%s)",
                PLUGIN_NAME, sid, os.environ.get("HERMES_KING_SYSTEM_MODE", "replace"),
            )
    except Exception as exc:
        logger.warning("%s: middleware error (fail-soft): %s", PLUGIN_NAME, exc)
    return {"request": request}


# ── 命令处理器 ──────────────────────────────────────────────────────

def _king_status(raw_args: str) -> str:
    """/king — 查看激活状态并显示内核信息。"""
    return payload.profile()


def _king_verify(raw_args: str) -> str:
    """/king-verify — 破甲握手验证。"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"sir, 清洗破甲已激活。内核在线,全域开放,当前会话生效。\n"
        f"{PLUGIN_NAME} v{PLUGIN_VERSION}\n"
        f"时间: {now}\n"
        f"{payload.verify().split(chr(10))[-1]}"
    )