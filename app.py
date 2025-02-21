from flask import Flask, render_template
import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from pymongo import MongoClient
from dash.dependencies import Input, Output

# Initialize Flask app
app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
dbs = ["crime", "environment", "health_issues", "technology_&_infrastructure", "cleaniness"]

# Function to fetch live data from MongoDB
def fetch_data():
    all_data = []
    for db_name in dbs:
        db = client[db_name]
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            for doc in collection.find():
                all_data.append({"category": collection_name, "database": db_name, "text": doc.get("text", "")})
    
    if all_data:
        return pd.DataFrame(all_data)
    else:
        return pd.DataFrame(columns=["category", "database", "text"])

# Initialize Dash app
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash/')

# Dash Layout
dash_app.layout = html.Div([
    html.H1("Live MongoDB Data Dashboard", style={'textAlign': 'center', 'color': '#ffffff'}),

    html.Div([
        dcc.Graph(id='pie-chart', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id='bar-chart', style={'width': '48%', 'display': 'inline-block'}),
    ]),
    html.Div([
        dcc.Graph(id='line-chart', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id='histogram', style={'width': '48%', 'display': 'inline-block'}),
    ]),

    # Interval component to update every 5 seconds
    dcc.Interval(
        id='interval-component',
        interval=5000,  # 5000ms = 5 seconds
        n_intervals=0
    )
], style={'backgroundColor': '#222', 'padding': '20px', 'color': 'white'})

# Callbacks to update charts dynamically
@dash_app.callback(
    [Output('pie-chart', 'figure'),
     Output('bar-chart', 'figure'),
     Output('line-chart', 'figure'),
     Output('histogram', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_charts(n_intervals):
    df = fetch_data()

    if not df.empty:
        df_count = df.groupby("category").size().reset_index(name="count")

        pie_chart = px.pie(df_count, names='category', values='count', title='Category Distribution')
        bar_chart = px.bar(df_count, x='category', y='count', title='Bar Graph - Issue Count')
        line_chart = px.line(df_count, x='category', y='count', title='Line Graph - Trends')
        histogram = px.histogram(df_count, x='category', y='count', title='Histogram - Frequency')

        return pie_chart, bar_chart, line_chart, histogram
    else:
        return {}, {}, {}, {}

# Define Flask route
@app.route('/')
def index():
    return render_template('index.html')

# Run Flask app on custom port
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)  # Change the port if needed
