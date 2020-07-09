import pandas as pd
import DataIO
import base64


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

def add_separation(sep_table, names, dates):
    """
    Adds the separation information to the table
    """
    sep_df = pd.DataFrame.from_dict(sep_table)
    new_data = [[name, date, f"{name}-{date}"] for name, date in zip(names, dates)]
    new_rows = pd.DataFrame(data=new_data, columns=['name', 'date', 'id'])
    sep_df = sep_df.append(new_rows, ignore_index=True)
    return sep_df
