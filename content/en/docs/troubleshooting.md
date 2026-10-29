---
title: Troubleshooting and limits
slug: en/docs/troubleshooting
lang: en
updated: 2026-10-24
claim_ids: [F-004, F-005]
audience: human
---

# Troubleshooting and limits

In one line: look at the signal first, then the limits. Most cases of "installed but does nothing" are the same thing — the host was not restarted.

## The checkpoint does not fire

Check in this order. Do not skip steps:

```
antinel agent --json
antinel install --check
```

1. Is `installed` `true`? If not → re-run `antinel install`, then **restart the host**.
2. Is `host_detected` the host you think it is? If not → use `antinel --host <host> install` to name it explicitly.
3. Does `install --check` return `3`? → the registration and the disk disagree. Re-run `antinel install`.

If all three pass and it still does not fire, read on.

## Common signals at a glance

| Signal | Meaning | Action |
|---|---|---|
| `AUDIT_WRITE_FAILED` | an audit write failed, allowed by default | check disk space and permissions; or switch to fail-closed |
| `rules_integrity_fallback` | the checkpoint degraded to the fallback rule set | re-run `antinel install` |
| Block count goes to zero but the tool is running | the host may no longer honour exit code 2 | run `python -m tools.enforce_probe` and report it to the vendor |
| Heartbeat days is 0 | the checkpoint is not on duty | restart the host |
| `policy_changed` lands on a sidecar | the policy change did not reach the main chain, but the record is still there | run `antinel verify` to see the whole |

"Block count goes to zero but the tool is running" is the one to watch most closely. That is not "no violations". It is "cannot block". Use the enforcement probe to tell those two apart — a passing probe means the checkpoint is capable of blocking. A failing one means the host is not calling it.

## Installed, but audit only and no blocking

Not a fault. The first version verified real blocking on Windows only, and only on Claude Code / ZCode / Qoder. The rest install into audit-and-scan mode, and `antinel install` says so plainly.

In that state you can use: recording, checkup, inventory, ledger. You cannot use: blocking on the spot.

## Performance

One checkpoint call costs about {{facts.F-004.value.p50_ms}} milliseconds, and most of that is the cost of starting the Python interpreter. A default install starts no resident process, and it does not scan the whole disk.

If it feels slow, confirm that number first — use `antinel digest --days 1` to see whether any single call was unusually long. If it is a slow interpreter start (cold start, antivirus real-time scanning, a Python on a network drive), that is not ours. It does stack, though.

## The audit chain reports an error

```
antinel verify
```

There are two kinds of error:

- **One day's file is broken**: that day's records were changed or truncated. The chain points at the entry from which nothing matches.
- **A missing file**: a date is missing in between. Copying a machine, or an accidental delete during cleanup, both cause this.

In neither case should you "fix it to make it go green". The value of the chain is precisely that it will not lie to look good. Keep the evidence, build a new stretch of chain, and write the break point down clearly.

## The disk is full

The audit chain has three gates: days, size, free space. Before it fills up it clears the oldest day to make room. It stops once it has cleared enough, does not delete today, and records what it deleted.

If you really have to clear it by hand, delete a whole date file. Do not edit file content — editing content is tampering.

## Known limits (said once more)

| Limit | Consequence |
|---|---|
| It matches call text only and does not parse scripts | write a dangerous action into a `.py` or `.sh` file and run it: cannot block, only a record and a warning |
| No sandbox provided | for isolation, use a container or a virtual machine |
| Alternate data streams: writes only | the content inside the stream cannot be read back |
| Not an inspection report | it carries no legal weight |
| It cannot replace kernel-level protection | if the host does not call the checkpoint, the checkpoint is not there |

The full honest list is in [threat model and limits](/en/threat-model/).

## Still not working

Bring three things before you ask: the output of `antinel agent --json`, the exit code of `antinel install --check`, and the `antinel digest --days 1` for the period when the problem happened.

With those three, the problem can usually be located. Without them, it is guesswork.
