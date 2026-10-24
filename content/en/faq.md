---
title: Questions
slug: en/faq
lang: en
updated: 2026-10-24
claim_ids: [F-001, F-003, F-004, F-005, F-008]
audience: human
---

# Questions

In one line: the twelve questions we are asked most. Each answer stands on its own — pull one out and it still makes sense.

## What is Antinel Steward, exactly

An independent third-party steward installed on your own computer, watching every tool call an AI coding tool makes: what should be blocked is blocked on the spot, what should be warned about is warned about, and every single one is recorded. It runs locally, takes no network at run time, uses the Python standard library only, and keeps no resident process.

## How is it different from antivirus software

Antivirus looks for malicious patterns in files. A steward asks whether this call's action was allowed in the first place. "An agent read your `.env` and then exited normally" is not a virus, so antivirus says nothing, while the steward blocks it on the spot and records it. Neither covers for the other.

## Will it slow my computer down

One checkpoint call costs about {{facts.F-004.value.p50_ms}} milliseconds, and most of that is the cost of starting the Python interpreter. There is no resident background process, it takes no memory, and it does not scan the whole disk. Only Windows was measured for that figure. Linux and macOS have not been.

## Could it send my data out

No. At run time there is no network, the standard library is all it uses, and there is no resident process. The checkup, the scan and the ledger all run to completion on this machine, and the result does not leave it. That is the premise of it being "a steward answerable to the principal" — one that reports to a cloud cannot answer to a local principal.

## Does it cost anything

No. The code is open source under Apache-2.0, and `pip install antinel` installs it. We do not sell "certification", "placement" or "pass marks", and we do not take "help us pass" work — that would stop the rules being neutral. See [license and neutrality](/en/license/).

## Which systems and AI tools are supported

The first-version platform is Windows. The hosts verified to block for real are Claude Code, ZCode and Qoder. The rest install into audit-and-scan mode: they still record and can still be checked up, they just cannot block. `antinel install` says so plainly, and that is not a failed install. The register holds {{facts.F-003.value.hosts}} kinds of hosts in total — **a tool that is not on the list is not therefore safe**, it only means the steward has no way to collect its records.

## Can data that was already taken out be recovered

No. A steward is a guard rail, not a recovery tool: it governs what comes after, and records what already happened. To judge "was anything taken out before", run one checkup and read the six verdicts — 🔴 it recorded that it packed, 🟠 it recorded that it sent, 🟡 it recorded that it syncs. Any of those three appearing means there are traces.

## What is the difference between "not checked" and "no record found"

A long way. ⚪ "checked, no record found" means the scanner got there and no evidence turned up this time. ⚫ "not checked" means the scanner never got there, so this item was not checked. Merging the two into one word like "safe" is lying to the reader, which is why the first screen has to report "not checked: N".

## Can it stop an agent deleting my files

It can block a command-level deletion (`DST-01`, critical, blocked on the spot). But **it does not parse what a script does**: put the deletion inside a `.py` or `.sh` file and run that file, and the checkpoint only sees "run a script". It cannot stop it. There is a record and a warning, and nothing more. For real isolation, use a container.

## I am not a programmer. Can I use it

Yes. Run `antinel ui`, open the local page in a browser, click "start check", and out comes a page of results you can read and screenshot. The command line is for people who want the detail. It is not required.

## How do I verify it is not fooling me

Three things. `antinel verify` checks whether the audit chain was touched. `python -m scripts.run_harness` re-runs every assertion so you arrive at your own conclusion, which can replace the one we ship. `python challenge/tamper.py` lets you watch it get broken and watch it report the break. The rules themselves are public in `rules/default.json` too. If you think one is wrong, change it.

## Why "steward" and not "sentry"

A sentry only shouts and does not record. A steward judges against rules written down beforehand, acts on the spot, writes it into the record, and lets you re-compute the whole thing afterwards. Shout without a record, and nobody can show the next day that it ever happened. The longer version is on [why we call it a steward](/en/steward/).

## What it cannot do, on one page

The boundaries are scattered through the answers above. Here they are in one place. It cannot do these five things:

- **It cannot stop a dangerous action written into a script.** Put the deletion into a `.py` file and run that file, and the checkpoint only sees "run a script". There is a record. It is not blocked.
- **It does not isolate.** It builds no sandbox and does no virtualisation. Real isolation needs a container or a virtual machine.
- **It knows only the {{facts.F-003.value.hosts}} kinds of AI tools on its register.** For a tool that is not registered, it cannot collect records.
- **What it prints is not an inspection report.** It carries no legal weight. For that kind of report, go to a qualified body.
- **"Not checked" is not the same as clean.** It reports "this item was not checked". It does not report "you have no problem".

The full boundary is in [threat model and limits](/en/threat-model/). Whether to use it depends on whether what you are missing is this book of records.
