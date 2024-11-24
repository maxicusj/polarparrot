"""
Dash Application for Data Analytics
This script sets up a Dash web application that processes JSON input for analytics
using YAML configurations. The app supports user inputs, backend interactions, and
data visualization.
"""

import time
import json
import dash
from dash import dcc, html
import dash_table
import requests
import dash_bootstrap_components as dbc

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define default JSON content
default_positions_json = json.dumps(
    [
        {
            "instrument_id": 1,
            "weight_1": 0.2777777777777778,
            "weight_2": 0.2222222222222222,
            "weight_3": 0.16666666666666666,
            "weight_4": 0.2777777777777778,
            "is_laggard": True,
        },
        {
            "instrument_id": 2,
            "weight_1": 0.2692307692307692,
            "weight_2": 0.23076923076923078,
            "weight_3": 0.2692307692307692,
            "weight_4": 0.23076923076923078,
            "is_laggard": False,
        },
    ],
    indent=4,
)

default_analytics_list_json = json.dumps(
    {"analytics": ["yaml/0001.yaml", "yaml/0002.yaml"]},
    indent=4,
)

# Define the layout of the app
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1(
                    "YAML Playground: Parrots like Polars",
                    className="text-center my-4",
                )
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Positions JSON:", className="fw-bold"),
                        dcc.Textarea(
                            id="positions-json",
                            value=default_positions_json,
                            style={"width": "100%", "height": 200},
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.Label("Analytics List JSON:", className="fw-bold"),
                        dcc.Textarea(
                            id="analytics-list-json",
                            value=default_analytics_list_json,
                            style={"width": "100%", "height": 200},
                        ),
                    ],
                    width=6,
                ),
            ],
            className="mb-4",
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "Submit",
                    id="submit-button",
                    n_clicks=0,
                    color="primary",
                    className="mb-4",
                ),
                className="text-center",
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(id="output-status", className="alert alert-info"),
                    className="mb-4",
                )
            ]
        ),
        dbc.Row(
            dbc.Col(
                dash_table.DataTable(
                    id="result-table",
                    columns=[],  # Columns will be dynamically updated
                    style_table={"height": "400px", "overflowY": "auto"},
                    style_as_list_view=True,
                    style_cell={"textAlign": "left", "padding": "5px"},
                    style_header={
                        "backgroundColor": "#f8f9fa",
                        "fontWeight": "bold",
                        "textAlign": "center",
                    },
                )
            )
        ),
    ],
    fluid=True,
)

# Define callback to submit data and display results
@app.callback(
    [
        dash.Output("result-table", "data"),
        dash.Output("result-table", "columns"),
        dash.Output("output-status", "children"),
    ],
    [dash.Input("submit-button", "n_clicks")],
    [
        dash.State("positions-json", "value"),
        dash.State("analytics-list-json", "value"),
    ],
)
def submit_data(n_clicks, positions_json, analytics_list_json):
    """
    Handles the submission of data by the user.

    Args:
        n_clicks (int): Number of clicks on the submit button.
        positions_json (str): JSON string for positions data.
        analytics_list_json (str): JSON string for analytics list.

    Returns:
        tuple: Updated table data, table columns, and a status message.
    """
    if n_clicks > 0:
        try:
            url = "http://localhost:8088/analytics"
            start_time = time.time()
            response = requests.post(
                url,
                json={
                    "positions_json": positions_json,
                    "analytics_list_json": analytics_list_json,
                },
            )
            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result_data = response.json()
                if result_data["status"] == "success":
                    results = []
                    for yaml_result in result_data["results"]:
                        if isinstance(yaml_result, list):
                            results.extend(yaml_result)
                        else:
                            results.append(yaml_result)

                    # Dynamically generate columns
                    if results:
                        columns = [{"name": col, "id": col} for col in results[0].keys()]
                    else:
                        columns = []

                    status_message = (
                        f"Generated {len(result_data['results'])} rows "
                        f"in {elapsed_time:.2f} seconds."
                    )
                    return results, columns, status_message
                return [], [], f"Error: {result_data.get('message', 'Unknown error.')}"
            return [], [], f"Error: Backend service returned status code {response.status_code}."

        except requests.exceptions.RequestException as exception_message:
            return [], [], f"Error: {str(exception_message)}"
    return [], [], ""


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
