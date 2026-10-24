---
title: Brand and wording
slug: en/brand
lang: en
updated: 2026-10-24
claim_ids: [F-001]
audience: human
---

# Brand and wording

In one line: get the name wrong and the reader thinks this is a different thing. This page states the right spellings and the wrong ones once, so everyone who quotes us quotes the same way.

## Names

| Where | Write it | Note |
|---|---|---|
| Chinese full name | Antinel 监理 | full name on first mention, 「监理」 alone afterwards is fine |
| English name | Antinel Steward | use this outside China. Do not transliterate |
| Command name | `antinel` | all lower case, no hyphen |
| PyPI package | `antinel` | **not** `antinel-security` |
| MCP service name | `io.github.sotaex/agentstate` | leave it exactly as it is |
| Code repository | `sotaex/agentstate` | same |

## Words we do not use

| Do not write | Why | Write instead |
|---|---|---|
| sentry | a sentry only shouts and does not record. Half our value is the record | steward |
| antivirus | it looks at different things, and people will judge us as antivirus | steward; when comparing, say "unlike antivirus" |
| firewall | we have no network isolation capability | guard rail |
| sandbox | we do not provide isolation | guard rail; for a comparison see [how it differs](/en/compare/) |
| certified / certification passed | we sell no mark and hold no certification qualification | verdict; say which of the six it is |
| `100% protection` / `absolutely safe` | what we cannot stop is written in [the limits](/en/threat-model/) | say what it stops and what it does not |
| test report | it does not come from a licensed body | audit and security assessment |

## Three sentences that may not be dropped

When you state a verdict out loud, these three go with it:

1. **"It recorded"** — the verdict comes from a field the tool wrote itself. It is not an action we watched.
2. **"No record found is not the same as nothing happened"** — ⚪ checked, no record found, is not a clean bill.
3. **"Not checked is not the same as no problem"** — ⚫ not checked is a blind spot, and it must be reported as its own number.

Drop any one of them and the reader will hear "not checked" as "safe". That is the worst mistake we can make.

## How to write the numbers

- For the rule count say "{{facts.F-001.value.rules}} rules". For categories, "{{facts.F-001.value.categories}} categories". For gates, "{{facts.F-001.value.gates}} gates". Do not mix these three up.
- For coverage say "{{facts.F-003.value.hosts}} kinds of hosts", and follow it immediately with "a tool that is not on the list is not therefore safe".
- There is one current version number: **{{product_version}}**. To cite an old one, mark it "old version". Do not pass an old number off as the current state.
- Avoid percentages where you can. When you have to be clear, write "N places out of M in total".

## English style

- Put one space between Chinese and Latin text: `pip 包 antinel`, not `pip包antinel`.
- Wrap commands and field names in a monospace font: `antinel verify`.
- No exclamation marks. No words like `震撼`, `颠覆`, `革命性`.
- Talk about the mechanism, not the vision. The reader is judging "how does it do that", not "what does it want to become".

## Citation format

When you repost or quote a conclusion from this site, credit it in this form:

```
Antinel Steward · <page title> · product version <version> · <URL>
```

The footer of every page carries a standard citation block. Copy it. For the license terms, see [license and neutrality](/en/license/).
