
import yfinance as yf
from datetime import datetime, timedelta
from scipy.interpolate import interp1d
import numpy as np
import warnings
import arrow
warnings.simplefilter(action='ignore', category=FutureWarning)

def filter_dates(dates):
    today = datetime.today().date()
    cutoff_date = today + timedelta(days=45)
    
    sorted_dates = sorted(datetime.strptime(date, "%Y-%m-%d").date() for date in dates)

    arr = []
    for i, date in enumerate(sorted_dates):
        if date >= cutoff_date:
            arr = [d.strftime("%Y-%m-%d") for d in sorted_dates[:i+1]]  
            break
    
    if len(arr) > 0:
        if arr[0] == today.strftime("%Y-%m-%d"):
            return arr[1:]
        return arr

    raise ValueError("No date 45 days or more in the future found.")


def yang_zhang(price_data, window=30, trading_periods=252, return_last_only=True):
    log_ho = (price_data['High'] / price_data['Open']).apply(np.log)
    log_lo = (price_data['Low'] / price_data['Open']).apply(np.log)
    log_co = (price_data['Close'] / price_data['Open']).apply(np.log)
    
    log_oc = (price_data['Open'] / price_data['Close'].shift(1)).apply(np.log)
    log_oc_sq = log_oc**2
    
    log_cc = (price_data['Close'] / price_data['Close'].shift(1)).apply(np.log)
    log_cc_sq = log_cc**2
    
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    
    close_vol = log_cc_sq.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    open_vol = log_oc_sq.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    window_rs = rs.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    k = 0.34 / (1.34 + ((window + 1) / (window - 1)) )
    result = (open_vol + k * close_vol + (1 - k) * window_rs).apply(np.sqrt) * np.sqrt(trading_periods)

    if return_last_only:
        return result.iloc[-1]
    else:
        return result.dropna()
    

def build_term_structure(days, ivs):
    days = np.array(days)
    ivs = np.array(ivs)

    sort_idx = days.argsort()
    days = days[sort_idx]
    ivs = ivs[sort_idx]


    spline = interp1d(days, ivs, kind='linear', fill_value="extrapolate")

    def term_spline(dte):
        if dte < days[0]:  
            return ivs[0]
        elif dte > days[-1]:
            return ivs[-1]
        else:  
            return float(spline(dte))

    return term_spline

def get_current_price(ticker):
    todays_data = ticker.history(period='1d')
    return todays_data['Close'][0]

