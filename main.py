import yfinance as yf
import pandas_ta as ta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
from PyQt5 import QtWidgets, QtWebEngineWidgets
import sys

# Parameters
rsi_period = 14
rsi_threshold = 40
sma_length = 14

import requests
import pandas as pd

# URL of the Nifty 500 companies list
url = 'https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv'

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Check if request was successful

    # Save CSV content to a local file
    with open('ind_nifty500list.csv', 'wb') as file:
        file.write(response.content)

    # Load CSV file into a DataFrame
    nifty500_data = pd.read_csv('ind_nifty500list.csv')
    nifty500_tickers = [f"{symbol}.NS" for symbol in nifty500_data['Symbol']]
    print("Downloaded Nifty 500 tickers successfully!")

except Exception as e:
    print("Error downloading or reading Nifty 500 symbols:", e)


# Function to calculate RSI and check if it's below the threshold
def get_low_rsi_stocks(tickers, rsi_period, rsi_threshold, sma_length):
    low_rsi_stocks = []
    
    for ticker in tickers:
        try:
            # Fetch weekly data for each stock
            stock_data = yf.download(ticker, period="6mo", interval="1wk")
            
            # Ensure we have enough data
            if len(stock_data) < rsi_period:
                continue

            # Calculate RSI with pandas_ta
            stock_data['RSI'] = ta.rsi(stock_data['Close'], length=rsi_period)
            
            # Calculate SMA of the RSI
            stock_data['RSI_SMA'] = stock_data['RSI'].rolling(window=sma_length).mean()
            
            # Check if the last RSI value is below the threshold
            if stock_data['RSI'].iloc[-1] < rsi_threshold:
                low_rsi_stocks.append(ticker)
        
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
    
    return low_rsi_stocks

# Get list of low RSI stocks
low_rsi_stocks = get_low_rsi_stocks(nifty500_tickers, rsi_period, rsi_threshold, sma_length)

print(low_rsi_stocks)

# Function to create and return the plotly figure
def create_plot(tickers, rsi_period=14):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Candlestick Chart", "RSI")
    )
    
    for i, ticker in enumerate(tickers):
        stock_data = yf.download(ticker, period="6mo", interval="1wk")
        stock_data['RSI'] = ta.rsi(stock_data['Close'], length=rsi_period)

        fig.add_trace(
            go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name=f"{ticker} Candlestick",
                visible=(i == 0)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data['RSI'],
                mode="lines",
                name=f"{ticker} RSI",
                visible=(i == 0)
            ),
            row=2, col=1
        )

    steps = []
    for i, ticker in enumerate(tickers):
        step = dict(
            method="update",
            args=[
                {"visible": [False] * (2 * len(tickers))},
                {"title": f"{ticker} Candlestick and RSI"}
            ],
        )
        step["args"][0]["visible"][2 * i] = True
        step["args"][0]["visible"][2 * i + 1] = True
        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Stock: "},
        pad={"t": 50},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders,
        title="Candlestick and RSI for Selected Stocks",
        xaxis_title="Date",
        yaxis_title="Price",
        yaxis2_title="RSI",
        height=800
    )
    fig.update_layout(template="plotly_dark", showlegend=False)
    
    return fig

# PyQt5 application to display plotly plot in a separate window
class PlotlyWindow(QtWidgets.QMainWindow):
    def __init__(self, fig):
        super().__init__()
        self.setWindowTitle("Interactive Stock Chart with RSI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Convert Plotly figure to HTML
        html = pio.to_html(fig, full_html=False)
        
        # Set up a WebEngineView for rendering HTML content
        web_view = QtWebEngineWidgets.QWebEngineView()
        web_view.setHtml(html)
        self.setCentralWidget(web_view)

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Create the Plotly figure
    fig = create_plot(low_rsi_stocks, rsi_period=14)
    
    # Show the figure in a PyQt window
    main_window = PlotlyWindow(fig)
    main_window.show()
    
    sys.exit(app.exec_())

# Run the application
if __name__ == "__main__":
    main()
