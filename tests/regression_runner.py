
import json
import yaml
import pandas as pd
import sys
import os

# Add the parent directory of the current script to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data import get_positions_data, get_instrument_categorization_data, get_expected_output_0002, get_expected_output_0004

def load_yaml(file_path):
    """Load and validate a YAML file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def validate_yaml_schema(yaml_data, schema_path):
    """Validate the YAML data against the schema."""
    from jsonschema import validate, ValidationError

    with open(schema_path, "r") as schema_file:
        schema = json.load(schema_file)

    try:
        validate(instance=yaml_data, schema=schema)
    except ValidationError as e:
        raise ValueError(f"YAML schema validation failed: {e.message}")

def load_input_data(input_data):
    """Load input data specified as functions or file paths."""
    datasets = {}
    for key, source in input_data.items():
        if callable(source):
            datasets[key] = source()
        else:
            datasets[key] = pd.read_csv(source)
    return datasets

def execute_steps(yaml_data, datasets):
    """Execute steps defined in the YAML file using Polars."""
    import polars as pl

    # Convert pandas DataFrames to Polars DataFrames
    polars_datasets = {key: pl.from_pandas(df) for key, df in datasets.items()}

    # Map dataset names to variables used in YAML code
    polars_context = {
        "positions_pl": polars_datasets.get("positions"),
        "instrument_categorization_pl": polars_datasets.get("instrument_categorization"),
        "pl": pl  # Add Polars library to the context
    }

    # Execute steps from YAML
    for step in yaml_data["task"]["steps"]:
        code = step.get("polars")
        if not code:
            raise ValueError(f"Polars code missing in step: {step['step']}")
        try:
            exec(code, {}, polars_context)
        except Exception as e:
            print(f"Error in step: {step['step']}")
            print(f"Code: {code}")
            print(f"Context: {list(polars_context.keys())}")
            raise e

        # # Debug: Print intermediate DataFrames
        # print(f"After step: {step['step']}")
        # for key, df in polars_context.items():
        #     if isinstance(df, pl.DataFrame):
        #         print(f"{key}:")
        #         print(df)
    if "result" not in polars_context:
        raise ValueError("Final result not computed in steps.")
    return polars_context["result"].to_pandas()

# def compare_results(output, expected_output):
#     """Compare the generated output with the expected output."""
#     return output.equals(expected_output)
def compare_dataframes(df1, df2, precision=8):
    """
    Compare two pandas DataFrames with rounding, data type alignment, and string normalization.

    Args:
        df1 (pd.DataFrame): First DataFrame to compare.
        df2 (pd.DataFrame): Second DataFrame to compare.
        precision (int): Number of decimal places to round to for floats.

    Returns:
        bool: True if DataFrames are identical (considering normalization), False otherwise.
    """
    # Align column data types
    for col in df1.columns:
        if col in df2.columns:
            # Handle numeric columns
            if pd.api.types.is_numeric_dtype(df1[col]):
                if pd.api.types.is_float_dtype(df1[col]) or pd.api.types.is_float_dtype(df2[col]):
                    df1[col] = df1[col].round(precision)
                    df2[col] = df2[col].round(precision)
                elif pd.api.types.is_integer_dtype(df1[col]) and pd.api.types.is_integer_dtype(df2[col]):
                    df1[col] = df1[col].astype("int64")
                    df2[col] = df2[col].astype("int64")

            # Handle string columns
            elif pd.api.types.is_string_dtype(df1[col]) or pd.api.types.is_string_dtype(df2[col]):
                df1[col] = df1[col].fillna("").str.strip().str.lower()
                df2[col] = df2[col].fillna("").str.strip().str.lower()

    # Check equality
    if not df1.equals(df2):
        print("DataFrames are different:")
        for col in df1.columns:
            if not df1[col].equals(df2[col]):
                print(f"Difference in column '{col}':")
                print(f"Expected: {df1[col].tolist()}")
                print(f"Actual: {df2[col].tolist()}")
        return False
    print("DataFrames are identical.")
    return True



def compare_results(output, expected_output, precision=8):
    """
    Compare the generated output with the expected output, allowing for rounding.

    Args:
        output (pd.DataFrame): Generated output DataFrame.
        expected_output (pd.DataFrame): Expected output DataFrame.
        precision (int): Number of decimal places to round to.

    Returns:
        bool: True if DataFrames match (considering rounding), False otherwise.
    """
    return compare_dataframes(output, expected_output, precision=precision)



def run_regression_test(yaml_file, input_data, expected_output, schema):
    """Run a single regression test."""
    try:
        # Load and validate YAML
        yaml_data = load_yaml(yaml_file)
        validate_yaml_schema(yaml_data, schema)

        # Load input data (functions or CSV paths)
        datasets = load_input_data(input_data)

        # Execute steps defined in the YAML file
        result = execute_steps(yaml_data, datasets)

        # Compare result with expected output
        print(result)
        print(expected_output)
        success = compare_results(result, expected_output)

        return TestResult(success=success, error_message=None if success else "Output does not match expected.")
    except Exception as e:
        return TestResult(success=False, error_message=str(e))

class TestResult:
    """Represents the result of a regression test."""
    def __init__(self, success, error_message=None):
        self.success = success
        self.error_message = error_message

def main():
    """Main function to execute all regression tests."""
    tests = [
        {
            "yaml_file": "yaml/0004.yaml",
            "input_data": {
                "positions": get_positions_data,  # Updated positions data
                "instrument_categorization": get_instrument_categorization_data,  # Updated categorization data
            },
            "expected_output": get_expected_output_0004,  # Dynamically generate expected output
            "schema": "yaml/yaml_schema.json"
        }
        ,
        {
            "yaml_file": "yaml/0002.yaml",
            "input_data": {
                "positions": get_positions_data,  # Updated positions data
                "instrument_categorization": get_instrument_categorization_data,  # Updated categorization data
            },
            "expected_output": get_expected_output_0002,  # Dynamically generate expected output
            "schema": "yaml/yaml_schema.json"
        }
    ]

    for test in tests:
        # Update expected_output comparison to use DataFrame directly
        expected_output_func = test["expected_output"]
        test["expected_output"] = expected_output_func()

        result = run_regression_test(**test)
        if result.success:
            print(f"Test for {test['yaml_file']} passed.")
        else:
            print(f"Test for {test['yaml_file']} failed: {result.error_message}")

if __name__ == "__main__":
    main()
