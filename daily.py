import polars as pl
import click
import arrow
from cal_spread import cal_spread_dict
from tqdm import tqdm
from datetime import datetime

@click.command()
@click.option('--filename', help='Filename of the list to parse', required=True)
def daily_process(filename):
    today = arrow.now().date()
    tomorrow = arrow.now().shift(days=1).date()
    today = arrow.get(datetime(2025,7,17)).date()
    tomorrow = arrow.get(datetime(2025,7,18)).date()

    df_amc = (pl.read_parquet(filename)
        .filter(pl.col("Date") == today)
        .filter(pl.col("Time") == "AMC")
    )
    df_bmo = (pl.read_parquet(filename)
        .filter(pl.col("Date") == tomorrow)
        .filter(pl.col("Time") == "BMO")
    )
    df = df_amc.extend(df_bmo)

    symbols = df.get_column("Symbol").to_list()
    # process each symbol into a list
    list_content = []
    for symbol in tqdm(symbols):
        result,error = cal_spread_dict(symbol)
        if result is not None:
            list_content.append(result)

    df2 = pl.DataFrame(list_content)
    df2 = df2.filter( (pl.col("avg_volume") == "PASS") & (pl.col("iv30_rv30") == "PASS") & (pl.col("ts_slope_0_45") == "PASS") ).sort("earnings")
    df2 = (df2.join(df, left_on="symbol", right_on="Symbol", how="left")).sort("Date").drop("earnings")
    if df2.shape[0] > 0:
        print(df2.to_pandas())
    else:
        print("nothing.")

if __name__ == "__main__":
    daily_process()
