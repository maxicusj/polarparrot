import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import ollama
import re
import asyncio
import threading
import time  # For time tracking
import yaml

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# List of available models
AVAILABLE_MODELS = [
    "phi3:latest",
    "phi3.5:latest",
    "mistral:latest",
    "llama3.2:latest",
    "sqlcoder:7b",
    "prompt/nsql-7b:latest",
    "qwen2.5-coder:latest",
    "duckdb-nsql:latest",
    "qwen2.5-coder:0.5b",
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b"    
]

# Layout of the app
app.layout = dbc.Container([
    html.H1("YAML Playground: GPT Parrot", className="mb-4 text-center"),

    # Model selector and sliders
    dbc.Row([
        dbc.Col([
            html.Label("Select Model:"),
            dcc.Dropdown(
                id='model-selector',
                options=[{'label': model, 'value': model} for model in AVAILABLE_MODELS],
                value='qwen2.5-coder:7b'
            )
        ], width=4),
        dbc.Col([
            html.Label("Select Creativity:"),
            dcc.Slider(
                id='temperature-slider',
                min=0.0,
                max=1.0,
                step=0.1,
                value=0.5,
                marks={i / 10: f'{i / 10}' for i in range(0, 11)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=4),
        dbc.Col([
            html.Label("Deterministic:"),
            dcc.Slider(
                id='deterministic-slider',
                min=0.0,
                max=1.0,
                step=0.1,
                value=0.5,
                marks={i / 10: f'{i / 10}' for i in range(0, 11)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=4)
    ], className="mb-4"),

    # Chat display
    html.Div(id='chat-display', style={
        'border': '1px solid #ccc',
        'padding': '10px',
        'height': '500px',
        'overflowY': 'scroll',
        'backgroundColor': '#f5f5f5'
    }, className='mb-3'),

    # Typing indicator
    html.Div(id='typing-output', style={'color': 'gray', 'fontStyle': 'italic'}),

    # User input area fixed at the bottom
    html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Textarea(
                    id='user-input',
                    placeholder='Type your message...',
                    style={'width': '100%', 'height': '84px'}
                )
            ], width=11),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    'Send',
                    id='send-btn',
                    n_clicks=0,
                    style={
                        'width': '30%',
                        'height': '40px',
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'marginTop': '5px',
                        'marginRight':'10px'
                    }
                ),
                dbc.Button(
                    'Cancel',
                    id='cancel-btn',
                    n_clicks=0,
                    style={
                        'width': '30%',
                        'height': '40px',
                        'backgroundColor': '#dc3545',
                        'color': 'white',
                        'marginTop': '5px',
                        'marginRight':'10px'
                    }
                ),
                dbc.Button(
                    'Delete History',
                    id='delete-btn',
                    n_clicks=0,
                    style={
                        'width': '30%',
                        'height': '40px',
                        'backgroundColor': '#6c757d',  # Gray background
                        'color': 'white',
                        'marginTop': '5px',
                        'marginRight':'10px'
                    }
                )
            ], width=10)
        ])
    
    ], style={'position': 'fixed', 'bottom': '0', 'width': '100%', 'backgroundColor': 'white', 'padding': '10px', 'borderTop': '1px solid #ccc'}),

    # Interval for streaming updates
    dcc.Interval(id='stream-interval', interval=500, n_intervals=0, disabled=True)
], fluid=True)

# Store chat messages for display
chat_history = []
# Store conversation history for ollama
conversation_history = []
stream_data = {
    "response": "",
    "in_progress": False,
    "new_response": False,
    "start_time": None,
    "cancel_requested": False
}


def format_response(response_text):
    """Formats the response to handle code blocks and styling."""
    parts = re.split(r'(```.*?```)', response_text, flags=re.DOTALL)
    formatted_parts = []

    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            code_content = part[3:-3].strip()
            formatted_parts.append(html.Pre(code_content, style={
                'backgroundColor': '#f8f8f8',
                'padding': '10px',
                'borderRadius': '5px',
                'overflowX': 'scroll'
            }))
        else:
            # Split text into paragraphs
            paragraphs = part.strip().split('\n\n')
            for para in paragraphs:
                formatted_parts.append(html.P(para))
    return formatted_parts


def start_stream(conversation, selected_model):
    async def stream_response():
        # Read the contents of the sample YAML and YAML schema JSON files
        try:
            with open('yaml/0001.yaml', 'r') as yaml_file:
                yaml_content = yaml_file.read()
            with open('yaml/yaml_schema.json', 'r') as json_file:
                json_content = json_file.read()
        except Exception as e:
            print(f"Error reading files: {e}")
            yaml_content = ""
            json_content = ""

        # Append file contents to the conversation with a line break
        conversation_with_files = conversation + [
            {"role": "system", "content": "code 0002.yaml"},
            {"role": "system", "content": "\n---\n"},
            {"role": "system", "content": yaml_content},
            {"role": "system", "content": "\n---\n"},
            {"role": "system", "content": "code yaml_schema.json:"},
            {"role": "system", "content": "\n---\n"},
            {"role": "system", "content": json_content}
            ]
    
        stream = ollama.chat(
            model=selected_model,
            messages=conversation_with_files,
            stream=True
        )
        try:
            for chunk in stream:
                if stream_data["cancel_requested"]:
                    break
                stream_data["response"] += chunk.get('message', {}).get('content', '')
                stream_data["new_response"] = True
            stream_data["in_progress"] = False
        except Exception as e:
            stream_data["in_progress"] = False

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream_response())
    loop.close()


