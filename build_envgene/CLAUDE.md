# build_envgene — EnvGene Docker Image Build

Docker image `qubership-envgene` (`build_envgene/build/Dockerfile`). `COPY scripts/ /module/scripts/` ships the whole single-job pipeline tree (see `scripts/CLAUDE.md`) into the image. `WORKDIR /module/scripts` is the container's entry point, running `pipeline/orchestrator.py`.

This directory only holds Docker build context now (`build/Dockerfile`, `build/requirements.txt`, `build/pip.conf`, `build/constraint.txt`, `build/sources.list`) and the `workflows/` template. The Python scripts that used to live at `build_envgene/scripts/` moved to `scripts/`: `git_commit.py` is now under `scripts/git_commit/`, `report.py` directly under `scripts/` — see `scripts/CLAUDE.md` for their responsibilities and `scripts/tests/git_commit/` for their tests.
