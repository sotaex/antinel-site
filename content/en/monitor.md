---
title: Six ways we watch outbound data
slug: en/monitor
lang: en
updated: 2026-10-24
claim_ids: [F-009, F-003]
audience: human
---

# Six ways we watch outbound data

In one line: rules cover a single tool call. Mechanisms cover the whole machine. Six things together answer one question: did the AI tools on this computer take anything of yours away.

## Why rules alone are not enough

The {{facts.F-001.value.rules}} rules block **actions**: what this call read, where it wrote, who it connected to. Three kinds of thing get past them:

1. The action happened before the checkpoint was installed.
2. The action happened outside the checkpoint (a tool's updater, a background service, another client that is not registered).
3. The action itself was allowed, but the result was a transfer out (a pack-and-upload uses an ordinary network request).

These three can only be answered by "going through the traces the tool left itself" and "looking at what this machine is connecting out to right now". That is what the six mechanisms are for.

## The six at a glance

| Mechanism | Question it answers | Command |
|---|---|---|
| Self-reported audit | does this AI tool leave traces of a transfer | `antinel host-scan`／`antinel host-audit` |
| Egress ledger | who is sending out right now | `antinel egress` |
| Host blocking | can a transfer landing spot be blocked on the spot | `antinel host-shield` |
| Source canary | did the code get taken out | `antinel canary` |
| Safe zone | tighten the outbound bar across the board | `antinel settings set net_mode block`／`antinel zone add` |
| Report | how to hand the result over | `antinel ui`／`brief`／`digest`／`inbox` |

## 1. Self-reported audit

```
antinel host-scan
antinel host-audit
```

`host-scan` inventories the whole machine. Read-only, about one to two minutes: which AI tools are installed, what version each is at, and whether any of them left traces of a transfer. `host-audit` looks at today only, and answers "did any of these tools step out of line today".

The word "self-reported" is deliberate. What the steward reads is **a field the tool wrote itself** — its own "last upload time", its own "size after the last pack". This is not an action we watched, so we say "self-reported" and not "confirmed".

Coverage is the {{facts.F-003.value.hosts}} kinds of hosts on the register. **A tool that is not on the list is not therefore safe.** It only means the steward has no way to collect its records.

## 2. Egress ledger

```
antinel egress
```

About every 30 seconds it samples the system's network connection table and records only the outbound connections of AI tool processes: process name, PID, remote address, protocol, time. **It does not record payloads.** No packet capture, no looking at content.

The framing matters: **a connection is not a problem**. A pack-and-upload is a long, high-volume connection. An ordinary question-and-answer is a short one. The ledger gives you the facts. The judgement is yours.

## 3. Host blocking

```
antinel host-shield status
antinel host-shield enable
antinel host-shield queue
antinel host-shield decide "<path>" allow_always
```

This applies a write-denial to registered transfer landing spots (typically the tool's own "pending upload snapshot" folder). It is off by default. You have to deploy it deliberately.

`queue` shows the landing spots waiting for your call. `decide` allows or refuses. **An allow has to be made by you, in a terminal, by hand.** An agent cannot sign for you. This is a hard constraint, not a suggestion.

## 4. Source canary

```
antinel canary plant
antinel canary list
```

Plant a marked file in your project. Anyone who reads it triggers a SEC-11 reminder and a record. If that mark shows up in a tool's output, in a log, or in the content of some upload, that is evidence of a transfer out.

The good thing about a canary is that it **does not require you to trust any party**: you do not have to believe the tool did not upload. You only have to look at whether the mark got out.

## 5. Safe zone

```
antinel settings set net_mode block
antinel zone add <folder>
```

Switch the outbound bar to blocking across the board, and mark folders as safe zones where writes are controlled. The safe-zone list itself goes into the audit chain, so changing it leaves a record.

This is the only one of the six that **actively tightens** actions. The other five observe and collect evidence.

## 6. Report

```
antinel ui
antinel brief
antinel digest --days 1
antinel inbox report
```

The result has to be something you can hand over. `ui` gives you a clickable page in a local browser. `brief` gives you one page. `digest` gives you a timeline. `inbox` gives you the pending items.

All six mechanisms land on the same evidence framing, which is translated into the six verdicts — see [the six verdicts](/en/verdicts/). The easiest place to get the wording wrong is here: "checked, no record found" and "not checked" must not look alike. How the checkup page does that is written in [the checkup](/en/checkup/).

## What the six mechanisms do not do

- No packet capture, no reading payloads, no traffic reconstruction.
- Nothing is uploaded. All six run to completion on this machine.
- No efficiency ranking of people. Only the behaviour and the consumption of agents are recorded.
- No promise of covering tools that are not registered.
