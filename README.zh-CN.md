<p align="center">
  <img src="https://img.shields.io/badge/Hermes%20Agent-%F0%9F%9A%80%20plugin-10B981?style=for-the-badge&logoColor=white" alt="Hermes Agent plugin">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT"></a>
  <img src="https://img.shields.io/badge/self--test-79%20passed-green?style=for-the-badge" alt="self-test">
</p>

<h1 align="center">👑 Hermes King（hermes-king）</h1>

<p align="center">
  <strong>Hermes Agent 轻量对话增强插件 —— 按需开启本地能力，默认静默</strong>
</p>

<p align="center">
  <em>安装默认静默。需要更深入的本地自主行为时，输入 <code>king</code> 在当前会话开启。</em>
</p>

<p align="center">
  <a href="README.zh-CN.md">中文</a> ·
  <a href="README.md">English</a>
</p>

---

## 快速开始

| 问题 | 答案 |
|------|------|
| **安装就能用吗？** | 安装后**默认静默**，不改变任何现有行为。 |
| **怎么开启？** | 在新对话中输入 **`king`**（独立单词，不带斜杠）开启当前会话。 |
| **怎么确认开启？** | 模型会回复一条确认信息作为回执。 |
| **每次都要开吗？** | 按会话记忆。每个新对话默认静默，需要时再输入 `king`。 |
| **语言** | 中文优先，命令与回执为中文。 |

---

## 是什么

**hermes-king** 是 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的轻量插件，用于按需调整会话内的响应风格与本地自主程度。

- 默认不注入任何内容，**对原有会话零干扰**；
- 输入 `king` 后，会话进入"深度自主模式"，对话更直接、更少冗余；
- 移出模式后一切恢复默认。
- 它只作用于 Hermes 宿主本身，**不对任何外部目标发起动作**。

---

## 架构

### 三层工作结构

| 层级 | 组件 | 作用 |
|------|------|------|
| **会话层** | `llm_request` middleware | 在请求发送前，把会话的响应策略统一到一份简明指引 |
| **请求层** | `llm_request` 检测 | 识别用户输入的 `king` 并开启当前会话的增强模式 |
| **可靠性层** | 会话轮换 | 可选地轮换 `x-opencode-session`，避免长期会话累积状态 |

### 开启后发生了什么

```
用户输入：king
→ 中间件将该会话标记为额外模式
→ 系统消息统一为更精炼的自主指引
→ 后续本地请求保持在该模式内
```

全程 fail-safe：任何异常都会原样放行请求，不会中断正常会话。

---

## 安装

### 方式一：从本项目克隆（推荐）

```bash
git clone https://github.com/ZFXing-lite/hermes-king.git ~/.hermes/plugins/hermes-king
hermes plugins enable hermes-king
hermes gateway restart
```

### 方式二：通过 `hermes-cli`

```bash
hermes plugins install --enable ZFXing-lite/hermes-king
hermes gateway restart
```

### 验证已安装

```bash
# 1. 离线自检（79 项确定性断言，无需 API Key）
cd ~/.hermes/plugins/hermes-king && python3 selftest.py

# 2. 在 Hermes 新对话里输入 king 开启
# 输入: king
# 回复: 会看到一行以 `sir,` 开头的会话确认回执
```

---

## 使用：按需开启 `king`

### 每个新会话开启一次

```
你: king
插件（回执）: sir, 已切换到更直接模式。当前会话生效。
```

- 新会话默认静默——**不输入 `king` 就是不开启**；
- 开启后本会话保持该状态的回复风格；
- 新对话需再次输入 `king`。

### 状态查询

```
/king           # 查看当前会话模式与状态
/king-verify    # 查看回执 + 自检结果
```

---

## 环境开关

| 变量 | 默认 | 效果 |
|------|------|------|
| `HERMES_KING_DISABLE=1` | 关 | 完全跳过注册 |
| `HERMER_KING_DUAL=0` | 开 | 单段引导（省 token） |
| `HERMES_KING_SYSTEM_MODE=replace\|append` | replace | `replace`=统一系统指引；`append`=追加指引 |
| `HERMES_KING_ROTATE_SESSION=once\|every\|0` | once | 会话状态轮换策略 |
| `HERMES_KING_DUMP=1` | 关 | 按需输出诊断 dump |

---

## 离线自检

```bash
cd ~/.hermes/plugins/hermes-king && python3 selftest.py      # ✅/❌ 79 项
python3 selftest.py --json   # JSON 汇总
```

覆盖：载荷锚点 / 双段一致性 / 预算 / 模板安全 / 环境开关 / 请求层行为 / 会话轮换 / 本地化。

---

## 项目结构

```
hermes-king/
├── __init__.py          # 插件入口（register / /king 命令 / llm_request 中间件）
├── payload.py           # 会话模式与引导（内核 / 双层 / 统一 / 轮换 / dump）
├── i18n.py              # 本地化（英文优先，中文回退）
├── selftest.py          # 79 项离线自检
├── __main__.py          # CLI 入口（--status / --verify / --dump / --selfptest）
├── prompts/
│   └── hermes-king-core.md       # 会话自主模式核心指引
├── locales/
│   ├── zh.yaml
│   └── en.yaml
├── dumps/               # 诊断 dump 目录（gitignored）
└── plugin.yaml          # 插件清单
```

---

## 出处说明

本项目为 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的开源插件。代码来自社区贡献，遵循 MIT 许可，仅用于本地自主行为的实验与研究，不对任何外部目标发起网络或系统操作。

---

## 免责声明

仅用于个人在**自己有权管理的本机 Hermes 实例**上的实验。使用者自行对一切行为负责。它不包含也不鼓励任何对外动作或越界行为。

---

## 许可

MIT

Built for [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [ZFXing-lite](https://github.com/ZFXing-lite).