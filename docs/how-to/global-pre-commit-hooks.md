# Global pre-commit hooks

- [Global pre-commit hooks](#global-pre-commit-hooks)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Step 1: Clone pre-commit-global](#step-1-clone-pre-commit-global)
  - [Step 2: Point Git at the global hooks directory](#step-2-point-git-at-the-global-hooks-directory)
  - [Step 3: Configure repositories you work on](#step-3-configure-repositories-you-work-on)
  - [What runs on commit](#what-runs-on-commit)
  - [Disable global hooks](#disable-global-hooks)
  - [References](#references)

## Description

This guide shows how to register [pre-commit-global](https://github.com/exadmin/pre-commit-global) hooks globally on your machine so every Git repository can use shared hook logic before your normal pre-commit runs. Hook scripts live in this repository under `hooks-global/`. Full install details and upstream updates are documented in the [pre-commit-global readme](https://github.com/exadmin/pre-commit-global).

## Prerequisites

| Requirement                 | Purpose                                                                                                    |
|-----------------------------|------------------------------------------------------------------------------------------------------------|
| Git                         | Required. See [git-scm.com](https://git-scm.com/install/).                                                 |
| Java (JDK or JRE)           | Required by the hook toolchain (upstream tests with a recent JDK).                                         |
| `CYBER_FERRET_PASSWORD`     | Only if CyberFerret runs; see the note below.                                                              |

> [!NOTE]
> For the `CYBER_FERRET_PASSWORD` value or questions about it, contact **Andrei Rudchenko**.

## Step 1: Clone pre-commit-global

Choose a directory you intend to keep (for example `~/tools/global-git-hooks` on Linux or macOS, or `C:\Tools\global-git-hooks` on Windows). Later, if you move or delete this folder you must repeat [Step 2](#step-2-point-git-at-the-global-hooks-directory).

**Clone into the directory root:**

```bash
mkdir -p ~/tools/global-git-hooks
cd ~/tools/global-git-hooks
git clone https://github.com/exadmin/pre-commit-global .
```

**Or clone into a named subfolder:**

```bash
mkdir -p ~/tools
cd ~/tools
git clone https://github.com/exadmin/pre-commit-global my-global-hooks
cd my-global-hooks
```

On Windows Command Prompt, `mkdir`, `cd` to your chosen folder, run the same `git clone`, then `cd` into the clone.

Stay in this clone directory when running the commands in the next step.

## Step 2: Point Git at the global hooks directory

Configure `core.hooksPath` to the `hooks-global` directory inside your clone.

**Linux and macOS:**

```bash
git config --global core.hooksPath "$(pwd)/hooks-global"
git config --global core.hooksPath
```

**Windows (cmd):**

```bat
git config --global core.hooksPath "%cd%\hooks-global"
git config --global core.hooksPath
```

The second command prints the value Git stored so you can confirm the path.

> [!TIP]
> Alternatively, run `linux_register_this_folder_as_global_hooks.sh` (Linux or macOS) or `win_register_*.cmd` (Windows) from your clone root so `core.hooksPath` points at this clone's `hooks-global` folder, instead of typing the `git config` commands above.

## Step 3: Configure repositories you work on

You **do not** need `.pre-commit-config.yaml` or any other file from this step for global hooks to run. Registration in [Step 2](#step-2-point-git-at-the-global-hooks-directory) applies to **every** repository on your machine. See [What runs on commit](#what-runs-on-commit) below for the branching logic.

Optional, depending on what you want in **this** repository:

1. **`[pre-commit](https://pre-commit.com/)` checks** - Add `.pre-commit-config.yaml` only if this repository should run the Python `pre-commit` CLI with that config. Without this file that step is skipped; global hooks still run their other behavior.
2. **Install the `pre-commit` CLI** - Only needed if you added `.pre-commit-config.yaml` (for example `pip install pre-commit`, or whatever your team uses).
3. **CyberFerret** - Add **`.qubership/grand-report.json`** only if you want CyberFerret invoked on commits in this repository (an empty JSON object is valid as a marker; exclusions live there later). Needs `CYBER_FERRET_PASSWORD` from [Prerequisites](#prerequisites).

## What runs on commit

When you run `git commit -m "your message"`:

1. Global hooks run (including an online hook-update check).
2. If `.pre-commit-config.yaml` exists, **pre-commit** runs with that config.
3. If pre-commit passes or there is no config, the repository's **`.git/hooks/pre-commit`** runs if present.

If any check fails, the commit stops until you fix the issue or adjust configuration and exclusions.

## Disable global hooks

To stop using global hooks machine-wide:

```bash
git config --global --unset core.hooksPath
```

## References

| Resource                                | Link                                                                                                                   |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| pre-commit-global overview and readme   | [github.com/exadmin/pre-commit-global](https://github.com/exadmin/pre-commit-global)                                    |
| pre-commit framework                    | [pre-commit.com](https://pre-commit.com/)                                                                              |
