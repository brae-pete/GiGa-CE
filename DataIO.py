import datetime
import io

import pandas as pd


def read_custom_ce_file(decoded_bytes):
    """
    Parses a custom CE data file.
    Data file should be strcutred with meta data contained in the first row of the csv file.
    Column headers labels should be: 'time', 'rfu', 'uA', 'kV'

    :param filename:
    :return: (electropherogram dataframe, information)
    :rtype: tuple[pd.DataFrame, dict]
    """

    def parse_header():
        """
        get any header informatino about the run in the first row of the csv file.
        :return:
        """
        info = decoded_bytes.decode()
        info.split('\n')
        header = info
        information = {"date": None, "method": None, "images": None, "tags":None,
                       "Name":"Separation"}
        header = header.strip('\n').split(' ')
        print(header)
        for key in information:
            try:
                information[key] = header[header.index(key) + 1]
            except ValueError:
                continue
        if information['date'] is not None:
            information['date']=datetime.datetime.fromisoformat(information['date'])
        return information


    df = pd.read_csv(io.StringIO(decoded_bytes.decode('utf-8')), header=[1])
    information = parse_header()
    return df, information
