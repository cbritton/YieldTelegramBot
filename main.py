import os
from fredapi import Fred
import pandas as pd
import arrow
import telebot
import plotly.graph_objects as go
import os.path 
from dotenv import load_dotenv

load_dotenv()


telegram_bot_key = os.getenv('TELEGRAM_BOT_KEY')
fred_api_key = os.getenv('FRED_API_KEY')

bot = telebot.TeleBot(telegram_bot_key)
# treasury list
yield_ids = ['DGS1MO','DGS3MO','DGS6MO','DGS1','DGS2','DGS3','DGS5', 'DGS7','DGS10', 'DGS20', 'DGS30' ]

row_names = ['1 Month', '3 Month', '6 Month', '1 Year', '2 Year', '3 Year', '5 Year', '7 Year', '10 Year', '20 Year', '30 Year']

def fetch_yield_data():
  '''Get the yield curve data from FRED'''
  global yield_ids
  global row_names
  global fred_api_key
  
  fred = Fred(api_key=fred_api_key)
  end_date = arrow.now()
  start_date = end_date.shift(days=-5)
  
  data = pd.DataFrame([
    dict(
      id=x['id'],
      Expiry=x['name'],
      Date=x['series'].index.date[0],
      Rate=x['series'][0]) 
        for x in [
          dict(
            name=name,
            id=yld,
            series=fred.get_series(
              yld,
              observation_start=start_date.format('YYYY-MM-DD'), 
              observation_end=end_date.format('YYYY-MM-DD')).dropna().iloc[-1:]) 
          for yld,name in zip(yield_ids,row_names)
        ]
  ])
  return data

def get_yields_data():
  end_date = arrow.now()
  tmp_filename = f"data/yields_{end_date.format('YYYYMMDD')}.parquet"
  data = None

  # if the file exist, get it and send it, otherwise, create it
  if not os.path.exists(tmp_filename):
    data = fetch_yield_data()
    # save this for future requests
    data.to_parquet(tmp_filename)
  else:
    # load the data
    data = pd.read_parquet(tmp_filename)

  return data



@bot.message_handler(commands=["yield"])
def get_yields(message):

  data = get_yields_data()
  table_content = data[['Date','Expiry','Rate']] \
      .to_markdown(index=False)
  bot.send_message(
    message.chat.id, f'''<pre>{table_content}</pre>''', 
    parse_mode='HTML'
  )

@bot.message_handler(commands=["curve"])
def get_curve(message):
  # crate a filename for saving
  end_date = arrow.now()
  tmp_filename = f"images/yc_{end_date.format('YYYYMMDD')}.png"

  # if the file exist, get it and send it, otherwise, create it
  if not os.path.exists(tmp_filename):
    # get the data
    data = get_yields_data()
    
    # create the figure
    traces = []
    traces.append(
        go.Scatter(
            x=data['Expiry'], 
            y=data['Rate'],
            mode="lines"
        )
    )
    fig = go.Figure()
    _ = [fig.add_trace(trace) for trace in traces]
  
    last_reported_date = arrow.get(data['Date'].loc[0])
    title=f"FRED Yield Curve {last_reported_date.format('YYYY-MM-DD')}"
    fig.update_layout(
        autosize=False,
        width=800,
        height=600,
        title =title,
        template="plotly_dark",
        xaxis_title="Time to Maturity",
        yaxis_title="Yield (%)"
    )
    
    # save the figure
    fig.write_image(tmp_filename)

  # send the figure
  figure = open(tmp_filename, 'rb')
  bot.send_photo(message.chat.id, figure)


bot.polling()
