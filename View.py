import base64
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px

import pandas as pd

import DataIO

app = dash.Dash(__name__)

separation_columns = ['name', 'filename', 'tags', 'date', 'imgs', 'method']
separation_columns_type = ['any', 'any', 'any', 'datetime', 'any', 'any']

app.layout = html.Div([
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
                                                               {'label': 'None', 'value':'none'}]),
        html.Div(id="filter_options")
    ])
])


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


class SeparationController:

    def __init__(self, app):
        self.app = app
        self.separations = {}
        self._row_id = 0
        app.callback(Output('data_table_separations', 'data'),
                     [Input('upload-data', 'contents')],
                     [State('upload-data', 'filename'),
                      State('upload-data', 'last_modified'),
                      State('data_table_separations', 'data')])(self.update_table)

        app.callback(
            Output('separation_graph', 'children'),
            [Input('data_table_separations', 'derived_virtual_row_ids'),
             Input('data_table_separations', 'selected_row_ids'),
             Input('data_table_separations', 'active_cell')])(self.select_table)

    def update_table(self, list_of_contents, list_of_names, list_of_dates, old_data):
        if list_of_contents is not None:
            if old_data is None:
                data_array = []
            else:
                data_array = old_data
            for content, file_name, modified in zip(list_of_contents, list_of_names, list_of_dates):
                all_data = {i: None for i in separation_columns}
                all_data['date'] = modified
                all_data['filename'] = file_name
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)
                df, info = DataIO.read_custom_ce_file(decoded)
                self.separations[self._row_id] = df
                all_data['id'] = self._row_id
                self._row_id += 1
                for key, value in info.items():
                    all_data[key] = value
                data_array.append(all_data)

            return data_array

    def select_table(self, row_ids, selected_rows, active_cells, *args):

        all_data_frames = []
        if selected_rows is None:
            return
        for row in selected_rows:
            df = self.separations[row]
            df['name'] = row
            all_data_frames.append(df)
        if len(all_data_frames) == 0:
            return
        data = pd.concat(all_data_frames)
        print(data.columns)
        fig = px.line(data, x="time", y=" rfu", color="name")

        return dcc.Graph(figure=fig)


if __name__ == '__main__':
    sep_controller = SeparationController(app)
    app.run_server(debug=True)
