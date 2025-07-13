import polars as pl
from ze import ZacksEarnings
import click
import time
import random
from tqdm import tqdm

def fetch_earnings_date(symbol: str):
    content = {}
    try:
        # Test next earnings estimate
        earnings = ZacksEarnings.get_next_earnings_estimate(symbol)
        if len(earnings) > 0:
            earnings_time, next_earnings_date = earnings[0]
            content["Symbol"] = symbol
            content["Date"] = next_earnings_date
            content["Time"] = earnings_time
        
    except Exception as e:
        pass

    return content

@click.command()
@click.option('--filename', help='Filename of the list to parse', required=True)
def process_list(filename):
    df = pl.read_csv(filename, truncate_ragged_lines=True, skip_lines=3)
    symbols = df.get_column("Symbol").to_list()
    # process each symbol into a list
    list_content = []
    for symbol in tqdm(symbols):
        # for each symbol in the file, check zack's for the earning date and time
        content = fetch_earnings_date(symbol)
        list_content.append(content)
        # wait random time so that zack's doesn't block us
        time.sleep(random.uniform(1.1, 4.5))
    # build the dataframe
    df2 = pl.DataFrame(list_content).with_columns(pl.col("Date").cast(pl.Date))
    # save to file
    filename = "latest_er_table.parquet"
    df2.write_parquet(filename)
    print(f"Saved content to '{filename}'")

if __name__ == "__main__":
    process_list()
