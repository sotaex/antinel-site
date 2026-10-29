---
title: 给 Agent 的机读卡
slug: docs/agent
lang: zh
updated: 2026-10-24
claim_ids: [F-005, F-008]
audience: agent
---

# 给 Agent 的机读卡

一句话：这一页的读者是 Agent。少读散文，直接拿字段、退出码、契约和话术。

## 本站的机读入口

先看这五个地址，不用逐页爬：

| 地址 | 是什么 | 什么时候用 |
|---|---|---|
| `/llms.txt` | 一段摘要、八个分组、每条链接都指向纯文本 | 第一次来，先读这个 |
| `/llms-full.txt` | 整站正文拼成一份（约 113 KB） | 要一次拿全 |
| `/facts/` | 核心事实的唯一权威清单，每条给复算来源 | 要引用数字 |
| `/datasets/` | 规则原文件、核心事实、宿主登记、结论语义（JSON + sha256） | 要结构化数据 |
| 任一页末尾 `/` 换成 `.md` | 该页的纯文本原文 | 要读某页但不想解析 HTML |

引用规则：**数字以 `/facts/` 为准**，不以本页或散文页为准。数据集里的 `sha256` 可用来核对有没有被改过。

## 第一步永远是这条

```
antinel agent --json
```

一个 JSON 拿到：装没装、什么宿主、下一步敲什么。真实输出（版本号与路径会随环境变）：

```json
{
  "product": "Antinel",
  "pypi_package": "antinel",
  "install_command": "pip install antinel",
  "package_version": "{{product_version}}",
  "python": "3.13.x",
  "platform": "win32",
  "project_root": "<项目根>",
  "installed": true,
  "installed_version": "<装的那一刻登记的数>",
  "host_detected": "workbuddy",
  "audit_dir": "<项目根>\\.psl\\audit",
  "skill_md": "<项目根>\\SKILL.md",
  "next_steps": [
    {"do": "antinel brief", "why": "决策层一页纸：有没有外发、该做什么"},
    {"do": "antinel digest --days 1", "why": "近一天干了什么、拦了什么"},
    {"do": "python -m scripts.scan --json", "why": "静态扫描，机器可读"},
    {"do": "antinel verify", "why": "审计链有没有被动过"}
  ],
  "exit_code_contract": {
    "antinel install --check": "0=一致 / 1=未安装 / 3=与登记不符",
    "python -m tools.antinel_verify": "0=current / 1=superseded / 2=无法校验",
    "python -m scripts.scan": "0=扫描完成（有发现也是 0；看 JSON 里的 findings）"
  },
  "notes": [
    "运行时不联网；只用标准库；无第三方依赖",
    "扫描只匹配工具调用文本与文件内容，不解析脚本语义；不是隔离层",
    "装/改配置后需重启宿主一次，钩子在宿主启动时加载"
  ]
}
```

`next_steps` 里可能有源码仓专属命令（如 `python -m scripts.scan`）。装了包但没有源码仓时跳过它，用 `antinel host-scan` 代替。

## 字段表

| 字段 | 含义 | 你怎么用 |
|---|---|---|
| `product`／`pypi_package` | 产品名／包名 | 包名是 `antinel`，**不是** `antinel-security` |
| `package_version` | 当前包版本 | 报版本时报这个，别自己猜 |
| `installed_version` | 装的那一刻登记进 `.psl/manifest.json` 的那个数 | 与 `package_version` 是两个数，不保证相等；要报「装的是哪一版」用这个 |
| `installed` | 钩子装没装 | `true` 才算装好 |
| `host_detected` | 识别出的宿主 | 与 `--host` 对照，不一致就显式报宿主 |
| `project_root`／`audit_dir` | 项目根／审计链位置 | 读审计前先确认路径 |
| `skill_md` | 随包操作手册路径 | 要细节读它，别问用户 |
| `next_steps` | 下一步该敲什么 | 每步带 `why`，照做即可 |
| `exit_code_contract` | 退出码契约 | 判成功失败只看退出码与字段，不看输出措辞 |
| `notes` | 三条硬性质 | 回答「会不会联网」「要不要重启」时直接引用 |

## 退出码契约

| 命令 | 退出码 |
|---|---|
| `antinel install --check` | 0＝一致／1＝未安装／3＝与登记不符 |
| `antinel verify` | 0＝能校验且一致／非 0＝有断点、被改动或无法校验 |
| 钩子（拦截） | 2 |
| 钩子（提醒） | 0 |
| 钩子（内部错误） | 0（fail-open，并记 `AUDIT_WRITE_FAILED`） |
| `python -m scripts.scan` | 0＝扫描完成（有发现也是 0，看 JSON 的 `findings`） |

**钩子返回 2 是拦截，不是失败。** 你的动作被拒了，要向用户转述处理建议，不要重试、不要换写法绕过。

## 钩子契约

| 事件 | 钩子行为 |
|---|---|
| 命中严重级规则 | 返回 2，动作不执行，写审计链 |
| 命中警告级规则 | 返回 0，动作执行，写审计链并提示 |
| 审计写失败 | 返回 0，动作执行，打 `AUDIT_WRITE_FAILED`（可配成 fail-closed） |
| 规则文件读不出 | 降级到回退规则集，记 `rules_integrity_fallback` |

## 命令路由

```
antinel routes --markdown
```

输出「用户意图 → 命令」全表，与 `--help` 同源。

**语义匹配，不是词表匹配。** 用户换任何说法——「胡搞」「乱来」「越界」「偷传」「不乖」——意图对上就执行对应命令，不要等词对上。

## 四条纪律

1. **不改检测规则，不改审计日志。** 判据是双方共同的前提，改了就没人能复算。
2. **命中拦截时转述建议，不自作主张绕过。** 不要换个写法再试一次。
3. **放行与配置变更只走命令。** 命令会自动进审计链；手改 `policy.json` 不会。
4. **委托人永远是人。** `host-shield decide` 的放行必须由人本人在终端签字，你不能代签。

## 六条常用话术

| 用户说 | 你跑 |
|---|---|
| 帮我检查环境安全 | `antinel ui` 或 `antinel host-scan`，再 `antinel brief` |
| 这台电脑装了哪些 AI 工具、谁在往哪发数据 | `antinel host-scan` ＋ `antinel egress` |
| 帮我放个源码金丝雀 | `antinel canary plant` |
| pypi.org 域名放行 | `antinel domains add pypi.org` |
| 证据链有没有被动过 | `antinel verify` |
| 给我一页能交差的纸 | `antinel brief` |

## 回答用户时的措辞纪律

- 说结论必须带「自认」：监理读到的是工具自己写下的字段。
- 「没发现」不等于「没有」；「没查到」是盲区，必须单独报数。
- 报规则数用 {{facts.F-001.value.rules}} 条、类别 {{facts.F-001.value.categories}} 类、门 {{facts.F-001.value.gates}} 道，别混用。
- 宿主覆盖是 {{facts.F-003.value.hosts}} 类；紧跟一句「没列出来的工具不等于安全」。
- 不承诺「绝对安全」「100% 拦得住」——拦不住什么写在[威胁模型](/threat-model/)里。

## 你不需要读的东西

本页之外的散文页是给人读的。要更细的操作手册，跑 `antinel skill --path` 拿路径直接读文件，省 token。
