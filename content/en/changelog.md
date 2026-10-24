---
title: Changelog
slug: en/changelog
lang: en
updated: 2026-10-24
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

## 2026-10-24 · the site goes live

**Product version**: {{product_version}}　**Data date**: {{data_date}}

First release of the site. Two things were done structurally:

- The human layer and the machine layer share one source: every page has a `.md` mirror, and `/llms.txt` and `/llms-full.txt` are generated from the same batch of content. There is no case of "the web page changed but the copy for AI did not".
- Every number comes from a source-of-truth snapshot: at build time `rules/default.json` and the host register are read out of the product repository, with a sha256 lock. If the lock does not match, the build fails outright.

**Fact changes (against the previous version at the time of writing)**:

| Item | Current value | Note |
|---|---|---|
| Rule count | {{facts.F-001.value.rules}} rules | unchanged |
| Category count | {{facts.F-001.value.categories}} categories | unchanged |
| Gate count | {{facts.F-001.value.gates}} gates | unchanged |
| Host count | {{facts.F-003.value.hosts}} kinds | unchanged |
| Assertion count | {{facts.F-007.value.assertions}} | **changed**: the previous version had 320, this one has 323 |
| Digest count | {{facts.F-007.value.digests}} | unchanged |

The assertion count changed during an overnight product iteration, and the snapshot-and-lock mechanism on this site got verified once because of it: if the snapshot had not followed, the build would have failed on the spot rather than quietly publishing an old number.

**Check changes**: the first version established 22 build-time checks, covering page count, dead links, version provenance, gate-membership provenance, invisible characters and placeholder pages. Each one is paired with a counter-example — deliberately inject an error and that check must go red on the spot. Run it before and after the injection, to prove it is not a decoration that is always green.

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
