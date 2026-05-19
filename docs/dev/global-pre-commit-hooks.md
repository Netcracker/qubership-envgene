# Global pre-commit hooks

- [Global pre-commit hooks](#global-pre-commit-hooks)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Set `CYBER_FERRET_PASSWORD` permanently](#set-cyber_ferret_password-permanently)
  - [Step 1: Clone pre-commit-global](#step-1-clone-pre-commit-global)
  - [Step 2: Point Git at the global hooks directory](#step-2-point-git-at-the-global-hooks-directory)
  - [Step 3: grand-report.json](#step-3-grand-reportjson)
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
| `CYBER_FERRET_PASSWORD`     | Only if CyberFerret runs; see [Set `CYBER_FERRET_PASSWORD` permanently](#set-cyber_ferret_password-permanently). |

> [!NOTE]
> For the `CYBER_FERRET_PASSWORD` value or questions about it, contact **Andrei Rudchenko**.

## Set `CYBER_FERRET_PASSWORD` permanently

CyberFerret hooks read `CYBER_FERRET_PASSWORD` from the environment of the process that runs `git commit` (terminal, IDE, or Git GUI). Set it once per user account so every new shell and application inherits it.

> [!IMPORTANT]
> Use the password value from **Andrei Rudchenko** (see [Prerequisites](#prerequisites)). Do not commit it to Git or store it in repository files.

> [!WARNING]
> After changing a user-level variable, close and reopen terminals, IDEs, and Git clients so they pick up the new value.

### Linux

1. Open your shell startup file in an editor:
   - Bash: `~/.bashrc` (or `~/.profile` on some distributions)
   - Zsh: `~/.zshrc`
2. Add a line (replace the placeholder with the real password):

   ```bash
   export CYBER_FERRET_PASSWORD='your-password-here'
   ```

3. Apply the change in the current terminal:

   ```bash
   source ~/.bashrc
   ```

   Use `source ~/.zshrc` instead if you edited Zsh config.

4. Confirm:

   ```bash
   echo "$CYBER_FERRET_PASSWORD"
   ```

   The command should print the value (avoid sharing this output).

### macOS

macOS is the same as [Linux](#linux) for Bash and Zsh: add `export CYBER_FERRET_PASSWORD='...'` to `~/.zshrc` (default on recent macOS) or `~/.bash_profile` / `~/.bashrc` if you use Bash.

If you use a login shell and variables are missing in GUI apps, also add the same `export` line to `~/.zprofile`, then run `source ~/.zprofile` or log out and back in.

### Windows

Pick one method below. All set a **user** variable (not system-wide).

**Option A - Settings (GUI):**

1. Open **Settings** → **System** → **About** → **Advanced system settings** (or search "environment variables").
2. Under **User variables**, click **New**.
3. Variable name: `CYBER_FERRET_PASSWORD`. Variable value: the password from Andrei Rudchenko.
4. Confirm with **OK**, then restart terminals and IDEs.

**Option B - PowerShell (recommended for scripting):**

```powershell
[Environment]::SetEnvironmentVariable('CYBER_FERRET_PASSWORD', 'your-password-here', 'User')
```

Open a **new** PowerShell or Command Prompt window, then check:

```powershell
$env:CYBER_FERRET_PASSWORD
```

**Option C - Command Prompt (`setx`):**

```bat
setx CYBER_FERRET_PASSWORD "your-password-here"
```

`setx` does not update the current window. Open a new cmd session before running `git commit`. If the password contains `&`, `%`, or quotes, prefer Option A or B.

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

## Step 3: grand-report.json

The **`.qubership/grand-report.json`** file at the repository root is **added by Andrei Rudchenko**. It is required on the CyberFerret-related hook path and holds ignores and exclusions for signatures as needed.

Use `CYBER_FERRET_PASSWORD` as in [Set `CYBER_FERRET_PASSWORD` permanently](#set-cyber_ferret_password-permanently).

> [!NOTE]
> For updates to this file or questions about it, contact **Andrei Rudchenko**.

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
