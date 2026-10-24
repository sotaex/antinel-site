---
title: 命令总表
slug: docs/commands
lang: zh
updated: 2026-10-24
claim_ids: [F-008]
audience: human
---

# 命令总表

一句话：按意图查，不按字母查。三条主线是审核、防范、账本——先想清楚你要回答哪个问题。

## 审核：这台机器有没有事

| 意图 | 命令 | 说明 |
|---|---|---|
| 一页能交差的纸 | `antinel brief` | 有没有外发、比上期变化、该做什么 |
| 本机点一下就查 | `antinel ui` | 浏览器打开本机页面，只读，不出本机 |
| 全机盘点 | `antinel host-scan` | 装了哪些工具、裁决、证据，约一到两分钟 |
| 今天有没有出格 | `antinel host-audit` | 只看当日 |
| 此刻谁在往外发 | `antinel egress` | 约 30 秒采样一次连接表，不记载荷 |
| 干了什么、拦了什么 | `antinel digest --days 1` | 时间线 |
| 跨工具汇总 | `antinel digest --scope all` | 多个宿主一起看 |
| 晨报 | `antinel morning` | 昨日汇总 |
| 待处理项 | `antinel inbox list` | 收件箱 |
| 历史账本 | `antinel ledger --days 7` | 按日历天；无记录的天是 `null`，不是 0 |

## 防范：让它挡得住

| 意图 | 命令 | 说明 |
|---|---|---|
| 埋外传检测标记 | `antinel canary plant` | 读取会触发 SEC-11 提醒 |
| 看埋了哪些 | `antinel canary list` | — |
| 外传落点门闸 | `antinel host-shield status` | 看在岗状态与已上锁落点 |
| 布防 | `antinel host-shield enable` | 默认关闭，需主动开 |
| 等你表态的落点 | `antinel host-shield queue` | — |
| 裁决放行 | `antinel host-shield decide "<路径>" allow_always` | **放行须你本人在终端操作** |
| 已上锁清单 | `antinel host-shield locks` | 解锁用 `unlock` |
| 划安全区 | `antinel zone add <目录>` | 区内写行为受控 |
| 外传切拦截 | `antinel settings set net_mode block` | 默认是 `warn`：只提醒不拦 |
| 域名放行 | `antinel domains add pypi.org` | 只放宽网络类规则，进审计链 |
| 路径放行 | `antinel paths add <前缀>` | 放宽敏感面规则并释放越界写 |
| 更大边界 | `antinel roots add D:\demo` | 整棵树放行 |
| 看当前策略 | `antinel settings list` | 单键用 `settings get <键>` |

放行类的命令都有记录、都可撤（`domains remove`／`paths remove`／`zone remove`）。放错了就撤，不要改规则。

## 账本：花了多少、还够不够

| 意图 | 命令 | 说明 |
|---|---|---|
| 这个会话花了多少 | `antinel report --session latest` | — |
| 近七天 | `antinel report --days 7` | 按严重度排序，每条带处理建议 |
| 记一下余额 | `antinel credits snapshot <余额>` | 也可带 `--reward N@到期日`、`--cycle 到期日` |
| 还够不够 | `antinel credits forecast` | — |
| 订阅 vs 直付 | `antinel credits reconcile` | 对账 |

账本只记 Agent 的行为与消耗，不做人的效率排名。

## 装与查

| 意图 | 命令 | 退出码 |
|---|---|---|
| 装钩子 | `antinel install` | — |
| 一致性检查 | `antinel install --check` | `0`＝一致／`1`＝未安装／`3`＝有漂移 |
| 卸载 | `antinel install --uninstall` | — |
| 当前状态 | `antinel agent --json` | — |
| 随包手册 | `antinel skill` | 只给路径用 `--path`，省 token |
| 话术表 | `antinel routes --markdown` | 与 `--help` 同源 |

## 退出码契约

| 命令 | 退出码 |
|---|---|
| `antinel install --check` | 0＝一致／1＝未安装／3＝与登记不符 |
| `antinel verify` | 0＝链能校验且一致／非 0＝有断点、被改动或无法校验 |
| 钩子拦截时 | 2 |
| 钩子提醒时 | 0 |
| 钩子内部错误 | 0（fail-open，并记 `AUDIT_WRITE_FAILED`） |

## 只在代码仓里跑的命令

下面这些不是 `antinel` 的子命令，要在源码仓根目录跑（`pip` 装出来的包里没有这些路径）：

```
python -m scripts.scan --root .
python -m scripts.run_harness
python -m tools.antinel_verify
python -m tools.enforce_probe
python challenge/verify.py
python challenge/tamper.py
```

它们分别做：静态扫描、复跑全部断言、独立校验审计链、执法有效性探针、独立复算、演示篡改。

装了包但没有源码仓的用户，用 `antinel` 子命令就够了：`host-scan` 顶静态扫描，`verify` 顶链校验。要复跑断言（拿自己的结论取代随包判定），需要源码仓。

## 写法约定

- `antinel` 不在 PATH 时，一律用 `python -m antinel <命令>`，两者等价。
- 多宿主机器上自报宿主：`antinel --host zcode <命令>`。
- 命令里的路径带空格要加引号。
