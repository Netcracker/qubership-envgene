import copy
import shutil
from os import getenv
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime

from deepmerge import always_merger
from jinja2 import Template, TemplateError
from pydantic import BaseModel, Field

from build_env.jinja.jinja import create_jinja_env
from build_env.jinja.replace_ansible_stuff import replace_ansible_stuff, escaping_quotation
from envgenehelper import Optional, OrderedDict, Path, copy_creds_to_env_creds_file, copy_path, create_yaml_processor, current_env_instance_store, dumpYamlToStr, dump_as_yaml_format, fill_missing_environment_name, find_cloud_passport_definition, find_files_by_basename, getAbsPath, getEnvDefinition, get_schema_dir, get_template_dirs, logger, merge_yaml_into_target, openFileAsString, openYaml, os, path, readYaml, render_workspace_dir, validate_yaml_by_scheme_or_fail, writeYamlToFile
from envgenehelper.config_helper import get_regdef_schema_for_content
from envgenehelper.deployer import get_deployer_config
from envgenehelper.process_pool import map_in_processes, parallel_workers
from envgenehelper.deploy_plan_adapter import DEPLOY_PLAN_FILE_NAME, EnvgeneDeployPlan
from envgenehelper.business_helper import (
    get_namespace_role, NamespaceRole, parse_bg_ns_target,
)
from envgenehelper.validations import ensure_valid_fields, ensure_required_keys

EXTERNAL_CRED_COMMENT = "external credential template"
PARAMSET_TAGS = ("deployParameterSets", "e2eParameterSets", "technicalConfigurationParameterSets")
ENV_SPECIFIC_PARAMSET_FIELDS = ("envSpecificParamsets", "envSpecificE2EParamsets", "envSpecificTechnicalParamsets")

yml = create_yaml_processor()


class SolutionStructureNotReady(Exception):
    pass


class PendingSolutionStructure:
    def _fail(self, *args, **kwargs):
        raise SolutionStructureNotReady()

    __getitem__ = __getattr__ = __iter__ = __len__ = __bool__ = __str__ = __contains__ = _fail


class Context(BaseModel):
    env: Optional[str] = ''
    render_dir: Optional[str] = ''
    cloud_passport: OrderedDict = Field(default_factory=OrderedDict)
    templates_dirs: dict = Field(default_factory=dict)
    output_dir: Optional[str] = ''
    cluster_name: Optional[str] = ''
    env_definition: OrderedDict = Field(default_factory=OrderedDict)
    current_env: OrderedDict = Field(default_factory=OrderedDict)
    current_env_dir: Optional[str] = ''
    current_env_template: OrderedDict = Field(default_factory=OrderedDict)
    peer_env_template: OrderedDict = Field(default_factory=OrderedDict)
    origin_env_template: OrderedDict = Field(default_factory=OrderedDict)
    tenant: Optional[str] = ''
    env_template: OrderedDict = Field(default_factory=OrderedDict)
    cloud_passport_file_path: Optional[str] = ''
    regdefs: OrderedDict = Field(default_factory=OrderedDict)
    appdefs: OrderedDict = Field(default_factory=OrderedDict)
    regdef_templates: list = Field(default_factory=list)
    appdef_templates: list = Field(default_factory=list)
    cloud: Optional[str] = ''
    deployer: Optional[str] = ''
    bgd: Optional[str] = ''
    render_parameters_dir: Optional[str] = ''
    env_vars: OrderedDict = Field(default_factory=OrderedDict)
    template_profiles_dir: Optional[str] = ''
    work_dir: Optional[str] = ''
    namespace_by_deploy_postfix: dict = Field(default_factory=dict)

    start_time: datetime | None = Field(default=None, exclude=True)
    end_time: datetime | None = Field(default=None, exclude=True)

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
            self.end_time = datetime.now()
            logger.debug(
                f"Exit context at {self.end_time}. Duration: {self.end_time - self.start_time}. "
                f"Final state: {self.dict(exclude_none=True)}"
            )

    def as_dict(self, include_none: bool = False) -> dict:
        return self.model_dump(exclude_none=not include_none)


def render_template_file(src_template_path, context: dict, stop_at_solution_structure: bool) -> tuple[dict, bool]:
    template = openFileAsString(src_template_path)
    template = replace_ansible_stuff(template_str=template, template_path=src_template_path)
    if stop_at_solution_structure:
        context["current_env"]["solution_structure"] = PendingSolutionStructure()
    rendered_parts = []
    try:
        for rendered_part in create_jinja_env().from_string(template).generate(context):
            rendered_parts.append(rendered_part)
    except SolutionStructureNotReady:
        complete_lines, _, cut_line = "".join(rendered_parts).rpartition("\n")
        rendered_fields = readYaml(escaping_quotation(complete_lines)) or {}
        if rendered_fields and (not cut_line or cut_line[0].isspace()):
            rendered_fields.popitem()
        logger.info(f"Template {src_template_path} uses solution_structure, postponed until the deployment plan")
        return rendered_fields, True
    rendered = "".join(rendered_parts)
    logger.debug(f"Rendered entity: \n{rendered}")
    return readYaml(escaping_quotation(rendered)), False


def render_obj_by_context(template: dict, context: Context) -> dict:
    template_str = replace_ansible_stuff(template_str=dumpYamlToStr(template))
    rendered_str = create_jinja_env().from_string(template_str).render(context.as_dict())
    return yml.load(rendered_str)


