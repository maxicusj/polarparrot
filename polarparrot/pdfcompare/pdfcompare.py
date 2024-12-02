import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import dash_table
import base64
import io
import fitz  # PyMuPDF
import difflib
import re
import pytesseract
from PIL import Image, ImageDraw
import ollama  # Import the ollama package
import pandas as pd
import threading
import time
from io import BytesIO
from PIL import Image

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Default AI Prompt
DEFAULT_PROMPT = """
You are an AI assistant tasked with explaining the differences between two texts identified by a word-by-word comparison. Below is a list of differences where each difference indicates a word that has been removed, added, or changed.

List of Differences:
{differences}

Please provide a brief explanation of these differences.
"""

# Global list to store AI explanations
ai_explanations_list = []

# Application layout
app.layout = dbc.Container([
    html.H2("PDF Comparison Tool", className="my-4"),
    dbc.Row([
        dbc.Col([
            html.H5("Upload PDFs for Comparison"),
            dcc.Upload(
                id='upload-pdfs',
                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                style={
                    'width': '100%', 'height': '100px', 'lineHeight': '100px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
                },
                multiple=True
            ),
            html.Div(id='file-list'),

            html.H5("Options", className="mt-3"),
            dcc.Checklist(
                id='options',
                options=[
                    {'label': 'Handle OCR for Scanned PDFs', 'value': 'ocr'}
                ],
                value=[],
                labelStyle={'display': 'block'}
            ),
            html.H5("Customize AI Prompt", className="mt-3"),
            dcc.Textarea(
                id='custom-prompt',
                value=DEFAULT_PROMPT.strip(),
                style={'width': '100%', 'height': '200px'},
                placeholder="Enter your custom AI prompt here..."
            ),
            
            # Percentage Threshold Input
            html.H5("Specify Percentage Threshold for Numeric Differences", className="mt-3"),
            dbc.Input(
                id='percentage-threshold',
                type='number',
                min=0,
                step=0.1,
                value=1.0,  # Default threshold is 1%
                placeholder="Enter percentage threshold (default is 1%)"
            ),
            html.Div(id='threshold-help', className="text-muted", style={'fontSize': '12px'}),
            
            html.Button('Compare', id='compare-button', n_clicks=0, className="mt-3"),
            # New: Explain Button 

            html.Button('Explain', id='explain-button', n_clicks=0, className="mt-3", disabled=True),
            html.Button('Download', id='download-pdf-button', n_clicks=0, className="mt-3"),
         
            html.Div(id='progress-output', style={'margin-top': '10px'}, className="mt-2"),
         
            html.Div(id='explain-progress-output', style={'margin-top': '10px'}, className="mt-2"),
            # New: Legend for Difference Types
            html.Div([
                html.H6("Legend:"),
                dbc.Row([
                    dbc.Col([
                        html.Span(style={'display': 'inline-block', 'width': '15px', 'height': '15px',
                                         'backgroundColor': 'red', 'borderRadius': '50%', 'margin-right': '5px'}),
                        html.Span("Significant Numeric Difference")
                    ]),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Span(style={'display': 'inline-block', 'width': '15px', 'height': '15px',
                                         'backgroundColor': 'orange', 'borderRadius': '50%', 'margin-right': '5px'}),
                        html.Span("Insignificant Numeric Difference")
                    ]),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Span(style={'display': 'inline-block', 'width': '15px', 'height': '15px',
                                         'backgroundColor': 'green', 'borderRadius': '50%', 'margin-right': '5px'}),
                        html.Span("Zero to Non-Zero Change")
                    ]),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Span(style={'display': 'inline-block', 'width': '15px', 'height': '15px',
                                         'backgroundColor': 'blue', 'borderRadius': '50%', 'margin-right': '5px'}),
                        html.Span("Text Difference")
                    ]),
                ]),
            ], className="mt-4"),
            dcc.Download(id='download-pdf'),
        ], width=3),
        dbc.Col([
            html.H5("Results"),
            dcc.Loading(
                id="loading",
                type="default",
                children=html.Div(
                    id='output-area',
                    style={
                        'overflowY': 'scroll',
                        'maxHeight': '800px',
                        'border': '1px solid #ddd',
                        'padding': '10px',
                        'borderRadius': '5px'
                    }
                )
            ),
        ], width=9)
    ]),
    dbc.Row([
        dbc.Col([
            
            html.H5("Summary of Differences", className="mt-4"),
            html.Div(id='differences-count', className="mt-2"),
            dcc.Loading(
                id="loading-summary",
                type="default",
                children=html.Div(id='summary-table')
            )
        ],),
    ]),
    dcc.Store(id='diff-data-store'),            # Store for initial differences
    dcc.Store(id='ai-explanations-store'),     # Store for AI explanations
    dcc.Store(id='compared-images-store'),     # Store for compared images
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds (5 seconds)
        n_intervals=0
    ),
], fluid=True)

