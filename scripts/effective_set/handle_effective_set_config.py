import json
import os
import shutil
import tempfile

from envgenehelper import logger, get_schema_dir


def handle_effective_set_config(config_str):
    if isinstance(config_str, str):
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise

    version = config.get("version") or "v2.0"
    extra_args = [f"--effective-set-version={version}"]

    app_chart_value = config.get("app_chart_validation", True)
    extra_args.append(f"--app_chart_validation={str(app_chart_value).lower()}")

    consumers = (
        config.get("contexts", {})
        .get("pipeline", {})
        .get("consumers", [])
    )

    if not isinstance(consumers, list) or not consumers:
        logger.info("No consumers provided; skipping schema generation.")
        result_args = {
            "extra_args": extra_args,  # Only --effective-set-version
        }
        logger.info(json.dumps(result_args))
        return result_args

    temp_root = tempfile.gettempdir()
    schema_output_dir = os.path.join(temp_root, "schemas", "registered_consumer_specific")
    os.makedirs(schema_output_dir, exist_ok=True)
    logger.info(f"Ensured directory exists: {schema_output_dir}")

    image_schema_dir = f"{get_schema_dir()}/registered_consumer_specific"

    for consumer in consumers:
        schema_json = consumer.get("schema")
        name = consumer.get("name")
        consumer_version = consumer.get("version")

        if not name or not consumer_version:
            logger.error(f"Consumer entry missing required 'name' or 'version'")
            continue

        filename = f"{name}-{consumer_version}.schema.json"
        schema_file_path = os.path.join(schema_output_dir, filename)

        if schema_json:
            try:
                logger.info(f"Processing schema file: {filename}")
                with open(schema_file_path, 'w') as schema_file:
                    json.dump(schema_json, schema_file, indent=2)
                if os.path.isfile(schema_file_path):
                    logger.info(
                        f"Schema file written successfully: {schema_file_path}, size={os.path.getsize(schema_file_path)}")
                else:
                    logger.error(f"Schema file NOT found after writing: {schema_file_path}")
                logger.info(f"Wrote schema for consumer '{name}' to {schema_file_path}")
            except Exception as e:
                logger.error(f"Failed to write schema for consumer '{name}': {e}")
                continue

        else:
            fallback_path = os.path.join(image_schema_dir, filename)
            if os.path.isfile(fallback_path):
                try:
                    shutil.copy(fallback_path, schema_file_path)
                    logger.info(f"Copied schema for {name} to {schema_file_path}")
                except Exception as e:
                    logger.error(f"Failed to copy schema: {e}")
                    continue
            else:
                logger.error(f"Schema not found: {fallback_path}")
                continue

        extra_args.append(f"--pipeline-consumer-specific-schema-path={schema_file_path}")

    result_args = {
        "extra_args": extra_args,
    }
    return result_args
