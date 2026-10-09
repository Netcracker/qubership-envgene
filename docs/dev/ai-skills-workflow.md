# AI skills workflow

- [Description](#description)
- [Skills](#skills)
- [Prerequisites](#prerequisites)
- [Work without dev-flow](#work-without-dev-flow)
- [Work through dev-flow](#work-through-dev-flow)
- [How the team rules reach a reviewer agent](#how-the-team-rules-reach-a-reviewer-agent)

## Description

This document shows which Claude Code skill runs at which point of a code change in this repository, and
who does the work at that point: you or an agent.

A dev design is the document that says how a change is built in code. You write it with Claude before any
code, and it lives in `docs/dev/designs/`.

The diagrams use six colors:

- Green: a team skill from `.claude/skills/`.
- Blue: a skill from the superpowers plugin.
- Purple: a skill built into Claude Code.
- Orange: a step that you do yourself.
- Gray: a step that an agent does.
- Yellow with a dashed border: a file.

The diagrams are `.drawio.svg` files in `docs/images/`. Open them in draw.io to edit them.

## Skills

| Skill                         | Source             | Purpose                              |
|-------------------------------|--------------------|--------------------------------------|
| `dev-design`                  | Repository         | Write the dev design in a dialog     |
| `envgene-code-review`         | Repository         | Check a diff against the team rules  |
| `dev-flow`                    | Repository         | Run the phases in order              |
| `design-to-cr`                | Repository         | File the CR from a settled design    |
| `writing-adrs`                | Repository         | Write the ADR                        |
| `writing-docs`                | Repository         | Apply the documentation style rules  |
| `writing-gherkin`             | Repository         | List the missing BDD scenarios       |
| `brainstorming`               | superpowers plugin | Lead the design dialog               |
| `writing-plans`               | superpowers plugin | Split the dev design into tasks      |
| `subagent-driven-development` | superpowers plugin | Run the agents that write the code   |
| `requesting-code-review`      | superpowers plugin | Start a separate reviewer agent      |
| `code-review`                 | Claude Code        | Find correctness bugs in a diff      |

Repository skills live in `.claude/skills/`. Claude Code loads them for everyone who clones the repository.

## Prerequisites

The `dev-flow` skill and the agent branch of `dev-design` call skills from the superpowers plugin. Install
the plugin once on your machine:

```bash
claude plugin install superpowers@claude-plugins-official
```

The plugin is not part of the repository. Without it, use `dev-design` and `envgene-code-review` only.

## Work without dev-flow

Use this path for a small change, or when you write the code in the same Claude Code session.

![Work without dev-flow](/docs/images/ai-skills-normal-work.drawio.svg)

No code and no plan exist before you approve the dev design.

To start a skill yourself, type its name as a command: `/dev-design` or `/envgene-code-review`. Claude
Code also loads both skills on its own, because `CLAUDE.md` tells it to. The explicit command is the
reliable way.

## Work through dev-flow

Use this path for a large change that has a settled design and that agents implement. The `dev-flow` skill
starts only on your request, for example `/dev-flow`. It runs one phase at a time and asks you before the
next phase.

![Phases of dev-flow](/docs/images/ai-skills-dev-flow.drawio.svg)

| Phase        | Who            | Output                           |
|--------------|----------------|----------------------------------|
| `design`     | You and Claude | ADR and documentation PR         |
| `cr`         | Agent          | Change request (CR) issue        |
| `dev-design` | You and Claude | Dev design file                  |
| `plan`       | Agent          | Plan file with tasks             |
| `implement`  | Agents         | Code, tests, and code PR         |
| `review`     | Agent          | Review report                    |
| `verify`     | Agent          | CI check results                 |
| `acceptance` | You            | Sign-off                         |

The flow keeps its state in `.superpowers/flow/<slug>.md`. Git ignores this file.

## How the team rules reach a reviewer agent

An agent starts with an empty context. It does not see the skills that the main session loaded. The team
rules from `envgene-code-review` reach a reviewer agent in two ways.

![How the team rules reach a reviewer agent](/docs/images/ai-skills-team-rules.drawio.svg)

- **Through the plan.** The dev design ends with a "Constraints" section. The plan repeats it as Global
  Constraints, and every task for an agent carries them.
- **Through `CLAUDE.md`.** A reviewer agent loads `CLAUDE.md` when it starts. `CLAUDE.md` tells it to load
  `envgene-code-review` before any review.
