# Anna's Test Program | Third Program Test Program | 7/16/26
Being young and getting into investing, the best way I thought of sticking to my goals was being able to see continuous progress. So, I made a program to visualize my stock portfolio so I can see the gains I make week-to-week; additionally, I enjoyed having custom colors for my portfolio and I have plans to add more features soon.

# Python Stock Portfolio Tracker

A small command-line portfolio tracker that stores holdings in CSV, downloads
current market prices with `yfinance`, and creates a portfolio-allocation donut
chart with Matplotlib.

## Features

- Add, remove, and update stock holdings.
- Refresh prices from Yahoo Finance.
- Display each holding's value and percentage of the portfolio.
- Show or save a gradient donut chart.
- Use either an interactive menu or command-line commands.

## Setup

Python 3.10 or newer is recommended.

```bash
git clone YOUR_REPOSITORY_URL
cd python_stock_tracker
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The program creates a private `portfolio.csv` automatically the first time it
runs. You can also copy `portfolio.example.csv` to `portfolio.csv` if you want
sample data. The real portfolio file is excluded from Git.

## Run the interactive menu

```bash
python3 main.py
```

## Commands

```bash
# Add a holding: ticker, shares, average cost per share
python3 main.py add AAPL 2 190.50

# Fetch the latest prices
python3 main.py refresh

# Print values and allocation percentages
python3 main.py view

# Change the total shares owned
python3 main.py shares AAPL 3.5

# Remove a holding
python3 main.py remove AAPL

# Open the allocation chart
python3 main.py chart

# Save the chart as an image
python3 main.py chart --save portfolio-chart.png
```

Run `refresh` before `view` or `chart` when you want current prices.

## CSV format

```csv
ticker,shares,average_cost,current_price
AAPL,2,190.50,null
```

`current_price` is filled when the refresh command succeeds.

## Project structure

```text
main.py                 Interactive menu and command-line interface
portfolio.py            CSV storage, portfolio actions, and price fetching
portfolio_chart.py      Matplotlib donut-chart rendering
portfolio.example.csv   Safe example data
requirements.txt        Python dependencies
tests/                   Offline unit tests
```

## Tests

The tests do not contact Yahoo Finance.

```bash
python3 -m unittest discover -s tests
```
