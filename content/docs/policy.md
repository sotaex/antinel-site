---
title: 策略与白名单
slug: docs/policy
lang: zh
updated: 2026-10-24
claim_ids: [F-011]
audience: human
---

# 策略与白名单

一句话：四把钥匙，各有各的放宽范围；一条红线——严重级永不放宽。

## 策略文件在哪

```
<项目根>/.psl/policy.json
```

`antinel install` 时生成模板。改它有两种方式：直接编辑，或者走命令（推荐，命令会自动进审计链）。

## 四把钥匙

| 键 | 放宽什么 | 不放宽什么 |
|---|---|---|
| `whitelist.domains` | 只放宽网络类规则（NET 族） | 敏感面、破坏性、注入 |
| `whitelist.paths` | 放宽敏感面规则，并释放「写到项目外」（DST-02） | 删除、持久化、注入 |
| `whitelist.commands` | 只放宽警告级规则 | **严重级一律不放宽** |
| `global_settings` | `net_mode`、`alert_threshold`、`fail_closed_on_audit_loss` 等运行档位 | 规则判据本身 |

四把钥匙的共同点：**每一把都只动一个维度**。没有「全部放行」的开关，这是我们刻意不做的。

## 三个放行例子

装包老被提醒域名：

```
antinel domains add pypi.org
```

某个资源目录要写：

```
antinel paths add D:\demo\assets
```

整棵树都要用（比如一个独立项目）：

```
antinel roots add D:\demo
```

三条都会进审计链。撤回去：

```
antinel domains remove pypi.org
antinel paths remove D:\demo\assets
```

## 红线：严重级永不放宽

{{facts.F-002.value.critical}} 条严重级规则，任何白名单都不放宽。

原因很直接：能放宽严重级的话，白名单就成了绕过全部判据的开关。要放行某一次拦截，走 `host-shield decide` 并留痕——**留痕的放行**和**改判据的放行**是两件事，前者可追、后者不可追。

## 审计写失败时的取舍

默认是 fail-open：写不进审计链就放行，并在 stderr 打出 `AUDIT_WRITE_FAILED`。

要改成 fail-closed：

```
antinel settings set fail_closed_on_audit_loss true
```

改了之后，磁盘满或者权限不对，所有动作都会被拦。取舍归你，机制归监理——我们把两种选择都做出来，不替你选。

## 网络档位

默认 `warn`：白名单外的网络命令只提醒、不拦截。

```
antinel settings set net_mode block
```

切成拦截后，未白名单的域名会被挡。切之前先把常用域名放行，否则装包、拉依赖都会失败。

看当前档位：

```
antinel settings get net_mode
```

## 安全区

```
antinel zone add D:\myproject
antinel zone list
```

安全区是「按目录收紧」：区内写行为受控，清单本身进审计链。

## 查看全部策略

```
antinel settings list
antinel domains list
antinel paths list
antinel roots list
```

## 改策略的三条纪律

1. **先看再改**：`settings list` 看现状，别凭印象改。
2. **改完验证**：跑一次 `antinel digest --days 1`，确认改动生效且没带来意外拦截。
3. **不要改判据**：判据在 `rules/default.json`，改它等于改「什么算违规」。要放行具体对象，用白名单。
