import base64
import io
from collections import OrderedDict

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
import pandas as pd
import Electropherogram
import DataIO
from sqlalchemy import update


app = dash.Dash(__name__)
separation_columns = ['name', 'date', 'savgol_len', 'savgol_poly']
separation_columns_type = ['any', 'datetime', 'any', 'any']

app.layout = html.Div([

    html.Div(id='electropherogram_df', style={'display': 'none'}),
    html.Div(id='separation_df', style={'display': 'none'}),
    html.Div(id='peak_df', style={'display': 'none'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div([
        dash_table.DataTable(
            id='data_table_separations',
            columns=[
                {"name": i, "id": i, "deletable": False, "selectable": True, "hideable": True,
                 'type': dtype} for i, dtype in zip(separation_columns, separation_columns_type)
            ],
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=15,
        ),
        html.Div(id='separation_graph')
    ]),
    html.Div(id="background_selection", children=[
        dcc.RadioItems(id="background_radio_selection", options=[{'label': 'Percentile Background',
                                                                  'value': 'median'},
                                                                 {'label': 'Polynomial Background',
                                                                  'value': 'poly'},
                                                                 {'label': 'None', 'value': 'None'}]),
        html.Div(id="background_options")
    ]),
    html.Div(children=[
        dcc.RadioItems(id="digital_filter_selection", options=[{'label': 'Butterworth', 'value': 'butter'},
                                                               {'label': 'Savintsky-Golay', 'value': 'savgol'},
                                                               {'label': 'None', 'value': 'none'}]),
        html.Div(id="filter_options", children =[
            html.Div(id = 'butter_div', children=[
            dcc.Input(id="butter_order",
                      placeholder='Filter Order',
                      type='number',
                      debounce=True, min=1),
            dcc.Input(id='butter_cutoff',
                      placeholder='Cutoff Frequency',
                      type='number',
                      debounce=True, min=0)]),
            html.Div(id='butter_dummy')]),

        html.Div(id="savgol_div", children=[dcc.Input(id="savgol_window_length",
                          placeholder='Window Length',
                          type='number',
                          debounce=True, min=1),
                dcc.Input(id='savgol_poly_fit',
                          placeholder='Poly_Fit',
                          type='number',
                          debounce=True, min=1)]),

                html.Div(id="savgol_dummy")
    ]),

])


# Background and Filtering Callbacks
@app.callback(Output('background_options', 'children'), [
    Input('background_radio_selection', 'value')])
def set_background_menu(background_selection_value):
    if background_selection_value == 'poly':
        return html.Div([dcc.Input(id="background_poly_order",
                                   placeholder='Polynomial Order',
                                   type='number',
                                   debounce=True, min=1, max=9),
                         dcc.Input(id='background_poly_skip_start',
                                   placeholder='Skip Start Pts',
                                   type='number',
                                   debounce=True, min=0),
                         dcc.Input(id='background_poly_skip_end',
                                   placeholder='Skip End Pts',
                                   type='number',
                                   debounce=True, min=0)
                         ])
    elif background_selection_value == 'median':
        return html.Div([dcc.Input(id='background_median_percentile',
                                   placeholder='Percentile (ie 30)',
                                   type='number',
                                   debounce=True, min=0, max=100)])


@app.callback([Output('butter_div', 'style'),
               Output('savgol_div', 'style')],
              [Input('digital_filter_selection', 'value')])
def set_filter_menu(filter_selection_value):
    if filter_selection_value == 'butter':
        return {'display':'block'}, {'display':'none'}

    elif filter_selection_value == 'savgol':
        return {'display':'none'}, {'display':'block'}

    else:
        return {'display':'none'}, {'display':'none'}

@app.callback(Output('savgol_dummy', 'children'),
              [Input('savgol_window_length','value'),
               Input('savgol_poly_fit','value')],
              [State('data_table_separations','selected_row_ids'),
               State('digital_filter_selection','value')])
def add_savgol_params(window_length, poly_fit, row_ids, filter):
    """
    Update the Filtering parameters
    """
    if filter != 'savgol':
        return None
    sql_ids = str(row_ids).replace('[','').replace(']','')
    window_length, poly_fit, filter = [ 'NULL' if x is None else x for x in [window_length, poly_fit, filter] ]
    with engine.connect() as con:
        rs = con.execute(f"UPDATE separation SET digital = '{filter}', digital_arg1 = {window_length}, digital_arg2={poly_fit} "
                         f"WHERE separation.id IN ({sql_ids})")
    return None

@app.callback(Output('butter_dummy', 'children'),
              [Input('butter_order','value'),
               Input('butter_cutoff','value')],
              [State('data_table_separations','selected_row_ids'),
               State('digital_filter_selection','value')])
def add_butter_params(order, cutoff, row_ids, filter):
    """
    Update the Filtering parameters
    """
    if filter != 'butter':
        return None
    sql_ids = str(row_ids).replace('[','').replace(']','')
    order, cutoff, filter = [ 'NULL' if x is None else x for x in [order, cutoff, filter] ]

    with engine.connect() as con:
        rs = con.execute(f"UPDATE separation SET digital='{filter}', digital_arg1={order}, digital_arg2={cutoff} "
                         f"WHERE separation.id IN ({sql_ids})")
    return None


# Separation Callbacks
@app.callback(
    Output('separation_graph', 'children'),
    [Input('data_table_separations', 'selected_row_ids')])
def graph_data(selected_rows):
    if selected_rows is None:
        return
    if not selected_rows:
        return
    sql_ids = str(selected_rows).replace('[','').replace(']','')
    sql_query = "SELECT separation.name, data.time, data.rfu, separation.id FROM separation INNER JOIN" \
                " data ON separation.id = data.separation_id"\
                " WHERE separation.id IN ({})".format(sql_ids)
    egram_df = pd.read_sql(sql_query, engine)
    egram_df = control.filter_data(egram_df, sql_ids, engine)
    print(egram_df.head())
    if egram_df.shape[0] < 1:
        return
    fig = px.line(egram_df, x="time", y="rfu", color="name")
    return dcc.Graph(figure=fig)


@app.callback(Output('data_table_separations', 'data'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_sep_table(contents, names, dates):
    """
    Adds data to a hidden dataframe in JSON
    Adds data to the Separations Datatable.
    """
    if names is not None:
        control.add_separation(engine, sesh, names, dates, contents)
    sep_df = pd.read_sql('SELECT * FROM separation', engine)
    return sep_df.to_dict('rows')


import control
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import DataSql

engine = create_engine('sqlite:///data.db', echo=True)
session = sessionmaker(bind=engine)
sesh = session()
DataSql.Base.metadata.create_all(engine)
if __name__ == '__main__':
    data = control

    app.run_server(debug=True)
