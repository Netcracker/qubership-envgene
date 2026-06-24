# Guide: Integrating E2E Tests into Implementation Projects

This directory contains templates for a quick start and integration of E2E testing using `qubership-envgene` in your implementation projects.

If your configurations (templates and environment instances) are stored in two separate Git repositories, we provide a ready CI template that automatically fetches the required data and runs the testing pipeline.

## How to use the GitLab CI template

1. Copy the file `implementation-project-template.gitlab-ci.yml` to the root of your project where CI/CD is configured (usually rename to `.gitlab-ci.yml` if it's the main CI file, or include it via `include:`).

2. **Set repository URLs:**
   Inside `.gitlab-ci.yml` update the variables:
   ```yaml
   ENV_TEMPLATES_REPO: "https://gitlab.example.com/my-group/env-templates.git"
   ENV_INSTANCES_REPO: "https://gitlab.example.com/my-group/env-instances.git"
   ```
   *You can also remove them from the file and define them in your GitLab repository settings (Settings -> CI/CD -> Variables).* 

3. **Configure access (for private repositories):**
   If the repositories are private, cloning over HTTP requires authentication.
   Uncomment the cloning block with authentication in the `before_script` section and set the `GIT_AUTH_USER` and `GIT_AUTH_PASSWORD` tokens.
   ```yaml
   git clone https://${GIT_AUTH_USER}:${GIT_AUTH_PASSWORD}@gitlab.example.com/my-group/env-templates.git $BDD_DATA_DIR/templates
   ```
   **Important:** Never hard‑code passwords directly in `gitlab-ci.yml`. Use protected CI/CD variables. Typically a Personal Access Token or Deploy Token is used. In some cases `$CI_JOB_TOKEN` works.

4. **Run the tests:**
   The `qubership-envgene` container automatically picks up data from the `$BDD_DATA_DIR` directory (which points to `/workspace/test_data`). It will contain two directories: `templates/` and `instances/`.

## Integration with local Python fixtures (optional)

If you need to further customize paths or write your own `pytest-bdd` checks, you can use the examples in this directory:
- `conftest_template.py`
- `workspace_template.py`

These files can be copied into your test directory (e.g., `tests/e2e/framework/`), renaming `_template` to normal file names.
