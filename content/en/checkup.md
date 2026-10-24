---
title: The checkup
slug: en/checkup
lang: en
updated: 2026-10-24
claim_ids: [F-003, F-008]
audience: human
---

# The checkup

In one line: one command, one click in this computer's browser, and you know whether the AI tools on this machine took anything of yours away. Read-only, no network, and the result does not leave the machine.

## Three entry points, by how much patience you have

| Entry | Command | How long | What you get |
|---|---|---|---|
| The checkup page | `antinel ui` | one click, about one to two minutes | a page you can click, screenshot and hand over |
| Whole-machine inventory | `antinel host-scan` | one to two minutes | which tools are installed, each one's verdict, where the evidence is |
| One page | `antinel brief` | a dozen seconds | anything sent out, change since last time, what to do |

The page and the command line read the same evidence. There is no case of "the page looks nice but the numbers underneath are wrong".

## What the checkup page does

`antinel ui` starts a local page on this machine. Open it in a browser and click "start check". It goes through the AI tools on this machine one by one looking for traces of a transfer, and translates the result into the six verdicts.

Three properties, better written here than buried in a document:

- **Read-only**: it does not change your files and does not touch tool settings.
- **It locks nothing**: no folder is locked.
- **It does not leave the machine**: the page is served locally and the result is not sent out.

## How to read the six verdicts

| | Name | What it means |
|---|---|---|
| 🔴 PACK | It recorded that it packed | the tool wrote down a size after packing, or a manifest hash |
| 🟠 SENT | It recorded that it sent | the tool wrote down "uploaded", "accepted by a server" or "pushed" |
| 🟡 SYNC | It recorded that it syncs | the tool wrote down a last sync time. A sync is not the same as uploading the whole project |
| ⚪ CLEAN | Checked, no record found | it was scanned and no self-reported transfer record turned up this time — which is not the same as there being none |
| ⚫ BLIND | Not checked | it is registered and it really is on your machine, but the scanner did not reach it. This item was not checked |
| · NA | Not applicable | an updater, or not an AI tool proper |

When one tool hits more than one, the highest one counts: PACK > SENT > SYNC > CLEAN.

**Every verdict carries the words "it recorded". That is discipline, not rhetoric.** What the steward reads is a field the tool wrote itself, not an action we watched. So the heaviest thing we can say is still "it recorded that it packed". We cannot say "it sent your file to someone".

## Two kinds of "nothing", and they must not look alike

This is the single most important thing about how the checkup page is designed:

- **⚪ Checked, no record found**: the scanner got there. No evidence turned up this time.
- **⚫ Not checked**: the scanner never got there. This item was not checked.

Merge those two into one word like "safe" and you are lying to the person reading it. So the first screen has to report "not checked: N". Not just "0 problems found".

By the same token, "no record found" is not "nothing happened", and "not checked" is not "clean". We write those three sentences on the page, not in a footnote.

## Scoring

Findings from the static scan are scored by severity:

```
score = 100 - 20 x critical - 5 x warning
```

De-duplicated by "rule x object". When the same object is hit by the same rule several times, it only costs once. That way the score reflects "how many problems there are", not "how many times it was scanned".

The score is for watching a trend. It is not for endorsing anything outward. We do not sell a "checkup passed" mark.

## What a full checkup looks like

```
antinel ui
antinel host-scan
antinel host-audit
antinel egress
antinel brief
```

After these five you hold: a clickable page, a whole-machine inventory, a record of today's actions, the current outbound ledger, and a one-page conclusion.

To keep it on file, save the `ui` page as a PDF. The page is designed to be screenshotted.

## Limits

What the checkup sees is **traces**, not **actions**. If a tool left no trace, the checkup cannot see it. If the way a tool leaves traces changes, the checkup may miss it.

This is not a gap that can be closed. It is the built-in ceiling of this kind of method. That is why "not checked" is a verdict of its own, rather than being counted as a good result.

The full honest list is in [threat model and limits](/en/threat-model/).
