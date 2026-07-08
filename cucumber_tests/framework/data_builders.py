import yaml
from .base_data_builders import BaseDataBuilder


class DataBuilder(BaseDataBuilder):
    """EnvGene-specific data builder.

    Inherits common operations (SBOM creation, BG state files, BG namespaces)
    from BaseDataBuilder. Adds envgene-specific methods for artifact definitions,
    template descriptors, paramsets, credentials, and resource profiles.
    """

    def create_regdef(self, app_name: str, content: dict = None):
        """Placeholder for creating RegDef files."""
        pass

    def create_cloud_passport(self, app_name: str, content: dict = None):
        """Placeholder for creating Cloud Passports."""
        pass

    def get_env_dir(self, cluster_name: str, env_name: str):
        """Returns the physical environment directory for a specific cluster and env."""
        d = self.workspace.base_dir / "environments" / cluster_name / env_name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def create_inventory_file(self, cluster_name: str, env_name: str, content: dict):
        """Creates env_definition.yml for a given environment."""
        inv_dir = self.get_env_dir(cluster_name, env_name) / "Inventory"
        inv_dir.mkdir(parents=True, exist_ok=True)
        with open(inv_dir / "env_definition.yml", "w") as f:
            yaml.dump(content, f)

    def create_paramset_file(self, place: str, name: str, content: dict, cluster: str = "test-cluster", env: str = "test-env"):
        """Creates a paramset file at the specified scope (env, cluster, site)."""
        base_dir = self.workspace.base_dir / "environments"
        if place == "env":
            target = base_dir / cluster / env / "Inventory" / "parameters"
        elif place == "cluster":
            target = base_dir / cluster / "Inventory" / "parameters"
        else:
            target = base_dir / "Inventory" / "parameters"
        target.mkdir(parents=True, exist_ok=True)
        with open(target / f"{name}.yml", "w") as f:
            yaml.dump(content, f)

    def create_credentials_file(self, place: str, name: str, content: dict, cluster: str = "test-cluster", env: str = "test-env"):
        """Creates a credentials file at the specified scope (env, cluster, site)."""
        base_dir = self.workspace.base_dir / "environments"
        if place == "env":
            target = base_dir / cluster / env / "Inventory" / "credentials"
        elif place == "cluster":
            target = base_dir / cluster / "credentials"
        else:
            target = base_dir / "credentials"
        target.mkdir(parents=True, exist_ok=True)
        with open(target / f"{name}.yml", "w") as f:
            yaml.dump(content, f)

    def create_resource_profile_file(self, place: str, name: str, content: dict, cluster: str = "test-cluster", env: str = "test-env"):
        """Creates a resource profile file at the specified scope."""
        base_dir = self.workspace.base_dir / "environments"
        if place == "env":
            target = base_dir / cluster / env / "Inventory" / "resource_profiles"
        elif place == "cluster":
            target = base_dir / cluster / "resource_profiles"
        else:
            target = base_dir / "resource_profiles"
        target.mkdir(parents=True, exist_ok=True)
        with open(target / f"{name}.yml", "w") as f:
            yaml.dump(content, f)

    def create_shared_template_vars_file(self, place: str, name: str, content: dict, cluster: str = "test-cluster", env: str = "test-env"):
        """Creates a shared template variables file at the specified scope."""
        base_dir = self.workspace.base_dir / "environments"
        if place == "env":
            target = base_dir / cluster / env / "shared-template-variables"
        elif place == "cluster":
            target = base_dir / cluster / "shared-template-variables"
        else:
            target = base_dir / "shared-template-variables"
        target.mkdir(parents=True, exist_ok=True)
        with open(target / f"{name}.yml", "w") as f:
            yaml.dump(content, f)

    def create_template_descriptor(self, cluster: str, env: str, namespaces: list):
        """Creates an env_template.yml descriptor mock for template generation."""
        td_dir = self.workspace.base_dir / "templates"
        td_dir.mkdir(parents=True, exist_ok=True)

        content = {"namespaces": namespaces}
        with open(td_dir / "env_template.yml", "w") as f:
            yaml.dump(content, f)

        self.workspace.config_data["env_templates_dir"] = str(td_dir).replace('\\', '/')

    def create_artifact_def(self, app_name: str, content: dict):
        """Creates an artifact definition file for the given app name."""
        target_dir = self.workspace.config_dir / "artifact_definitions"
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / f"{app_name}.yaml", "w") as f:
            yaml.dump(content, f)
