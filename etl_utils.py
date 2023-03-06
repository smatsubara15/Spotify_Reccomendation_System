# Credit Akshat Palnitkar

import pandas as pd

def clean_date(date_str):
    
    """Cleans a date string
    If the string is of size 4, it only contains the year
    We set the month and day to 01-01"""

    if len(date_str)==4:
        date_str = date_str + '-01-01'

    return date_str

def get_unique_map_from_df_col(df, col_name):
    
    """Returns a dictionary with ids assigned to unique values in a dataframe column"""
    
    unique_map = {}
    
    curr_id = 1
    unique_list = df[col_name].unique().tolist()
    for u in unique_list:
        if u!='':
            unique_map[str(u)] = curr_id
            curr_id += 1
        
    return unique_map



