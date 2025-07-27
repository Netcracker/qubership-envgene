import argparse
import json
from typing import Mapping
from typing import Tuple

import jschon

from ._main import process_json_doc
from ._yaml import create_yaml_processor
from ._yaml import YamlIndent


def _make_parser(*, prog: str, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
    )
    parser.add_argument('path', help='path to the JSON / YAML document')
    parser.add_argument(
        '--schema', required=True, metavar='/path/to/schema.json', help='path to the JSON Schema document'
    )
    parser.add_argument(
        '--dry-run',
        '-n',
        help='if set, result is not persisted back to the original file',
        action='store_true',
    )
    parser.add_argument('--indent', type=int, default=4, help='indent size')
    parser.add_argument(
        '--yaml-indent',
        type=lambda s: YamlIndent(*map(int, s.split(','))),
        metavar='MAPPING,SEQUENCE,OFFSET',
        default=YamlIndent(2, 4, 2),
        help='YAML indent size',
    )
    return parser


def _is_yaml_path(path: str) -> bool:
    return path.endswith('.yaml') or path.endswith('.yml')


def _load_doc_and_schema(
    args: argparse.Namespace,
) -> Tuple[jschon.json.JSONCompatible, Mapping[str, jschon.json.JSONCompatible]]:
    with open(args.path) as f:
        if _is_yaml_path(args.path):
            yaml = create_yaml_processor(indent=args.yaml_indent)
            doc_data = yaml.load(f)
        else:
            doc_data = json.load(f)

    with open(args.schema) as f:
        schema_data = json.load(f)

    return doc_data, schema_data


def _maybe_persist(doc_data: jschon.json.JSONCompatible, args: argparse.Namespace) -> None:
    if args.dry_run:
        return

    if _is_yaml_path(args.path):
        with open(args.path, 'w') as f:
            yaml = create_yaml_processor(indent=args.yaml_indent)
            yaml.dump(doc_data, f)
    else:
        with open(args.path, 'w') as f:
            json.dump(doc_data, f, indent=args.indent)


def sort_main() -> None:
    jschon.create_catalog('2020-12')

    parser = _make_parser(
        prog='jschon-sort',
        description="Sorts a JSON or YAML document to match a JSON Schema's order of properties",
    )
    args = parser.parse_args()

    doc_data, schema_data = _load_doc_and_schema(args)
    doc_data = process_json_doc(doc_data=doc_data, schema_data=schema_data, sort=True)
    _maybe_persist(doc_data, args)


def remove_additional_props_main() -> None:
    jschon.create_catalog('2020-12')

    parser = _make_parser(
        prog='jschon-remove-additional-props',
        description="Processes a JSON or YAML document to remove additional properties not defined in the schema",
    )
    args = parser.parse_args()

    doc_data, schema_data = _load_doc_and_schema(args)
    doc_data = process_json_doc(doc_data=doc_data, schema_data=schema_data, remove_additional_props=True)
    _maybe_persist(doc_data, args)
