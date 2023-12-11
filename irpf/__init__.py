import math
import pandas as pd
import os

bonificacao = {
    ('ITSA4', '2021-12-22'): 18.891662,
    ('ITSA4', '2022-11-14'): 13.65162423,
    ('ITSA4', '2023-11-29'): 17.917246,
    ('PSSA3', '2021-10-22'): 12.37267626833,
}


def read_data(data_dir='data') -> pd.DataFrame:
    dfs = []
    for file in os.listdir(data_dir):
        path = os.path.join(data_dir, file)
        df = pd.read_excel(path)
        dfs.append(df)
        
    return pd.concat(dfs, ignore_index=True)


def convert_rows(df: pd.DataFrame) -> pd.DataFrame:
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
    df['Quantidade'] = df['Quantidade']
    df['Preço unitário'] = pd.to_numeric(df['Preço unitário'], errors='coerce')
    df['Valor da Operação'] = pd.to_numeric(df['Valor da Operação'], errors='coerce')
    df = df.rename(columns={
        'Entrada/Saída': 'type',
        'Data': 'date',
        'Movimentação': 'description',
        'Quantidade': 'quantity',
        'Preço unitário': 'unit_price',
        'Valor da Operação': 'total_price',
        'Instituição': 'institution',
        'Produto': 'product',
    })
    return df


def split_description(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Buy / sell operations
    desc = ['Atualização', 'Transferência - Liquidação', 'Bonificação em Ativos', 'Fração em Ativos']
    df = df[df['description'].isin(desc)].copy()
    return {'operations': df}


def preprocess_operations(df: pd.DataFrame) -> pd.DataFrame:
    df['ticker'] = df['product'].str.split(' ', expand=True)[0]
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
        For some reasom, sometimes 'Atualização' refers to name changes (so, quantity should not update)
        and other times 'Atualização' should sum in the quantity, because it represents a new buy/sell.

        Also, 'Fração em Ativos' should be treated specially.
        """
        lst = []
        last_quant = 0
        for _, row in df.iterrows():
            if (row['description'] == 'Atualização') and (row['quantity'] == last_quant):
                last_quant = 0
            if (row['description'] == 'Fração em Ativos'):
                last_quant = math.floor(last_quant)
            last_quant += row['quantity']
            lst.append(last_quant)
        return pd.DataFrame(lst, index=df.index.get_level_values(1), columns=['cum_quant'])

    df['cum_quant'] = df.groupby(level=0).apply(smart_cumsum)

    def compute_pm(df):
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



df = read_data()
df = convert_rows(df)
dfs = split_description(df)

op = dfs['operations']
op = preprocess_operations(op)

op = op.groupby(level=0)[['cum_quant', 'pm']].last()
op = op[op['cum_quant'] != 0]
op['total_price'] = op['cum_quant'] * op['pm']
op.round(decimals=2)