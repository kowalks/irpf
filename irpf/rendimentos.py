"""Module for rendimento preprocessing."""
import pandas as pd


def preprocess_rendimentos(df: pd.DataFrame) -> pd.DataFrame:
    df['year'] = df['date'].dt.year
    df = df.pivot_table(
        index=['year', 'ticker'],
        columns='description',
        values='total_price',
        aggfunc='sum',
        dropna=True,
        fill_value=0
    )
    return df