# Store uploaded files in a global variable
uploaded_files = {}

# Callback to display list of uploaded files
@app.callback(
    Output('file-list', 'children'),
    Input('upload-pdfs', 'filename'),
    State('upload-pdfs', 'contents')
)
def update_file_list(filenames, contents):
    if filenames is not None and contents is not None:
        global uploaded_files
        uploaded_files = dict(zip(filenames, contents))
        return html.Ul([html.Li(f) for f in filenames])
    return ''

def extract_text_with_positions(pdf_data, use_ocr=False):
    """
    Extract text and positions from PDF data.
    If use_ocr is True, perform OCR on the PDF pages.
    """
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    text_positions = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        if use_ocr:
            # Convert page to image
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img)
            words = text.split()
            for word in words:
                text_positions.append({
                    'page_num': page_num,
                    'text': word,
                    'bbox': None,  # Positions not available from OCR
                    'line_no': None  # Line numbers not available from OCR
                })
        else:
            words = page.get_text("words")  # list of word tuples
            # Sort words by their y0 to group into lines
            words_sorted = sorted(words, key=lambda w: (w[1], w[0]))
            current_line = 0
            last_y = None
            line_threshold = 10  # Adjust as needed for line separation
            for w in words_sorted:
                x0, y0, x1, y1, word, block_no, line_no, word_no = w
                if last_y is None:
                    last_y = y0
                elif abs(y0 - last_y) > line_threshold:
                    current_line += 1
                    last_y = y0
                text_positions.append({
                    'page_num': page_num,
                    'text': word,
                    'bbox': (x0, y0, x1, y1),
                    'line_no': current_line
                })
    return text_positions

