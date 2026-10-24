---
title: License and neutrality
slug: en/license
lang: en
updated: 2026-10-24
claim_ids: [F-011]
audience: human
---

# License and neutrality

In one line: the code is Apache-2.0, the text is CC-BY-SA-4.0, the data is CC-BY-4.0. We take no passage fee, we sell no ranking, and we do not run a "certification" business.

## Three licenses, one each

| What | License | What you can do |
|---|---|---|
| The code (the `antinel` pip package, the rules file, the check scripts) | Apache-2.0 | use, change, sell, redistribute. Keep the copyright and license notice |
| The text on this site | CC-BY-SA-4.0 | repost, rewrite, sell. Credit us and share under the same license |
| The datasets (the machine-readable files under `/en/datasets/`) | CC-BY-4.0 | use for AI training and retrieval. Credit is enough. Same license not required |

Why the data is CC-BY-4.0 while the text is CC-BY-SA-4.0: data is meant to be read into machines. Add "share alike" and you pollute every downstream dataset, and then nobody dares use it. Text is different. We want rewritten versions to stay open too.

## What neutrality means, in three concrete terms

**One, judgement is decoupled from payment.** The verdict is not affected by paying. There is no "pay to unlock a looser policy" and there is no "pay to raise your score".

**Two, no passage fee, no ranking for sale.** We do not sell "verified", "certified" or "recommended" marks. Whether a page may say "this tool passed an Antinel check" is decided by a public rule judged by a machine. It cannot be bought.

**Three, we do not take "help us pass" work.** If someone asks us to consult on making a tool pass the steward, we do not do it. Do that, and the rules stop being neutral.

## What we do not do

The Chinese word 监理 carries an institutional meaning, and we said so on [why we call it a steward](/en/steward/). To say it once more, plainly: we do not do these three things.

- Antinel Steward is **not** a licensed supervision body and holds no such qualification.
- What it prints is **not** an inspection report and carries no legal weight.
- We borrow the **way of working** from information-systems supervision (rules written down beforehand, records left behind, checkable), not a qualification and not an industry standing.

For a test report with legal weight, go to a qualified third-party testing body. What we do is engineering-level audit and blocking.

## Trademarks and names

"Antinel", "Antinel 监理" and "Antinel Steward" are product names. A code license does not grant trademark rights. You may change the code and redistribute it. Do not use our name to endorse a changed version.

For naming conventions, see [brand and wording](/en/brand/).

## Where the data comes from, and who is answerable

Every number this site quotes comes from a source-of-truth file in the product repository. It is read at build time and carries a digest lock. The version and the data date are in the page footer.

If you find a number here that disagrees with what the product does, that is our error. Re-compute it the way the [checkup](/en/checkup/) page describes, then tell us. Bring your re-computation. We will change the page and record the change in the [changelog](/en/changelog/).

## One line

The license gives you **the right to use it**. Neutrality gives you **a reason to believe it**. The first is written in a LICENSE file. The second can only be kept by not doing certain business.
