"""
Backend Service for Flask API
This module handles asynchronous data fetching and YAML file processing for the backend service.
"""

from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify

import aiohttp

import yaml
from calculation_engine import CalculationEngine

# Initialize Flask app and thread pool
app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=4)


async def async_fetch_required_data(session, table_name, columns):
    """
    Asynchronously fetch required data from the data web service.

    Args:
        session (aiohttp.ClientSession): HTTP session for making requests.
        table_name (str): Name of the database table.
        columns (list): List of columns to fetch.

    Returns:
        dict: Fetched data.
    """
    url = f"http://data-service/{table_name}?columns={','.join(columns)}"
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as exception_message:
        raise RuntimeError("Failed to fetch required data") from exception_message


def parse_yaml_file(file_content):
    """
    Parse a YAML file content into a Python object.

    Args:
        file_content (str): YAML file content as a string.

    Returns:
        dict: Parsed YAML content.
    """
    try:
        return yaml.safe_load(file_content)
    except yaml.YAMLError as exception_message:
        raise ValueError("Invalid YAML file format") from exception_message


@app.route("/process", methods=["POST"])
def process_request():
    """
    Handle POST requests to process JSON and YAML inputs.

    Returns:
        Response: Flask JSON response with status and results.
    """
    try:
        data = request.get_json()
        json_data = data.get("positions_json")
        yaml_file = data.get("analytics_list_yaml")

        if not json_data or not yaml_file:
            return jsonify({"status": "error", "message": "Missing required data"}), 400

        parsed_yaml = parse_yaml_file(yaml_file)
        results = []

        for item in parsed_yaml:
            # Example logic: Append processed results
            results.append(item)

        return jsonify({"status": "success", "results": results})
    except ValueError as exception_message:
        return jsonify({"status": "error", "message": str(exception_message)}), 400
    except Exception as generic_exception:
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def perform_calculations(data, calculations):
    """
    Perform calculations using the provided data and calculations list.

    Args:
        data (list): List of data points.
        calculations (list): List of calculations to perform.

    Returns:
        list: Results of the calculations.
    """
    engine = CalculationEngine()
    results = []
    for calc in calculations:
        try:
            result = engine.compute(data, calc)
            results.append(result)
        except Exception as exception_message:
            raise RuntimeError("Calculation failed") from exception_message
    return results


if __name__ == "__main__":
    app.run(debug=True, port=5000)