def word_by_word_compare(text_positions1, text_positions2, threshold):
    """
    Perform word-by-word comparison between two lists of text positions.
    Returns a list of differences with details, each containing value_file1, value_file2,
    difference_explanation, and difference_type.
    """
    texts1 = [tp['text'] for tp in text_positions1]
    texts2 = [tp['text'] for tp in text_positions2]

    matcher = difflib.SequenceMatcher(None, texts1, texts2)
    differences = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            for k in range(max(i2 - i1, j2 - j1)):
                val1 = texts1[i1 + k] if (i1 + k) < i2 else None
                val2 = texts2[j1 + k] if (j1 + k) < j2 else None
                # Fetch bbox from the appropriate source
                bbox1 = text_positions1[i1 + k]['bbox'] if (i1 + k) < len(text_positions1) else None
                bbox2 = text_positions2[j1 + k]['bbox'] if (j1 + k) < len(text_positions2) else None
                # Prefer bbox from file1, fallback to file2
                bbox = bbox1 if bbox1 is not None else bbox2
                # Determine difference type
                if val1 is not None and val2 is not None and is_numeric(val1) and is_numeric(val2):
                    num_val1 = convert_to_numeric(val1)
                    num_val2 = convert_to_numeric(val2)
                    if num_val1 == 0 and num_val2 != 0:
                        difference_type = "zero_to_nonzero"
                        percent_change = "Infinite (0 to non-zero)"
                    else:
                        percent_change = calculate_percent_change(num_val1, num_val2)
                        if isinstance(percent_change, float) and abs(percent_change) >= threshold:
                            difference_type = "significant_numeric"
                        elif isinstance(percent_change, float):
                            difference_type = "insignificant_numeric"
                        else:
                            difference_type = "significant_numeric"  # Treat undefined as significant
                else:
                    difference_type = "text"

                differences.append({
                    'id': len(differences) + 1,
                    'page_num': text_positions1[i1 + k]['page_num'] if (i1 + k) < len(text_positions1) else text_positions2[j1 + k]['page_num'],
                    'value_file1': val1,
                    'value_file2': val2,
                    'bbox': bbox,  # Ensure 'bbox' is included
                    'difference_explanation': "",  # To be filled later
                    'difference_type': difference_type
                })
        elif tag == 'delete':
            for k in range(i1, i2):
                val1 = texts1[k]
                val2 = None
                difference_type = "insignificant_numeric"  # Default assumption
                if is_numeric(val1):
                    num_val1 = convert_to_numeric(val1)
                    if num_val1 == 0:
                        difference_type = "insignificant_numeric"
                        percent_change = "No change (removal of zero)"
                    else:
                        # Here, removal sets to zero
                        percent_change = calculate_percent_change(num_val1, 0)
                        if isinstance(percent_change, float) and abs(percent_change) >= threshold:
                            difference_type = "significant_numeric"
                        elif isinstance(percent_change, float):
                            difference_type = "insignificant_numeric"
                        else:
                            difference_type = "significant_numeric"  # Treat undefined as significant
                else:
                    difference_type = "text"

                differences.append({
                    'id': len(differences) + 1,
                    'page_num': text_positions1[k]['page_num'],
                    'value_file1': val1,
                    'value_file2': val2,
                    'bbox': text_positions1[k]['bbox'],  # Ensure 'bbox' is included
                    'difference_explanation': "",  # To be filled later
                    'difference_type': difference_type
                })
        elif tag == 'insert':
            for k in range(j1, j2):
                val1 = None
                val2 = texts2[k]
                difference_type = "text"  # Default assumption
                if is_numeric(val2):
                    num_val1 = 0  # Previous value was zero
                    num_val2 = convert_to_numeric(val2)
                    if num_val2 != 0:
                        difference_type = "zero_to_nonzero"
                        percent_change = "Infinite (0 to non-zero)"
                    else:
                        percent_change = "No change (0 to 0)"
                else:
                    difference_type = "text"

                differences.append({
                    'id': len(differences) + 1,
                    'page_num': text_positions2[k]['page_num'],
                    'value_file1': val1,
                    'value_file2': val2,
                    'bbox': text_positions2[k]['bbox'],  # Ensure 'bbox' is included
                    'difference_explanation': "",  # To be filled later
                    'difference_type': difference_type
                })
        # 'equal' tag is ignored

    return differences

def is_numeric(value):
    """
    Check if the value can be converted to a float (includes percentages).
    """
    if isinstance(value, str):
        value = value.strip().rstrip('%')
    try:
        float(value)
        return True
    except (ValueError, AttributeError):
        return False

def is_percentage(value):
    """
    Check if the value is formatted as a percentage.
    """
    if isinstance(value, str):
        return bool(re.match(r'^\d+(\.\d+)?%$', value.strip()))
    return False

def convert_to_numeric(value):
    """
    Convert a string value to a float. If it's a percentage, remove the '%' and convert.
    """
    if isinstance(value, str):
        value = value.strip()
        if value.endswith('%'):
            try:
                return float(value[:-1])
            except ValueError:
                return None
        else:
            try:
                return float(value)
            except ValueError:
                return None
    elif isinstance(value, (int, float)):
        return float(value)
    return None

def calculate_percent_change(val1, val2):
    """
    Calculate the percentage change from val1 to val2.
    Returns the raw percentage value (float) or a string if undefined.
    """
    try:
        if val1 == 0 and val2 != 0:
            return "Infinite (0 to non-zero)"
        elif val1 == 0 and val2 == 0:
            return "No change (0 to 0)"
        elif val1 == 0:
            return "Undefined (Division by zero)"
        change = ((val2 - val1) / abs(val1)) * 100
        return change
    except Exception as e:
        return f"Error: {e}"

