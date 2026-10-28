---
title: Changelog
slug: en/changelog
lang: en
updated: 2026-10-29
claim_ids: [F-001, F-007]
audience: human
---

# Changelog

In one line: the site and the numbers both change. This page records where they changed. Only what has already happened is recorded. Nothing planned goes here.

## What gets recorded, and what does not

Three kinds get recorded:

1. **A fact changed**: a number that gets quoted — rule count, category count, host count, assertion count.
2. **A page changed**: a page added, a page removed, a structure change, a wording convention change.
3. **A check changed**: a build-time check added, removed, or changed in how it judges.

Not recorded: style tweaks, typo fixes, internal refactors. Those mean nothing to someone quoting us.

## What this site currently presents

**Product version**: {{product_version}}　**Data date**: {{data_date}}

The version number appears in that one place only. Each entry below records what changed at that time, relative to the previous sync. It does not repeat the current version — putting a live placeholder inside a dated entry means every sync rewrites what was true back then.

## 2026-10-29 · second sync

**Facts that changed**:

| Item | Previous sync | This one |
|---|---|---|
| Assertion count | 323 | {{facts.F-007.value.assertions}} |
| Rule count | 37 rules | {{facts.F-001.value.rules}} rules (unchanged) |
| Category count | 8 categories | {{facts.F-001.value.categories}} categories (unchanged) |
| Severity split | 21 blocking／16 warning | {{facts.F-002.value.critical}} blocking／{{facts.F-002.value.warning}} warning (unchanged) |
| Host count | 24 kinds | {{facts.F-003.value.hosts}} kinds (unchanged) |

The counts did not move, but **what they watch did**: 11 of them had their matching conditions revised, concentrated in secret reads, environment probing and destructive actions. Which files, which commands and which content features each one now watches is stated on [the rule index](/en/rules/) — it is not copied here, because two copies drift.

**Pages that changed**: this page was rewritten. The dated entries used to carry a live placeholder that the build filled with the current version, so every sync rewrote the version number of the day the site went live — a record that edits itself. Dated entries now record what was true then and what changed relative to it. The current version sits in one place, above.

**Checks that changed**: the version-provenance check used to recognise only one shape of version number. Once the product moved to a new version family, the check could not see a wrong version from that family at all — writing the immediately preceding version into the text still produced "0 mismatched versions". It now accepts any version shape, and a counter-example holds it in place. Also recorded here: the build-time checks grew from 22 in the first release to 30. The additions in between were never logged on this page, which was an omission on our part.

## 2026-10-24 · the site goes live

First release of the site. Two things were done structurally:

- The human layer and the machine layer share one source: every page has a `.md` mirror, and `/llms.txt` and `/llms-full.txt` are generated from the same batch of content. There is no case of "the web page changed but the copy for AI did not".
- Every number comes from a source-of-truth snapshot: at build time `rules/default.json` and the host register are read out of the product repository, with a sha256 lock. If the lock does not match, the build fails outright.

The numbers on launch day: 37 rules, 8 categories, 4 gates, 24 host kinds, 21 blocking, 16 warning, 323 assertions, 21 digests.

The assertion count had risen from 320 to 323 during an overnight product iteration, and the snapshot-and-lock mechanism on this site got verified once because of it: if the snapshot had not followed, the build would have failed on the spot rather than quietly publishing an old number.

**Checks**: the first version established 22 build-time checks, covering page count, dead links, version provenance, gate-membership provenance, invisible characters and placeholder pages. Each one is paired with a counter-example — deliberately inject an error and that check must go red on the spot. Run it before and after the injection, to prove it is not a decoration that is always green.

## How to look up an old version

Dataset file names carry the version. Old versions are kept permanently and never overwritten:

```
/datasets/rules@{{product_version}}.json
/datasets/hosts@{{product_version}}.json
/datasets/facts.json
/datasets/verdicts.json
```

The product's own change record is in the commit history of the `sotaex/agentstate` repository — that is the source of truth for the facts. This site is its readable presentation.

## If you find a mismatch

Bring your re-computation and tell us: which page, which number, and how you arrived at it. We change the page and record an entry here.

The source of truth for a number is always the product repository, never this site. If this site is wrong, the product repository wins.

## What this site does not do

A changelog is easy to turn into a page of self-congratulation. So first, the four things this site does not do:

- **Old entries are not deleted.** If a change was wrong, write another entry changing it back. The previous one is not erased.
- **Numbers are not changed quietly.** Every number on a page comes from a source of truth read at build time. Change one and it leaves an entry on this page.
- **No ranking is promised and no paid placement is accepted.** This site has no ad slots and sells no positions.
- **It does not endorse the product.** What is written here is re-computable fact, not remarks like "trustworthy".
