# from flask import Flask, request, jsonify
# import polars as pl

# app = Flask(__name__)

# # Simulated data table as Polars DataFrame
# data_tables = {
#     "instrument_categorization": pl.DataFrame({
#         "instrument_id": [1, 2, 3, 4, 5],
#         "credit_parent_name": ["Parent A", "Parent B", "Parent A", "Parent C", "Parent B"],
#         "sector1": ["Finance", "Healthcare", "Finance", "Energy", "Healthcare"]
#     })
# }

# @app.route('/fetch_table', methods=['POST'])
# def fetch_table():
#     request_data = request.json
#     table_name = request_data.get("table_name")
#     columns = request_data.get("columns")

#     if table_name not in data_tables:
#         return jsonify({"error": f"Table '{table_name}' not found"}), 404

#     # Select only the requested columns
#     filtered_table = data_tables[table_name].select(columns)

#     # Convert to JSON-compatible format
#     return jsonify({"data": filtered_table.to_dicts()})

# if __name__ == '__main__':
#     app.run(debug=True, port=8089)

from flask import Flask, request, jsonify
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

load_dotenv()

# Set up SQL Server connection
def get_sql_server_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to SQL Server: {e}")
        return None

# Flask route to fetch data
@app.route('/fetch_table', methods=['POST'])
def fetch_table():
    request_data = request.json
    table_name = request_data.get("table_name")
    columns = request_data.get("columns")

    # Validate input
    if not table_name or not columns:
        return jsonify({"error": "Both 'table_name' and 'columns' are required"}), 400

    # Ensure columns is a list
    if not isinstance(columns, list):
        return jsonify({"error": "'columns' should be a list"}), 400

    # Connect to SQL Server
    conn = get_sql_server_connection()
    if not conn:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Build the SQL query
        columns_str = ", ".join(columns)
        query = f"SELECT {columns_str} FROM {table_name};"

        # Execute the query
        cursor.execute(query)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]  # Get column names

        # Convert rows to a list of dictionaries
        result = [dict(zip(col_names, row)) for row in rows]

        conn.close()

        # Return the result as JSON
        return jsonify({"data": result})
    except Exception as e:
        print(f"Error executing query: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8089)
