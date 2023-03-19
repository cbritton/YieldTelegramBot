import os
import arrow
import telebot
import plotly.graph_objects as go
import os.path 
from common import get_yields_data
from config import data_content
from config import telegram_bot_key


bot = telebot.TeleBot(telegram_bot_key)

@bot.message_handler(commands=["yield"])
def get_yields(message):
    '''Bot response handler to print the yields table.'''
    data, _ = get_yields_data(data_content)
    table_content = data[['Date','Expiry','Rate']] \
        .to_markdown(index=False)
    bot.send_message(
        message.chat.id, f'''<pre>{table_content}</pre>''', 
        parse_mode='HTML'
    )

@bot.message_handler(commands=["curve"])
def get_curve(message):
    '''Bot response handler to return the curve image.'''
    # crate a filename for saving
    tmp_filename = f"images/yc.png"

    # get the data and update indicator
    data, update = get_yields_data(data_content)

    # if the file does not exist, create it and save it
    if update or not os.path.exists(tmp_filename):
        
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
        
        print("new image created")
        # save the figure
        fig.write_image(tmp_filename)

    # send the figure
    figure = open(tmp_filename, 'rb')
    bot.send_photo(message.chat.id, figure)


print("Ready.")
bot.polling()
