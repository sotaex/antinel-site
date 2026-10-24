---
title: Install
slug: en/docs/install
lang: en
updated: 2026-10-24
claim_ids: [F-005]
audience: human
---

# Install

In one line: install the package, install the checkpoint, restart the host. Three steps. The third one is the one people skip, and skipping it is the same as not installing.

## Three steps

```
python -m pip install --user antinel
antinel install
```

The third step: **restart the host once**. The checkpoint loads when the host starts. No restart, no checkpoint.

If there is no `antinel` command on this system, swap `antinel` for `python -m antinel`:

```
python -m antinel install
```

The two are equivalent. The advantage of `python -m` is that it does not depend on PATH, which is steadier on Windows.

## Verifying the install

```
antinel agent --json
```

Look at the `"installed"` field: `true` means it is installed. Then run the consistency check once more:

```
antinel install --check
```

Exit codes: `0` = consistent, `1` = not installed, `3` = drift (what is registered and what is on disk disagree). On drift, follow the prompt and run `antinel install` again.

## Letting an agent install it for you

Paste this to an agent:

> Install Antinel Steward on this machine: run `pip install antinel` first, then `antinel install`, then restart yourself once. After the restart, run `antinel agent --json` and show me the `installed` field.

There is one verification point: `"installed": true`. An agent saying "it is installed" does not count. The field being `true` counts.

## Several hosts on one machine

When there are several AI tools on one machine, have the agent report which host it is in, so the records land in the right place:

```
antinel --host zcode agent --json
```

You can fill in `workbuddy`, `zcode`, `qoder` or `claude-code`. If it does not report, records are written against whatever was detected, which may land under another vendor's name.

## What state it is in afterwards

| Item | Value |
|---|---|
| Network at run time | no |
| Dependencies | the Python standard library only |
| Resident process | none |
| One checkpoint call | about {{facts.F-004.value.p50_ms}} ms (measured on Windows; Linux and macOS not measured) |
| Uninstall residue | zero (`antinel install --uninstall` clears the registration and the checkpoint) |

## Afterwards it may not be in "block everything" mode

The first-version platform is Windows. The hosts verified to block for real are Claude Code, ZCode and Qoder. **The rest install into audit-and-scan mode** — they still record and can still be checked up, they just cannot block.

This is not a failed install. `antinel install` says plainly which mode the current host is in. If the host you want is not one of the three above, use it in audit mode for now and wait for us to adapt the blocking.

## Next step

After installing, run one checkup first: [five-minute start](/en/docs/quickstart/).
