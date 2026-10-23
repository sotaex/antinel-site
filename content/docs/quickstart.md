---
title: 五分钟上手
slug: docs/quickstart
lang: zh
updated: 2026-10-24
claim_ids: [F-003, F-008]
audience: human
---

# 五分钟上手

一句话：装 → 查 → 守。三组命令，全程可复制，每一步都有验证点。

## 第 0 步：装

```
python -m pip install --user antinel
antinel install
```

然后**重启宿主一次**。

验证：

```
antinel agent --json
```

看 `"installed": true`。不是 `true` 就回[安装](/docs/install/)看。

## 第 1 步：查

在本机浏览器里点一下，看这台电脑上的 AI 工具有没有把东西带出去：

```
antinel ui
```

浏览器打开后点「开始检查」。只读、不上锁、结果不出本机。

要命令行版本：

```
antinel host-scan
```

它给全机清单：装了哪些工具、各自什么版本、六档裁决、证据在哪。约一到两分钟。

## 第 2 步：读

先看首屏那个数：**「没查到 N 个」**。不是「发现 0 个问题」——这两个不是一回事。

| 你看到 | 意思是 |
|---|---|
| 🔴 PACK 自认打包过 | 工具自己记了打包后的体积或清单哈希 |
| 🟠 SENT 自认往外发过 | 工具自己记了「已上传」「已被接受」 |
| 🟡 SYNC 自认在同步 | 工具自己记了同步时间。同步 ≠ 上传整份项目 |
| ⚪ CLEAN 查过没发现记录 | 扫到了，这次没找到证据。**不等于清白** |
| ⚫ BLIND 没查到 | 扫描器没走到。**这一项没查** |

细节见[六档裁决](/verdicts/)与[安全体检](/checkup/)。

## 第 3 步：守

看此刻谁在往外连：

```
antinel egress
```

看今天拦了什么：

```
antinel digest --days 1
```

要一页能交差的纸：

```
antinel brief
```

## 第 4 步（可选）：埋个标记

想知道代码有没有被带出去，埋一个金丝雀：

```
antinel canary plant
```

之后正常干活。如果标记出现在工具的输出或上传内容里，那就是外传证据，`antinel report` 的 canaries 统计里能看到。

## 日常就这三条

```
antinel morning
antinel digest --days 1
antinel verify
```

第一条给晨报，第二条给昨天的时间线，第三条查审计链有没有被动过。

## 想更严一点

```
antinel settings set net_mode block
antinel zone add <你的项目目录>
```

外传口径从「提醒」切到「拦截」，并按目录划安全区。改完进审计链，可查可撤。

放行某个域名（装包老被提醒时）：

```
antinel domains add pypi.org
```

## 出问题先看这

钩子不生效、拦截数归零、审计写失败——[故障与边界](/docs/troubleshooting/)有信号速查表。
