
from fredapi import Fred
import pandas as pd
import arrow
from dataContent import DataContent
from config import fred_api_key

# treasury list
yield_ids = ['DGS1MO','DGS3MO','DGS6MO','DGS1','DGS2','DGS3','DGS5', 'DGS7','DGS10', 'DGS20', 'DGS30' ]

row_names = ['1 Month', '3 Month', '6 Month', '1 Year', '2 Year', '3 Year', '5 Year', '7 Year', '10 Year', '20 Year', '30 Year']

def fetch_yield_data():
    '''Get the yield curve data from FRED'''
    
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


def get_yields_data(data_content: DataContent):
    '''If it's been more than 1 hour, then fetch the data, otherwise return the dataframe.
    @return the dataframe and indicate if the data is updated'''
    now = float(arrow.utcnow().format("X"))
    update = False

    if (now - data_content.last_updated) > 3600.0:
        data_content.last_updated = now
        data_content.df_yields = fetch_yield_data()
        update = True
    
    return data_content.df_yields, update


