---
title: Why we call it a steward
slug: en/steward
lang: en
updated: 2026-10-24
claim_ids: [F-001, F-002, F-011]
audience: human
---

# Why we call it a steward

In one line: a steward does not write your content and does not make your decisions. It checks against rules agreed on beforehand, records what it sees, stops what it must, and hands the decision back to you.

## A steward is not a sentry

We do not use the word "sentry" in our public material. The reason is simple: a sentry only shouts, and then it walks away. A steward leaves a record.

- Sentry: sees something odd → raises an alarm → done.
- Steward: sees something odd → judges it against rules written down beforehand → acts on the spot → writes it into the record. You can re-compute the whole thing later.

An alarm with no record behind it cannot be shown to have happened the next day. Half the value of a steward is on the spot. The other half is afterwards.

## A steward is not antivirus

Antivirus looks for malicious signatures inside a file. A steward looks at whether **the action this AI tool just took was allowed**.

| | Looks at | When | Leaves behind |
|---|---|---|---|
| Antivirus | malicious patterns in file content | after the file lands | a quarantine area |
| Steward | the parameters and targets of a tool call | before it runs | a record that cannot be edited |

Neither one covers for the other. Antivirus cannot stop "the agent read your key file and then exited normally". That is not a virus. That is a compliance problem.

## Where the word comes from

The Chinese word 监理 carries an institutional meaning. Information-systems supervision has a mature body of practice behind it. It is the kind of work the GB/T 19668 family of standards describes. Four things define it. It is a third party. It works to a contract and to written rules. It answers for the process rather than the outcome. It produces records that can be checked.

Antinel borrows that way of working. It does not borrow a qualification:

- It judges by **rules written down beforehand**, not by how anyone feels at the time.
- It **records facts only**. It does not reach the conclusion for you.
- Judgement and money are **kept apart**. We do not earn from "the judgement came out positive".

> To be clear: Antinel Steward is not a licensed supervision body, and what it prints is not an inspection report. We say so on the [license page](/en/license/) without hedging.

## Three parties in one call

There are three parties in a single AI tool call:

1. **The principal** — you. You decide what may and may not happen on this machine.
2. **The supervised party** — the AI tool. It performs the action.
3. **The steward** — Antinel. It watches the second party against the rules you set, and reports to you.

The third point is the one that matters: a steward answers **to the principal, not to the supervised party**. So it cannot be played by the AI tool itself, and it cannot be played by whoever sold you the AI tool.

That is also why it has to **run locally and stay off the network at run time**. A steward that reports to a cloud cannot answer to a local principal.

## Three rules we hold to

**First, it generates no content.** A steward does not change your code, does not write files for you, does not improve your project. It looks at actions.

**Second, the bar is consistent.** The same call is blocked today and blocked tomorrow. The bar lives in the rules file, its version is checkable, and it does not change with the person.

**Third, we keep it decoupled from payment.** The verdict does not depend on whether anyone paid. We take no "passage fee" and we sell no "verified" mark. A mark can only come out of a public rule judged by a machine.

## What it actually stops

Four gates and {{facts.F-001.value.rules}} rules: {{facts.F-002.value.critical}} of them block on hit, {{facts.F-002.value.warning}} of them warn and let the action through. Each one has its own page in the [rule index](/en/rules/); the way the gates divide them is in [the four gates](/en/gates/).

## The limits, stated here too

A steward is a guard rail, not an isolation layer. It reads only the text of a tool call. It does not parse what a script does. Slip a dangerous action inside a `.py` file and run that file. The steward has no way to stop it. There will be a record and a warning, and that is all. The complete honest list is in [threat model and limits](/en/threat-model/).

If you need real isolation, that is a container's job, not ours. If you need accountability and re-computation, that is a steward's. Neither one stands in for the other.
