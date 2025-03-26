# --- app.py ---
import pandas as pd
from flask import Flask, render_template_string, request, send_file
from datetime import datetime, timedelta
from fetch_data import fetch_stock_data
import os
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.layouts import column, Spacer
from bokeh.models import Span, HoverTool
from bokeh.resources import CDN

app = Flask(__name__)

TICKER_OPTIONS = ["TSLQ", "TSLL"]

def default_date_range():
    end_date = datetime.today()
    start_date = end_date - timedelta(days=14)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

@app.route("/", methods=["GET"])
def index():
    selected_ticker = request.args.get("ticker", "TSLQ")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_date_range()

    filename = fetch_stock_data(selected_ticker, start=start_date, end=end_date)

    if filename is None or not os.path.exists(filename):
        return f"<h2>No data found for {selected_ticker} between {start_date} and {end_date}</h2>"

    df = pd.read_csv(filename)
    df['Date'] = pd.to_datetime(df['Date'])

    from bokeh.models import ColumnDataSource
    source = ColumnDataSource(df)

    # גרף מחירים עם רצועות בולינג'ר
    p1 = figure(x_axis_type="datetime", height=300, sizing_mode="stretch_width", title=f"{selected_ticker} - Price & Bollinger Bands", tools="pan,wheel_zoom,box_zoom,reset,save,hover")
    p1.line('Date', 'Close', legend_label="Close", color="black", source=source)
    if 'Bollinger Top' in df:
        p1.line('Date', 'Bollinger Top', legend_label="Bollinger Top", color="red", source=source)
    if 'Bollinger Mid' in df:
        p1.line('Date', 'Bollinger Mid', legend_label="Bollinger Mid", color="blue", source=source)
    if 'Bollinger Bottom' in df:
        p1.line('Date', 'Bollinger Bottom', legend_label="Bollinger Bottom", color="green", source=source)
    p1.legend.location = "top_left"

    # גרף RSI
    p2 = figure(x_axis_type="datetime", height=200, sizing_mode="stretch_width", title="RSI", tools="pan,wheel_zoom,box_zoom,reset,save,hover")
    if 'RSI' in df:
        p2.line('Date', 'RSI', color="orange", source=source)
        p2.add_layout(Span(location=70, dimension='width', line_dash='dashed', line_color='gray'))
        p2.add_layout(Span(location=30, dimension='width', line_dash='dashed', line_color='gray'))

    # גרף CCI
    p3 = figure(x_axis_type="datetime", height=200, sizing_mode="stretch_width", title="CCI", tools="pan,wheel_zoom,box_zoom,reset,save,hover")
    if 'CCI' in df:
        p3.line('Date', 'CCI', color="purple", source=source)

    layout = column(p1, Spacer(height=20), p2, Spacer(height=20), p3, sizing_mode="stretch_width")
    script, div = components(layout)

    return render_template_string("""
    <html>
<head>
    <title>Stock Analysis with Bokeh</title>
    {{ resources|safe }}
    {{ script|safe }}
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .container {
            max-width: 1200px;
            margin: auto;
            padding: 20px;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>Analyze Stock Data</h1>
        <form method="get">
            <label for="ticker">Select Ticker:</label>
            <select name="ticker">
                {% for t in tickers %}
                    <option value="{{ t }}" {% if t == selected_ticker %}selected{% endif %}>{{ t }}</option>
                {% endfor %}
            </select><br><br>

            <label for="start_date">Start Date:</label>
            <input type="date" name="start_date" value="{{ start_date }}">

            <label for="end_date">End Date:</label>
            <input type="date" name="end_date" value="{{ end_date }}">

            <button type="submit">Analyze</button>
        </form>

        <form method="get" action="/download">
            <input type="hidden" name="file" value="{{ filename }}">
            <button type="submit">Download CSV</button>
        </form>

        <hr>
        {{ div|safe }}
    </div>
</body>
</html>
    """, script=script, div=div, tickers=TICKER_OPTIONS, selected_ticker=selected_ticker,
           start_date=start_date, end_date=end_date, filename=filename, resources=CDN.render())

@app.route("/download")
def download():
    file_path = request.args.get("file")
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)
