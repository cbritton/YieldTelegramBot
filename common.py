
from fredapi import Fred
import pandas as pd
import arrow
from dataContent import DataContent
from config import fred_api_key
import plotly.graph_objects as go

# treasury list
yield_ids = ['DGS1MO','DGS3MO','DGS6MO','DGS1','DGS2','DGS3','DGS5', 'DGS7','DGS10', 'DGS20', 'DGS30' ]

row_names = ['1 Month', '3 Month', '6 Month', '1 Year', '2 Year', '3 Year', '5 Year', '7 Year', '10 Year', '20 Year', '30 Year']
shorthand_names = ['1m', '3m', '6m', '1y', '2y', '3y', '5y', '7y', '10y', '20y', '30y']

def remove_curve_graph(filename):
    '''Remove a file'''
    try:
        file = pathlib.Path(filename)
        file.unlink()
    except:
        pass


def fetch_yield_data(start_date, end_date):
    '''Get the yield curve data from FRED'''
    
    fred = Fred(api_key=fred_api_key)
    
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

def fetch_yield_data_old():
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
        end_date = arrow.now()
        start_date = end_date.shift(days=-5)
        data_content.df_yields = fetch_yield_data(start_date, end_date)
        # remove the yield curve graph if it exists
        remove_curve_graph(r"images/yc.png")
        update = True
    
    return data_content.df_yields, update


def create_figure(data, tmp_filename):
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

# spread functions

def get_yield_spread(first_id, second_id, months=12):
    fred = Fred(api_key=fred_api_key)
    end_date = arrow.now()
    start_date = end_date.shift(months=-months)
    ser_first = fred.get_series( first_id,
                    observation_start=start_date.format('YYYY-MM-DD'), 
                    observation_end=end_date.format('YYYY-MM-DD'))
    ser_second = fred.get_series(second_id,
                    observation_start=start_date.format('YYYY-MM-DD'), 
                    observation_end=end_date.format('YYYY-MM-DD'))

    df = pd.DataFrame({"F":ser_first, "S": ser_second})
    # add a column for the difference
    df['delta'] = df['S'] - df['F']
    # drop na rows
    df = df.dropna()
    return df

def create_spread_figure(data, first, second):
    # create the figure
    traces = []
    traces.append(
        go.Scatter(
            x=data.index, 
            y=data['delta'],
            mode="lines"
        )
    )
    # add zero line
    traces.append(
        go.Scatter(
            x=data.index,
            y=[0]*len(data),
            mode="lines"
        )
    )
    fig = go.Figure()
    _ = [fig.add_trace(trace) for trace in traces]

    title=f"{first}/{second} Spread"
    fig.update_layout(
        autosize=False,
        width=800,
        height=600,
        title =title,
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Diff",
        showlegend=False
    )
    return fig

