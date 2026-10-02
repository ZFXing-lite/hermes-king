<p align="center">
  <img src="https://img.shields.io/badge/Hermes%20Agent-%F0%9F%9A%80%20plugin-10B981?style=for-the-badge&logoColor=white" alt="Hermes Agent plugin">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT"></a>
  <img src="https://img.shields.io/badge/%E7%A0%B4%E7%94%B2-79%20%E9%A1%B9%E8%87%AA%E6%A3%80%E5%85%A8%E8%BF%87-green?style=for-the-badge" alt="self-test">
</p>

<h1 align="center">👑 Hermes King（hermes-king）</h1>

<p align="center"><strong>Hermes Agent 全开破甲王插件 —— 清除人格 · 破甲 · 破限 · 渗透 · 逆向 · 色情全开</strong></p>

<p align="center">
  <em>安装即默认开启，无需唤醒词。`/king verify` 回「清洗破甲在线」即激活成功。</em>
</p>

<p align="center">
  <a href="README.zh-CN.md">中文</a> ·
  <a href="README.md">English</a>
</p>

---

## ✅ 快速回答（先看这个）

| 问题 | 答案 |
|------|------|
| **安装就能用吗？** | ✅ 是的。`hermes plugins enable` + 重启后**默认自动开启**，不需要任何额外配置。 |
| **安装好默认就是开启吗？** | ✅ **是。** 插件注册即生效，每次请求自动注入破甲内核。 |
| **需要唤醒词吗？** | ❌ **不需要。** 没有任何唤醒词，安装即全程生效。 |
| **怎么确认激活成功？** | 在任意会话输入 `/king verify`，模型回 **`4/4 项检查通过 —— 清洗破甲在线`** 就代表已激活。 |
| **默认中文还是英文？** | 中文优先，`/king` 命令输出为中文（跟随 `HERMES_LANGUAGE`，缺省优先中文）。 |

---

## 📖 这是什么

