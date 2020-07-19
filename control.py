import datetime

import pandas as pd
import DataIO
import DataSql
import base64
from sqlalchemy.orm import sessionmaker
import Electropherogram


def add_egram(egram_json, contents, names, dates):
    """
    Adds egrams to the egram table
    """
    egram_df = pd.read_json(egram_json)
    for content, file_name, modified in zip(contents, names, dates):
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        df, info = DataIO.read_custom_ce_file(decoded)
        df['id'] = f"{file_name}-{modified}"
        df['name'] = file_name
        df['raw'] = df['rfu']

        egram_df = egram_df.append(df, ignore_index=True)
    return egram_df.to_json()


def get_single_egram(egram, content, sep_id):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    df = DataIO.read_custom_ce_file(decoded)
    df['separation_id'] = sep_id
    if egram is None:
        egram = df
    else:
        egram = egram.append(df, ignore_index=True)
    return egram


def add_separation(engine, sesh, names, dates, contents):
    """
    Adds the separation information to the table
    """
    egram_df = None
    for name, date, content in zip(names, dates, contents):
        date = datetime.datetime.fromtimestamp(date)
        new_sep = DataSql.Separation(name=name, date=date)
        sesh.add(new_sep)
        sesh.commit()
        egram_df = get_single_egram(egram_df, content, new_sep.id)

    egram_df.to_sql('data', engine, if_exists='append', index=False)
    return


def filter_data(egram_df, sql_ids, engine):
    sql_query = f"SELECT id, digital, digital_arg1, digital_arg2 FROM separation WHERE separation.id IN ({sql_ids})"
    in_data = pd.read_sql(sql_query, engine)
    for idx in in_data['id'].unique():
        single_gram = egram_df[egram_df['id'] == idx]
        single_sep = in_data[in_data['id'] == idx].iloc[0, :]
        rfu = single_gram
        if single_sep.digital == 'butter' and single_sep.digital_arg1 is not None and single_sep.digital_arg2 is not None:
            rfu = Electropherogram.filter_butter(rfu, single_sep.digital_arg2, single_sep.digital_arg1)
        elif single_sep.digital == 'savgol' and single_sep.digital_arg1 is not None and single_sep.digital_arg2 is not None:
            rfu = Electropherogram.filter_savgol(rfu, single_sep.digital_arg1, single_sep.digital_arg2)
        single_gram['rfu']=rfu
        egram_df[egram_df['id'] == idx] = single_gram
    return egram_df