def build_render_context_vars(env_name: str, cluster_name: str, env_dir: str, base_dir: str,
                              templates_dirs: dict | None = None) -> dict:
    from build_env.build_env import process_additional_template_parameters  # TODO: circular import, fix properly
    from cloud_passport.cloud_passport import update_env_definition_with_cloud_name
    output_dir = f"{base_dir}/environments"
    templates_dirs = templates_dirs or get_template_dirs()
    env_definition = getEnvDefinition(env_dir)
    process_additional_template_parameters(env_definition, env_dir, output_dir)
    update_env_definition_with_cloud_name(env_definition, env_dir, output_dir)
    fill_missing_environment_name(env_definition, env_name)
    cmdb_url, _, _ = get_deployer_config()

    return {
        "env": env_name,
        "current_env": {"name": env_name, "environmentName": env_definition["inventory"]["environmentName"]},
        "cluster_name": cluster_name,
        "templates_dirs": templates_dirs,
        "templates_dir": templates_dirs.get(NamespaceRole.COMMON, ""),
        "current_env_dir": getAbsPath(env_dir),
        "render_parameters_dir": getAbsPath(str(render_workspace_dir(base_dir) / "parameters")),
        "cloud_passport_file_path": find_cloud_passport_definition(env_dir, output_dir, env_definition),
        "cmdb_url": cmdb_url,
        "output_dir": output_dir,
        "template_profiles_dir": str(Path(templates_dirs[NamespaceRole.COMMON]) / "resource_profiles"),
        "work_dir": str(base_dir),
        "env_definition": env_definition,
    }


