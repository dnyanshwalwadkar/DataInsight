import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import io
import base64
import json

# Initialize the Dash app
app = dash.Dash(__name__)


# --- Functions for Analysis and Plotting ---
def perform_placeholder_analysis(df):
    """
    This is a placeholder function for your actual analysis logic.
    It simulates generating a report and a simple plot.
    """
    if df is None or df.empty:
        return "No data to analyze.", {}

    report_text = f"""
    ## Analysis Report

    ### Domain Overview
    This is a placeholder domain overview generated from a dataset with {len(df.columns)} columns and {len(df)} rows.

    ### Data Health
    - The dataset has {df.isnull().sum().sum()} missing values.
    - There are {df.duplicated().sum()} duplicate rows.

    ### Key Insights
    - Insight 1: A key placeholder insight.
    - Insight 2: Another key placeholder insight.
    """

    # Generate a placeholder plot
    if 'price' in df.columns and 'category' in df.columns:
        fig = px.box(df, x='category', y='price', title='Placeholder Price Distribution by Category')
    elif 'age' in df.columns:
        fig = px.histogram(df, x='age', title='Placeholder Age Distribution')
    else:
        fig = {}  # Return an empty figure if no suitable columns are found

    return report_text, fig


# --- Dash Application Layout ---
app.layout = html.Div(
    style={'font-family': 'Arial, sans-serif', 'margin': '20px'},
    children=[
        html.H1("ALL Insights into data by single click", style={'text-align': 'center'}),
        html.P("Upload your data to get a comprehensive report and a conversational assistant.",
               style={'text-align': 'center'}),

        # File Upload Component
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select a File')
            ]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
            },
            multiple=False
        ),

        # Hidden storage for the DataFrame
        dcc.Store(id='stored-dataframe'),
        dcc.Store(id='report-output'),
        dcc.Store(id='plot-output'),

        html.Hr(),

        # Button to trigger analysis
        html.Button('Analyze Data', id='analyze-button', n_clicks=0, style={'margin-bottom': '20px'}),

        # Loading spinner for analysis
        dcc.Loading(
            id="loading-analysis",
            type="circle",
            children=[
                html.Div(id='analysis-output-container')
            ]
        ),

        html.Hr(),

        # Placeholder for Chat Interface
        html.H2("Chat with your Data"),
        html.Div(id='chat-history',
                 style={'height': '300px', 'overflow-y': 'scroll', 'border': '1px solid #ccc', 'padding': '10px',
                        'margin-bottom': '10px'}),
        dcc.Input(id='chat-input', type='text', placeholder='Ask a question...', style={'width': '80%'}),
        html.Button('Send', id='chat-send-button', n_clicks=0),
    ]
)


# --- Callbacks ---

# Callback to handle file upload and store the data
@app.callback(
    Output('stored-dataframe', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)

            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xlsx' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return dash.no_update

            # Store the DataFrame in a JSON serializable format
            return df.to_json(date_format='iso', orient='split')

        except Exception as e:
            print(e)
            return dash.no_update
    return dash.no_update


# Callback to trigger the analysis and store the results
@app.callback(
    [Output('report-output', 'data'),
     Output('plot-output', 'data')],
    Input('analyze-button', 'n_clicks'),
    State('stored-dataframe', 'data'),
    prevent_initial_call=True
)
def run_analysis(n_clicks, json_data):
    if n_clicks > 0 and json_data:
        df = pd.read_json(json_data, orient='split')
        report_text, fig = perform_placeholder_analysis(df)

        # Store the report text and plot figure data
        return report_text, fig
    return dash.no_update, dash.no_update


# Callback to display the analysis results
@app.callback(
    Output('analysis-output-container', 'children'),
    [Input('report-output', 'data'),
     Input('plot-output', 'data')]
)
def display_analysis_results(report_text, fig):
    if report_text is None:
        return html.P("Please upload a file and click 'Analyze Data'.")

    return html.Div([
        dcc.Markdown(report_text),
        html.H2("Visualizations"),
        dcc.Graph(figure=fig)
    ])


# Callback for chat interaction (to be implemented with Gemini API)
@app.callback(
    Output('chat-history', 'children'),
    Input('chat-send-button', 'n_clicks'),
    State('chat-input', 'value'),
    prevent_initial_call=True
)
def update_chat(n_clicks, user_message):
    if user_message:
        # Placeholder for Gemini API call and response
        # In a real app, this is where you'd call a function similar to your chat_plot_request
        # and get a response or a plot.

        # Placeholder logic:
        new_chat_message = f"User: {user_message}"

        # This is a basic way to update, in a real app you'd append to a list in a store
        return html.P(new_chat_message)
    return dash.no_update


# Run the app
if __name__ == '__main__':
    app.run(debug=True)