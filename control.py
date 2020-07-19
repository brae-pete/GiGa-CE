import datetime
import logging

import pandas as pd
import sqlalchemy
from sqlalchemy.exc import IntegrityError

import DataIO
import DataSql
import base64
from sqlalchemy.orm import sessionmaker
import Electropherogram
import plotly.express as px


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


def get_grams(engine, selected_rows):
    if selected_rows is None:
        return
    if not selected_rows:
        return
    sql_ids = str(selected_rows).replace('[', '').replace(']', '')
    sql_query = "SELECT separation.name, data.time, data.rfu, separation.id FROM separation INNER JOIN" \
                " data ON separation.id = data.separation_id" \
                " WHERE separation.id IN ({})".format(sql_ids)
    egram_df = pd.read_sql(sql_query, engine)
    egram_df = filter_data(egram_df, sql_ids, engine)
    if egram_df.shape[0] < 1:
        return
    return egram_df


def get_peak_lut(engine):
    sql_query = "SELECT id, name, start, stop, center, deviation, buffer " \
                "FROM peak_lookup"
    lut_df = pd.read_sql(sql_query, engine)
    return lut_df


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


def update_peak_lut(engine, data):
    if len(data) < 1:
        return

    with engine.connect() as con:
        for row in data:
            if row['id'] is not None:
                try:
                    con.execute(f"UPDATE peak_lookup SET name='{row['name']}', start={row['start']}, "
                                f"stop={row['stop']}, center={row['center']}, deviation={row['deviation']}, "
                                f"buffer='{row['buffer']}' "
                                f"WHERE peak_lookup.id IN ({row['id']})")
                except IntegrityError as e:
                    logging.warning("Cannot Duplicate Names")
            else:
                if not row['name'] == 'New':
                    try:
                        con.execute(f"INSERT INTO peak_lookup (name, start, stop, center, deviation, buffer) "
                                    f"VALUES ('{row['name']}', {row['start']}, {row['stop']}, {row['center']},"
                                    f" {row['deviation']}, '{row['buffer']}')")

                    except IntegrityError as e:
                        row_df = pd.read_sql(f"SELECT id FROM peak_lookup WHERE name=='{row['name']}'", engine)
                        row_id = row_df['id'].values[0]
                        con.execute(f"UPDATE peak_lookup SET name='{row['name']}', start={row['start']}, "
                                    f"stop={row['stop']}, center={row['center']}, deviation={row['deviation']}, "
                                    f"buffer='{row['buffer']}' "
                                    f"WHERE peak_lookup.id IN ({row_id})")


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
        single_gram['rfu'] = rfu
        egram_df[egram_df['id'] == idx] = single_gram
    return egram_df
