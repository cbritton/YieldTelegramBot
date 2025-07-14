import polars as pl
import click
import arrow
from cal_spread import cal_spread_dict
from datetime import datetime
import telebot

def daily_process(filename:str, start_date:arrow, end_date:arrow, show_passed:bool = True) -> pl.DataFrame:

    df_amc = (pl.read_parquet(filename)
        .filter(pl.col("Date") >= start_date.date())
        #.filter(pl.col("Time") == "AMC")
    )
    df_bmo = (pl.read_parquet(filename)
        .filter(pl.col("Date") <= end_date.date())
        #.filter(pl.col("Time") == "BMO")
    )
    df = df_amc.extend(df_bmo)

    symbols = df.get_column("Symbol").to_list()
    # process each symbol into a list
    list_content = []
    for symbol in symbols:
        result,error = cal_spread_dict(symbol)
        if result is not None:
            list_content.append(result)

    df2 = pl.DataFrame(list_content)
    if show_passed:
        df2 = df2.filter( (pl.col("avg_volume") == "PASS") & (pl.col("iv30_rv30") == "PASS") & (pl.col("ts_slope_0_45") == "PASS") ).sort("earnings")
    df2 = (df2.join(df, left_on="symbol", right_on="Symbol", how="left")).sort("Date").drop("earnings")
    return df2

@click.command()
@click.option('--filename', help='Filename of the list to parse', required=True)
def daily_process_cmd(filename):
    start_date = arrow.now()
    end_date = arrow.now().shift(days=8)
    df2 = daily_process(filename,start_date,end_date,show_passed=False)
    #bot = telebot.TeleBot(telegram_bot_key)
    if df2.shape[0] > 0:
        print(df2.to_pandas())
        df2.write_parquet("daily.parquet")
    else:
        print("nothing.")
    #bot.send_message(chat_id=chat_id, text="Hello, this is a test message!")

if __name__ == "__main__":
    daily_process_cmd()
