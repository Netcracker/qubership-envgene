# Global pre-commit hooks

- [Global pre-commit hooks](#global-pre-commit-hooks)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Set `CYBER_FERRET_PASSWORD` permanently](#set-cyber_ferret_password-permanently)
  - [Step 1: Clone pre-commit-global](#step-1-clone-pre-commit-global)
  - [Step 2: Point Git at the global hooks directory](#step-2-point-git-at-the-global-hooks-directory)
  - [Step 3: grand-report.json](#step-3-grand-reportjson)
  - [What runs on commit](#what-runs-on-commit)
  - [CyberFerret output examples](#cyberferret-output-examples)
    - [Successful scan](#successful-scan)
    - [Failed scan](#failed-scan)
    - [Local `commit-msg` hook](#local-commit-msg-hook)
  - [Disable global hooks](#disable-global-hooks)
  - [References](#references)

## Description

This guide shows how to register [pre-commit-global](https://github.com/exadmin/pre-commit-global) hooks globally on your machine so every Git repository can use shared hook logic before your normal pre-commit runs. Hook scripts live in this repository under `hooks-global/`. Full install details and upstream updates are documented in the [pre-commit-global readme](https://github.com/exadmin/pre-commit-global).

## Prerequisites

| Requirement                 | Purpose                                                                                                    |
|-----------------------------|------------------------------------------------------------------------------------------------------------|
| Git                         | Required. See [git-scm.com](https://git-scm.com/install/).                                                 |
| Java (JDK or JRE)           | Required by the hook toolchain. Examples below were verified with **JDK 25**.                              |
| `CYBER_FERRET_PASSWORD`     | Only if CyberFerret runs; see [Set `CYBER_FERRET_PASSWORD` permanently](#set-cyber_ferret_password-permanently). |

> [!NOTE]
> For the `CYBER_FERRET_PASSWORD` value or questions about it, contact **Andrei Rudchenko**.

## Set `CYBER_FERRET_PASSWORD` permanently

CyberFerret hooks read `CYBER_FERRET_PASSWORD` from the environment of the process that runs `git commit` (terminal, IDE, or Git GUI). Set it once per user account so every new shell and application inherits it.

> [!IMPORTANT]
> Use the password value from **Andrei Rudchenko** (see [Prerequisites](#prerequisites)). Do not commit it to Git or store it in repository files.
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

1. Global **pre-commit** runs (including a periodic `git pull` of the hooks repository, then any repository **`.git/hooks/pre-commit`** if present).
2. If `.pre-commit-config.yaml` exists, the **pre-commit** framework may also run when configured in the repository.
3. Global **commit-msg** runs. If the repository has **`.git/hooks/commit-msg`**, that local script runs instead of CyberFerret (see [Local `commit-msg` hook](#local-commit-msg-hook)).
4. Otherwise, if **`.qubership/grand-report.json`** exists, CyberFerret scans changed files (see [CyberFerret output examples](#cyberferret-output-examples)).

If any check fails, the commit stops until you fix the issue or adjust configuration and exclusions.

## CyberFerret output examples

CyberFerret runs during the global **commit-msg** hook when `.qubership/grand-report.json` is present and the repository does not define its own `.git/hooks/commit-msg`. Terminal output is prefixed with `[QUBERSHIP]`.

Paths in the samples below match a typical Windows layout (`hooks-global` clone and a Qubership repository). Your paths will differ if you chose another install location.

### Successful scan

No matching signatures in the scanned files. The commit continues.

```text
[QUBERSHIP] Calling CyberFerret checks for C:/Users/andy-/Desktop/Work_folder/Qubership/qubership-envgene
[QUBERSHIP] java -cp "C:/Users/andy-/Desktop/Work_folder/Qubership/tools/hooks-global/../cyberferret-dist/cyberferret-cli.jar" com.github.exadmin.cyberferret.CyberFerretCLI "C:/Users/andy-/Desktop/Work_folder/Qubership/qubership-envgene" "C:/Users/andy-/Desktop/Work_folder/Qubership/qubership-envgene/.git/cf_files.list"
[INFO ]CyberFerretCLI version: 1.2.7
[INFO ]Checking if new online dictionary exists
[INFO ]Skipping dictionary download, local cache is still fresh: C:\Users\andy-\Desktop\Work_folder\Qubership\tools\hooks-global\.\dictionary-latest-cache.encrypted
[INFO ]Signatures are loaded successfully, number of signatures is 70
[INFO ]Number of allowed signatures is 13
[INFO ]Dictionary version is 1.33
[INFO ]Scan rate is 100%
[INFO ]Scanning completed for 100%
[INFO ]Scan is completed. Errors are not found :)
```

### Failed scan

CyberFerret found a blocked signature in a changed file. The commit is rejected. The `[ERROR]` line names the matched dictionary term and the file path with line number.

```text
[QUBERSHIP] Calling CyberFerret checks for C:/Users/andy-/Desktop/Work_folder/Qubership/qubership-envgene
[QUBERSHIP] java -cp "C:/Users/andy-/Desktop/Work_folder/Qubership/tools/hooks-global/../cyberferret-dist/cyberferret-cli.jar" com.github.exadmin.cyberferret.CyberFerretCLI "C:/Users/andy-/Desktop/Work_folder/Qubership/qubership-envgene" "C:/Users/andy-/Desktop/Work_folder/Qubership/qubership-envgene/.git/cf_files.list"
[INFO ]CyberFerretCLI version: 1.2.7
[INFO ]Checking if new online dictionary exists
[INFO ]Skipping dictionary download, local cache is still fresh: C:\Users\andy-\Desktop\Work_folder\Qubership\tools\hooks-global\.\dictionary-latest-cache.encrypted
[INFO ]Signatures are loaded successfully, number of signatures is 70
[INFO ]Number of allowed signatures is 13
[INFO ]Dictionary version is 1.33
[INFO ]Scan rate is 100%
[ERROR]Signature '<matched-name>' is found in C:\Users\andy-\Desktop\Work_folder\Qubership\qubership-envgene\docs\dev\example.md:42
[INFO ]Scanning completed for 100%
[INFO ]Scan is completed. Errors are found :( Breaking commit!
[QUBERSHIP] Commit is not allowed
[QUBERSHIP] If you think this warning must be ignored once - use any of magic words '@cf_ignore, @cf_skip, @ignore_cf, @skip_cf' right in the commit message (any place)
[QUBERSHIP] If found signatures must be added to permanent ignores - use CyberFerret GUI app
```

To bypass CyberFerret for a single commit, add one of `@cf_ignore`, `@cf_skip`, `@ignore_cf`, or `@skip_cf` anywhere in the commit message. For permanent exclusions, use the CyberFerret GUI or update `.qubership/grand-report.json` with **Andrei Rudchenko**.

### Local `commit-msg` hook

If the repository defines **`.git/hooks/commit-msg`**, the global hook delegates to it and **does not** run CyberFerret:

```text
[QUBERSHIP] Local hook is defined - calling it
```

Remove or rename the local `commit-msg` hook if you want CyberFerret checks in that repository.

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