@app.callback(
    [Output('chat-display', 'children'),
     Output('stream-interval', 'disabled'),
     Output('typing-output', 'children'),
     Output('user-input', 'value')],
    [Input('send-btn', 'n_clicks')],
    [State('user-input', 'value'),
     State('model-selector', 'value'),
     State('temperature-slider', 'value'),
     State('deterministic-slider', 'value')]
)
def update_chat(n_clicks, user_message, selected_model, temperature, deterministic):
    if not user_message:
        return chat_history, True, '', ''

    # Append user message to chat history with bubble styling
    chat_history.append(
        html.Div(
            html.Div(
                user_message,
                style={
                    'backgroundColor': '#007bff',
                    'color': 'white',
                    'padding': '10px',
                    'borderRadius': '15px',
                    'maxWidth': '60%',
                    'marginLeft': 'auto',
                    'marginBottom': '10px',
                    'boxShadow': '0px 2px 2px rgba(0, 0, 0, 0.1)'
                }
            ),
            style={'display': 'flex', 'justifyContent': 'flex-end'}
        )
    )

    # Append user message to conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # Clear user input field
    user_input_value = ''

    # Initialize streaming
    stream_data["response"] = ""
    stream_data["in_progress"] = True
    stream_data["new_response"] = False
    stream_data["start_time"] = time.time()
    stream_data["cancel_requested"] = False

    # Start streaming in a separate thread
    threading.Thread(target=start_stream, args=(conversation_history.copy(), selected_model)).start()

    # Set typing output with 0 seconds elapsed
    typing_output = "0 seconds - Bot is typing..."

    return chat_history, False, typing_output, user_input_value


@app.callback(
    [Output('chat-display', 'children', allow_duplicate=True),
     Output('typing-output', 'children', allow_duplicate=True),
     Output('stream-interval', 'disabled', allow_duplicate=True)],
    [Input('stream-interval', 'n_intervals'),
     Input('cancel-btn', 'n_clicks'),
     Input('delete-btn', 'n_clicks')],
    prevent_initial_call=True
)
def stream_update(n_intervals, cancel_n_clicks, delete_n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    else:
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_input == 'cancel-btn':
        if stream_data["in_progress"]:
            # Cancel the request
            stream_data["cancel_requested"] = True
            stream_data["in_progress"] = False
            stream_data["start_time"] = None
            # Update typing output
            return chat_history, "Request cancelled.", True
        else:
            # No ongoing request, do nothing
            raise dash.exceptions.PreventUpdate
    elif triggered_input == 'delete-btn':
        # Cancel any ongoing request
        if stream_data["in_progress"]:
            stream_data["cancel_requested"] = True
            stream_data["in_progress"] = False
            stream_data["start_time"] = None
        # Clear chat history and conversation history
        chat_history.clear()
        conversation_history.clear()
        # Update display
        return [], "", True  # Return empty chat history
    elif triggered_input == 'stream-interval':
        if stream_data["cancel_requested"]:
            # Handle cancellation
            stream_data["in_progress"] = False
            stream_data["start_time"] = None
            typing_output = "Request cancelled."
            return chat_history, typing_output, True
        elif stream_data["in_progress"] or stream_data["new_response"]:
            # Update response
            elapsed_time = int(time.time() - stream_data["start_time"]) if stream_data["start_time"] else 0
            formatted_bot_response = format_response(stream_data["response"])
            stream_data["new_response"] = False

            # Display the bot's message as it's being typed
            chat_history_display = chat_history.copy()
            chat_history_display.append(
                html.Div(
                    html.Div(
                        formatted_bot_response,
                        style={
                            'backgroundColor': '#e9ecef',
                            'padding': '10px',
                            'borderRadius': '15px',
                            'maxWidth': '60%',
                            'marginRight': 'auto',
                            'marginBottom': '10px',
                            'boxShadow': '0px 2px 2px rgba(0, 0, 0, 0.1)'
                        }
                    ),
                    style={'display': 'flex', 'justifyContent': 'flex-start'}
                )
            )

            typing_output = f"{elapsed_time} seconds - Bot is typing..."
            return chat_history_display, typing_output, False
        else:
            # Streaming completed
            stream_data["in_progress"] = False
            stream_data["start_time"] = None  # Reset start time
            formatted_bot_response = format_response(stream_data["response"])

            # Append bot response to chat history
            chat_history.append(
                html.Div(
                    html.Div(
                        formatted_bot_response,
                        style={
                            'backgroundColor': '#e9ecef',
                            'padding': '10px',
                            'borderRadius': '15px',
                            'maxWidth': '60%',
                            'marginRight': 'auto',
                            'marginBottom': '10px',
                            'boxShadow': '0px 2px 2px rgba(0, 0, 0, 0.1)'
                        }
                    ),
                    style={'display': 'flex', 'justifyContent': 'flex-start'}
                )
            )

            # Append assistant's response to conversation history
            conversation_history.append({"role": "assistant", "content": stream_data["response"]})

            return chat_history, "", True
    else:
        raise dash.exceptions.PreventUpdate


if __name__ == '__main__':
    app.run_server(debug=True, port=8080)
