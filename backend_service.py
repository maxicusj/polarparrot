from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import polars as pl
import yaml
import json
import asyncio
import aiohttp
import io
from calculation_engine import CalculationEngine

app = Flask(__name__)

# Create a thread pool for parallel YAML processing
executor = ThreadPoolExecutor(max_workers=4)


async def async_fetch_required_data(session, table_name, columns):
    """
    Asynchronously fetch required data from the data web service.

    Args:
        session (aiohttp.ClientSession): The session for making HTTP requests.
        table_name (str): Name of the table to fetch.
        columns (list): List of columns to select.

    Returns:
        pl.DataFrame: Fetched data as a Polars DataFrame.
    """
    try:
        async with session.post(
            "http://localhost:8089/fetch_table",
            json={"table_name": table_name, "columns": columns}
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"Error fetching table '{table_name}': {await response.text()}")
            data = await response.json()
            return pl.DataFrame(data["data"])
    except Exception as e:
        raise RuntimeError(f"Failed to fetch required data for table '{table_name}': {str(e)}")


async def fetch_all_required_data(required_data):
    """
    Fetch all required data asynchronously.

    Args:
        required_data (list): List of data requirements from the YAML file.

    Returns:
        list: List of Polars DataFrames fetched for each required table.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [
            async_fetch_required_data(session, data_req["table"], [data_req["join_on"]] + data_req["columns"])
            for data_req in required_data
        ]
        return await asyncio.gather(*tasks)


def fetch_data_async(required_data):
    """
    Synchronously fetch all required data using asyncio.
    """
    return asyncio.run(fetch_all_required_data(required_data))


def process_yaml(yaml_file_path, positions_json):
    """
    Process the YAML file and return the result.

    Args:
        yaml_file_path (str): Path to the YAML file.
        positions_json (str): JSON string for positions.

    Returns:
        dict: Result of processing the YAML.
    """
    try:
        # Load YAML
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)

        metric_name = yaml_data.get("metric_name", "Unknown Metric")
        required_data = yaml_data.get("required_data", [])

        # Convert positions JSON string to Polars LazyFrame
        positions_pl = pl.read_json(io.StringIO(positions_json)).lazy()

        # Fetch required tables asynchronously
        fetched_tables = fetch_data_async(required_data)

        # Prepare the data namespace
        data_namespace = {
            'positions_pl': positions_pl,  # Add positions to the namespace
            'pl': pl                       # Add Polars for execution in YAML steps
        }

        # Add fetched tables to the namespace
        for fetched_data, data_req in zip(fetched_tables, required_data):
            table_name = data_req["table"]
            data_namespace[f"{table_name}_pl"] = fetched_data.lazy()

        # Execute YAML steps
        engine = CalculationEngine(yaml_file_path)
        engine.parsed_yaml = yaml_data
        result = engine.execute_steps(data_namespace)

        # Collect the result if it's a LazyFrame
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        # Convert result to JSON-compatible format
        result = result.to_dicts()
        for row in result:
            row['metric_name'] = metric_name

        return result

    except Exception as e:
        raise RuntimeError(f"Error processing YAML file '{yaml_file_path}': {str(e)}")


@app.route('/analytics', methods=['POST'])
def analytics():
    """
    Backend service to accept JSON data for positions and analytics YAML files,
    execute the analytics in parallel, and return the results.

    Returns:
        Response: JSON response containing success or error message and results.
    """
    # Get JSON data from the request
    data = request.json

    positions_json = data.get("positions_json")
    analytics_list_json = data.get("analytics_list_json")

    try:
        # Parse the analytics list JSON
        analytics_list = json.loads(analytics_list_json).get("analytics", [])

        if not analytics_list:
            return jsonify({"status": "error", "message": "Analytics list is empty or invalid."})

        # Run analytics in parallel
        futures = []
        for yaml_file in analytics_list:
            futures.append(executor.submit(process_yaml, yaml_file, positions_json))

        # Gather results
        results = []
        for future, yaml_file in zip(futures, analytics_list):
            try:
                yaml_result = future.result()  # Retrieve the result from each YAML
                results.extend(yaml_result)  # Combine all rows from each YAML result
            except Exception as e:
                return jsonify({"status": "error", "message": f"Error processing YAML file '{yaml_file}': {str(e)}"})

        return jsonify({"status": "success", "results": results})

    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": f"File not found: {str(e)}"})
    except ValueError as e:
        return jsonify({"status": "error", "message": f"Invalid input data: {str(e)}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8088)