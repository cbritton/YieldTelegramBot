from dataclasses import dataclass
import pandas as pd

@dataclass
class DataContent:
    '''Content storage for the data. df_yields stores the dataframe, last_updated stores
    the last time the data was updated.'''
    df_yields: pd.DataFrame
    last_updated: float
        
    def __init__(self):
        self.df_yields = None
        self.last_updated = 0