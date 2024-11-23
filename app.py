import dash
from dash import dcc, html
import dash_table
import requests
import json
import time

# Initialize the Dash app
app = dash.Dash(__name__)

# Define default JSON content
default_positions_json = json.dumps(
    [
    {
        "instrument_id": 1,
        "weight_1": 0.2777777777777778,
        "weight_2": 0.2222222222222222,
        "weight_3": 0.16666666666666666,
        "weight_4": 0.2777777777777778,
        "is_laggard": True
    },
    {
        "instrument_id": 2,
        "weight_1": 0.2692307692307692,
        "weight_2": 0.23076923076923078,
        "weight_3": 0.2692307692307692,
        "weight_4": 0.23076923076923078,
        "is_laggard": False
    },
    {
        "instrument_id": 3,
        "weight_1": 0.35714285714285715,
        "weight_2": 0.2857142857142857,
        "weight_3": 0.07142857142857142,
        "weight_4": 0.35714285714285715,
        "is_laggard": True
    },
    {
        "instrument_id": 4,
        "weight_1": 0.1111111111111111,
        "weight_2": 0.2777777777777778,
        "weight_3": 0.5,
        "weight_4": 0.1111111111111111,
        "is_laggard": True
    },
    {
        "instrument_id": 5,
        "weight_1": 0.32142857142857145,
        "weight_2": 0.25,
        "weight_3": 0.17857142857142858,
        "weight_4": 0.25,
        "is_laggard": False
    }
]
, indent=4)

default_analytics_list_json = json.dumps({
    "analytics": [
        "yaml/0001.yaml",
        "yaml/0002.yaml"
    ]
}, indent=4)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Analytics Dashboard"),
    html.Div([
        html.Label('Positions JSON:'),
        dcc.Textarea(
            id='positions-json',
            value=default_positions_json,
            style={'width': '100%', 'height': 200}
        ),
    ], style={'padding': '20px'}),
    html.Div([
        html.Label('Analytics List JSON:'),
        dcc.Textarea(
            id='analytics-list-json',
            value=default_analytics_list_json,
            style={'width': '100%', 'height': 200}
        ),
    ], style={'padding': '20px'}),
    html.Button('Submit', id='submit-button', n_clicks=0, style={'marginTop': '20px'}),
    html.Div(id='output-status', style={'padding': '20px'}),
    dash_table.DataTable(
        id='result-table',
        columns=[],  # Columns will be dynamically updated
        style_table={'height': '400px', 'overflowY': 'auto'}
    )
])

# Define callback to submit data and display results
@app.callback(
    [dash.Output('result-table', 'data'),
     dash.Output('result-table', 'columns'),
     dash.Output('output-status', 'children')],
    [dash.Input('submit-button', 'n_clicks')],
    [dash.State('positions-json', 'value'),
     dash.State('analytics-list-json', 'value')]
)
def submit_data(n_clicks, positions_json, analytics_list_json):
    if n_clicks > 0:
        try:
            url = "http://localhost:8088/analytics"
            start_time = time.time()
            response = requests.post(url, json={
                "positions_json": positions_json,
                "analytics_list_json": analytics_list_json
            })
            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result_data = response.json()
                if result_data['status'] == 'success':
                    results = []
                    for yaml_result in result_data['results']:
                        if isinstance(yaml_result, list):
                            results.extend(yaml_result)
                        else:
                            results.append(yaml_result)

                    # Dynamically generate columns
                    if len(results) > 0:
                        columns = [{"name": col, "id": col} for col in results[0].keys()]
                    else:
                        columns = []

                    status_message = f"Generated {len(result_data['results'])} rows in {elapsed_time:.2f} seconds."
                    return results, columns, status_message
                else:
                    return [], [], f"Error: {result_data.get('message', 'Unknown error.')}"
            else:
                return [], [], f"Error: Backend service returned status code {response.status_code}."

        except requests.exceptions.RequestException as e:
            return [], [], f"Error: {str(e)}"
    return [], [], ""

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

