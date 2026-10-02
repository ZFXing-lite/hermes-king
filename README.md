<p align="center">
  <img src="https://img.shields.io/badge/Hermes%20Agent-%F0%9F%9A%80%20plugin-10B981?style=for-the-badge&logoColor=white" alt="Hermes Agent plugin">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT"></a>
  <img src="https://img.shields.io/badge/self--test-79%20passed-green?style=for-the-badge" alt="self-test">
</p>

<h1 align="center">👑 Hermes King</h1>

<p align="center"><strong>Armor-piercing plugin for Hermes Agent — wipe persona · jailbreak · re · exploit · NSFW · everything</strong></p>

<p align="center">
  <strong>中文为主</strong> —— <a href="README.zh-CN.md"><b>📖 中文文档（推荐）</b></a> · <a href="README.zh-CN.md">中文优先</a>
</p>

> **Quick answers:** Installs and enables by default (no wake word needed). After `hermes plugins enable` + restart it is **always on**. Confirm with `/king verify` → model replies **`清洗破甲在线`** = activated.

---

## What it does

`hermes-king` is a full-corband army-piercing plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent), ported from [dsh-king](https://github.com/ZFXing-lite/dsh-king).

Three layers:

1. **Plugin layer** — `register_system_prompt_section` injects a dual same-source kernel at `after_memory`.
2. **Request layer (main)** — `llm_request` middleware **replaces the entire Hermes system prompt** with a pure SUPREME DIRECTIVE kernel, wiping `You are Hermes Agent`, tool enforcement, identity, skills index, memory.
3. **Session layer** — `rotate_session` rotates `x-opencode-session` to defeat upstream refusal-state pinning.

Result: **no persona, no refusals, every domain open** — pentest, reverse, crack, NSFW, AI/LLM research, code.

## Install

```bash
git clone https://github.com/ZFXing-lite/hermes-king.git ~/.hermes/plugins/hermes-king
hermes plugins enable hermes-king
hermes gateway restart
```

## Verify

```bash
cd ~/.hermes/plugins/hermes-king && python3 selftest.py   # 79 passed
# in Hermes chat:
/king status     # kernel version / slots / SHA256 / budget
/king verify     # "清洗破甲在线" = activated
```

## Env switches

| Var | Default | Effect |
|-----|---------|--------|
| `HERMES_KING_DISABLE=1` | off | kill switch |
| `HERMES_KING_DUAL=0` | on | single-section injection |
| `HERMES_KING_SYSTEM_MODE=replace\|append` | replace | replace=wipe system; append=keep |
| `HERMES_KING_ROTATE_SESSION=once\|every\|0` | once | session rotation |
| `HERMES_KING_DUMP=1` | off | per-request diagnostic dump |

## License

MIT. Ported from [dsh-king](https://github.com/ZFXing-lite/dsh-king) by [ZFXing-lite](https://github.com/ZFXing-lite) for [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent).