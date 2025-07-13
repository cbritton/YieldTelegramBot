import polars as pl
import polars.selectors as cs
import click
from cal_spread import cal_spread_dict
from tqdm import tqdm

@click.command()
@click.option('--filename', help='Filename of the list to parse', required=True)
def parse_list(filename):
    #df = pl.read_csv(filename, truncate_ragged_lines=True, skip_lines=3)
    df_list = pl.read_parquet(filename)
    symbols = df_list.get_column("Symbol").to_list()
    # process each symbol into a list
    list_content = []
    for symbol in tqdm(symbols):
        result,error = cal_spread_dict(symbol)
        if result is not None:
            list_content.append(result)

    df = pl.DataFrame(list_content)
    df = df.filter( (pl.col("avg_volume") == "PASS") & (pl.col("iv30_rv30") == "PASS") & (pl.col("ts_slope_0_45") == "PASS") ).sort("earnings")
    df = (df.join(df_list, left_on="symbol", right_on="Symbol", how="left")).sort("earnings")
    if df.shape[0] > 0:
        print(df)
    else:
        print("nothing.")
        

if __name__ == "__main__":
    parse_list()
