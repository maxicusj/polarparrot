import json
import yaml
from jsonschema import validate, ValidationError

def load_yaml_schema(schema_path):
    """
    Load the JSON schema for YAML validation.

    Args:
        schema_path (str): Path to the JSON schema file.

    Returns:
        dict: Loaded schema.
    """
    with open(schema_path, 'r') as schema_file:
        return json.load(schema_file)

def validate_yaml_file(yaml_file_path, schema):
    """
    Validate a YAML file against the schema.

    Args:
        yaml_file_path (str): Path to the YAML file.
        schema (dict): JSON schema to validate against.

    Returns:
        bool: True if valid, raises ValidationError if invalid.
    """
    with open(yaml_file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    # Validate YAML data against the schema
    validate(instance=yaml_data, schema=schema)
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate YAML files against a schema.")
    parser.add_argument("yaml_file", help="Path to the YAML file to validate.")
    parser.add_argument("schema_file", help="Path to the JSON schema file.")

    args = parser.parse_args()

    try:
        schema = load_yaml_schema(args.schema_file)
        validate_yaml_file(args.yaml_file, schema)
        print(f"YAML file '{args.yaml_file}' is valid.")
    except ValidationError as e:
        print(f"YAML file '{args.yaml_file}' is invalid:\n{e.message}")
    except Exception as e:
        print(f"An error occurred: {e}")