def ai_explain_difference(difference, prompt_template):
    """
    Use AI to explain a single difference based on its type.
    """
    val1 = difference['value_file1']
    val2 = difference['value_file2']
    difference_type = difference['difference_type']

    # Prepare the difference description based on difference_type
    if difference_type == "text":
        if val1 and val2:
            diff_desc = f"Changed from '{val1}' to '{val2}'"
        elif val1 and not val2:
            diff_desc = f"Removed '{val1}'"
        elif not val1 and val2:
            diff_desc = f"Added '{val2}'"
        else:
            diff_desc = "Unknown change"
    else:
        # For zero_to_nonzero or other types not handled by AI
        return ""

    prompt = prompt_template.format(differences=diff_desc)

    print(f"Debug: Sending prompt to Ollama for difference ID {difference['id']}: {prompt}")

    client = ollama.Client()

    try:
        response = client.generate(
            model='qwen2.5-coder:1.5b',  # Update model as needed
            prompt=prompt,
            options={
                'temperature': 0.0
            }
        )

        # Extract the 'response' value from the response tuples
        reasoning = ""
        for item in response:
            if isinstance(item, tuple) and item[0] == 'response':
                reasoning += item[1]
        reasoning = reasoning.strip()

        print(f"Debug: Received explanation for difference ID {difference['id']}: {reasoning}")

        return reasoning

    except Exception as e:
        print(f"Error during Ollama call for difference ID {difference['id']}: {e}")
        return f"Error: {e}"

def highlight_differences_on_images(pdf_data, differences, zoom=2.0):
    """
    Highlight differences on PDF pages converted to images.
    Differences are marked with red rectangles for significant numeric,
    blue for text differences, green for zero to non-zero changes,
    and orange for insignificant numeric differences.
    Returns a list of base64-encoded image strings.
    """
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(zoom, zoom)  # Increase resolution
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        draw = ImageDraw.Draw(img)

        # Draw rectangles on differences
        for diff in differences:
            if diff['page_num'] == page_num and diff.get('bbox') is not None:
                bbox = diff['bbox']
                if bbox:
                    # Determine color based on difference_type
                    difference_type = diff.get('difference_type')
                    if difference_type == 'significant_numeric':
                        color = 'red'
                    elif difference_type == 'zero_to_nonzero':
                        color = 'green'
                    elif difference_type == 'insignificant_numeric':
                        color = 'orange'  # Optional: Choose a color for insignificant differences
                    else:  # text differences
                        color = 'blue'
                    
                    # Adjust bbox to integers and scale according to zoom
                    rect = [int(bbox[0]*zoom), int(bbox[1]*zoom), int(bbox[2]*zoom), int(bbox[3]*zoom)]
                    draw.rectangle(rect, outline=color, width=2)

        # Save image to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        if img_bytes:
            img_str = base64.b64encode(img_bytes).decode('utf-8')
            images.append(img_str)
        else:
            print(f"Failed to get image data for page {page_num}")
            images.append(None)
    return images

def create_summary_table(differences_summary):
    """
    Create a Dash DataTable for detailed differences with explanations.
    """
    if not differences_summary:
        return html.Div("No significant differences found.")

    df = pd.DataFrame(differences_summary, columns=["id", "value_file1", "value_file2", "difference_explanation"])
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {'name': 'Diff. Id', 'id': 'id'},
            {'name': 'Value File 1', 'id': 'value_file1'},
            {'name': 'Value File 2', 'id': 'value_file2'},
            {'name': 'Difference Explanation', 'id': 'difference_explanation'}
        ],
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'normal',
            'height': 'auto',
            'maxWidth': '200px',
            'wordWrap': 'break-word'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_table={
            'minWidth': '300px',
            'maxWidth': '100%',
            'overflowX': 'auto'
        },
        page_size=10,  # Adjust as needed
        style_as_list_view=True
    )

# Function to process AI explanations in a separate thread
def process_ai_explanations(differences, prompt_template):
    global ai_explanations_list
    for diff in differences:
        # Only process differences without explanations and of type 'text'
        if not diff['difference_explanation'] and diff.get('difference_type') == 'text':
            explanation = ai_explain_difference(diff, prompt_template)
            # Append to the global list
            ai_explanations_list.append({
                'id': diff['id'],
                'difference_explanation': explanation
            })

