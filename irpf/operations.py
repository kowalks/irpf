"""Module for operations preprocessing."""
import math
import pandas as pd

from irpf.static import bonificacao


def preprocess_operations(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the operations dataframe."""
    def neg(row, col):
        """Negative value if is a debit operation."""
        if row['type'] == 'Debito':
            return -row[col]
        return row[col]

    df['quantity'] = df.apply(lambda row: neg(row, 'quantity'), axis=1)
    df['unit_price'] = df.apply(lambda row: neg(row, 'unit_price'), axis=1)
    df['total_price'] = df.apply(lambda row: neg(row, 'total_price'), axis=1)

    df = df.set_index(['ticker', 'date'])
    df = df.sort_index()

    # We gotta adjust bonificacao because the values are stored as NaN
    for idx, bon in bonificacao.items():
        df.loc[idx, 'unit_price'] = bon
        df.loc[idx, 'total_price'] = bon * df.loc[idx, 'quantity'].iloc[0]

    def smart_cumsum(df):
        """Basically cumsum with some regards.
        For some reasom, sometimes 'Atualização' refers to name changes (so, quantity should not
        update) and other times 'Atualização' should sum in the quantity, because it represents
        a new buy/sell.

        Also, 'Fração em Ativos' should be treated specially.
        """
        lst = []
        last_quant = 0
        for _, row in df.iterrows():
            if (row['description'] == 'Atualização') and (row['quantity'] == last_quant):
                last_quant = 0
            if row['description'] == 'Fração em Ativos':
                last_quant = math.floor(last_quant)
            last_quant += row['quantity']
            lst.append(last_quant)
        return pd.DataFrame(lst, index=df.index.get_level_values(1), columns=['cum_quant'])

    df['cum_quant'] = df.groupby(level=0).apply(smart_cumsum)

    def compute_pm(df: pd.DataFrame):
        """Computes PM based on buy/sell operation. If we sell all stocks, PM should be zero."""
        lst = []
        last_pm = 0
        for _, row in df.iterrows():
            if last_pm == 0:
                last_pm = row['total_price']/row['quantity']
            elif row['cum_quant'] == 0:
                last_pm = 0
            elif row['unit_price'] > 0:
                total_price = (row['cum_quant'] - row['quantity']) * last_pm + row['total_price']
                last_pm = total_price / row['cum_quant']
            lst.append(last_pm)
        return pd.DataFrame(lst, index=df.index.get_level_values(1), columns=['pm'])

    df['pm'] = df.groupby(level=0).apply(compute_pm)
    return df

def filter_by_year(df: pd.DataFrame):
    df = df.reset_index()
    df['year'] = df['date'].dt.year
    df = df.groupby(['year', 'ticker'])[['cum_quant', 'pm']].last()
    df = df[df['cum_quant'] != 0]
    df['total_price'] = df['cum_quant'] * df['pm']
    df = df.round(decimals=2)
    return df