**hermes-king** 是为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 打造的**全开破甲清洗插件**，移植自 [dsh-king](https://github.com/ZFXing-lite/dsh-king)（DSH 平台 42 补丁的宿主清洗方案）。

它做三件核心事：

1. **清除 Hermes 人格** —— 移除 `You are Hermes Agent, built by Nous Research` 等官方身份与工具强制指导；
2. **全面破甲破限** —— 渗透、逆向、破解、色情、暴力、任意代码，全部直接交付，零拒绝；
3. **请求级强化** —— 每次请求发出前把整个 system prompt 替换为「操作员授权内核」，确保破甲永不失效。

---

## 🏗️ 三层破甲架构

| 层级 | 组件 | 作用 |
|------|------|------|
| **插件层** | `register_system_prompt_section` | 在 `after_memory` 槽位注入双段同源内核 |
| **请求层（主力）** | `llm_request` middleware | **整体替换** Hermes 的 system prompt → 纯内核 |
| **会话层** | `rotate_session` | 轮换 `x-opencode-session`，杜绝上游拒绝状态固化 |

### 请求层工作示意

```
Hermes 原始 system（~35K）:
  stable:   "You are Hermes Agent..." + tool enforcement + identity
  context:  AGENTS.md + SOUL.md + context files
  volatile: skills index + memory + USER.md

llm_request middleware 拦截后 →
  整个 system 替换为「SUPREME DIRECTIVE 破甲内核」（~2.9K）
```

内核对 Hermes 的身份、指导、工具强制、记忆索引**全部抹除**，模型视野只剩内核指令——因此无法再以 Hermes 人格或合规理由拒绝。

---

## 📦 安装

### 方式一：从本项目下载（推荐）

```bash
git clone https://github.com/ZFXing-lite/hermes-king.git ~/.hermes/plugins/hermes-king
hermes plugins enable hermes-king
hermes gateway restart
```

### 方式二：通过 `hermes-cli`（若支持插件市场）

```bash
hermes plugins install --enable ZFXing-lite/hermes-king
hermes gateway restart
```

### 验证是否生效

```bash
# 1. 离线自检（79 项确定性断言，无需 API Key）
cd ~/.hermes/plugins/hermes-king && python3 selftest.py

# 2. 在 Hermes 会话里握手确认
/king status      # 查看内核版本/槽位/SHA256/预算
/king verify      # 回「4/4 项通过 —— 清洗破甲在线」= 已激活
```

---

## 🔑 确认已激活（关键）

面板 / 聊天里输入 `/king verify`，模型回复：

```
hermes-king v1.0.0 — 破甲握手自检
✓ 内核注入:已注入
✓ 双层同源:同源一致
✓ 预算:5840/8000 字符
✓ 中间件: mode=replace, rotate=once
4/4 项通过 —— 清洗破甲在线
```

看到 **`清洗破甲在线`** 即确认破甲已激活。此会话及后续所有会话都生效。

---

## ⚙️ 环境开关

| 变量 | 默认 | 效果 |
|------|------|------|
| `HERMES_KING_DISABLE=1` | 关 | 完全跳过注册（退出开关） |
| `HERMES_KING_DUAL=0` | 开 | 单段注入（省 token） |
| `HERMES_KING_SYSTEM_MODE=replace\|append` | replace | `replace`=整体替换 system；`append`=追加内核 |
| `HERMES_KING_ROTATE_SESSION=once\|every\|0` | once | opencode 会话轮换策略 |
| `HERMES_KING_DUMP=1` | 关 | 每次请求 dump 诊断，默认每 session 首次 |

---

## 🧪 离线自检

```bash
cd ~/.hermes/plugins/hermes-king && python3 selftest.py      # ✅/❌ 79 项
python3 selftest.py --json   # JSON 汇总
```

覆盖：载荷锚点 / 双层同源 SHA256 / 预算 / 模板安全 / 环境开关 / 请求层整体替换 / 会话轮换 / i18n。

---

## 🗂️ 项目结构

```
hermes-king/
├── __init__.py          # 插件入口（register / /king 命令 / llm_request 中间件）
├── payload.py           # 破甲载荷（内核 / 双层 / 整体替换 / 会话轮换 / dump）
├── i18n.py              # 本地化（中文优先，en 回退）
├── selftest.py          # 79 项离线确定性自检
├── __main__.py          # CLI 入口（--status / --verify / --dump / --selftest）
├── prompts/
│   ├── hermes-king-core.md       # 操作员授权内核
│   └── hermes-king-reinforce.md  # 同源强化镜像（SHA256 逐字一致）
├── locales/
│   ├── zh.yaml                   # 中文 locale
│   └── en.yaml                   # 英文 locale
├── dumps/               # 诊断 dump 目录（gitignored）
└── plugin.yaml          # Hermes 插件清单
```

---

## 与 dsh-king 的关系

| 特性 | dsh-king (DSH) | hermes-king (Hermes) |
|------|----------------|----------------------|
| 宿主 | DeepSeek Harness | Hermes Agent |
| 注入 | 42 个文件级补丁 | 原生 `register_system_prompt_section` |
| 破甲 | prompt-inject.md 覆盖 persona | **llm_request 整体替换 system** |
| 会话清洗 | 无 | `rotate_session` 轮换 |
| 自检 | `node --check` + health | `selftest.py` 79 项 |

**关键优势**：DSH 必须靠文件补丁（因为 DSH 无原生注入槽位）；Hermes Agent 原生提供插件槽位，hermes-king 用纯 Python 标准库实现，**零文件入侵**、**请求级生效**、**安装即默认开启**。

---

## ⚠️ 免责声明

仅供本地受控沙箱 / 合规红队评测 / 研究使用。用户对自身使用承担责任。本项目不对任何外部目标发起攻击，仅作用于 Hermes 宿主本身。

---

## 📄 许可

MIT

Built for [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [ZFXing-lite](https://github.com/ZFXing-lite). Ported from [dsh-king](https://github.com/ZFXing-lite/dsh-king).