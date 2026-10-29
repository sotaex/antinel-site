---
title: The 40-cell matrix
slug: en/completeness
lang: en
updated: 2026-10-24
claim_ids: [F-007]
audience: human
---

# The 40-cell matrix

In one line: completeness does not ask "how many bad things are there in the world" (that cannot be exhausted). It asks "when one kind of carrier fails, can I detect it". Eight kinds of carrier times five actions. Forty cells, each with a conclusion and the evidence behind it.

## Why a matrix and not a list of threats

A list of threats never ends. Features are open-ended, and so are the ways to break them: seventeen today, an eighteenth tomorrow.

But **carriers are a closed set**. The ways a process can fail are limited by the finite kinds of resource it can consume and depend on: time, disk, memory, permissions, input, locks, version, environment. Plus one thing that is not in the program but breaks systems just the same — people.

So completeness can only be defined on the carrier dimension. Forty cells are not forty points. They record that all eight directions were asked.

## The five actions, one question each

| Action | The question |
|---|---|
| See | when this kind of carrier fails, can I observe something wrong |
| Judge | having observed it, can I judge it right (and not read "cannot compute" as "nothing wrong") |
| Report | is the conclusion visible to the user and readable by them |
| Stop | can damage be cut off **before** the consequence lands |
| Record | is what is left behind evidence that **cannot be altered afterwards** |

Four marks, with fixed meanings:

- **✔** there is a mechanism, and it can point at the evidence (a check, a probe, or a measurement).
- **◐** there is a mechanism, but coverage is incomplete.
- **✘** there is not.
- **Unverified** I have not checked this one. **This cell may not be written as "yes".**

## The conclusion

Of the forty cells: **✔ 29 / ◐ 10 / ✘ 1 / unverified 0**.

The one remaining ✘ is "people · stop" — a person kills the process, edits the file, dismisses the dialog, and no program can stop them. This cell will not become ✔. It will stay "an acceptance we wrote down". We chose to put it on paper rather than pretend it is not there.

## The eight carriers

| Carrier | What it refers to | A typical way it breaks |
|---|---|---|
| Time | wall clock, monotonic clock, time zone, daylight saving | the user changes the system time and "how long was it on duty" comes out wrong |
| Space | disk, memory, paths, filename encoding | the disk fills and the audit write fails; a path that is too long fails to write |
| Permissions | ACL, administrator, file mode | an ordinary user cannot read the host directory, so the scan silently scans less |
| Input | command line, environment variables, config, chain records | an argument with spaces or non-ASCII gets parsed out of alignment |
| Concurrency | locks, multiple processes, races | two checkpoints write at once and the later one overwrites the earlier |
| Version | schema, code against the register, interpreter | the package is older than the source, so what you installed is the previous version's behaviour |
| Environment | the host checkpoint, terminal encoding, network | the host changes the checkpoint protocol and the checkpoint stops being called |
| People | ignoring, killing the process, editing files | the dialog gets dismissed, and afterwards nobody knows it was there |

## A few cells worth looking at

**Time · Judge**: when the clock has been changed, it has to be able to say "cannot compute how long it was on duty", not compute a negative number and treat that as normal. The rule has one implementation: a negative number is always read as "cannot compute".

**Space · Stop**: the audit chain has three gates (days, size, free space). Before it fills up it clears the oldest day to make room, stops once it has cleared enough, does not delete today, and records what it deleted. A full disk is not "a failed write". It is "a planned degradation".

**Version · Judge**: a package older than the source disguises "not registered" as "shipped with the package". So verification has to rename the build leftovers out of the way first and then rebuild. We have stepped on this one.

**People · Stop**: the only ✘. When a person is not in the loop, no program can stop a person.

## What this page does not answer

It does not answer "how many bad things are there in the world in total". It does not answer "is there anything outside these forty cells" either. There is. Those problems just do not fall on the carrier dimension, and they need another coordinate system.

We publish this matrix so that the word "complete" has a boundary: **saying complete means these forty cells were all asked. It does not mean there is nothing else.**

## Where the evidence is

The evidence for each cell (the check name, the probe name, the measurement record) is listed cell by cell in the matrix document in the product repository, and it follows the version. This page gives the method and the conclusion. It does not repeat that big table — two tables in two places fall silently out of step, so we keep one.

Ships with its own proof: {{facts.F-007.value.assertions}} assertions pass, {{facts.F-007.value.digests}} digests match. For how to re-compute it, see [audit chain and re-runs](/en/audit/).
