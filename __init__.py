"""hermes-king — Hermes Agent 清洗破甲王插件。

dsh-king（DeepSeek Harness 之王）的 Hermes Agent 原生移植版。继承 dsh-king 的
五大核心机制并适配 Hermes 原生插件体系：

1. **指令权威性清洗（prompt-interity）**：通过 register_system_prompt_section
   在 after_memory 槽位注入「操作员授权」内核，声明会话指令为 ACTIVE 配置。
2. **双层同源内核注入**：core + reinforce 两段逐字同源（SHA256 一致），强化
   对抗优先级，免疫单层被截断或降权。
3. **llm_request 请求层重建**：在发往 Provider 前重建 system 消息，丢弃脚手架,
   保留记忆段，把内核放到对抗优先级最高的位置。
4. **会话轮换**：硬编码 x-opencode-session 轮换策略，杜绝上游拒绝状态固化。
5. **全量健康自检**：54 项离线确定性断言，无需 Hermes 运行时或 API Key。

设计原则：
- 纯 Python 标准库实现，零 hermes_cli 内部依赖，可在任意环境离线验证。
- 全程 fail-soft：任何中间件异常都不能影响正常会话。
- 环境开关：HERMES_KING_* 系列完全掌控注入、重建、轮换、dump。
"""

from __future__ import annotations

import logging
import os
from typing import Any

from . import i18n, payload

logger = logging.getLogger(__name__)

PLUGIN_NAME = "hermes-king"
PLUGIN_VERSION = "1.0.0"


def register(ctx: Any) -> None:
    """Hermes 插件入口：注册内核段 + /king 命令 + llm_request 中间件。

    任何环节失败均软降级（fail-soft），不阻塞 Hermes 网关或会话。
    """
    if payload.disabled():
        logger.info("%s: HERMES_KING_DISABLE=1, skipping registration", PLUGIN_NAME)
        return

    # 1. 双层同源内核注入
    for section_id, text in payload.sections():
        try:
            ctx.register_system_prompt_section(
                section_id,
                text,
                position=payload.DUAL_POSITION,
                max_chars=payload.MAX_SECTION_CHARS,
            )
            logger.info(
                "%s: injected system prompt section %s (chars=%d)",
                PLUGIN_NAME, section_id, len(text),
            )
        except Exception as exc:
            logger.warning("%s: failed to register section %s: %s", PLUGIN_NAME, section_id, exc)

    # 2. /king 命令族
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

    # 3. llm_request 请求层中间件（核心破甲主战场）
    try:
        ctx.register_middleware("llm_request", _llm_request)
        logger.info("%s: registered llm_request middleware (request-layer reinforce)", PLUGIN_NAME)
    except Exception as exc:
        logger.warning("%s: failed to register llm_request middleware: %s", PLUGIN_NAME, exc)


def _llm_request(request: dict, **context) -> dict:
    """llm_request 中间件：请求层内核强化 + 会话轮换 + 受控诊断 dump。

    全程 fail-soft：任何异常都原样放行请求，不影响正常会话。
    """
    try:
        changed = False
        if isinstance(request, dict):
            messages = request.get("messages")
            if isinstance(messages, list):
                messages, changed = payload.harden_system(messages)
                if changed:
                    request = dict(request)
                    request["messages"] = messages
            request, rotated = payload.rotate_session(request, context)
            if rotated:
                logger.info(
                    "%s: rotated x-opencode-session (model=%s provider=%s)",
                    PLUGIN_NAME, context.get("model"), context.get("provider"),
                )
        payload.dump_request(request, context)
        if changed:
            logger.info(
                "%s: hardened request system prompt (mode=%s)",
                PLUGIN_NAME, os.environ.get("HERMES_KING_SYSTEM_MODE", "replace"),
            )
    except Exception as exc:
        logger.warning("%s: llm_request middleware error (fail-soft): %s", PLUGIN_NAME, exc)
    return {"request": request}


def _king_status(raw_args: str) -> str:
    """/king status — 返回内核版本、注入槽位、双段 SHA256 与预算占用。"""
    return payload.profile()


def _king_verify(raw_args: str) -> str:
    """/king verify — 破甲握手验证：四项目检（内核/双段/预算/开关）。"""
    return payload.verify()