def compute_recommendation(ticker):
    earnings_date = None
    try:
        ticker = ticker.strip().upper()
        if not ticker:
            return "No stock symbol provided."
        
        try:
            stock = yf.Ticker(ticker)
            if len(stock.options) == 0:
                raise KeyError()

            calendar = stock.calendar

            if calendar is not None and 'Earnings Date' in calendar:
                earnings_date = calendar['Earnings Date'][0]
            else:
                print("empty calendar")
        except KeyError:
            return f"Error: No options found for stock symbol '{ticker}'."
        except Exception as ex:
            return f"Rate limited"
        
        exp_dates = list(stock.options)
        try:
            exp_dates = filter_dates(exp_dates)
        except:
            return "Error: Not enough option data."
        
        options_chains = {}
        for exp_date in exp_dates:
            options_chains[exp_date] = stock.option_chain(exp_date)
        
        try:
            underlying_price = get_current_price(stock)
            if underlying_price is None:
                raise ValueError("No market price found.")
        except Exception:
            return "Error: Unable to retrieve underlying stock price."
        
        atm_iv = {}
        straddle = None 
        atm_content = []
        i = 0
        for exp_date, chain in options_chains.items():
            calls = chain.calls
            puts = chain.puts

            if calls.empty or puts.empty:
                continue

            call_diffs = (calls['strike'] - underlying_price).abs()
            call_idx = call_diffs.idxmin()
            call_iv = calls.loc[call_idx, 'impliedVolatility']

            put_diffs = (puts['strike'] - underlying_price).abs()
            put_idx = put_diffs.idxmin()
            put_iv = puts.loc[put_idx, 'impliedVolatility']

            atm_iv_value = (call_iv + put_iv) / 2.0
            atm_iv[exp_date] = atm_iv_value

            if i == 0:
                call_bid = calls.loc[call_idx, 'bid']
                call_ask = calls.loc[call_idx, 'ask']
                put_bid = puts.loc[put_idx, 'bid']
                put_ask = puts.loc[put_idx, 'ask']

                call_strike = calls.loc[call_idx, 'strike']
                put_strike = calls.loc[put_idx, 'strike']
                
                if call_bid is not None and call_ask is not None:
                    call_mid = (call_bid + call_ask) / 2.0
                else:
                    call_mid = None

                if put_bid is not None and put_ask is not None:
                    put_mid = (put_bid + put_ask) / 2.0
                else:
                    put_mid = None

                if call_mid is not None and put_mid is not None:
                    straddle = (call_mid + put_mid)
                    message = f"date: {exp_date}, SELL: call strike: {call_strike} @ call mid: {call_mid}"
                    atm_content.append(dict(exp_date=exp_date, strike=call_strike, message=message, call_mid=call_mid))

            if i == 1:
                call_bid = calls.loc[call_idx, 'bid']
                call_ask = calls.loc[call_idx, 'ask']
                put_bid = puts.loc[put_idx, 'bid']
                put_ask = puts.loc[put_idx, 'ask']

                call_strike = calls.loc[call_idx, 'strike']
                put_strike = calls.loc[put_idx, 'strike']
                
                if call_bid is not None and call_ask is not None:
                    call_mid = (call_bid + call_ask) / 2.0
                else:
                    call_mid = None

                if call_mid is not None:
                    message = f"date: {exp_date}, BUY: call strike: {call_strike} @ call mid: {call_mid}"
                    atm_content.append(dict(exp_date=exp_date, strike=call_strike, message=message, call_mid=call_mid))

            i += 1
        if not atm_iv:
            return "Error: Could not determine ATM IV for any expiration dates."
        
        today = datetime.today().date()
        dtes = []
        ivs = []
        for exp_date, iv in atm_iv.items():
            exp_date_obj = datetime.strptime(exp_date, "%Y-%m-%d").date()
            days_to_expiry = (exp_date_obj - today).days
            dtes.append(days_to_expiry)
            ivs.append(iv)
        
        term_spline = build_term_structure(dtes, ivs)
        
        ts_slope_0_45 = (term_spline(45) - term_spline(dtes[0])) / (45-dtes[0])
        
        price_history = stock.history(period='3mo')
        iv30_rv30 = term_spline(30) / yang_zhang(price_history)

        avg_volume = price_history['Volume'].rolling(30).mean().dropna().iloc[-1]

        expected_move = str(round(straddle / underlying_price * 100,2)) + "%" if straddle else None

        if earnings_date is None:
            earnings_date = ""
        else:
            earnings_date = arrow.get(earnings_date).format("YYYY-MM-DD")

        return {'sell': atm_content[0]['message'], 'sell_mid': atm_content[0]['call_mid'], 'buy': atm_content[1]['message'], 'buy_mid':  atm_content[1]['call_mid'],
            "earnings_date": earnings_date,
        'sell_exp_date': atm_content[0]['exp_date'], 'buy_exp_date': atm_content[1]['exp_date'], 'sell_strike': atm_content[0]['strike'], 'buy_strike': atm_content[1]['strike'],
        'avg_volume': avg_volume >= 1500000, 'iv30_rv30': iv30_rv30 >= 1.25, 'ts_slope_0_45': ts_slope_0_45 <= -0.00406, 'expected_move': expected_move} #Check that they are in our desired range (see video)
    except Exception as e:
        #raise Exception(f'Error occured processing')
        raise e
  
