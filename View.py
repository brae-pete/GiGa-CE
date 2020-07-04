import base64
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px

import pandas as pd

from TeraCE import DataIO

app = dash.Dash(__name__)

separation_columns = ['name', 'filename', 'tags', 'date', 'imgs', 'method']
separation_columns_type = ['any','any','any','datetime','any','any']

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
            {"name": i, "id": i, "deletable": False, "selectable": True, "hideable":True,
             'type':dtype} for i,dtype in zip(separation_columns, separation_columns_type)
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
])
    ])


# Callbacks

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
                all_data['id']=self._row_id
                self._row_id += 1
                for key, value in info.items():
                    all_data[key] = value
                data_array.append(all_data)

            return data_array

    def select_table(self,row_ids, selected_rows, active_cells, *args):

        all_data_frames = []
        if selected_rows is None:
            return
        for row in selected_rows:
            df = self.separations[row]
            df['name']=row
            all_data_frames.append(df)
        data = pd.concat(all_data_frames)
        print(data.columns)
        fig = px.line(data, x="time", y=" rfu", color="name")

        return dcc.Graph(figure=fig)

if __name__ == '__main__':
    sep_controller = SeparationController(app)
    app.run_server(debug=True)
