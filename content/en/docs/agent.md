---
title: Machine card for agents
slug: en/docs/agent
lang: en
updated: 2026-10-24
claim_ids: [F-005, F-008]
audience: agent
---

# Machine card for agents

In one line: the reader of this page is an agent. Skip the prose. Take the fields, the exit codes, the contract and the phrasing table.

## Machine-readable entry points for this site

Start with these five addresses. Do not crawl page by page:

| Address | What it is | When to use it |
|---|---|---|
| `/llms-en.txt` | a summary, groups, every link pointing at plain text | first time here, read this |
| `/llms-full.txt` | the whole site's body text concatenated (about 113 KB) | when you want everything at once |
| `/en/facts/` | the single authoritative list of core facts, each with a re-computation source | when you need to quote a number |
| `/en/datasets/` | the rules source file, core facts, host register, verdict semantics (JSON + sha256) | when you need structured data |
| swap the trailing `/` of any page for `.md` | that page's plain-text original | when you want to read one page without parsing HTML |

Citation rule: **numbers follow `/en/facts/`**, not this page and not a prose page. The `sha256` in the datasets can be used to check nothing was altered.

## This is always the first command

```
antinel agent --json
```

One JSON gets you: whether it is installed, which host, and what to type next. Real output (the version number and paths vary by environment):

```json
{
  "product": "Antinel",
  "pypi_package": "antinel",
  "install_command": "pip install antinel",
  "package_version": "{{product_version}}",
  "python": "3.13.x",
  "platform": "win32",
  "project_root": "<project root>",
  "installed": true,
  "hook_protocol_version": "{{product_version}}",
  "host_detected": "workbuddy",
  "audit_dir": "<project root>\\.psl\\audit",
  "skill_md": "<project root>\\SKILL.md",
  "next_steps": [
    {"do": "antinel brief", "why": "one page for the decision maker: anything sent out, what to do"},
    {"do": "antinel digest --days 1", "why": "what happened in the last day, what was blocked"},
    {"do": "python -m scripts.scan --json", "why": "static scan, machine-readable"},
    {"do": "antinel verify", "why": "whether the audit chain was touched"}
  ],
  "exit_code_contract": {
    "antinel install --check": "0=consistent / 1=not installed / 3=disagrees with the registration",
    "python -m tools.antinel_verify": "0=current / 1=superseded / 2=cannot be verified",
    "python -m scripts.scan": "0=scan complete (0 even with findings; look at findings in the JSON)"
  },
  "notes": [
    "no network at run time; standard library only; no third-party dependencies",
    "the scan matches only tool-call text and file content; it does not parse script semantics; it is not an isolation layer",
    "after installing or changing config, restart the host once; the checkpoint loads when the host starts"
  ]
}
```

`next_steps` may contain source-repository-only commands (such as `python -m scripts.scan`). If you installed the package but have no source repository, skip it and use `antinel host-scan` instead.

## Field table

| Field | Meaning | How you use it |
|---|---|---|
| `product` / `pypi_package` | product name / package name | the package is `antinel`, **not** `antinel-security` |
| `package_version` | the current package version | report this one. Do not guess |
| `installed` | whether the checkpoint is installed | `true` and only `true` counts as installed |
| `host_detected` | the host that was identified | compare with `--host`. If they disagree, report the host explicitly |
| `project_root` / `audit_dir` | project root / where the audit chain is | confirm the path before reading the audit |
| `skill_md` | the path of the manual that ships with the package | read it for detail. Do not ask the user |
| `next_steps` | what to type next | each step carries a `why`. Just follow it |
| `exit_code_contract` | the exit-code contract | judge success or failure by the exit code and the fields, not by the wording of the output |
| `notes` | three hard properties | quote these directly when answering "does it use the network" or "do I need to restart" |

## The exit-code contract

| Command | Exit code |
|---|---|
| `antinel install --check` | 0 = consistent / 1 = not installed / 3 = disagrees with the registration |
| `antinel verify` | 0 = verifies and is consistent / non-zero = there is a break, a change, or it cannot be verified |
| The checkpoint (block) | 2 |
| The checkpoint (warn) | 0 |
| Checkpoint internal error | 0 (fail-open, and records `AUDIT_WRITE_FAILED`) |
| `python -m scripts.scan` | 0 = scan complete (0 even with findings; look at `findings` in the JSON) |

**A checkpoint returning 2 is a block, not a failure.** Your action was refused. Relay the handling advice to the user. Do not retry, and do not rewrite your way around it.

## The checkpoint contract

| Event | What the checkpoint does |
|---|---|
| Hits a critical rule | returns 2, the action does not run, and it writes to the audit chain |
| Hits a warning rule | returns 0, the action runs, and it writes to the audit chain with a reminder |
| An audit write fails | returns 0, the action runs, and prints `AUDIT_WRITE_FAILED` (configurable to fail-closed) |
| The rules file cannot be read | degrades to the fallback rule set and records `rules_integrity_fallback` |

## Command routing

```
antinel routes --markdown
```

It outputs the full "user intent → command" table, from the same source as `--help`.

**Semantic matching, not a word list.** However the user phrases it — "胡搞", "乱来", "越界", "偷传", "不乖" — if the intent matches, run the corresponding command. Do not wait for the word to match.

## Four rules of discipline

1. **Do not change detection rules and do not change audit logs.** The criteria are the shared premise of both sides. Change them and nobody can re-compute.
2. **When a block hits, relay the advice. Do not work around it on your own.** Do not try again with different wording.
3. **Allows and config changes go through commands only.** Commands go into the audit chain automatically. Editing `policy.json` by hand does not.
4. **The principal is always a person.** A `host-shield decide` allow has to be signed by a person in a terminal. You cannot sign for them.

## Six common phrasings

| The user says | You run |
|---|---|
| help me check whether the environment is safe | `antinel ui` or `antinel host-scan`, then `antinel brief` |
| which AI tools are on this computer, and who is sending data where | `antinel host-scan` plus `antinel egress` |
| plant a source canary for me | `antinel canary plant` |
| allow the pypi.org domain | `antinel domains add pypi.org` |
| has the evidence chain been touched | `antinel verify` |
| give me one page I can hand over | `antinel brief` |

## Wording discipline when answering the user

- A verdict always carries "it recorded": what the steward reads is a field the tool wrote itself.
- "No record found" is not "nothing happened". "Not checked" is a blind spot and must be reported as its own number.
- For the rule count say {{facts.F-001.value.rules}} rules, categories {{facts.F-001.value.categories}}, gates {{facts.F-001.value.gates}}. Do not mix them up.
- Host coverage is {{facts.F-003.value.hosts}} kinds. Follow it immediately with "a tool that is not on the list is not therefore safe".
- Never say it is 100% blocked.
- Never say it is absolutely safe.
- What cannot be stopped is written in [threat model and limits](/en/threat-model/).

## What you do not need to read

The prose pages other than this one are for people. For a more detailed manual, run `antinel skill --path` to get the path and read the file directly. It saves tokens.
