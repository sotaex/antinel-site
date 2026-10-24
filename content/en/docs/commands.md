---
title: Command reference
slug: en/docs/commands
lang: en
updated: 2026-10-24
claim_ids: [F-008]
audience: human
---

# Command reference

In one line: look up by intent, not alphabetically. The three main lines are audit, guard and ledger. First work out which question you are trying to answer.

## Audit: is anything wrong on this machine

| Intent | Command | Note |
|---|---|---|
| One page you can hand over | `antinel brief` | anything sent out, change since last time, what to do |
| One click on this machine | `antinel ui` | opens a local page in a browser. Read-only, does not leave the machine |
| Whole-machine inventory | `antinel host-scan` | which tools, verdicts, evidence. About one to two minutes |
| Anything out of line today | `antinel host-audit` | looks at the current day only |
| Who is sending out right now | `antinel egress` | samples the connection table about every 30 seconds. No payloads |
| What was done, what was blocked | `antinel digest --days 1` | a timeline |
| Cross-tool summary | `antinel digest --scope all` | several hosts at once |
| Morning report | `antinel morning` | yesterday's summary |
| Pending items | `antinel inbox list` | the inbox |
| Historical ledger | `antinel ledger --days 7` | by calendar day. A day with no records is `null`, not 0 |

## Guard: make it able to block

| Intent | Command | Note |
|---|---|---|
| Plant a transfer-detection mark | `antinel canary plant` | reading it triggers a SEC-11 reminder |
| See what is planted | `antinel canary list` | — |
| Transfer landing-spot gate | `antinel host-shield status` | on-duty status and locked landing spots |
| Deploy it | `antinel host-shield enable` | off by default, you have to turn it on |
| Landing spots awaiting your call | `antinel host-shield queue` | — |
| Decide an allow | `antinel host-shield decide "<path>" allow_always` | **an allow has to be made by you, in a terminal, by hand** |
| Locked list | `antinel host-shield locks` | to unlock, use `unlock` |
| Mark a safe zone | `antinel zone add <folder>` | writes inside the zone are controlled |
| Switch outbound to block | `antinel settings set net_mode block` | the default is `warn`: warn only, no block |
| Allow a domain | `antinel domains add pypi.org` | relaxes network rules only, and goes into the audit chain |
| Allow a path | `antinel paths add <prefix>` | relaxes sensitive-surface rules and releases "writes outside the project" |
| A bigger boundary | `antinel roots add D:\demo` | allow a whole tree |
| See the current policy | `antinel settings list` | for a single key, `settings get <key>` |

Every allow-type command is recorded and can be undone (`domains remove` / `paths remove` / `zone remove`). If you allowed the wrong thing, undo it. Do not change the rule.

## Ledger: what was spent, and whether there is enough left

| Intent | Command | Note |
|---|---|---|
| What this session spent | `antinel report --session latest` | — |
| The last seven days | `antinel report --days 7` | sorted by severity, each entry with handling advice |
| Record a balance | `antinel credits snapshot <balance>` | also takes `--reward N@expiry` and `--cycle expiry` |
| Is there enough left | `antinel credits forecast` | — |
| Subscription vs pay-as-you-go | `antinel credits reconcile` | reconciliation |

The ledger records only the behaviour and the consumption of agents. It does not rank people by efficiency.

## Install and check

| Intent | Command | Exit code |
|---|---|---|
| Install the checkpoint | `antinel install` | — |
| Consistency check | `antinel install --check` | `0` = consistent / `1` = not installed / `3` = drift |
| Uninstall | `antinel install --uninstall` | — |
| Current state | `antinel agent --json` | — |
| The manual that ships with the package | `antinel skill` | for the path only, use `--path` to save tokens |
| Phrasing table | `antinel routes --markdown` | same source as `--help` |

## The exit-code contract

| Command | Exit code |
|---|---|
| `antinel install --check` | 0 = consistent / 1 = not installed / 3 = disagrees with the registration |
| `antinel verify` | 0 = the chain verifies and is consistent / non-zero = there is a break, a change, or it cannot be verified |
| When the checkpoint blocks | 2 |
| When the checkpoint warns | 0 |
| Checkpoint internal error | 0 (fail-open, and records `AUDIT_WRITE_FAILED`) |

## Commands that only run in the code repository

These are not subcommands of `antinel`. They run from the root of the source repository (these paths do not exist in a pip-installed package):

```
python -m scripts.scan --root .
python -m scripts.run_harness
python -m tools.antinel_verify
python -m tools.enforce_probe
python challenge/verify.py
python challenge/tamper.py
```

What each does: static scan, re-run every assertion, independently verify the audit chain, an enforcement effectiveness probe, an independent re-computation, and a tamper demonstration.

If you installed the package but have no source repository, the `antinel` subcommands are enough: `host-scan` covers the static scan, `verify` covers chain verification. To re-run the assertions (and replace the shipped verdict with your own), you need the source repository.

## Conventions

- When `antinel` is not on PATH, always use `python -m antinel <command>`. The two are equivalent.
- On a multi-host machine, report the host yourself: `antinel --host zcode <command>`.
- Put quotes around paths that contain spaces.
