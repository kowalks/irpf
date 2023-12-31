import pandas as pd
import yfinance as yf

def make_portfolio(df: pd.DataFrame):
    """Makes a portfolio from operations dataframe."""
    tickers = df.index.get_level_values(0).unique().to_list()
    tickers = [x + '.SA' for x in tickers]

    raw_data : pd.DataFrame = yf.download(tickers, period='5y', auto_adjust=False)
    data = (raw_data['Close']
        .rename(lambda x: x[:-3], axis=1)
        .ffill()
        .fillna(0)
    )

    df = (df
        .pivot_table(columns='ticker', values='cum_quant', index='date')
        .sort_index()
        .reindex(raw_data['Close'].index)
        .ffill()
        .fillna(0)
    )

    quantity = df*data
    quantity.sum(axis=1).plot()

    return quantity.sum(axis=1)
