import os
import datetime as dt
import database as db
import pandas as pd


def ExportEgrams(ids, saveas, session):
    """
    During egram export,
    in same query,
    add second loop for second file
    loop through peaks.
    rows == peaks
    columns == shortname/name
    values == CA
    
    
    """

    time = []
    data = {}
    saveas = saveas + '.csv'
    # Get all of our data, organize it into a dictionary with headers as keys
    for i in session.query(db.Separation).filter(db.Separation.id.in_(ids)):
        Filename = i.filename
        T, RFU = Readfile(Filename)
        if T > time:  # Let our longest run set the X axis
            time = T
        # data['Time']=time
        if i.shortname == None or i.shortname == "None":
            shortname = i.name
        else:
            shortname = i.shortname
        data[shortname] = RFU
    # Write our data to a CSV File

    fopen = open(saveas, 'w')
    fopen.write('Time,')
    for header in data:
        fopen.write('{},'.format(header))

    fopen.write('\n')
    # Go line by line and write 
    for x in range(len(time)):
        fopen.write('{},'.format(time[x]))
        for y in data:
            if x < len(data[y]):
                rfu = data[y][x]
            else:
                rfu = ""
            fopen.write('{},'.format(rfu))
        fopen.write('\n')
    fopen.close()


def ExportPeaks(ids, saveas, engine):
    """ Reads in database using raw engine connection. Joins separation and peaks database
    rearranges data so names is in front
    sorts and groups the data by peak name then by run id
    saves to a csv
    """
    print("Starting")
    if saveas[-4:] != '.csv':
        saveas = saveas + '.csv'
    con = engine.engine.raw_connection()
    peaks = pd.read_sql_query("select * from peaks", con)
    runs = pd.read_sql_query("select id, name, shortname, date from separations", con)
    joined = peaks.join(runs.set_index('id'), on='run_id', how='left', lsuffix='_left', rsuffix='_right')
    joined = joined[joined.run_id.isin(ids)].sort_values(['name_left', 'run_id'])
    joined.to_csv(saveas)
    print("saved")


def getfolder(user):
    directory = os.getcwd()
    today = dt.date.today()
    folder = directory + '\\' + user
    # folder = os.getcwd()+'\\'+self.user Use for actual GUI
    if not os.path.exists(folder):
        os.makedirs(folder)
    folder = folder + '\\' + today.isoformat()
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def Readfile(filename, time=True, rfu=True, voltage=False, current=False):
    """Opens and read converted file, where first 2 lines are headers, returns
    a data list that is determined by time,rfu,current,voltage argruments

    Assume all files are stored within the working directory
    so that folders can be transferred without having to match filepaths"""
    filename = filename.split('\\')  # Split filename by directory
    filename = filename[-3:]  # Remove User, Date, and Filename information
    di = os.getcwd()  # Get CWD
    # Create filename that is unique for this computer
    filename = di + "\\{}\\{}\\{}".format(filename[0], filename[1], filename[2])

    fin = open(filename, 'r')  # open file
    lines = fin.readlines()
    # Create lists for each data aspect
    Time = []
    RFU = []
    Voltage = []
    Current = []
    # Ignoring the header step through data and pull out information
    for line in lines[2:]:
        line = line.replace('\n', '')
        t, f, v, a = line.split(',')
        Time.append(float(t))
        RFU.append(float(f))
        Voltage.append(float(v))
        Current.append(float(a))
    # Prepare a data list
    data = []
    # depending on function arguments, append data
    if time:
        data.append(Time)
    if rfu:
        data.append(RFU)
    if voltage:
        data.append(Voltage)
    if current:
        data.append(Current)
    # print(data, "\n that was data")
    return data


