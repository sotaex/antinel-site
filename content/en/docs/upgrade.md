---
title: Upgrade and uninstall
slug: en/docs/upgrade
lang: en
updated: 2026-10-24
claim_ids: [F-007]
audience: human
---

# Upgrade and uninstall

In one line: an upgrade is three steps, and the middle one, "install the checkpoint", cannot be skipped. Skip it and the checkpoint degrades to the built-in fallback rule set while still appearing to run.

## Three steps to upgrade

```
python -m pip install --user -U antinel
antinel install --check
antinel install
```

The second line checks consistency first: `0` means the registration and the disk agree, `3` means there is drift. **Whichever it is, run `antinel install` once more after the second line**, otherwise the checkpoint does not pick up the new rules.

Restart the host once after the upgrade.

## How to tell the checkpoint has degraded

Two signals. Either one appearing means degradation:

1. The `rules fallback` line in the output of `antinel report` is not 0.
2. A `rules_integrity_fallback` event appears in the audit chain.

What degradation means: the checkpoint did not read the new rules and is using a small set of built-in fallback rules. Blocking capability drops sharply at that point, but **on the surface everything looks normal** — which is why these two signals are the only way to find it. You cannot find it by feel.

There is exactly one fix: re-run `antinel install`.

## What to re-verify after an upgrade

```
antinel agent --json
antinel verify
antinel host-scan
```

The first checks `installed` and `package_version`. The second checks whether the chain was broken by the upgrade process. The third checks whether the verdicts changed.

All three passing is what makes an upgrade complete.

## Does an upgrade lose history

No. The audit chain lives in `<project root>/.psl/audit/`. An upgrade changes the code only and does not touch the ledger. The policy file `.psl/policy.json` is kept too.

If the policy changed after the upgrade, run `antinel settings list` first to see the difference. Do not change it straight back — the new version may have added keys, and changing it back loses the defaults.

## Uninstall

```
antinel install --uninstall
```

Zero residue: it clears `.psl/manifest.json` and the checkpoint registration.

**The audit chain is not deleted.** That is deliberate: the ledger is evidence, and an uninstaller should not have the power to delete evidence. To delete it, remove `.psl/audit/` by hand.

## Moving to another machine

Three steps:

1. On the new machine, install the package, install the checkpoint, restart the host.
2. Copy the old machine's `.psl/audit/` across (optional, to continue the history).
3. Run `antinel verify` to confirm the chain joins up.

The chain is stored by file and by day, so copying it across does not break it — unless there are missing date files in between, and that gets reported.

## Where the version number lives

| Where | Command |
|---|---|
| The package version | `package_version` in `antinel agent --json` |
| The product version | the first line of `antinel --help` |
| This site's data version | the page footer |

All three should agree. If they do not, something was not updated somewhere — look at the data date in the footer first.