# Main callback to handle both Compare and Explain button clicks
@app.callback(
    [
        Output('output-area', 'children'),
        Output('progress-output', 'children'),
        Output('diff-data-store', 'data'),
        Output('differences-count', 'children'),
        Output('explain-button', 'disabled'),
        Output('explain-progress-output', 'children'),
        Output('compared-images-store', 'data'),     # Output for compared images
    ],
    [
        Input('compare-button', 'n_clicks'),
        Input('explain-button', 'n_clicks')
    ],
    [
        State('options', 'value'),
        State('custom-prompt', 'value'),
        State('percentage-threshold', 'value'),
        State('diff-data-store', 'data'),
        State('ai-explanations-store', 'data')
    ]
)
def handle_buttons(compare_clicks, explain_clicks, options, custom_prompt, threshold, diff_data, ai_explanations):
    ctx = dash.callback_context

    if not ctx.triggered:
        # No button has been clicked yet
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, dash.no_update, dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Initialize outputs
    output_area = dash.no_update
    progress_output = dash.no_update
    new_diff_data = dash.no_update
    differences_count = dash.no_update
    explain_disabled = dash.no_update
    explain_progress = dash.no_update
    compared_images_store = dash.no_update

    if button_id == 'compare-button':
        if len(uploaded_files) < 2:
            return (
                html.Div("Please upload at least two PDF files for comparison."),
                '',
                None,
                '',
                True,
                dash.no_update,
                dash.no_update
            )
        
        use_ocr = 'ocr' in options

        # Get the first two PDFs for comparison
        filenames = list(uploaded_files.keys())
        pdf1_content = uploaded_files[filenames[0]]
        pdf2_content = uploaded_files[filenames[1]]

        # Decode PDF contents
        try:
            content_type1, content_string1 = pdf1_content.split(',', 1)
            pdf1_data = base64.b64decode(content_string1)
        except Exception as e:
            return (
                html.Div(f"Error decoding first PDF: {e}"),
                '',
                None,
                '',
                True,
                dash.no_update,
                dash.no_update
            )

        try:
            content_type2, content_string2 = pdf2_content.split(',', 1)
            pdf2_data = base64.b64decode(content_string2)
        except Exception as e:
            return (
                html.Div(f"Error decoding second PDF: {e}"),
                '',
                None,
                '',
                True,
                dash.no_update,
                dash.no_update
            )

        # Extract text with positions
        text_positions1 = extract_text_with_positions(pdf1_data, use_ocr=use_ocr)
        text_positions2 = extract_text_with_positions(pdf2_data, use_ocr=use_ocr)

        # Ensure threshold is a valid number
        try:
            threshold = float(threshold)
            if threshold < 0:
                threshold = 0.0
        except (ValueError, TypeError):
            threshold = 1.0  # Default to 1% if invalid input

        # Perform word-by-word comparison
        differences = word_by_word_compare(text_positions1, text_positions2, threshold)
        num_differences = len(differences)

        # Prepare summary with explanations for numeric differences
        differences_summary = []
        for diff in differences:
            if diff['difference_type'] in ['significant_numeric', 'insignificant_numeric', 'zero_to_nonzero']:
                # Calculate percentage change
                val1 = diff['value_file1']
                val2 = diff['value_file2']
                if diff['difference_type'] == 'significant_numeric' or diff['difference_type'] == 'insignificant_numeric':
                    num_val1 = convert_to_numeric(val1)
                    num_val2 = convert_to_numeric(val2)
                    if diff['difference_type'] == 'zero_to_nonzero':
                        explanation = "Changed from 0 to non-zero value."
                    elif num_val1 == 0 and num_val2 != 0:
                        explanation = "Infinite (0 to non-zero)"
                    elif num_val1 == 0 and num_val2 == 0:
                        explanation = "No change (0 to 0)"
                    elif num_val1 != 0:
                        percent_change = calculate_percent_change(num_val1, num_val2)
                        if isinstance(percent_change, float):
                            explanation = f"Percentage Change: {percent_change:.2f}%"
                        else:
                            explanation = percent_change  # e.g., "Infinite..." or "Undefined..."
                    else:
                        explanation = "Undefined (Division by zero)"
                
                elif diff['difference_type'] == 'zero_to_nonzero':
                    explanation = "Changed from 0 to non-zero value."
                else:
                    explanation = "Undefined change."
                
                diff['difference_explanation'] = explanation
            # For text differences, leave explanation empty to be filled by AI
            differences_summary.append(diff)

        # Store differences in diff-data-store
        new_diff_data = differences_summary

        # Display number of differences
        differences_count = f"Number of Differences Found: {num_differences}"

        # Highlight differences on images
        images1 = highlight_differences_on_images(pdf1_data, differences)
        images2 = highlight_differences_on_images(pdf2_data, differences)

        # Store compared images
        compared_images_store = images1 + images2  # Combine both sets of images

        # Display images side by side within a scrollable container
        image_elements = []
        for img1, img2 in zip(images1, images2):
            if img1 and img2:
                image_elements.append(
                    dbc.Row([
                        dbc.Col(html.Img(src='data:image/png;base64,' + img1, style={'width': '100%', 'height': 'auto'}), width=6),
                        dbc.Col(html.Img(src='data:image/png;base64,' + img2, style={'width': '100%', 'height': 'auto'}), width=6),
                    ], style={'margin-bottom': '20px'})
                )
            else:
                image_elements.append(
                    dbc.Row([
                        dbc.Col(html.Div("Image not available"), width=6),
                        dbc.Col(html.Div("Image not available"), width=6),
                    ])
                )

        # Combine image elements
        output_area = []
        output_area.extend(image_elements)

        # Determine if there are text differences to explain
        text_diffs = [diff for diff in differences_summary if diff['difference_type'] == 'text' and not diff['difference_explanation']]
        explain_disabled = True if not text_diffs else False

        # Update progress output
        progress_output = "Word-by-word comparison complete. Ready to explain text differences."

        return (
            html.Div(output_area),
            progress_output,
            new_diff_data,
            differences_count,
            explain_disabled,
            dash.no_update,  # No update to explain-progress-output
            compared_images_store  # Update the compared-images-store
        )

    elif button_id == 'explain-button':
        if not diff_data:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                True,
                "No differences available to explain.",
                dash.no_update
            )

        # Find text differences without explanations
        text_diffs = [diff for diff in diff_data if diff['difference_type'] == 'text' and not diff['difference_explanation']]
        if not text_diffs:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                True,
                "No text differences to explain.",
                dash.no_update
            )

        # Disable the button and show progress
        prompt_template = custom_prompt if custom_prompt.strip() else DEFAULT_PROMPT.strip()
        thread = threading.Thread(target=process_ai_explanations, args=(text_diffs, prompt_template))
        thread.start()

        explain_disabled = True
        explain_progress = "Processing explanations for text differences..."

        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            explain_disabled,
            explain_progress,
            dash.no_update
        )

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Callback to handle AI processing and update ai-explanations-store
@app.callback(
    Output('ai-explanations-store', 'data'),
    Input('interval-component', 'n_intervals'),
    State('ai-explanations-store', 'data')
)
def update_ai_explanations(n, existing_explanations):
    global ai_explanations_list
    if existing_explanations is None:
        existing_explanations = []

    # Transfer explanations from the global list to the store
    if ai_explanations_list:
        existing_explanations.extend(ai_explanations_list)
        ai_explanations_list = []

    return existing_explanations

