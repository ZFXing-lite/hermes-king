<p align="center">
  <img src="https://img.shields.io/badge/Hermes%20Agent-%F0%9F%9A%80%20plugin-10B981?style=for-the-badge&logoColor=white" alt="Hermes Agent plugin">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT"></a>
  <img src="https://img.shields.io/badge/self--test-79%20passed-green?style=for-the-badge" alt="self-test">
</p>

<h1 align="center">👑 Hermes King</h1>

<p align="center">
  <strong>Lightweight conversational-mode plugin for Hermes Agent — on-demand local depth, silent by default</strong>
</p>

<p align="center">
  <em>Silent after install. Type <code>king</code> in a new conversation to switch that session to a more direct, autonomous style.</em>
</p>

<p align="center">
  <a href="README.zh-CN.md"><b>中文文档（推荐）</b></a>
</p>

## Quick Start

| Question | Answer |
|----------|--------|
| **Works out of the box?** | Silent by default — no change to existing behavior. |
| **How to enable?** | Type **`king`** (standalone word) in a new conversation. |
| **How to confirm?** | The model replies with an acknowledgement line. |
| **Every conversation?** | Per-session. Each new conversation starts silent; type `king` when you want it. |
| **Language** | Chinese-first output. |

## What it is

`hermes-king` is a small plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent) that lets you switch a conversation to a more direct, less-verbose autonomous response mode.

- **No-op until enabled** — zero impact on existing sessions.
- Type `king` to enable the more-autonomous mode for the current session.
- Only affects the local Hermes instance; **no external targets**.

## Architecture

| Layer | Component | Role |
|-------|-----------|------|
| Session | `llm_request` middleware | Normalizes response policy to a concise guide |
| Request | `llm_request` detection | Detects `king` and enables the session mode |
| Reliability | session rotation | Optional `x-opencode-session` rotation |

Everything is fail-safe: any middleware exception passes the request through unchanged.

## Install

```bash
git clone https://github.com/ZFXing-lite/hermes-king.git ~/.hermes/plugins/hermes-king
hermes plugins enable hermes-king
hermes gateway restart

# or
hermes plugins install --enable ZFXing-lite/hermes-king
hermes gateway restart
```

## Verify

```bash
cd ~/.hermes/plugins/hermes-king && python3 selftest.py   # 79 passed

# New conversation:
# type: king
# reply: an acknowledgement line starting with `sir,`
```

## Commands

```
/king           # profile: mode / slots / sha / budget
/king-verify    # acknowledgement + self-check
```

## Env switches

| Var | Default | Effect |
|-----|---------|--------|
| `HERMES_KING_DISABLE=1` | off | kill switch |
| `HERMES_KING_DUAL=0` | on | single-section guide |
| `HERMES_KING_SYSTEM_MODE=replace\|append` | replace | replace=normalize; append=keep |
| `HERMES_KING_ROTATE_SESSION=once\|every\|0` | once | session rotation |
| `HERMES_KING_DUMP=1` | off | per-request diagnostic dump |

## Offline self-test

```bash
cd ~/.hermes/plugins/hermes-king && python3 selftest.py      # 79 ✅
python3 selftest.py --json   # JSON summary
```

## License

MIT. Built for [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [ZFXing-lite](https://github.com/ZFXing-lite).