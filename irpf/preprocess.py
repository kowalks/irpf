"""Preprocesses the data."""
import os
import pandas as pd


def read_data(data_dir='data') -> pd.DataFrame:
    """Reads all excel files in data_dir and returns a single dataframe."""
    dfs = []
    excel_files = (file for file in os.listdir(data_dir) if file.endswith('.xlsx'))
    for file in excel_files:
        path = os.path.join(data_dir, file)
        df = pd.read_excel(path)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def convert_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Converts rows to the correct type."""
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
    df['ticker'] = df['product'].str.split(' ', expand=True)[0]
    return df


def split_description(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Splits the dataframe into multiple dataframes, each one with a different description."""
    dsc = ['Atualização', 'Transferência - Liquidação', 'Bonificação em Ativos', 'Fração em Ativos']
    op = df[df['description'].isin(dsc)].copy()

    dsc = ['Rendimento', 'Juros Sobre Capital Próprio', 'Dividendo']
    rd = df[df['description'].isin(dsc)].copy()
    return {'operations': op, 'rendimentos': rd}