def cal_spread_dict(symbol):
    try:
        result = compute_recommendation(symbol)
        if type(result) is str:
            return (None, result)
        else:
            avg_volume_bool    = result['avg_volume']
            iv30_rv30_bool     = result['iv30_rv30']
            ts_slope_bool      = result['ts_slope_0_45']
            if 'expected_move' in result.keys() and result['expected_move'] is not None:
                expected_move      = result['expected_move']
            else:
                expected_move      = ""
            sell_message       = result['sell']
            buy_message        = result['buy']
            earnings_date      = result['earnings_date']
            
            if 'sell_exp_date' in result.keys():
                sell_exp_date      = result['sell_exp_date']
            else:
                sell_exp_date      = ""
            
            if 'buy_exp_date' in result.keys():
                buy_exp_date       = result['buy_exp_date']
            else:
                buy_exp_date       = ""
            
            if 'sell_strike' in result.keys():
                sell_strike        = result['sell_strike']
            else:
                sell_strike        = ""
            
            if 'buy_strike' in result.keys():
                buy_strike         = result['buy_strike']
            else:
                buy_strike         = ""
            
            if 'buy_mid' in result.keys():
                buy_mid            = result['buy_mid']
            else:
                buy_mid            = None
            
            if 'sell_mid' in result.keys():
                sell_mid           = result['sell_mid']
            else:
                sell_mid           = None
            
            if buy_mid is not None and sell_mid is not None:
                entry_cost         = (buy_mid - sell_mid) * 100
            else:
                entry_cost         = 0.0

            content = {}
            content["symbol"] = symbol.upper()
            content["earnings"] = earnings_date
            content["buy strike"] = buy_strike
            content["buy expiry"] = buy_exp_date
            content["sell strike"] =sell_strike
            content["sell expiry"] = sell_exp_date
            content["cost"] = f"{entry_cost:<10.2f}"
            content["avg_volume"] = 'PASS' if avg_volume_bool else 'FAIL'
            content["iv30_rv30"] =  'PASS' if iv30_rv30_bool else 'FAIL'
            content["ts_slope_0_45"] = 'PASS' if ts_slope_bool else 'FAIL'
            content["Expected Move"] = expected_move
            return (content, None)
    except Exception as e:
        #print("Exception in caltrade:")
        #print(e)
        return (None, f'{e}')



def cal_spread(symbol):
    try:
        result = compute_recommendation(symbol)
        if type(result) is str:
            return (None, result)
        else:
            avg_volume_bool    = result['avg_volume']
            iv30_rv30_bool     = result['iv30_rv30']
            ts_slope_bool      = result['ts_slope_0_45']
            if 'expected_move' in result.keys() and result['expected_move'] is not None:
                expected_move      = result['expected_move']
            else:
                expected_move      = ""
            sell_message       = result['sell']
            buy_message        = result['buy']

            if 'earnings_date' in result.keys():
                earnings_date      = result['earnings_date']
            else:
                earnings_date      = " "

            
            if 'sell_exp_date' in result.keys():
                sell_exp_date      = result['sell_exp_date']
            else:
                sell_exp_date      = ""
            
            if 'buy_exp_date' in result.keys():
                buy_exp_date       = result['buy_exp_date']
            else:
                buy_exp_date       = ""
            
            if 'sell_strike' in result.keys():
                sell_strike        = result['sell_strike']
            else:
                sell_strike        = ""
            
            if 'buy_strike' in result.keys():
                buy_strike         = result['buy_strike']
            else:
                buy_strike         = ""
            
            if 'buy_mid' in result.keys():
                buy_mid            = result['buy_mid']
            else:
                buy_mid            = None
            
            if 'sell_mid' in result.keys():
                sell_mid           = result['sell_mid']
            else:
                sell_mid           = None
            
            if buy_mid is not None and sell_mid is not None:
                entry_cost         = (buy_mid - sell_mid) * 100
            else:
                entry_cost         = 0.0

            content = []
            content.append("| Field         | Value      |")
            content.append("|---------------|------------|")
            content.append(f"| symbol        | {symbol.upper():<10} |")
            content.append(f"| earnings      | {earnings_date:<10} |")
            content.append(f"| buy strike    | {buy_strike:<10} |")
            content.append(f"| buy expiry    | {buy_exp_date:<10} |")
            content.append(f"| sell strike   | {sell_strike:<10} |")
            content.append(f"| sell expiry   | {sell_exp_date:<10} |")
            content.append(f"| cost          | {entry_cost:<10.2f} |")
            content.append(f"| avg_volume    | {'PASS' if avg_volume_bool else 'FAIL':<10} |")
            content.append(f"| iv30_rv30     | {'PASS' if iv30_rv30_bool else 'FAIL':<10} |")
            content.append(f"| ts_slope_0_45 | {'PASS' if ts_slope_bool else 'FAIL':<10} |")
            content.append(f"| Expected Move | {expected_move:<10} |")
            content.append("|---------------|------------|")
            return ("\n".join(content), None)
    except Exception as e:
        print("Exception in caltrade:")
        print(e)
        return (None, f'{e}')