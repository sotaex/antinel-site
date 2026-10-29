---
title: Five-minute start
slug: en/docs/quickstart
lang: en
updated: 2026-10-24
claim_ids: [F-003, F-008]
audience: human
---

# Five-minute start

In one line: install → check → guard. Three groups of commands, all copy-paste, and every step has a verification point.

## Step 0: install

```
python -m pip install --user antinel
antinel install
```

Then **restart the host once**.

Verify:

```
antinel agent --json
```

Look at `"installed": true`. If it is not `true`, go back to [install](/en/docs/install/).

## Step 1: check

Click once in a local browser to see whether the AI tools on this computer took anything out:

```
antinel ui
```

After the browser opens, click "start check". Read-only, locks nothing, and the result does not leave the machine.

For the command-line version:

```
antinel host-scan
```

It gives the whole-machine inventory: which tools are installed, what version each is at, the six verdicts, and where the evidence is. About one to two minutes.

## Step 2: read

Look at the number on the first screen first: **"not checked: N"**. Not "0 problems found" — those are not the same thing.

| What you see | What it means |
|---|---|
| 🔴 PACK it recorded that it packed | the tool recorded a size after packing, or a manifest hash |
| 🟠 SENT it recorded that it sent | the tool recorded "uploaded" or "accepted" |
| 🟡 SYNC it recorded that it syncs | the tool recorded a sync time. A sync is not the same as uploading the whole project |
| ⚪ CLEAN checked, no record found | it was scanned and no evidence turned up this time. **Not the same as a clean bill** |
| ⚫ BLIND not checked | the scanner never got there. **This item was not checked** |

For detail, see [the six verdicts](/en/verdicts/) and [the checkup](/en/checkup/).

## Step 3: guard

See who is connecting out right now:

```
antinel egress
```

See what was blocked today:

```
antinel digest --days 1
```

For one page you can hand over:

```
antinel brief
```

## Step 4 (optional): plant a mark

To find out whether the code got taken out, plant a canary:

```
antinel canary plant
```

Then work as normal. If the mark shows up in a tool's output or in the content of an upload, that is evidence of a transfer out. You can see it in the canaries count of `antinel report`.

## Three commands for every day

```
antinel morning
antinel digest --days 1
antinel verify
```

The first gives the morning report, the second gives yesterday's timeline, the third checks whether the audit chain was touched.

## If you want it stricter

```
antinel settings set net_mode block
antinel zone add <your project folder>
```

Switch the outbound bar from "warn" to "block", and mark folders as safe zones by directory. The change goes into the audit chain and can be looked up and undone.

To allow a domain (when package installs keep warning you):

```
antinel domains add pypi.org
```

## If something goes wrong, look here first

The checkpoint does not fire, the block count goes to zero, an audit write fails — [troubleshooting and limits](/en/docs/troubleshooting/) has a signal lookup table.
