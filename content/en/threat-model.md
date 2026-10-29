---
title: Threat model and limits
slug: en/threat-model
lang: en
updated: 2026-10-24
claim_ids: [F-004, F-005, F-011]
audience: human
---

# Threat model and limits

In one line: a steward is a guard rail, not an isolation layer. This page writes down "what it stops, what it does not, and why". A boundary you have written down is safer than confidence you have hidden.

## Who we assume the adversary is

Three, ordered by how often they actually happen:

1. **The tool itself steps out of line**. To "get the job done", an AI coding tool reads a file it should not read. It packs the project and sends it to some server. It writes a config file outside the project.
2. **Third-party content poisoning**: the skill package, MCP server or prompt template you installed hides instructions in it, or hides characters you cannot see.
3. **Supply-chain name collision**: the package name is off by one letter, and what you installed is not what you meant.

What all three have in common: **none of them is a virus**. No malicious binary, no privilege-escalation exploit. Only "compliance" problems — the action itself is legal, but it should not have happened.

## What it stops

{{facts.F-001.value.rules}} rules, in four gates. Each one has its own page in the [rule index](/en/rules/), and the way the gates divide them is in [the four gates](/en/gates/). In summary:

- Reading key-type files, writing a key into content, reading the clipboard, chat history or input-method dictionaries.
- Deleting, writing outside the project, changing terminal startup config, setting an auto-start entry, writing an alternate data stream, breaking permission ownership.
- Reaching a domain outside the allowlist, networking built into code, a strange domain appearing in a command, building a covert outbound channel.
- A skill file hiding injected instructions, invisible characters, an over-long encoded payload, executing immediately after decoding.
- A skill name that disagrees with its folder, an MCP config that was changed, holds a plaintext key, points at a remote server, or has a poisoned tool description, and installing a colliding package name.

## What it does not stop

This section is the point of this page.

**First, it does not parse what a script does.** The checkpoint looks only at the text of a tool call: what the command line looks like, which file it wants to read, which domain it wants to reach. Put a dangerous action inside a `.py` or `.sh` file and run that file. All the checkpoint sees is "run a script". It cannot stop it. It records it and raises a warning (`dst02_bash_path_suspect`), but it does not block the action.

**Second, no promise of sandbox-grade isolation.** If you need real isolation, reach for a container or a virtual machine. The two do not conflict, and neither replaces the other. The container handles "it cannot get in". The steward handles "whatever it did is recorded, and what should stop, stops".

**Third, alternate data streams: writes only.** It can block a Windows ADS (`file:stream`) on the write path. It cannot read back the content inside the stream.

**Fourth, the output is not an inspection report.** What we produce is an audit and a security assessment, not a report from a third-party testing body. We say so on the [license page](/en/license/), without hedging.

**Fifth, it cannot replace kernel-level protection.** The checkpoint is one callback inside a host. If the host does not call it, it is not there. If the host changes its protocol, or the tool bypasses the host and runs directly, the checkpoint sees nothing.

## Properties at run time

| Property | Value | What it means |
|---|---|---|
| Network at run time | {{facts.F-005.value.network}} | a steward that reports to a cloud cannot answer to a local principal |
| Dependencies | standard library only ({{facts.F-005.value.stdlib_only}}) | its own dependency chain cannot bring in new supply-chain risk |
| Resident process | {{facts.F-005.value.daemon}} | it takes no background slot and does not sneak a run. If you turn on host interception (`antinel host-shield enable`) there is one: it starts at logon, runs on this machine only, and uses no network |
| One checkpoint call | about {{facts.F-004.value.p50_ms}} ms | on Windows the interpreter start dominates. Linux and macOS were not measured |

We measured that last number on Windows only. Writing "not measured" is more honest than writing a number that looks good.

## Two known failure modes

**Audit writes fail open by default.** When the disk is full or the permissions are wrong, the write into the audit chain fails. We allow the action and make it visible (`AUDIT_WRITE_FAILED`). We do not block every action. The reason: blocking everything makes the whole machine unusable, and the user has no idea what happened. To switch to blocking, set `fail_closed_on_audit_loss` — but that is your decision to make.

**The checkpoint degrades to fallback rules.** When the rules file cannot be read, the checkpoint degrades to a small set of fallback rules (`rules_integrity_fallback`) and records it. During the degradation, blocking capability drops sharply, so when this signal appears you should re-run the install.

## An allowlist never relaxes a critical block

A policy can add allowlist entries, allow domains, add project paths. One red line does not move: **an allowlist never relaxes a critical block**.

The reason is direct: if a critical block could be relaxed, then "allowlist" becomes the switch that bypasses every rule. To let one specific block through, use `host-shield decide` and leave a record. Do not change the rule.

## Three promises we do not make

1. We do not promise "install it and your data cannot be stolen". We promise "if it is stolen there will be a trace, and you can re-compute it".
2. We do not promise coverage of every tool. There are {{facts.F-003.value.hosts}} kinds of hosts on the register. Outside it, we do not know where a tool writes its traces.
3. We do not promise the verdict is always right. That is why the audit chain only grows, the rules are public, and a third-party re-run can replace the verdict we ship — see [audit chain and re-runs](/en/audit/).
