import os
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from deepmerge import always_merger
from envgenehelper import logger, openYaml, readYaml, writeYamlToFile, openFileAsString, copy_path, dumpYamlToStr, \
    create_yaml_processor, find_all_yaml_files_by_stem, ensure_directory, dump_as_yaml_format
from envgenehelper.validation import ensure_valid_fields, ensure_required_keys
from jinja2 import Template, TemplateError
from pydantic import BaseModel, Field

from jinja import create_jinja_env
from replace_ansible_stuff import replace_ansible_stuff

yml = create_yaml_processor()


class Context(BaseModel):
    env: Optional[str] = ''
    render_dir: Optional[str] = ''
    cloud_passport: Optional[dict] = Field(default_factory=dict)
    templates_dir: Optional[Path] = None
    output_dir: Optional[str] = ''
    cluster_name: Optional[str] = ''
    env_definition: Optional[dict] = Field(default_factory=dict)
    current_env: Optional[dict] = Field(default_factory=dict)
    current_env_dir: Optional[str] = ''
    current_env_template: Optional[dict] = Field(default_factory=dict)
    tenant: Optional[str] = ''
    env_template: Optional[dict] = Field(default_factory=dict)
    env_instances_dir: Optional[str] = ''
    cloud_passport_file_path: Optional[str] = ''
    sd_config: Optional[dict] = Field(default_factory=dict)
    sd_file_path: Optional[str] = ''
    regdefs: Optional[dict] = Field(default_factory=dict)
    appdefs: Optional[dict] = Field(default_factory=dict)
    regdef_templates: Optional[list] = Field(default_factory=list)
    appdef_templates: Optional[list] = Field(default_factory=list)
    cloud: Optional[str] = ''
    deployer: Optional[str] = ''
    render_parameters_dir: Optional[str] = ''

    start_time: datetime | None = Field(default=None, exclude=True)

    class Config:
        extra = "allow"
        validate_assignment = True

    def update(self, data: dict | None = None, **kwargs):
        if data:
            for key, value in data.items():
                setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)
        logger.debug(f"Context updated: {data or kwargs}")

    @contextmanager
    def use(self):
        self.start_time = datetime.now()
        logger.debug(f"Enter context at {self.start_time}")
        try:
            yield self
        finally:
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.debug(f"Exit context (duration {duration:.2f}s)")
            logger.debug(f"Final state: {self.dict(exclude_none=True)}")

    def as_dict(self, include_none: bool = False) -> dict:
        return self.model_dump(exclude_none=not include_none)


