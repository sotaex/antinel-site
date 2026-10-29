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
| Assertion count | 323 | 325 |
| Rule count | 37 rules | 37 rules (unchanged) |
| Category count | 8 categories | 8 categories (unchanged) |
| Severity split | 21 blocking／16 warning | 21 blocking／16 warning (unchanged) |
| Host count | 24 kinds | 24 kinds (unchanged) |

The counts did not move, but **what they watch did**. Compared with the previous sync, 11 of the 37 rules had their matching conditions revised: five in secret reads, three in destructive actions, and one each in context, injection and metadata. That is the net change between two syncs, not what any single release changed. Which files, which commands and which content features each one now watches is stated on [the rule index](/en/rules/). It is not copied here, because two copies drift.

**Pages that changed**: this page was rewritten. The dated entries used to carry a live placeholder that the build filled with the current version. Every sync therefore rewrote the version number of the day the site went live: a record that edits itself. Dated entries now record what was true then and what changed relative to it. The current version sits in one place, above.

One more fix. In the `antinel agent --json` example, the hook-registration version was hard-coded to a much older value. It is a placeholder now. The field table states plainly that it is a different number from the package version, and not guaranteed to match it.

**Checks that changed**: the version-provenance check used to recognise only one shape of version number. Once the product moved to a new version family, the check could not see a wrong version from that family at all: writing the immediately preceding version into the text still produced "0 mismatched versions". It now accepts any version shape.

While adding the counter-example, two siblings of the same defect surfaced. Code samples were skipped wholesale, so an old version written inside an example (the one fixed just above) was never checked at all. The pattern's tail also excluded a full stop, so the most natural English phrasing — a version at the end of a sentence — never matched. Both now have counter-examples, so this one check is held in place by three: body text, code block, sentence end.

One last gap was closed too. Of the 30 checks, only the input-count self-check had no counter-example. There are 35 counter-examples now, matching all 30 one by one.

Also recorded here: the build-time checks grew from 21 in the first release to 30. That is 22 the same day, 29 once the human layer was filled in, and 30 with the English mirror. The additions in between were never logged on this page, which was an omission on our part.

## 2026-10-29 · third sync

**Facts that changed**:

| Item | Previous sync | This one |
|---|---|---|
| Resident process | none | none on a default install; one after you turn on host interception |
| Rule count / categories / severity / host kinds / assertions | — | unchanged |

**Pages that changed**: two, and both were the site saying something wrong.

The first is the resident-process wording. One page said "no resident process". Another page told you to run `antinel host-shield enable`. After that command there is a resident process on this machine, started at logon. The two pages contradicted each other, so a reader who followed one ran into the other. Both now say "none by default". The threat-model page adds what that one process does after you enable it: it runs on this machine only, and uses no network.

The second is the English term note. A human page adds a short explanation the first time a term appears: it matches the word stem, then inserts brackets right after it. English has plurals, so the rendered page carried `six verdict(the one conclusion a tool gets after a check)s` — the word split in two. Reverting the fix and rebuilding reports eight places across the site. A spot check of the live site found six in three pages: `/en/faq/` three, `/en/monitor/` two, `/en/checkup/` one. Chinese has no word endings, so it was not affected.

**Checks that changed**: three new ones, each with a counter-example. A check with no counter-example does not count on this site.

- **Sentence-length ceiling**: 70 characters in Chinese, 35 words in English. One sentence over, and it goes red. ASD-STE100 puts the descriptive limit at 25 words. This site does not meet that yet, so there is a second line (50 characters, 25 words) that may only go down. Every build prints how far off we still are.
- **Brackets must not split a word**: in the rendered body, a bracket followed directly by a lower-case letter is red.

That takes the checks from 30 to 33 and the counter-examples from 35 to 38.

## 2026-10-24 · the site goes live

First release of the site. Two things were done structurally:

- The human layer and the machine layer share one source: every page has a `.md` mirror, and `/llms.txt` and `/llms-full.txt` are generated from the same batch of content. There is no case of "the web page changed but the copy for AI did not".
- Every number comes from a source-of-truth snapshot: at build time `rules/default.json` and the host register are read out of the product repository, with a sha256 lock. If the lock does not match, the build fails outright.

The numbers on launch day: 37 rules, 8 categories, 4 gates, 24 host kinds, 21 blocking, 16 warning, 323 assertions, 21 digests.

The assertion count had risen from 320 to 323 during an overnight product iteration. The snapshot-and-lock mechanism on this site got verified once because of it. If the snapshot had not followed, the build would have failed on the spot instead of quietly publishing an old number.

**Checks**: the first version established 21 build-time checks, covering page count, dead links, version provenance, gate-membership provenance, invisible characters and placeholder pages. Each one is paired with a counter-example — deliberately inject an error and that check must go red on the spot. Run it before and after the injection, to prove it is not a decoration that is always green.

## How to fetch the datasets

Dataset file names carry the version, which makes reconciliation easy:

```
/datasets/rules@{{product_version}}.json
/datasets/hosts@{{product_version}}.json
/datasets/facts.json
/datasets/verdicts.json
```

The version in a file name is the version that build read. The live site only carries the set produced by the current build — the previous version's address is overwritten, so download and keep it yourself if you need it (the licence allows that).

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
