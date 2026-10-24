---
title: How it differs
slug: en/compare
lang: en
updated: 2026-10-24
claim_ids: [F-001, F-010]
audience: human
---

# How it differs

In one line: antivirus, sandboxes, DLP, SIEM and compliance audits all answer other questions. A steward answers "should this AI tool call have happened, and can it be proven afterwards that it did".

## One table

| | Looks at | When | Leaves behind | Does it govern AI tools |
|---|---|---|---|---|
| Antivirus | malicious patterns in file content | after the file lands | a quarantine area | no: a compliant action is not a virus |
| Sandbox／container | the execution environment boundary | at run time | an environment snapshot | it governs the range, not "what was done inside the range" |
| DLP | sensitive content and where it flows | in transit | policy alerts | it often treats an agent's normal work as a false positive |
| SIEM | log aggregation and correlation | after the fact | alerts and reports | it needs logs first, and the tool may not leave any |
| Compliance audit | an organisation-level compliance baseline | periodic | an audit report | organisation-facing, not single-call-facing |
| **Steward** | **the parameters and targets of a tool call** | **before it runs** | **a re-computable audit chain** | **built for exactly this** |

## Against antivirus

Antivirus looks for virus signatures in files. A steward looks at whether this call's action was allowed.

"An agent read your `.env` and then exited normally" — that is not a virus, so antivirus says nothing. But it is a compliance problem, and the steward blocks it on the spot and records it.

The two do not replace each other. Your machine should have both antivirus and a steward, because they look at different things.

## Against a sandbox

A sandbox governs **range**: let it run in the box, and if it breaks the box, throw the box away. A steward governs **behaviour**: every call inside the box is recorded, and what should stop, stops.

The sandbox's limit is "inside the box": it does not govern the actions inside. The steward's limit is "outside the box": it has no isolation capability. So the common combination is "container plus steward" — the container guarantees it cannot cross the line, the steward guarantees what happens inside the line can be accounted for.

## Against DLP

DLP finds sensitive data leaving by content rules. It suits people writing documents and sending email. AI tools work differently: reading a file is a normal action for them, and the content they read is meant to be reasoned over. DLP easily judges a whole workflow a false positive, and then gets switched off.

A steward moves the decision point forward to the **call** layer: it does not look at what the content it read looks like. It looks at whether what it read was a "key-type file". The rule is narrower, so there are fewer false positives.

## Against SIEM

SIEM aggregates and correlates logs, and its premise is **that logs exist first**. An AI tool does not necessarily give you logs: it may only write one field in its own directory, "last upload time", in a different format for every vendor.

What a steward does first is find those traces (see [the six mechanisms](/en/monitor/)), then translate them into one framing. SIEM is downstream. A steward is the upstream collection.

## Against a compliance audit

A compliance audit is an organisation-level baseline. It faces the organisation, runs periodically, and produces an audit report. A steward faces **a single call on a single machine**, in real time, entry by entry, re-computably.

The two are not substitutes. An organisation passing a compliance audit, and a particular agent on this machine secretly reading a key, are two different questions.

## Against an "AI security gateway"

Gateway products usually route requests to a cloud for inspection. That brings two problems: your call content passes through a third party, and the gateway itself has to be online.

A steward is local, takes no network at run time, and uses the standard library only. The price is that the rules can only do "text matching plus structural checking". They cannot do semantic understanding. We accept that price — see [threat model and limits](/en/threat-model/).

## What we do not claim

- We do not claim to be "the most complete": {{facts.F-001.value.rules}} rules is a countable set, not "everything covered".
- We do not claim "zero false positives": the warning level contains entries that do misfire (hitting a strange domain during a package install is common), which is why it is designed as warn-and-allow.
- We do not claim "passing means safe": ⚪ checked, no record found is not a clean bill, and ⚫ not checked is not "no problem". See [the six verdicts](/en/verdicts/).

## One line

Others ask "is this thing bad". A steward asks "should this action have happened, and if it did, can it be proven".

Both questions need answering. We only do the second one.
