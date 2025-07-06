import os
import uuid
import telebot
import os.path 
from common import get_yields_data
from common import create_figure
from common import shorthand_names
from common import get_yield_spread
from common import create_spread_figure
from config import data_content
from config import telegram_bot_key
from cal_spread import cal_spread

bot = telebot.TeleBot(telegram_bot_key)

def map_request_to_fred_key(request):
    # Xm -> DSGXMO
    # Zy -> DSGZ
    id = None
    if "m" in request.lower():
        id = f"DGS{request.lower().split('m')[0]}MO"
    elif "y" in request.lower():
        id = f"DGS{request.lower().split('y')[0]}"
    return id

@bot.message_handler(commands=["spread"])
def yield_spread_handeler(message):
    request = message.text.split()
    # format should be: /comapre X Y # where # is the number of months back in time to get, default is 12
    if len(request) < 3:
        response = f"Incomplete request. Format: '/spread X Y N' where X and Y are one of {','.join(shorthand_names)} an N is the number of months as a number."
        bot.send_message( message.chat.id, response)
    else:
        first = request[1]
        second = request[2]
        months = 12
        done = False
        if len(request) >= 4:
            months = request[3]
            try:
                months = abs(int(months))
            except:
                response = f"Month value is not understood: '{request[3]}'"
                bot.send_message( message.chat.id, response)
                done = True
        if first.lower() == second.lower():
            response = "Please enter 2 different maturities"
            bot.send_message( message.chat.id, response)
            return
        # first and second must be one of the shorthand names
        if first.lower() not in shorthand_names:
            response = f"Unknown value: '{first}'"
            bot.send_message( message.chat.id, response)
            done = True
        if second.lower() not in shorthand_names:
            response = f"Unknown value: '{second}'"
            bot.send_message( message.chat.id, response)
            done = True
        if not done:
            # get the fred id from the first and second parameter
            first_id = map_request_to_fred_key(first)
            second_id = map_request_to_fred_key(second)
            # get the fred data for both
            df = get_yield_spread(first_id, second_id, months)
            # plot the curve
            fig = create_spread_figure(df, first, second)

            # save the figrue to a file
            tmp_filename = f"images/spread_{first}_{second}_{str(uuid.uuid4())}.png"

            fig.write_image(tmp_filename)

            # return the figure
            figure = open(tmp_filename, 'rb')
            bot.send_photo(message.chat.id, figure)


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

@bot.message_handler(commands=["caltrade"])
def get_yields(message):
    request = message.text.split()
    '''Bot response handler to print the calendar spread trade information.'''
    if len(request) < 2:
        response = f"Incomplete request. Format: '/caltrade S' where S is a ticker symbol, i.e. AAPL."
        bot.send_message( message.chat.id, response)
    else:
        symbol = request[1]
        content, error = cal_spread(symbol)
        if content is not None:
            bot.send_message(
                message.chat.id, f'''<pre>{content}</pre>''', 
                parse_mode='HTML'
            )
        else:
            bot.send_message(
                message.chat.id, f'''<pre>{error}</pre>''',
                parse_mode='HTML'
            )

@bot.message_handler(commands=["curve"])
def get_curve(message):
    '''Bot response handler to return the curve image.'''
    # crate a filename for saving
    tmp_filename = r"images/yc.png"

    # get the data and update indicator
    data, update = get_yields_data(data_content)

    # if update == True then create it
    # if update == False AND the graph file does not exists, then create it
    if update or (not update and not os.path.exists(tmp_filename)):
        create_figure(data, tmp_filename)       
 
    # send the figure
    figure = open(tmp_filename, 'rb')
    bot.send_photo(message.chat.id, figure)


print("Ready.")
while True:
    try:
        bot.polling()
    except Exception as e:
        print(e) 