class EnvGenerator:
    def __init__(self):
        self.ctx = Context()
        logger.debug(f"EnvGenerator initialized with context: {self.ctx.dict(exclude_none=True)}")

    def set_inventory(self):
        inventory_path = Path(self.ctx.env_instances_dir) / "Inventory" / "env_definition.yml"
        env_definition = openYaml(filePath=inventory_path, safe_load=True)
        logger.info(f"env_definition = {env_definition}")
        self.ctx.env_definition = env_definition

    def set_cloud_passport(self):
        cloud_passport_file_path = self.ctx.cloud_passport_file_path.strip()
        if cloud_passport_file_path:
            cloud_passport = openYaml(filePath=cloud_passport_file_path, safe_load=True)
            logger.info(f"cloud_passport = {cloud_passport}")
            self.ctx.cloud_passport = cloud_passport

    def generate_config(self):
        templates_dir = Path(__file__).parent / "templates"
        template = create_jinja_env(str(templates_dir)).get_template("env_config.yml.j2")
        config = readYaml(text=template.render(self.ctx.as_dict()), safe_load=True)
        logger.info(f"config = {config}")
        self.ctx.config = config

    def set_env_template(self):
        env_template_path_stem = f'{self.ctx.templates_dir}/env_templates/{self.ctx.current_env["env_template"]}'
        env_template_path = next(iter(find_all_yaml_files_by_stem(env_template_path_stem)), None)
        if not env_template_path:
            raise ValueError(f'Template descriptor was not found in {env_template_path_stem}')

        env_template = openYaml(filePath=env_template_path, safe_load=True)
        logger.info(f"env_template = {env_template}")
        self.ctx.current_env_template = env_template

    def validate_applications(self):
        applications = self.ctx.sd_config.get("applications", [])

        for app in applications:
            version = app.get("version")
            deploy_postfix = app.get("deployPostfix")

            if "version" not in app:
                raise ValueError(f"Missing 'version' in application: {app}")
            if "deployPostfix" not in app:
                raise ValueError(f"Missing 'deployPostfix' in application: {app}")
            if not isinstance(version, str):
                raise ValueError(f"'version' must be string in application: {app}")
            if not isinstance(deploy_postfix, str):
                raise ValueError(f"'deployPostfix' must be string in application: {app}")

            logger.info(f"Valid application: {app}")

    def generate_ns_postfix(self, ns, ns_template_path) -> str:
        deploy_postfix = ns.get("deploy_postfix")
        if deploy_postfix:
            ns_template_name = deploy_postfix
        else:
            # get base name(deploy postfix) without extensions
            ns_template_name = Path(ns_template_path).name.replace(".yml.j2", "").replace(".yaml.j2", "")
        return ns_template_name

    def generate_solution_structure(self):
        sd_path_stem = f'{self.ctx.current_env_dir}/Inventory/solution-descriptor/sd'
        sd_path = next(iter(find_all_yaml_files_by_stem(sd_path_stem)), None)
        solution_structure = {}
        if sd_path:
            self.ctx.sd_file_path = str(sd_path)
            sd_config = openYaml(filePath=sd_path, safe_load=True)
            self.ctx.sd_config = sd_config
            if "applications" not in sd_config:
                raise ValueError("Missing 'applications' key in root")
            self.validate_applications()

            namespaces = self.ctx.current_env_template.get("namespaces", [])
            postfix_template_map = {}
            for ns in namespaces:
                namespace_template_path = Template(ns["template_path"]).render(self.ctx.as_dict())
                postfix = self.generate_ns_postfix(ns, namespace_template_path)
                postfix_template_map[postfix] = namespace_template_path

            for app in sd_config["applications"]:
                app_version = app["version"]
                app_name, version = app_version.split(":", 1)
                postfix = app["deployPostfix"]

                ns_template_path = postfix_template_map.get(postfix)
                ns_name = None
                if ns_template_path:
                    rendered_ns = self.render_from_file_to_obj(ns_template_path)
                    ns_name = rendered_ns.get("name")

                small_dict = {
                    app_name: {
                        postfix: {
                            "version": version,
                            "namespace": ns_name
                        }
                    }
                }
                always_merger.merge(solution_structure, small_dict)

            always_merger.merge(self.ctx.current_env, {"solution_structure": solution_structure})
        logger.info(f"Rendered solution_structure: {solution_structure}")

    def render_from_file_to_file(self, src_template_path: str, target_file_path: str):
        template = openFileAsString(src_template_path)
        template = replace_ansible_stuff(template_str=template, template_path=src_template_path)
        rendered = create_jinja_env().from_string(template).render(self.ctx.as_dict())
        writeYamlToFile(target_file_path, readYaml(rendered))

    def render_from_file_to_obj(self, src_template_path) -> dict:
        template = openFileAsString(src_template_path)
        template = replace_ansible_stuff(template_str=template, template_path=src_template_path)
        rendered = create_jinja_env().from_string(template).render(self.ctx.as_dict())
        return readYaml(rendered)

    def render_from_obj_to_file(self, template, target_file_path):
        template = replace_ansible_stuff(template_str=dumpYamlToStr(template))
        rendered = create_jinja_env().from_string(template).render(self.ctx.as_dict())
        writeYamlToFile(target_file_path, readYaml(rendered))

    def generate_tenant_file(self):
        logger.info(f"Generate Tenant yaml for {self.ctx.tenant}")
        tenant_file = f'{self.ctx.current_env_dir}/tenant.yml'
        tenant_tmpl_path = self.ctx.current_env_template["tenant"]
        self.render_from_file_to_file(Template(tenant_tmpl_path).render(self.ctx.as_dict()), tenant_file)

    def generate_override_template(self, template_override, template_path: Path, name):
        if template_override:
            logger.info(f"Generate override {template_path.stem} yaml for {name}")
            self.render_from_obj_to_file(template_override, template_path)

    def generate_cloud_file(self):
        cloud = self.calculate_cloud_name()
        cloud_template = self.ctx.current_env_template["cloud"]
        current_env_dir = self.ctx.current_env_dir
        cloud_file = f'{current_env_dir}/cloud.yml'
        context = self.ctx.as_dict()
        is_template_override = isinstance(cloud_template, dict)
        if is_template_override:
            logger.info(f"Generate Cloud yaml for cloud {cloud} using cloud.template_path value")
            cloud_tmpl_path = cloud_template["template_path"]
            self.render_from_file_to_file(Template(cloud_tmpl_path).render(context), cloud_file)

            template_override = cloud_template.get("template_override")
            self.generate_override_template(template_override, Path(f'{current_env_dir}/cloud.yml_override'), cloud)
        else:
            logger.info(f"Generate Cloud yaml for cloud {cloud}")
            self.render_from_file_to_file(Template(cloud_template).render(context), cloud_file)

    def generate_namespace_file(self):
        context = self.ctx.as_dict()
        namespaces = self.ctx.current_env_template["namespaces"]
        for ns in namespaces:
            ns_template_path = Template(ns["template_path"]).render(context)
            ns_template_name = self.generate_ns_postfix(ns, ns_template_path)
            logger.info(f"Generate Namespace yaml for {ns_template_name}")
            current_env_dir = self.ctx.current_env_dir
            ns_dir = f'{current_env_dir}/Namespaces/{ns_template_name}'
            namespace_file = f'{ns_dir}/namespace.yml'
            self.render_from_file_to_file(ns_template_path, namespace_file)

            self.generate_override_template(ns.get("template_override"), Path(f'{ns_dir}/namespace.yml_override'),
                                            ns_template_name)

    def calculate_cloud_name(self) -> str:
        inv = self.ctx.env_definition["inventory"]
        cluster_name = self.ctx.cluster_name
        candidates = [
            inv.get("cloudName"),
            inv.get("passportCloudName", "").replace("-", "_") if inv.get("passportCloudName") else "",
            inv.get("cloudPassport", "").replace("-", "_") if inv.get("cloudPassport") else "",
            inv.get("environmentName", "").replace("-", "_"),
            f"{cluster_name}_{inv.get('environmentName', '')}".replace("-", "_")
            if cluster_name and inv.get("environmentName") else ""
        ]

        return next((c for c in candidates if c), "")

    def get_template_name(self, template_path: Path) -> str:
        return (
            template_path.name
            .replace(".yml.j2", "")
            .replace(".yaml.j2", "")
        )

    def generate_composite_structure(self):
        composite_structure = self.ctx.current_env_template.get("composite_structure")
        if composite_structure:
            logger.info(f"Generate Composite Structure yaml for {composite_structure}")
            current_env_dir = self.ctx.current_env_dir
            cs_file = Path(current_env_dir) / "composite_structure.yml"
            cs_file.parent.mkdir(parents=True, exist_ok=True)
            self.render_from_file_to_file(Template(composite_structure).render(self.ctx.as_dict()), str(cs_file))

    def generate_paramset_templates(self):
        render_dir = Path(self.ctx.render_parameters_dir).resolve()
        patterns = ["*.yml.j2", "*.yaml.j2"]

        paramset_templates = []
        for pattern in patterns:
            paramset_templates.extend(render_dir.rglob(pattern))
        logger.info(f"Total parameter set templates list found: {paramset_templates}")

        for template_path in paramset_templates:
            template_name = self.get_template_name(template_path)
            target_path = Path(str(template_path).replace(".yml.j2", ".yml").replace(".yaml.j2", ".yml"))

            try:
                logger.info(f"Try to render paramset {template_name}")
                self.render_from_file_to_file(Template(str(template_path)).render(self.ctx.as_dict()), target_path)
                logger.info(f"Successfully generated paramset: {template_name}")
                if template_path.exists():
                    template_path.unlink()
            except TemplateError as e:
                logger.warning(f"Skipped paramset {template_name}. Error details: {e}")
                if target_path.exists():
                    target_path.unlink()

    def find_templates(self, templates_dir: Path, def_type: str) -> list[Path]:
        search_path = templates_dir / def_type
        if not search_path.exists():
            logger.info(f"Directory with templates for {def_type} not found: {search_path}")
            return []

        patterns = ["*.yaml.j2", "*.yml.j2", "*.j2", "*.yaml", "*.yml"]
        templates = []

        for pattern in patterns:
            for f in search_path.rglob(pattern):
                if f.is_file():
                    templates.append(f)

        logger.info(f"{def_type.capitalize()} Found: {len(templates)}")
        return templates

    def render_app_defs(self):
        for def_tmpl_path in self.ctx.appdef_templates:
            app_def_str = openFileAsString(def_tmpl_path)
            matches = re.findall(
                r'^\s*(name|artifactId|groupId):\s*"([^"]+)"',
                app_def_str,
                flags=re.MULTILINE,
            )
            appdef_meta = dict(matches)
            ensure_valid_fields(appdef_meta, ["artifactId", "groupId", "name"])
            group_id = appdef_meta["groupId"]
            artifact_id = appdef_meta["artifactId"]
            self.ctx.update({
                "app_lookup_key": f"{group_id}:{artifact_id}",
                "groupId": group_id,
                "artifactId": artifact_id,
            })
            app_def_trg_path = f"{self.ctx.current_env_dir}/AppDefs/{appdef_meta.get("name")}.yml"
            self.render_from_file_to_file(def_tmpl_path, app_def_trg_path)

    def render_reg_defs(self):
        for def_tmpl_path in self.ctx.regdef_templates:
            reg_def_str = openFileAsString(def_tmpl_path)
            matches = re.findall(
                r'^\s*(name):\s*"([^"]+)"',
                reg_def_str,
                flags=re.MULTILINE,
            )
            regdef_meta = dict(matches)
            ensure_valid_fields(regdef_meta, ["name"])
            reg_def_trg_path = f"{self.ctx.current_env_dir}/RegDefs/{regdef_meta['name']}.yml"
            self.render_from_file_to_file(def_tmpl_path, reg_def_trg_path)

    def set_appreg_def_overrides(self):
        output_dir = Path(self.ctx.output_dir)
        cluster_name = self.ctx.cluster_name
        config_file_name = Path("configuration") / "appregdef_config"
        config_file_name_yaml = f"{config_file_name}.yaml"
        config_file_name_yml = f"{config_file_name}.yml"

        potential_config_files = [
            output_dir / cluster_name / config_file_name_yaml,
            output_dir / cluster_name / config_file_name_yml,
            output_dir.parent / config_file_name_yaml,
            output_dir.parent / config_file_name_yml,
        ]
        appregdef_config_paths = [f for f in potential_config_files if f.exists()]
        if appregdef_config_paths:
            appregdef_config = {}
            appregdef_config_path = appregdef_config_paths[0]
            try:
                appregdef_config = openYaml(appregdef_config_path)
                logger.info(f"Overrides applications/registries definitions config found at: {appregdef_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config at: {appregdef_config_path}. Error: {e}")

            appdefs = self.ctx.appdefs
            regdefs = self.ctx.regdefs
            appdefs["overrides"] = appregdef_config.get(appdefs, {}).get("overrides", {})
            regdefs["overrides"] = appregdef_config.get(regdefs, {}).get("overrides", {})

    def process_app_reg_defs(self):
        current_env_dir = self.ctx.current_env_dir
        templates_dir = self.ctx.templates_dir
        appdef_templates = self.find_templates(templates_dir, "appdefs")
        regdef_templates = self.find_templates(templates_dir, "regdefs")
        self.ctx.appdef_templates = appdef_templates
        self.ctx.regdef_templates = regdef_templates

        ensure_directory(Path(current_env_dir).joinpath("AppDefs"), 0o755)
        ensure_directory(Path(current_env_dir).joinpath("RegDefs"), 0o755)
        self.set_appreg_def_overrides()
        self.render_app_defs()
        self.render_reg_defs()

    def generate_config_env(self, env_name: str, extra_env: dict):
        logger.info(f"Starting rendering environment {env_name}. Input params are:\n{dump_as_yaml_format(extra_env)}")
        with self.ctx.use():
            all_vars = dict(os.environ)
            ci_vars = {
                "CI_COMMIT_TAG": all_vars.get("CI_COMMIT_TAG"),
                "CI_COMMIT_REF_NAME": all_vars.get("CI_COMMIT_REF_NAME"),
            }
            self.ctx.update(extra_env)
            self.ctx.update(ci_vars)
            self.set_inventory()
            self.set_cloud_passport()
            self.generate_config()

            current_env = self.ctx.config["environment"]
            self.ctx.current_env = current_env

            self.ctx.cloud = self.calculate_cloud_name()
            self.ctx.tenant = current_env.get("tenant", '')
            self.ctx.deployer = current_env.get('deployer', '')
            logger.info(f"current_env = {current_env}")

            self.ctx.update({
                "ND_CMDB_CONFIG_REF": all_vars.get("CI_COMMIT_SHORT_SHA", "No SHA"),
                "ND_CMDB_CONFIG_REF_NAME": all_vars.get("CI_COMMIT_REF_NAME", "No Ref Name"),
                "ND_CMDB_CONFIG_TAG": all_vars.get("CI_COMMIT_TAG", "No Ref tag"),
                "ND_CDMB_REPOSITORY_URL": all_vars.get("CI_REPOSITORY_URL", "No Ref URL"),
            })
            env_template = self.ctx.env_template
            if env_template:
                self.ctx.update({
                    "ND_CMDB_ENV_TEMPLATE": env_template
                })
            else:
                self.ctx.update({
                    "ND_CMDB_ENV_TEMPLATE": self.ctx.current_env["env_template"]
                })

            current_env_dir = f'{self.ctx.render_dir}/{self.ctx.env}'
            self.ctx.current_env_dir = current_env_dir
            self.set_env_template()

            self.generate_solution_structure()
            self.generate_tenant_file()
            self.generate_cloud_file()
            self.generate_namespace_file()
            self.generate_composite_structure()

            env_specific_schema = self.ctx.current_env_template.get("envSpecificSchema")
            if env_specific_schema:
                copy_path(source_path=env_specific_schema, target_dir=current_env_dir)
            self.generate_paramset_templates()

            ensure_required_keys(self.ctx.as_dict(),
                                 required=["templates_dir", "env_instances_dir", "cluster_name", "current_env_dir"])
            self.process_app_reg_defs()
            logger.info("Rendering of templates for environment generation was successful")
