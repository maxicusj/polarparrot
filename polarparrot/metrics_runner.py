"""
metrics_runner.py

Main script to run multiple analytics calculations using the CalculationEngine.
Accepts a JSON file containing a list of YAML analytics files to execute.
"""

import json
import sys
import polars as pl
import io
import yaml
from data.data import get_positions_data, get_instrument_categorization_data
from calculation_engine import CalculationEngine


def initialize_data_namespace(positions_df, instrument_categorization_df):
    """
    Initialize the data namespace with positions and instrument categorization.

    Args:
        positions_df (pandas.DataFrame): Pandas DataFrame of positions data.
        instrument_categorization_df (pandas.DataFrame): Instrument categorization data.

    Returns:
        dict: A data namespace containing Polars LazyFrames and other required data.
    """
    data_namespace = {}

    # Convert positions Pandas DataFrame to JSON string and then to Polars LazyFrame
    try:
        positions_json = positions_df.to_json(orient="records")
        positions_pl = pl.read_json(io.StringIO(positions_json)).lazy()
        data_namespace["positions_pl"] = positions_pl
    except Exception as e:
        raise RuntimeError(f"Failed to initialize positions_pl: {str(e)}")

    # Convert instrument categorization Pandas DataFrame to Polars LazyFrame
    try:
        instrument_categorization_pl = pl.from_pandas(instrument_categorization_df).lazy()
        data_namespace["instrument_categorization_pl"] = instrument_categorization_pl
    except Exception as e:
        raise RuntimeError(f"Failed to initialize instrument_categorization_pl: {str(e)}")

    # Add Polars namespace
    data_namespace["pl"] = pl

    return data_namespace


def main():
    """
    Main function to execute analytics calculations based on a JSON file.
    """
    # Check if a JSON file path is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python metrics_runner.py analytics_list.json")
        sys.exit(1)

    json_file = sys.argv[1]

    # Step 1: Load the JSON file containing the list of YAML analytics files
    try:
        with open(json_file, "r") as file:
            analytics_list = json.load(file)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file. {e}")
        sys.exit(1)

    # Validate the JSON structure
    if "analytics" not in analytics_list or not isinstance(analytics_list["analytics"], list):
        print("Error: JSON file must contain a key 'analytics' with a list of YAML file paths.")
        sys.exit(1)

    # Step 2: Get Data
    positions_df = get_positions_data()  # Assuming this function returns a Pandas DataFrame
    instrument_categorization_df = get_instrument_categorization_data()  # Assuming this returns a Pandas DataFrame

    # Initialize data namespace
    try:
        data_namespace = initialize_data_namespace(positions_df, instrument_categorization_df)
    except Exception as e:
        print(f"Error initializing data namespace: {e}")
        sys.exit(1)

    # Step 3: Execute each analytics YAML file
    for yaml_file in analytics_list["analytics"]:
        print(f"\nExecuting Analytics from YAML File: {yaml_file}")
        # Initialize Calculation Engine with the YAML file
        engine = CalculationEngine(yaml_file)
        try:
            engine.load_yaml()
        except FileNotFoundError:
            print(f"Error: YAML file '{yaml_file}' not found.")
            continue
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML file '{yaml_file}'. {e}")
            continue

        # Execute Steps
        try:
            result = engine.execute_steps(data_namespace)

            # Collect the result if it's a Polars LazyFrame
            if isinstance(result, pl.LazyFrame):
                result = result.collect()

            # Step 4: Print Result
            print("\nResult:")
            print(result)
        except Exception as e:
            print(f"An error occurred while executing '{yaml_file}': {e}")



if __name__ == "__main__":
    main()
