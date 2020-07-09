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

app = dash.Dash(__name__)
separation_columns = ['name', 'date']
separation_columns_type = ['any', 'datetime']

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
        html.Div(id="filter_options")
    ])
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


@app.callback(Output('filter_options', 'children'),
              [Input('digital_filter_selection', 'value')])
def set_filter_menu(filter_selection_value):
    if filter_selection_value == 'butter':
        return [dcc.Input(id="butter_order",
                          placeholder='Filter Order',
                          type='number',
                          debounce=True, min=1),
                dcc.Input(id='butter_cutoff',
                          placeholder='Cutoff Frequency',
                          type='number',
                          debounce=True, min=0)]

    elif filter_selection_value == 'savgol':
        return [dcc.Input(id="savgol_window_length",
                          placeholder='Window Length',
                          type='number',
                          debounce=True, min=1),
                dcc.Input(id='savgol_poly_fit',
                          placeholder='Poly_Fit',
                          type='number',
                          debounce=True, min=1)]


# Separation Callbacks
@app.callback(
    Output('separation_graph', 'children'),
    [Input('data_table_separations', 'derived_virtual_row_ids'),
     Input('data_table_separations', 'selected_row_ids')],
    [State('electropherogram_df', 'children')])
def select_table(selected_rows, row_ids, egram_data):
    if egram_data is None or selected_rows is None:
        return
    if not selected_rows:
        return
    print(selected_rows, " is selected rows")
    egram_df = pd.read_json(egram_data)
    if egram_df.shape[0] <1:
        return
    selected_df = egram_df[egram_df['id'].isin(selected_rows)]
    fig = px.line(selected_df, x="time", y="rfu", color="name")
    return dcc.Graph(figure=fig)


@app.callback(Output('electropherogram_df', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified'),
               State('electropherogram_df', 'children')])
def update_egrams(contents, names, dates, old_json):
    if old_json == None:
        new_json = pd.DataFrame(columns=['time','rfu','raw','kV','uA','id','name']).to_json()
    else:
        new_json = control.add_egram(old_json, contents, names, dates)
    return new_json


@app.callback(Output('data_table_separations', 'data'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified'),
               State('data_table_separations', 'data')])
def update_sep_table(_, names, dates, old_data):
    """
    Adds data to a hidden dataframe in JSON
    Adds data to the Separations Datatable.
    """
    if names is None:
        return old_data
    new_data = control.add_separation(old_data, names, dates)

    return new_data.to_dict('rows')


import control

if __name__ == '__main__':
    app.run_server(debug=True)
    data = control
