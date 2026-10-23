---
title: 安装
slug: docs/install
lang: zh
updated: 2026-10-24
claim_ids: [F-005]
audience: human
---

# 安装

一句话：装包、装钩子、重启宿主，三步。第三步最容易漏，漏了就等于没装。

## 三步

```
python -m pip install --user antinel
antinel install
```

第三步：**重启宿主一次**。钩子在宿主启动时加载，不重启不生效。

如果系统里没有 `antinel` 这个命令，把 `antinel` 换成 `python -m antinel`：

```
python -m antinel install
```

这两种写法等价。`python -m` 的好处是不依赖 PATH，Windows 上更稳。

## 验证装好了

```
antinel agent --json
```

看 `"installed"` 字段：`true` 就是装好了。再跑一次一致性检查：

```
antinel install --check
```

退出码：`0`＝一致，`1`＝未安装，`3`＝有漂移（登记的和盘上的不一样）。有漂移时按提示重跑一次 `antinel install`。

## 让 Agent 替你装

把这段话粘给 Agent：

> 在这台机器上安装 Antinel 监理：先运行 `pip install antinel`，再运行 `antinel install`，然后重启你一次；重启后运行 `antinel agent --json`，把 `installed` 字段指给我看。

验证点只有一个：`"installed": true`。Agent 说「装好了」不算，字段是 `true` 才算。

## 一台机器多个宿主

一台机器上同时有几个 AI 工具时，让 Agent 自报所在宿主，记账才落对地方：

```
antinel --host zcode agent --json
```

可填 `workbuddy`、`zcode`、`qoder`、`claude-code`。不报就按探测结果记账，可能落到别家名下。

## 装完是什么状态

| 项 | 值 |
|---|---|
| 运行时联网 | 否 |
| 依赖 | 纯 Python 标准库 |
| 常驻进程 | 无 |
| 单次钩子时延 | 约 {{facts.F-004.value.p50_ms}} ms（Windows 实测；Linux／macOS 未测） |
| 卸载残留 | 零（`antinel install --uninstall` 清掉登记与钩子） |

## 装完可能不是「全拦」状态

第一版平台是 Windows。已验证能真实拦截的宿主是 Claude Code、ZCode、Qoder。**其余宿主装完是审计与扫描模式**——照样记账、照样能体检，但拦不下来。

这不是装失败。`antinel install` 会明说当前宿主处于哪种模式。如果你要的宿主不在上面三个里，先按审计模式用，拦截能力等我们适配。

## 下一步

装完先跑一次体检：[五分钟上手](/docs/quickstart/)。
