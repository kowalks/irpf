from irpf.preprocess import read_data, convert_rows, split_description
from irpf.operations import preprocess_operations, filter_by_year
from irpf.rendimentos import preprocess_rendimentos


if __name__ == '__main__':
    df = read_data()
    df = convert_rows(df)
    dfs = split_description(df)

    op = dfs['operations']
    op = preprocess_operations(op)
    op = filter_by_year(op)

    rd = dfs['rendimentos']
    rd = preprocess_rendimentos(rd)