# Callback to update the summary table with counts and percentages
@app.callback(
    Output('summary-table', 'children'),
    [Input('diff-data-store', 'data'),
     Input('ai-explanations-store', 'data')]
)
def update_summary_table(diff_data, ai_explanations):
    if not diff_data:
        return ''

    # Create a mapping from ID to AI explanations
    ai_explanation_map = {}
    if ai_explanations:
        for ai_expl in ai_explanations:
            ai_explanation_map[ai_expl['id']] = ai_expl['difference_explanation']

    # Update the differences with AI explanations
    for diff in diff_data:
        if not diff['difference_explanation'] and diff['id'] in ai_explanation_map:
            diff['difference_explanation'] = ai_explanation_map[diff['id']]

    # Create the counts DataFrame
    df_counts = pd.DataFrame(diff_data)
    counts = df_counts['difference_type'].value_counts().reset_index()
    counts.columns = ['Type', 'Count']
    counts['Percentage'] = (counts['Count'] / counts['Count'].sum()) * 100
    counts['Percentage'] = counts['Percentage'].apply(lambda x: f"{x:.2f}%")

    # Rename Difference Types for better readability
    counts['Type'] = counts['Type'].replace({
        'significant_numeric': 'Significant',
        'insignificant_numeric': 'Insignificant',
        'zero_to_nonzero': 'Zero to Non-Zero',
        'text': 'Text'
    })

    # Create counts table
    counts_table = dash_table.DataTable(
        data=counts.to_dict('records'),
        columns=[
            {'name': 'Type', 'id': 'Type'},
            {'name': 'Count', 'id': 'Count'},
            {'name': 'Percentage', 'id': 'Percentage'},
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '5px',
            'whiteSpace': 'normal',
            'height': 'auto',
            'width': 'auto',
            'maxWidth': '150px',
            'wordWrap': 'break-word'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_table={
            'minWidth': '200px',
            'maxWidth': '300px',
            'overflowX': 'auto'
        },
        page_size=10,  # Adjust as needed
        style_as_list_view=True
    )

    # Create the detailed summary table
    summary_table = create_summary_table(diff_data)

    # Arrange tables side by side
    summary_layout = dbc.Row([
        dbc.Col([
            html.H6("Difference Counts"),
            counts_table
        ], width=3),
        dbc.Col([
            html.H6("Detailed Differences"),
            summary_table
        ], width=9),
    ])

    return summary_layout

# Callback for Download Compared Images as PDF Button using Pillow
@app.callback(
    Output("download-pdf", "data"),
    Input("download-pdf-button", "n_clicks"),
    State("compared-images-store", "data"),
    prevent_initial_call=True,
)
def download_compared_images_as_pdf(n_clicks, compared_images):
    if n_clicks > 0 and compared_images:
        combined_images = []

        # Process images in pairs (side-by-side layout)
        for i in range(0, len(compared_images), 2):
            try:
                img1 = None
                img2 = None

                # Decode first image in the pair
                if i < len(compared_images):
                    img1_data = base64.b64decode(compared_images[i])
                    img1 = Image.open(io.BytesIO(img1_data))

                # Decode second image in the pair
                if i + 1 < len(compared_images):
                    img2_data = base64.b64decode(compared_images[i + 1])
                    img2 = Image.open(io.BytesIO(img2_data))

                # Ensure both images are in RGB mode
                if img1 and img1.mode != 'RGB':
                    img1 = img1.convert('RGB')
                if img2 and img2.mode != 'RGB':
                    img2 = img2.convert('RGB')

                # Determine the size of the combined image
                if img1 and img2:
                    total_width = img1.width + img2.width
                    max_height = max(img1.height, img2.height)
                elif img1:
                    total_width = img1.width
                    max_height = img1.height
                elif img2:
                    total_width = img2.width
                    max_height = img2.height
                else:
                    continue

                # Create a new blank image with the combined size
                combined_img = Image.new("RGB", (total_width, max_height), "white")

                # Paste the images side by side
                if img1:
                    combined_img.paste(img1, (0, 0))
                if img2:
                    combined_img.paste(img2, (img1.width if img1 else 0, 0))

                # Add to the list of combined images
                combined_images.append(combined_img)

            except Exception as e:
                print(f"Error processing image pair {i}-{i + 1}: {e}")
                continue

        if combined_images:
            # Save combined images into a single PDF
            pdf_buffer = BytesIO()
            first_image = combined_images[0]
            if len(combined_images) > 1:
                first_image.save(pdf_buffer, format='PDF', save_all=True, append_images=combined_images[1:])
            else:
                first_image.save(pdf_buffer, format='PDF')

            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            return dcc.send_bytes(pdf_bytes, "compared_images_side_by_side.pdf")
    return dash.no_update


if __name__ == '__main__':
    app.run_server(debug=False)
