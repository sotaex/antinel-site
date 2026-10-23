---
title: 升级与卸载
slug: docs/upgrade
lang: zh
updated: 2026-10-24
claim_ids: [F-007]
audience: human
---

# 升级与卸载

一句话：升级是三步，中间那步「装钩子」不能省——省了钩子会降级到内置回退规则集，还照样跑。

## 升级三步

```
python -m pip install --user -U antinel
antinel install --check
antinel install
```

第二条先看一致性：`0` 说明登记与盘上一致，`3` 说明有漂移。**不管哪一步，第二条跑完都要再跑一次 `antinel install`**，否则钩子吃不到新规则。

升级完再重启宿主一次。

## 怎么知道钩子降级了

两个信号，任一个出现就是降级：

1. `antinel report` 输出里的 `rules fallback` 行不是 0。
2. 审计链里出现 `rules_integrity_fallback` 事件。

降级的含义：钩子没读到新规则，正在用一小批内置回退规则。这时候拦截能力显著下降，但**表面上一切正常**——所以必须靠这两个信号发现，不能靠感觉。

修法只有一个：重跑 `antinel install`。

## 升级后要重新验一遍

```
antinel agent --json
antinel verify
antinel host-scan
```

第一条看 `installed` 与 `package_version`，第二条看链有没有被升级过程弄断，第三条看裁决有没有变化。

三条都过，升级才算完成。

## 升级会不会丢历史

不会。审计链在 `<项目根>/.psl/audit/`，升级只换代码，不动台账。策略文件 `.psl/policy.json` 同样保留。

如果升级后策略变了，先跑 `antinel settings list` 看差异，别直接改回去——新版本可能新增了键，改回去会丢默认值。

## 卸载

```
antinel install --uninstall
```

零残留：清掉 `.psl/manifest.json` 与钩子登记。

**审计链不会被删。** 这是刻意的：台账是证据，卸载程序不该有删证据的权力。要删自己手动删 `.psl/audit/`。

## 换机器

三步：

1. 新机器上装包、装钩子、重启宿主。
2. 把旧机器的 `.psl/audit/` 拷过来（可选，用于接续历史）。
3. 跑 `antinel verify` 确认链能接上。

链是按文件按天存的，拷过来不会断——除非中间有缺日期的文件，那会被报出来。

## 版本号在哪看

| 位置 | 命令 |
|---|---|
| 包版本 | `antinel agent --json` 的 `package_version` |
| 产品版本 | `antinel --help` 首行 |
| 本站数据版本 | 页脚 |

三个数应该一致。不一致就说明某处没更新——先看页脚的数据日期。
