---
title: Audit chain and re-runs
slug: en/audit
lang: en
updated: 2026-10-24
claim_ids: [F-010, F-012]
audience: human
---

# Audit chain and re-runs

In one line: do not take our word for it. The audit chain only grows, every entry carries a re-computable digest, and the rules are public. Anyone who re-runs it and gets a different answer — theirs wins.

## What the chain looks like

Every entry carries a digest:

```
hash(n) = sha256( hash(n-1) + this entry's canonical JSON )
```

Change one byte and from that entry onwards nothing matches. That is what "cannot be altered afterwards" means in practice. Not "we promise not to change it", but "if it is changed, it can be computed out".

To verify:

```
antinel verify
```

Exit code 0 means the chain is clean. Anything other than 0 means there is a break or a change somewhere in the middle.

## Append-only

The audit chain is an append-only ledger. Cleanup only rolls by date (the retention days are configurable), and the rolling itself is recorded: which dates were removed, how many entries.

Two failure modes are recorded explicitly rather than swallowed quietly:

- **A failed write**: recorded as `AUDIT_WRITE_FAILED`, allowed by default and visible (the reason is in [threat model and limits](/en/threat-model/)).
- **A lost entry**: a compensating write catches up the records it missed, recorded across processes in `lost.json`, filled in next time.

"Cannot be recorded" and "did not happen" have to be distinguishable. Otherwise the ledger is just a log that looks nice.

## Third-party re-runs

```
python -m scripts.run_harness
```

Re-run every assertion, arrive at your own conclusion, write it into `psl/judgment.json`. **Anyone who re-runs it and gets a different answer replaces the verdict we ship** — append-only, the original records are neither deleted nor changed.

This is the pivot of the whole trust model: we do not ask you to believe the verdict we ship. We ask that when you disagree, you can leave your own conclusion, and that the system must accept it.

## Watch it get broken with your own eyes

```
python challenge/verify.py
python challenge/tamper.py
python challenge/tamper-lab.html
```

The first is an independent re-computation that does not depend on this package. The second changes one entry, re-computes, and reports tamper. The third lets you edit by hand in a browser and watch it fail on the spot.

These three scripts exist so that "tamper-proof" stops being a claim and becomes something you can do yourself.

## Enforcement effectiveness self-check

```
python -m tools.enforce_probe
```

It synthesizes an event that must be blocked, runs the real checkpoint, and asserts that every delivery channel received it.

**A passing probe does not mean the host is on duty.** The probe proves "the checkpoint is capable of blocking". It does not prove "the host is calling the checkpoint". On-duty evidence is only the real traffic records on the audit chain. Those two kinds of evidence are recorded separately and are not merged into one sentence like "running normally".

## Ships with its own proof

{{facts.F-007.value.assertions}} assertions pass, {{facts.F-007.value.digests}} digests match. This is the self-proof record from when the package was released. It is not something we wrote up afterwards.

You can run the same set of assertions yourself:

```
python -m scripts.run_harness
```

## Three levels of re-computation

| Level | What you re-compute | What you need |
|---|---|---|
| One | whether the chain was touched | the installed package, and one `antinel verify` |
| Two | whether the shipped verdict is right | re-run the assertions and arrive at your own verdict |
| Three | whether the rules themselves are sensible | read the rules file and write a rule of your own to replace it |

The third level is the point: the rules live in `rules/default.json` and the format is public. If you think a rule judges too loosely or too tightly, change it and re-compute. You do not need our permission.

## Where the public re-computation lives

The code and every check are public at [github.com/sotaex/agentstate](https://github.com/sotaex/agentstate). The audit chain format, the assertion set and the challenge scripts are all in there.

The machine-readable version of every number on this page is in the [datasets](/en/datasets/).