def CSV_conversion(filename, new_id, user):
    with open(filename, 'r') as fin:
        header = fin.readline().split(',')
        data = fin.readlines()

    if len(header) > 5:
        rfu_key = 4
        time_key = 0
        kv_key = 2
        ua_key = 3
    else:
        rfu_key = 1
        time_key = 0
        kv_key = 2
        ua_key = 3
    RFU = []
    uA = []
    KV = []
    DT = []
    for line in data:
        line = line.split(',')
        RFU.append(eval(line[rfu_key]))
        DT.append(eval(line[time_key]))
        KV.append(eval(line[kv_key]))
        uA.append(eval(line[ua_key]))
    newname = get_new_name(user, new_id)
    timemult = DT[1] - DT[0]
    write_file(RFU, uA, KV, timemult, newname, '')
    return newname

def get_new_name(user, new_id):
    print('Get folder:', getfolder(user), 'new id:', new_id)
    newfile = getfolder(user) + '\\{}'.format(new_id) + '.csv'
    return newfile

def ASCconversion(filename, new_id, user, ohms=False, Stuff=True):
    "Saves files as User\\date\\new_id.csv or User\\date\\new_idOHMS.csv"
    # filename.replace('.asc','')
    if filename[-3:] == 'csv':
        CSV_conversion(filename, new_id, user)
        return
    if ohms:  # We will create 2 files if we are doing an OHMS plot
        # ohmfile = getfolder(user)+'\\{}'.format(new_id)+'OHMS.csv'
        fin = open(filename, 'r')
        newfile = ohmfile = getfolder(user) + '\\{}'.format(new_id) + 'OHMS.csv'
        fout = open(ohmfile, 'w')

    else:
        fin = open(filename, 'r')
        newfile = get_new_name(user, new_id)
        # filename=newname#.replace('.asc','')
        # filename+='.csv'
        fout = open(newfile, 'w')
    lines = fin.readlines()
    # print(lines)
    try:
        points = lines[8].split('\t')
        points = eval(points[1])

        timetitle = lines[9].split('\t')
        timetitle = timetitle[1]

        timemult = lines[11].split('\t')
        timemult = eval(timemult[1])

        yvalue = lines[10].split('\t')
        yvalue = yvalue[1:4]

        yaxis = lines[12].split('\t')
        yaxis = yaxis[1:4]
    except:
        points = lines[8].split(',')
        points = eval(points[1])

        timetitle = lines[9].split(',')
        timetitle = timetitle[1]

        timemult = lines[11].split(',')
        timemult = eval(timemult[1])

        yvalue = lines[10].split(',')
        yvalue = yvalue[1:4]

        yaxis = lines[12].split(',')
        yaxis = yaxis[1:4]

    RFU = lines[13:13 + points]
    KV = lines[13 + points:13 + points + points]
    uA = lines[13 + points + points:]

    # print(len(RFU),len(KV),len(uA))
    headertop = {}
    timemult = 0.25
    for i in range(13):
        # print(lines[i])
        new = lines[i].replace('\n', '')
        if new.count(',') > 0:
            new = new.split(',')
        else:
            new = new.split('\t')
        key1 = new[0]
        headertop[key1] = new[1:]
    fin.close()
    for m in range(len(RFU)):
        F = eval(RFU[m].replace('\n', ''))
        V = eval(KV[m].replace('\n', ''))
        A = eval(uA[m].replace('\n', ''))
        RFU[m] = F * eval(yaxis[0])
        KV[m] = V * eval(yaxis[1])
        uA[m] = A * eval(yaxis[2])
    write_file(RFU, uA, KV, timemult, newfile)
    return newfile

def write_file(RFU, uA, KV, timemult, filename, header):
    fout = open(filename, 'w')
    fout.write(str(header) + '\n')
    fout.write("time,RFU,kV,uA \n")
    dt = 0
    for m in range(len(RFU)):
        f = RFU[m]
        v = KV[m]
        a = uA[m]
        fout.write('{},{},{},{}\n'.format(dt, f, v, a))
        dt += timemult
    fout.close()

    return filename
