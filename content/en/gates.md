---
title: The four gates
slug: en/gates
lang: en
updated: 2026-10-24
claim_ids: [F-001, F-002]
audience: human
---

# The four gates

In one line: the four gates are not four categories. They are four checkpoints. One tool call passes through them in order, hits the earliest one that matches, and gets handled the way that gate says.

## Categories answer "what it covers". Gates answer "where in the flow it is asked"

Rules are sorted into categories (secrets, destructive, network, injection and so on) and they pass through gates. These are two independent coordinates:

- **Category**: which kind of risk this rule cares about. Rules in one category are written in a similar style.
- **Gate**: at which step of the flow this rule gets asked. Rules in one gate share one way of being handled.

The payoff of keeping them apart: a new rule only has to hang off an existing gate and category. The handling does not have to be rewritten.

## What each gate stops

| Gate | What it stops | Categories that land on it |
|---|---|---|
| Gate 1 Content safety | a skill or prompt gets poisoned: injected instructions, invisible characters, encoded payloads | injection (CTX-02／03／04／07) |
| Gate 2 Sensitive surface | something that should not be read gets read; a key that should not appear shows up in content | secrets (SEC-01…SEC-10), canary files (SEC-11) |
| Gate 3 Metadata and outbound | identity disguise, domains outside the allowlist, tunnels and covert channels | metadata (CTX-05) |
| Gate 4 Behaviour | deletion, writes outside the project, alternate data streams, persistence, privilege escalation, environment enumeration | destructive (DST-01…DST-11), network (NET-01…NET-04) |

## Two kinds of rule sit on two gates at once

Two kinds of risk cross a step in the flow. One gate cannot hold them, so they are registered on two gates at the same time:

| Category | Gates | Why it crosses |
|---|---|---|
| Environment probing (CTX-01 enumerates every environment variable) | Gate 1／4 | reading an environment variable is visible at the content layer, but the damage shows up later in the outbound behaviour |
| MCP supply chain (MCP-01…MCP-04, SLOP-01) | Gate 2／3 | a plaintext key in a config file belongs to the sensitive surface; a poisoned tool description and a remote server belong to metadata and outbound |

The crossing is **registered in the rules file**. It is not decided on the spot on a web page. The table on this page is read out of the `gates` field of the rules file at build time.

## There are only two levels of handling

{{facts.F-002.value.critical}} rules are critical: **blocked on the spot**, and written into the record. The tool call does not run.

{{facts.F-002.value.warning}} rules are warnings: **warned and let through**, and written into the record just the same. The reason is that this kind of signal does not support a conclusion on its own. Reaching a domain outside the allowlist, for example, also happens during a normal package install.

The line between the two levels is drawn by "can this be undone afterwards". A private key that has been read out cannot be called back, so that is critical. A strange domain may just be a flaky network, so that is a warning.

## Gate membership is read from one place

We do not keep a second table for gate membership.

The `gates` field in `rules/default.json` is the only source of truth. Every gate number shown on a rule page is parsed out of it at build time. One check watches this during the build: if any page shows a gate number that disagrees with the rules file, the build fails.

We do it this way because "the same fact in two places" is an error that does not raise. It falls silently behind. The page says Gate 3; the rules file was changed to Gate 4 weeks ago. Both open fine. Nobody notices.

## What a gate does not do

The four gates check the **text of a tool call**. Write a dangerous action into a `.py` or `.sh` file and run it, and the checkpoint sees "run a script". It cannot stop it, but there will be a record and a warning.

For real isolation you need a container or a virtual machine. The job of a gate is "let what should be seen be seen, and stop on the spot what should be stopped". It is not "guarantee nothing bad gets in". The full boundary is written in [threat model and limits](/en/threat-model/).

Rule by rule in the [rule index](/en/rules/).
