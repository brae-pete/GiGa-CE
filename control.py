import datetime
import logging

import pandas as pd
import sqlalchemy
from scipy import signal
from sqlalchemy.exc import IntegrityError
import numpy as np
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
                if not row['name'] == 'New' or row['id'] is not None:

                    con.execute(f"INSERT INTO peak_lookup (name, start, stop, center, deviation, buffer) "
                                f"VALUES ('{row['name']}', {row['start']}, {row['stop']}, {row['center']},"
                                f" {row['deviation']}, '{row['buffer']}')")

                else:
                    row_df = pd.read_sql(f"SELECT id FROM peak_lookup WHERE name=='{row['name']}'", engine)
                    row_id = row_df['id'].values[-1]
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

def assign_peaks(peak_info:pd.DataFrame, peak_lut):
    peak_lut = pd.DataFrame.from_dict(peak_lut)
    lut_names = peak_info['name'].values
    for index, peak in peak_info.iterrows():
        smallest = 1*10**12
        for _, lut in peak_lut.iterrows():
            if lut['center']==0:
                continue
            rsd = (peak['m1']-lut['center'])/lut['center']*100
            if abs(rsd) < lut['deviation'] and abs(rsd) < smallest:
                smallest = rsd
                lut_names[index]=lut['name']
    peak_info['name']=lut_names
    return peak_info
def find_peaks(egrams):
    """
    Find peaks for each chromatogram from a dataframe of electropherograms and a table of possible peaks
    """
    peak_df = None
    for sep in egrams['id'].unique():
        df = egrams[egrams['id'] == sep]
        peaks, _ = signal.find_peaks(df['rfu'], prominence=0.001)
        prominences = signal.peak_prominences(df['rfu'], peaks, 500)
        widths = signal.peak_widths(df['rfu'], peaks, 0.995, prominence_data=prominences)
        rows = get_peak_information(df, peaks, widths)
        if peak_df is None:
            peak_df = rows
        else:
            peak_df = peak_df.append(rows, ignore_index=True)
    return peak_df

def get_peak_information(df, peaks, widths):
    # Get Peak information
    row = pd.DataFrame()
    row['name'] = [f"peak_{df['time'].values[x]}" for x in peaks]
    indices = np.asarray([Electropherogram.get_indices(df['time'].values, start, stop)
                          for start, stop in zip(widths[2], widths[3])])

    row['start_idx'] = indices[:,0]
    row['stop_idx'] = indices[:,1]
    row['start'] = indices[:,2]
    row['stop'] = indices[:, 3]
    row['max'] = [df['rfu'].values[x] for x in peaks]
    moments = np.asarray([Electropherogram.peak_moments(row_id, df) for _, row_id in row.iterrows()])
    row['m1'] = moments[:, 0]
    row['m2'] = moments[:, 1]
    row['m3'] = moments[:, 2]
    row['m4'] = moments[:, 3]
    row['area'] = [Electropherogram.peak_area(row_id, df) for _, row_id in row.iterrows()]
    row['corrected_area'] = [Electropherogram.peak_corrected_area(row_id, df) for _, row_id in row.iterrows()]
    return row