class EnvGenerator:
    def __init__(self):
        self.ctx = Context()
        self.used_paramset_names = set()
        self.is_external_cred_env = False
        self.render_context_vars = None
        self.env_templates_ready = False
        self.shared_chain_ready = False
        self.solution_structure_ready = False
        self.bg_domain = None
        self.composite_structure = None
        self.cloud_object = None
        self.namespace_templates = {}
        self.postponed_templates = {}
        self.given_namespace_templates = set()
        self.namespaces = {}
        logger.debug("EnvGenerator initialized with context: %s",
                     self.ctx.dict(exclude_none=True, exclude={"env_vars"}))

    def set_inventory(self):
        fill_missing_environment_name(self.ctx.env_definition, self.ctx.env)
        logger.info(f"env_definition = {self.ctx.env_definition}")

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

    def find_env_template_in_dir(self, template_dir, env_template_name):
        if not template_dir:
            return None, []
        extensions = ("yml.j2", "yaml.j2", "yml", "yaml")
        env_templates_dir = Path(f'{template_dir}/env_templates')
        env_template_basename = env_templates_dir / env_template_name
        suitable_files = find_files_by_basename(env_template_basename, extensions)
        env_template_path = suitable_files[0] if suitable_files else None
        if not env_template_path:
            return None, suitable_files

        env_tmpl_final_path = env_template_path
        if env_template_path.suffix.endswith("j2"):
            logger.info(f"Template descriptor is {env_template_path}, rendering required")
            env_tmpl_final_path = str(env_template_path).removesuffix(".j2")
            self.render_from_file_to_file(env_template_path, env_tmpl_final_path)

        validate_yaml_by_scheme_or_fail(env_tmpl_final_path, get_schema_dir() / "template-descriptor.schema.json")
        env_template = openYaml(filePath=env_tmpl_final_path, safe_load=True)
        logger.info(f"Loaded env_template from {env_tmpl_final_path}")
        return env_template, suitable_files

    def set_env_templates(self):
        env_template_name = self.ctx.current_env["env_template"]

        env_templates_dir = Path(f'{self.ctx.templates_dirs.get(NamespaceRole.COMMON)}/env_templates')
        env_template_basename = env_templates_dir / env_template_name
        env_template, suitable_files = self.find_env_template_in_dir(self.ctx.templates_dirs.get(NamespaceRole.COMMON),
                                                                     env_template_name)
        if not env_template:
            all_files = [f for f in env_templates_dir.iterdir() if f.is_file()]
            remains_files = list(set(all_files) - set(suitable_files))
            raise ValueError(
                f"Template descriptor not found: {env_template_basename}."
                f" Expected location in template repository: {env_template_basename}"
                f" Allowed extensions: 'yml', 'yaml', 'yml.j2', 'yaml.j2'."
                f" Found templates: {remains_files}")
        logger.info(f"env_template = {env_template}")
        self.ctx.current_env_template = env_template

        if self.ctx.templates_dirs:
            peer_template, _ = self.find_env_template_in_dir(self.ctx.templates_dirs.get(NamespaceRole.PEER),
                                                             env_template_name)
            if peer_template:
                self.ctx.peer_env_template = peer_template

            origin_template, _ = self.find_env_template_in_dir(self.ctx.templates_dirs.get(NamespaceRole.ORIGIN),
                                                               env_template_name)
            if origin_template:
                self.ctx.origin_env_template = origin_template

    def setup_base_context(self, extra_env: dict):
        if self.render_context_vars is not None:
            return
        self.render_context_vars = extra_env
        all_vars = dict(os.environ)
        self.ctx.update(extra_env)
        self.ctx.env_vars.update(all_vars)

        self.set_inventory()
        self.set_cloud_passport()
        self.generate_config()

        current_env = self.ctx.config["environment"]
        self.ctx.current_env = current_env
        self.ctx.cloud = self.calculate_cloud_name()
        self.ctx.tenant = current_env.get("tenant", '')
        self.ctx.deployer = current_env.get('deployer', '')
        self.ctx.bgd = current_env.get('bg_domain', '')
        self.ctx.update({
            "ND_CMDB_CONFIG_REF": all_vars.get("CI_COMMIT_SHORT_SHA", "No SHA"),
            "ND_CMDB_CONFIG_REF_NAME": all_vars.get("CI_COMMIT_REF_NAME", "No Ref Name"),
            "ND_CMDB_CONFIG_TAG": all_vars.get("CI_COMMIT_TAG", "No Ref tag"),
            "ND_CDMB_REPOSITORY_URL": all_vars.get("CI_REPOSITORY_URL", "No Ref URL"),
        })
        self.ctx.update({"ND_CMDB_ENV_TEMPLATE": self.ctx.env_template or self.ctx.current_env["env_template"]})

    def ensure_env_templates(self):
        if not self.env_templates_ready:
            self.set_env_templates()
            self.env_templates_ready = True

    def ensure_shared_chain(self):
        if self.shared_chain_ready:
            return
        self.ensure_env_templates()
        self.bg_domain = self.render_bgd()
        self.composite_structure = self.render_composite_structure()
        self.compute_composite_topology(self.composite_structure, self.bg_domain)
        self.shared_chain_ready = True

    def validate_bgd(self):
        logger.info('Validating that all namespaces mentioned in BG domain object are available in namespaces')
        env_instance_store = current_env_instance_store()
        namespace_names = [ns.name for ns in env_instance_store.namespaces()]
        bgd = env_instance_store.bg_domain()
        mismatch = ""
        for k, v in bgd.items():
            if 'Namespace' not in k:
                continue
            if v['name'] not in namespace_names:
                mismatch += f"\n{v['name']} from {k}"
        if mismatch:
            logger.info(f'Available namespaces: {namespace_names}')
            raise ValueError(f'Next namespaces were not found in available namespaces: {mismatch}')
        logger.info('Validation was successful')

    def _get_bgd_suffix(self, ns_name: str | None, bgd: dict | None) -> str:
        if not ns_name:
            return ""
        role = get_namespace_role(ns_name, bgd)
        return {NamespaceRole.ORIGIN: "-origin", NamespaceRole.PEER: "-peer"}.get(role, "")

    def _get_ns_name_for_bgd(self, ns: dict, ns_template_path: str) -> str | None:
        override_name = self._fetch_template_override_name(ns)
        if override_name:
            return override_name
        if ns_template_path:
            return self.namespace_template_name(ns_template_path)
        return None

    def _get_template_dir_for_role(self, role: NamespaceRole) -> Path:
        if role == NamespaceRole.ORIGIN and self.ctx.templates_dirs.get(NamespaceRole.ORIGIN):
            return Path(self.ctx.templates_dirs[NamespaceRole.ORIGIN])
        if role == NamespaceRole.PEER and self.ctx.templates_dirs.get(NamespaceRole.PEER):
            return Path(self.ctx.templates_dirs[NamespaceRole.PEER])
        return self.ctx.templates_dirs[NamespaceRole.COMMON]

    def _get_env_template_for_role(self, role: NamespaceRole) -> dict:
        if role == NamespaceRole.ORIGIN and self.ctx.origin_env_template:
            return self.ctx.origin_env_template
        if role == NamespaceRole.PEER and self.ctx.peer_env_template:
            return self.ctx.peer_env_template
        return self.ctx.current_env_template

    def _resolve_template_path(self, template_path_expr: str, templates_dir: Path = None) -> str:
        ctx = self.ctx.as_dict()
        if templates_dir is not None:
            ctx["templates_dir"] = str(templates_dir)
        return Template(template_path_expr).render(ctx)

    def _find_ns_config_by_name(self, env_template: dict, ns_name: str, templates_dir: Path = None) -> dict | None:
        for ns in env_template.get("namespaces", []):
            override_name = self._fetch_template_override_name(ns)
            if override_name == ns_name:
                return ns
            ns_template_path = self._resolve_template_path(ns["template_path"], templates_dir)
            if ns_template_path and self.namespace_template_name(ns_template_path) == ns_name:
                return ns
        return None

    def get_ns_base_postfix(self, ns: dict, ns_template_path: str) -> str:
        return ns.get("deploy_postfix") or self.get_template_name(ns_template_path)

    def generate_ns_postfix(self, ns: dict, ns_template_path: str, bgd: dict | None) -> str:
        base_name = self.get_ns_base_postfix(ns, ns_template_path)
        ns_name = self._get_ns_name_for_bgd(ns, ns_template_path)
        return base_name + self._get_bgd_suffix(ns_name, bgd)

    def generate_solution_structure(self):
        self.solution_structure_ready = True
        deploy_plan_path = Path(self.ctx.current_env_dir) / "Inventory" / DEPLOY_PLAN_FILE_NAME
        application_entries = EnvgeneDeployPlan.read(deploy_plan_path).entities if deploy_plan_path.is_file() else None
        solution_structure = {}
        if not application_entries:
            logger.info(f"Rendered solution_structure: {solution_structure}")
            return

        namespace_by_deploy_postfix = self.ctx.namespace_by_deploy_postfix

        for entry in application_entries:
            app_name, version = entry.version.split(":", 1)
            postfix = entry.deploy_postfix
            ns_name = entry.namespace or namespace_by_deploy_postfix.get(postfix)

            small_dict = {
                app_name: {
                    postfix: {
                        "version": version,
                        "namespace": ns_name,
                    }
                }
            }
            always_merger.merge(solution_structure, small_dict)

        always_merger.merge(self.ctx.current_env, {"solution_structure": solution_structure})
        logger.info(f"Rendered solution_structure: {solution_structure}")

    def render_from_file_to_file(self, src_template_path: str, target_file_path: str) -> dict:
        template = openFileAsString(src_template_path)
        template = replace_ansible_stuff(template_str=template, template_path=src_template_path)
        rendered = create_jinja_env().from_string(template).render(self.ctx.as_dict())
        logger.debug(f"Rendered entity: \n{rendered}")
        rendered_obj = readYaml(escaping_quotation(rendered))
        writeYamlToFile(target_file_path, rendered_obj)
        return rendered_obj

    def render_from_file_to_store(self, src_template_path, target_file_path) -> dict:
        return current_env_instance_store().put(target_file_path, self.render_from_file_to_obj(src_template_path))

    def render_from_file_to_obj(self, src_template_path) -> dict:
        template = openFileAsString(src_template_path)
        template = replace_ansible_stuff(template_str=template, template_path=src_template_path)
        rendered = create_jinja_env().from_string(template).render(self.ctx.as_dict())
        logger.debug(f"Rendered entity: \n{rendered}")
        return readYaml(escaping_quotation(rendered))

    def render_before_deploy_plan(self, src_template_path) -> tuple[dict, bool]:
        return render_template_file(src_template_path, self.ctx.as_dict(), True)

    def render_files_in_processes(self, template_paths: list) -> list[dict] | None:
        if parallel_workers() < 2 or len(template_paths) < 2:
            return None
        context = self.ctx.as_dict()
        return [rendered for rendered, _ in map_in_processes(
            render_template_file, [(str(template_path), context, False) for template_path in template_paths])]

    def prefetch_namespace_templates(self, template_paths: list[str]):
        if parallel_workers() < 2:
            return
        wanted_paths = [template_path for template_path in dict.fromkeys(template_paths)
                        if template_path not in self.namespace_templates
                        and (self.solution_structure_ready or template_path not in self.postponed_templates)]
        if len(wanted_paths) < 2:
            return
        context = self.ctx.as_dict()
        results = map_in_processes(render_template_file, [
            (template_path, context, not self.solution_structure_ready) for template_path in wanted_paths])
        for template_path, (rendered, is_postponed) in zip(wanted_paths, results):
            self.postponed_templates.pop(template_path, None)
            if is_postponed:
                self.postponed_templates[template_path] = rendered
            else:
                self.namespace_templates[template_path] = rendered

    def load_namespace_template(self, template_path: str):
        if template_path in self.namespace_templates:
            return
        if self.solution_structure_ready:
            self.postponed_templates.pop(template_path, None)
            self.namespace_templates[template_path] = self.render_from_file_to_obj(template_path)
            return
        if template_path in self.postponed_templates:
            return
        rendered, is_postponed = self.render_before_deploy_plan(template_path)
        if is_postponed:
            self.postponed_templates[template_path] = rendered
        else:
            self.namespace_templates[template_path] = rendered

    def namespace_template_name(self, template_path) -> str | None:
        template_path = str(template_path)
        self.load_namespace_template(template_path)
        if template_path not in self.postponed_templates:
            return self.namespace_templates[template_path].get("name")
        rendered_fields = self.postponed_templates[template_path]
        if "name" not in rendered_fields:
            logger.warning(f"Template {template_path} uses solution_structure before 'name', rendered twice")
            rendered_fields["name"] = self.render_from_file_to_obj(template_path).get("name")
        return rendered_fields["name"]

    def namespace_object(self, template_path: str, has_template_override: bool) -> dict:
        rendered = self.namespace_templates[template_path]
        if has_template_override or template_path in self.given_namespace_templates:
            return copy.deepcopy(rendered)
        self.given_namespace_templates.add(template_path)
        return rendered

    def render_from_obj_to_obj(self, template) -> dict:
        template = replace_ansible_stuff(template_str=dumpYamlToStr(template))
        rendered = create_jinja_env().from_string(template).render(self.ctx.as_dict())
        logger.debug(f"Rendered entity: \n{rendered}")
        return readYaml(escaping_quotation(rendered))

    def generate_tenant_file(self):
        logger.info(f"Generate Tenant yaml for {self.ctx.tenant}")
        tenant_file = f'{self.ctx.current_env_dir}/tenant.yml'
        tenant_tmpl_path = self.ctx.current_env_template["tenant"]
        self.render_from_file_to_store(Template(tenant_tmpl_path).render(self.ctx.as_dict()), tenant_file)

    def apply_template_override(self, template_override, rendered_object: dict, object_file_name: str, schema_path,
                                name):
        if not template_override:
            return
        logger.info(f"Apply template override to {object_file_name} for {name}")
        merge_yaml_into_target(rendered_object, '', self.render_from_obj_to_obj(template_override))
        validate_yaml_by_scheme_or_fail(input_yaml_content=rendered_object, schema_file_path=schema_path)

    def render_cloud(self) -> tuple[dict, bool]:
        if self.cloud_object is not None:
            return self.cloud_object, False
        cloud = self.calculate_cloud_name()
        cloud_template = self.ctx.current_env_template["cloud"]
        is_template_override = isinstance(cloud_template, dict)
        cloud_tmpl_path = cloud_template["template_path"] if is_template_override else cloud_template
        cloud_tmpl_path = Template(cloud_tmpl_path).render(self.ctx.as_dict())
        logger.info(f"Generate Cloud yaml for cloud {cloud}")
        if self.solution_structure_ready:
            rendered_cloud = self.render_from_file_to_obj(cloud_tmpl_path)
        else:
            rendered_cloud, is_postponed = self.render_before_deploy_plan(cloud_tmpl_path)
            if is_postponed:
                if is_template_override or not {"e2eParameterSets", "e2eParameters"} <= rendered_cloud.keys():
                    logger.warning(f"Template {cloud_tmpl_path} uses solution_structure before the e2e parameters, "
                                   "rendered twice")
                    rendered_cloud = self.render_from_file_to_obj(cloud_tmpl_path)
                    if is_template_override:
                        self.apply_template_override(cloud_template.get("template_override"), rendered_cloud,
                                                     "cloud.yml", get_schema_dir() / "cloud.schema.json", cloud)
                return rendered_cloud, True
        if is_template_override:
            self.apply_template_override(cloud_template.get("template_override"), rendered_cloud, "cloud.yml",
                                         get_schema_dir() / "cloud.schema.json", cloud)
        self.cloud_object = rendered_cloud
        return rendered_cloud, False

    def generate_cloud_file(self):
        cloud, _ = self.render_cloud()
        current_env_instance_store().put(Path(self.ctx.current_env_dir) / "cloud.yml", cloud)

    def render_bgd(self) -> dict | None:
        logger.info(f"Generate bg domain yaml for {self.ctx.bgd}")
        template = self.ctx.current_env_template.get("bg_domain", None)
        if not template:
            logger.info("'bg_domain' key not found in template descriptor, skipping bg domain rendering")
            return None
        return self.render_from_file_to_obj(Template(template).render(self.ctx.as_dict()))

    def _fetch_template_override_name(self, ns: dict) -> str:
        template_override = ns.get("template_override")
        if not template_override:
            return ""
        rendered = create_jinja_env().from_string(str(template_override)).render(self.ctx.as_dict())
        if not rendered:
            return ""
        return readYaml(rendered).get("name", "")

    def render_namespaces(self, bgd: dict | None) -> Iterator[tuple[str, dict]]:
        context = self.ctx.as_dict()
        namespace_schema = get_schema_dir() / "namespace.schema.json"
        namespace_by_deploy_postfix = {}
        self.prefetch_namespace_templates([
            Template(ns["template_path"]).render(context) for ns in self.ctx.current_env_template["namespaces"]])
        for ns in self.ctx.current_env_template["namespaces"]:
            ns_template_path = Template(ns["template_path"]).render(context)
            map_key = self.get_ns_base_postfix(ns, ns_template_path)
            folder_postfix = self.generate_ns_postfix(ns, ns_template_path, bgd)

            ns_name = self._get_ns_name_for_bgd(ns, ns_template_path)
            role = get_namespace_role(ns_name, bgd) if ns_name else NamespaceRole.COMMON

            role_templates_dir = self._get_template_dir_for_role(role)
            role_env_template = self._get_env_template_for_role(role)

            effective_ns = ns
            effective_template_path = ns_template_path

            if role != NamespaceRole.COMMON and role_env_template is not self.ctx.current_env_template:
                role_ns_config = self._find_ns_config_by_name(role_env_template, ns_name, role_templates_dir)
                if role_ns_config:
                    effective_ns = role_ns_config
                    effective_template_path = self._resolve_template_path(role_ns_config["template_path"],
                                                                          role_templates_dir)
                    logger.info(f"Using {role.name} template for namespace {ns_name}")

            effective_template_path = str(effective_template_path)
            override_name = self._fetch_template_override_name(effective_ns)
            rendered_ns = self.namespaces.get(folder_postfix)
            if rendered_ns is not None:
                yield folder_postfix, rendered_ns
                namespace_name = override_name or rendered_ns.get("name")
            else:
                self.load_namespace_template(effective_template_path)
                if effective_template_path in self.postponed_templates:
                    namespace_name = override_name or self.namespace_template_name(effective_template_path)
                else:
                    logger.info(f"Generate Namespace yaml for {folder_postfix}")
                    template_override = effective_ns.get("template_override")
                    rendered_ns = self.namespace_object(effective_template_path, bool(template_override))
                    yield folder_postfix, rendered_ns
                    namespace_name = override_name or rendered_ns.get("name")
                    self.apply_template_override(template_override, rendered_ns, "namespace.yml",
                                                 namespace_schema, folder_postfix)
                    self.namespaces[folder_postfix] = rendered_ns

            if role in (NamespaceRole.ORIGIN, NamespaceRole.PEER):
                sides = namespace_by_deploy_postfix.setdefault(map_key, {})
                sides[role.name.lower()] = namespace_name
            else:
                namespace_by_deploy_postfix[map_key] = namespace_name

        self.ctx.namespace_by_deploy_postfix = namespace_by_deploy_postfix

    def generate_namespace_files_and_map(self) -> dict:
        env_instance_store = current_env_instance_store()
        for folder_postfix, rendered_ns in self.render_namespaces(env_instance_store.bg_domain()):
            ns_file = Path(self.ctx.current_env_dir) / "Namespaces" / folder_postfix / "namespace.yml"
            env_instance_store.put(ns_file, rendered_ns)
        return self.ctx.namespace_by_deploy_postfix

    def calculate_cloud_name(self) -> str:
        inv = self.ctx.env_definition["inventory"]
        cluster_name = self.ctx.cluster_name
        env_name = inv.get("environmentName") or ""
        candidates = [
            inv.get("cloudName"),
            (inv.get("passportCloudName", "") + "_" + env_name).replace("-", "_") if inv.get("passportCloudName") else "",
            (inv.get("cloudPassport", "") + "_" + env_name).replace("-", "_") if inv.get("cloudPassport") else "",
            f"{cluster_name}_{env_name}".replace("-", "_") if cluster_name and env_name else "",
            env_name.replace("-", "_"),
        ]

        return next((c for c in candidates if c), "")

    def get_template_name(self, template_path: str) -> str:
        template_path = Path(template_path)
        return (
            template_path.name
            .replace(".yml.j2", "")
            .replace(".yaml.j2", "")
        )

    def render_composite_structure(self) -> dict | None:
        composite_structure = self.ctx.current_env_template.get("composite_structure")
        if not composite_structure:
            return None
        logger.info(f"Generate Composite Structure yaml for {composite_structure}")
        composite = self.render_from_file_to_obj(Template(composite_structure).render(self.ctx.as_dict()))
        validate_yaml_by_scheme_or_fail(input_yaml_content=composite,
                                        schema_file_path=get_schema_dir() / "composite-structure.schema.json")
        return composite

    def generate_external_cred(self):
        # render external creds
        external_credential_template = self.ctx.current_env_template.get("external_credential_template")
        if not external_credential_template:
            return
        external_cred_path = Template(external_credential_template).render(self.ctx.as_dict())
        logger.info(f"Found external template. Render external credentials for {external_cred_path}")
        external_creds = openYaml(external_cred_path)
        default_remote_path = "{{ current_env.cloud }}/{{ current_env.name }}"
        for cred_config in external_creds.values():
            if isinstance(cred_config, dict) and "remoteRefPath" not in cred_config:
                cred_config["remoteRefPath"] = default_remote_path
        rendered_external_creds = render_obj_by_context(external_creds, self.ctx)
        logger.debug(f"Rendered external credentials is: \n{rendered_external_creds}")

        # validate secret file
        secret_store_file = f"{self.ctx.work_dir}/configuration/secret-stores.yml"
        validate_yaml_by_scheme_or_fail(yaml_file_path=secret_store_file,
                                        schema_file_path=get_schema_dir() / "secret-stores.schema.json")

        # copy rendered creds to env creds file
        copy_creds_to_env_creds_file(self.ctx.current_env_dir, rendered_external_creds, EXTERNAL_CRED_COMMENT,
                                     get_schema_dir() / "credential.schema.json")
        self.is_external_cred_env = True

    def get_rendered_target_path(self, template_path: Path) -> Path:
        path_str = str(template_path)
        path_str = path_str.replace(".yml.j2", ".yml").replace(".yaml.j2", ".yml")
        return Path(path_str)

    def generate_paramset_templates(self, paramset_names: Iterable[str]):
        render_dir = Path(self.ctx.render_parameters_dir).resolve()
        paramset_templates = self.find_templates(render_dir, ["*.yml.j2", "*.yaml.j2"])
        for template_path in paramset_templates:
            template_name = self.get_template_name(template_path)
            if template_name not in paramset_names:
                continue
            target_path = self.get_rendered_target_path(template_path)
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

    def validate_used_paramsets(self, paramset_names: Iterable[str]):
        render_dir = Path(self.ctx.render_parameters_dir).resolve()
        errors = []
        files_by_template_dir = {}
        for paramset_path in self.find_templates(render_dir, ["*.yml", "*.yaml"]):
            if paramset_path.stem not in paramset_names:
                continue
            paramset = openYaml(paramset_path)
            try:
                validate_yaml_by_scheme_or_fail(input_yaml_content=paramset,
                                                schema_file_path=get_schema_dir() / "paramset.schema.json")
            except ValueError:
                errors.append(f'Parameter file at {paramset_path} is invalid, look for details above')
            if paramset.get("name") != paramset_path.stem:
                errors.append(f'Parameter "name" must be equal to filename without extension in file {paramset_path}')
            template_dir = next((p for p in paramset_path.parts if p.startswith("from_") and p.endswith("template")),
                                None)
            if template_dir:
                files_by_template_dir.setdefault((template_dir, paramset_path.stem), []).append(str(paramset_path))
        for (template_dir, name), files in sorted(files_by_template_dir.items()):
            if len(files) > 1:
                errors.append(f"duplicate Paramset names {{'{name}'}} in {template_dir}: {files}")
        if errors:
            raise ReferenceError("\n" + "\n".join(errors))

    def find_templates(self, path: str, patterns) -> list[Path]:
        path = Path(path)
        if not path.exists():
            logger.warning(f"Templates directory not found: {path}")
            return []
        templates = []
        for pattern in patterns:
            for f in path.rglob(pattern):
                if f.is_file():
                    templates.append(f)

        logger.info(f"Found templates: {templates}")
        return templates

    def render_app_defs(self) -> dict:
        app_defs = {}
        rendered_in_processes = self.render_files_in_processes(self.ctx.appdef_templates)
        for index, def_tmpl_path in enumerate(self.ctx.appdef_templates):
            app_def = rendered_in_processes[index] if rendered_in_processes else self.render_from_file_to_obj(
                def_tmpl_path)
            ensure_valid_fields(app_def, ["artifactId", "groupId", "name"])

            app_name = app_def.get("name")
            group_id = app_def["groupId"]
            artifact_id = app_def["artifactId"]

            self.ctx.update({
                "app_lookup_key": f"{group_id}:{artifact_id}",
                "groupId": group_id,
                "artifactId": artifact_id,
            })
            logger.info(f"Validating AppDef {app_name} rendered from {def_tmpl_path}")
            validate_yaml_by_scheme_or_fail(input_yaml_content=app_def,
                                            schema_file_path=get_schema_dir() / "appdef.schema.json")
            app_defs[app_name] = app_def
        if not app_defs:
            logger.warning("No AppDef templates rendered")
        return app_defs

    def render_reg_defs(self) -> dict:
        reg_defs = {}
        rendered_in_processes = self.render_files_in_processes(self.ctx.regdef_templates)
        for index, def_tmpl_path in enumerate(self.ctx.regdef_templates):
            reg_def = rendered_in_processes[index] if rendered_in_processes else self.render_from_file_to_obj(
                def_tmpl_path)
            ensure_valid_fields(reg_def, ["name"])
            logger.info(f"Validating RegDef {reg_def.get('name')} rendered from {def_tmpl_path}")
            validate_yaml_by_scheme_or_fail(input_yaml_content=reg_def,
                                            input_schema_content=get_regdef_schema_for_content(reg_def))
            reg_defs[reg_def.get('name')] = reg_def
        if not reg_defs:
            logger.warning("No RegDef templates rendered")
        return reg_defs

    def set_appreg_def_overrides(self):
        output_dir = Path(self.ctx.output_dir)
        cluster_name = self.ctx.cluster_name
        config_file_name = Path("configuration") / "appregdef_config"

        potential_global_config_files = [
            output_dir / f"{config_file_name}.yaml",
            output_dir / f"{config_file_name}.yml",
        ]

        potential_cluster_config_files = [
            output_dir / cluster_name / f"{config_file_name}.yaml",
            output_dir / cluster_name / f"{config_file_name}.yml",
        ]

        global_config_paths = [f for f in potential_global_config_files if f.exists()]
        cluster_config_paths = [f for f in potential_cluster_config_files if f.exists()]

        if not global_config_paths and not cluster_config_paths:
            logger.info("No appregdef_config file found, skipping overrides")
            return

        global_appdefs, global_regdefs = {}, {}
        cluster_appdefs, cluster_regdefs = {}, {}

        if len(global_config_paths) > 0:
            global_path = global_config_paths[0]
            try:
                cfg = openYaml(global_path)
                global_appdefs = cfg.get("appdefs", {}).get("overrides", {})
                global_regdefs = cfg.get("regdefs", {}).get("overrides", {})
                logger.info(f"Loaded global config from {global_path}")
            except Exception as e:
                logger.warning(f"Failed to load global config: {e}")

        if len(cluster_config_paths) > 0:
            cluster_path = cluster_config_paths[0]
            try:
                cfg = openYaml(cluster_path)
                cluster_appdefs = cfg.get("appdefs", {}).get("overrides", {})
                cluster_regdefs = cfg.get("regdefs", {}).get("overrides", {})
                logger.info(f"Loaded cluster config from {cluster_path}")
            except Exception as e:
                logger.warning(f"Failed to load cluster config: {e}")

        self.ctx.appdefs["overrides"] = always_merger.merge(global_appdefs, cluster_appdefs)
        self.ctx.regdefs["overrides"] = always_merger.merge(global_regdefs, cluster_regdefs)

    def generate_profiles(self, profile_names: Iterable[str]):
        logger.info(f"Start rendering profiles from list: {profile_names}")
        template_profiles_dir = self.ctx.template_profiles_dir
        profile_templates = self.find_templates(template_profiles_dir, ["*.yaml.j2", "*.yml.j2"])
        for template_path in profile_templates:
            template_name = self.get_template_name(template_path)
            if template_name in profile_names:
                self.render_from_file_to_store(template_path, self.get_rendered_target_path(template_path))

    def _load_appregdef_templates(self) -> None:
        templates_dir = self.ctx.templates_dirs[NamespaceRole.COMMON]
        patterns = ["*.yaml.j2", "*.yml.j2", "*.j2", "*.yaml", "*.yml"]
        self.ctx.appdef_templates = self.find_templates(f"{templates_dir}/appdefs", patterns)
        self.ctx.regdef_templates = self.find_templates(f"{templates_dir}/regdefs", patterns)

    def _render_app_reg_defs(self) -> dict:
        self._load_appregdef_templates()
        self.set_appreg_def_overrides()
        return {"AppDefs": self.render_app_defs(), "RegDefs": self.render_reg_defs()}

    def render_app_reg_defs(self, env_name: str, extra_env: dict) -> dict:
        logger.info(
            f"Starting rendering app_reg_defs for {env_name}. Input params are:\n{dump_as_yaml_format(extra_env)}")
        with self.ctx.use():
            self.setup_base_context(extra_env)
            return self._render_app_reg_defs()

    def render_namespaces_for_map(self, env_name: str, extra_env: dict) -> dict:
        logger.info(
            f"Starting rendering namespaces for {env_name}. Input params are:\n{dump_as_yaml_format(extra_env)}")
        with self.ctx.use():
            self.setup_base_context(extra_env)
            self.ensure_shared_chain()
            list(self.render_namespaces(self.bg_domain))
            return self.ctx.namespace_by_deploy_postfix

    def _cloud_e2e_paramset_names(self, cloud: dict) -> list[str]:
        env_specific = self.ctx.env_definition.get("envTemplate", {}).get("envSpecificE2EParamsets") or {}
        return (cloud.get("e2eParameterSets") or []) + (env_specific.get("cloud") or [])

    def render_cloud_e2e_parameters(self, env_name: str, extra_env: dict, env_dir: str,
                                    render_parameters_dir: Path) -> dict:
        from build_env.build_env import mergeParameterSetsIntoParameters, copy_instance_paramsets, \
            copy_template_paramsets, create_paramset_map

        logger.info(
            f"Starting rendering cloud e2e parameters for {env_name}. Input params are:\n{dump_as_yaml_format(extra_env)}")
        with self.ctx.use():
            self.setup_base_context(extra_env)
            self.ensure_shared_chain()
            cloud, _ = self.render_cloud()

            cloud_file = Path(self.ctx.current_env_dir) / "cloud.yml"

            if render_parameters_dir.exists():
                shutil.rmtree(render_parameters_dir)

            copy_template_paramsets({NamespaceRole.COMMON: self.ctx.templates_dir}, str(render_parameters_dir))
            copy_instance_paramsets(env_dir, str(render_parameters_dir))
            self.ctx.render_parameters_dir = str(render_parameters_dir)
            e2e_paramset_names = self._cloud_e2e_paramset_names(cloud)
            self.validate_used_paramsets(e2e_paramset_names)
            self.generate_paramset_templates(e2e_paramset_names)

        paramset_map = create_paramset_map(str(render_parameters_dir), NamespaceRole.COMMON, False, False)
        cloud_e2e = {"e2eParameterSets": e2e_paramset_names, "e2eParameters": cloud["e2eParameters"]}
        e2e_parameters, _ = mergeParameterSetsIntoParameters(
            str(cloud_file), cloud_e2e, "e2eParameterSets", "e2eParameters", paramset_map, {},
            extra_env["env_definition"])
        return e2e_parameters


    def _resolve_composite_member(self, member: dict, bgd: dict | None = None) -> dict:
        member_type = member.get("type")

        if member_type == "namespace":
            return {
                "originNamespace": member["name"]
            }

        if member_type == "bgdomain":
            if bgd is None:
                raise ValueError(
                    f"BG Domain '{member.get('name')}' cannot be resolved "
                    "because bg_domain.yml is missing or empty"
                )

            bgd_name = member.get("name")

            if bgd.get("name") != bgd_name:
                raise ValueError(
                    f"Composite Structure references BG Domain '{bgd_name}', "
                    f"but bg_domain.yml contains '{bgd.get('name')}'"
                )

            return {
                "originNamespace": bgd["originNamespace"]["name"],
                "peerNamespace": bgd["peerNamespace"]["name"],
                "controllerNamespace": bgd["controllerNamespace"]["name"],
            }

        raise ValueError(f"Unknown composite member type: {member_type}")

    def compute_composite_topology(self, composite: dict | None, bg_domain: dict | None):
        if composite is None:
            logger.info("Composite Structure not found. composite_topology={}")
            self.ctx.current_env["composite_topology"] = {}
            return

        baseline = composite.get("baseline")
        if not baseline:
            raise ValueError("Composite Structure is missing required 'baseline'")

        members = [baseline] + composite.get("satellites", [])
        has_bgd = any(member.get("type") == "bgdomain" for member in members)

        bgd = bg_domain if has_bgd else None

        topology = {
            "baseline": self._resolve_composite_member(baseline, bgd)
        }

        satellites = [
            self._resolve_composite_member(member, bgd)
            for member in composite.get("satellites", [])
        ]

        if satellites:
            topology["satellites"] = satellites

        self.ctx.current_env["composite_topology"] = topology

        logger.info(
            f"Resolved composite_topology:\n"
            f"{dump_as_yaml_format(topology)}"
        )

    def collect_used_paramset_names(self) -> set[str]:
        env_dir = Path(self.ctx.current_env_dir)
        env_instance_store = current_env_instance_store()
        paths = [p for p in (env_dir / "tenant.yml", env_dir / "cloud.yml") if env_instance_store.exists(p)]
        paths += env_instance_store.list(env_dir / "Namespaces" / "*" / "namespace.yml")
        names = {name for p in paths for tag in PARAMSET_TAGS for name in (env_instance_store.get(p).get(tag) or [])}
        env_template = self.ctx.env_definition.get("envTemplate") or {}
        for field_name in ENV_SPECIFIC_PARAMSET_FIELDS:
            for paramsets in (env_template.get(field_name) or {}).values():
                names.update(paramsets or [])
        logger.info(f"Used paramsets: {sorted(names)}")
        return names

    def render_config_env(self, env_name: str, extra_env: dict):
        logger.info(f"Starting rendering environment {env_name}. Input params are:\n{dump_as_yaml_format(extra_env)}")
        with self.ctx.use():
            self.setup_base_context(extra_env)
            logger.info(f"current_env = {self.ctx.current_env}")

            current_env_dir = self.ctx.current_env_dir
            self.ensure_shared_chain()
            env_instance_store = current_env_instance_store()
            if self.bg_domain is not None:
                env_instance_store.put(Path(current_env_dir) / "bg_domain.yml", self.bg_domain)
            if self.composite_structure is not None:
                env_instance_store.put(Path(current_env_dir) / "composite_structure.yml", self.composite_structure)
            self.generate_solution_structure()
            self.generate_namespace_files_and_map()
            self.generate_tenant_file()
            self.generate_cloud_file()
            self.generate_external_cred()

            env_specific_schema = self.ctx.current_env_template.get("envSpecificSchema")
            if env_specific_schema:
                copy_path(source_path=env_specific_schema, target_dir=current_env_dir)
            self.used_paramset_names = self.collect_used_paramset_names()
            self.validate_used_paramsets(self.used_paramset_names)
            self.generate_paramset_templates(self.used_paramset_names)

            ensure_required_keys(self.ctx.as_dict(),
                                 required=["templates_dir", "cluster_name", "current_env_dir"])
            logger.info(f"Rendering of templates for environment {env_name} generation was successful")

            self.validate_bgd()


_env_generator_of_run = None


@contextmanager
def open_env_generator_of_run():
    global _env_generator_of_run
    _env_generator_of_run = EnvGenerator()
    try:
        yield _env_generator_of_run
    finally:
        _env_generator_of_run = None


def env_generator() -> EnvGenerator:
    return _env_generator_of_run or EnvGenerator()
