""" From mainmenu
    From buffers with buffer id

"""
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# import mainmenu
import tkinter.filedialog as dialog
import database as db
import datetime as dt
import Injection
import Fileconversion
import peaks
import numpy as np


class separationsmenu(tk.Frame):
    """ Separations menu
    Menu
        1) Analyze new separations (batch)
        2) Analyze new separation (filename)
        3) View separation

        Function 1: Adds all files in batch to queue
        Function 2: Adds filename to queue
        Function 3: Converts ASCII, CSV, TSV to new file
        Function 4: Creates separation db instance
        Function 5: Creates new filename for separation

"""

    def __init__(self, parent, controller, session, user, *args):
        tk.Frame.__init__(self, parent)  # initialize frame
        self.controller = controller  # save to move between windows
        self.session = session
        self.user = user
        # Create buttons that will move between different windows

        bufferbutton = tk.Button(self, text="Analyze New Separations",
                                 command=self.openseparations)
        bufferbutton.grid()

        instrumentbutton = tk.Button(self, text="View old separation",
                                     )  # command = self.queryseparations)

        mainmenubutton = tk.Button(self, text="Go to Main Menu",
                                   command=lambda: controller.show_frame \
                                       (mainmenu.mainmenu))
        mainmenubutton.grid()

    def openseparations(self):
        queue = dialog.askopenfilenames()
        session = self.session

        for file in queue:
            if file[-3:] == 'dat':
                print("This is a dat file, cannot load in GigaCE")

            else:
                shortfile = file.split('/')
                # print('Shortfile', shortfile[-1])

                newrun = db.Separation(date=dt.date.today(), name=shortfile[-1])
                session.add(newrun)
                session.commit()
                newfile = self.filetype(file, new_id=newrun.id)
                newrun.filename = newfile
                session.commit()

        # convert queue?
        frame = self.controller.frames["separationview"]
        frame.clear_separation_tree()
        frame.fillseparationstable()  # update frame
        self.controller.show_frame("separationview")

    def filetype(self, filename, new_id):
        " Determines the file type and calls appropriate conversion"
        last = filename[-3:].upper()

        if last == "ASC":
            newfile = Fileconversion.ASCconversion(filename, new_id, self.user)
            return newfile
        else:
            newfile = Fileconversion.CSV_conversion(filename, new_id, self.user)
            return newfile
            # TXTconversion(filename, new_id)


class separationview(tk.Frame):
    """ Separations view frame
    Lists all items in queue as a table.
        INFORMATION
        NAME | SHORT NAME | BUFFER | INJ VOLUME | INSTRUMENT | PLATES
    Displays electropherogram
    Displays peak information
        INFORMATION
        NAME | SHORT NAME | CENTER | WIDTH | CA | CA% | RES(following)|
    Add Peak function
        Creates new row, allows user to select peak manually
    Add Noise function
        Saves the start and stop of a noise section for S/N calculations
    Tree View
        Allows users to select multiple peaks to compare across separations (same short name)
        Allows users to select multiple separations to compare electropherograms and peak information
    Export
        Exports selected separations to csv for ORIGIN
        Exports selected separations+peak info for excel    
"""
    volume = 0

    def __init__(self, parent, controller, session, user, engine, *args, **kwargs):
        """Requires: User(Str)"""

        tk.Frame.__init__(self, parent)  # initialize frame

        self.rowconfigure(0, weight=3)
        self.columnconfigure(0, weight=3)
        self.canvas = tk.Canvas(self, width=900, height=700, highlightthickness=0, scrollregion=(0, 0, 1300, 1300))
        self.canvas.grid(sticky="NSEW")
        self.session = session
        self.engine = engine
        self.selection = 0
        self.controller = controller
        # self.session=self.dbengine.get_session()

        self.interior = interior = Frame(self.canvas)
        self.plotframe = Frame(interior)
        self.plotframe.grid(row=0, column=0, columnspan=1)

        self.separationframe = Frame(interior)
        self.separationframe.grid(row=1, column=0, sticky="W")

        self.peakframe = Frame(interior)
        self.peakframe.grid(row=2, column=0, columnspan=2, sticky="W")

        self.separationstable()
        self.peakstable()

        self.plot_setup()
        self.vline1 = None
        self.vline2 = None
        # Create scroll bars
        vbar = Scrollbar(self, orient=VERTICAL)
        vbar.grid(row=0, column=1, sticky="NS")
        vbar.config(command=self.canvas.yview)
        hbar = Scrollbar(self, orient=HORIZONTAL)
        hbar.grid(row=1, column=0, sticky="EW")
        hbar.config(command=self.canvas.xview)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.create_window(0, 0, window=interior,
                                  anchor=NW)
        # Resize Canvas when window changes
        self.canvas.bind("<Configure>", self.on_resize)

        Addpeakbutton = Button(self.peakframe, text="Add Peak", command=self.newpeak)
        Addpeakbutton.grid(row=1, column=1, sticky="NSEW")

        AddNoise = Button(self.peakframe, text='Add Noise', command=self.new_noise)
        AddNoise.grid(row=5, column=1)

        button = Button(self.peakframe, text="Main Menu", command=lambda: self.controller.show_frame("mainmenu"))
        button.grid(column=1, row=2, sticky="NSEW")
        button2 = Button(self.peakframe, text="    Export \n Electropherograms", command=self.export_separations)
        button2.grid(column=1, row=3, sticky="NSEW")
        buttonpeakexport = Button(self.peakframe, text=" Export Peaks", command=self.export_peaks)
        buttonpeakexport.grid(column=1, row=4, sticky="NSEW")

        # Create labels and spinboxes for determining apparent mobility
        # Because the Voltage may not be the ohms voltage the user may change this
        # Because the Length to detector can change, the user may change this

        LDlabel = Label(self.separationframe, text="Length to Detector \n (cm)")
        LDlabel.grid(row=0, column=1, sticky="SW")
        LDspin = Spinbox(self.separationframe)
        LDspin.grid(row=1, column=1, sticky="NW")
        LDspin.delete(0, "end")
        LDspin.insert(0, 0)
        LDcolumn = Label(self.separationframe, text="Capillary Length \n (cm)")
        LDcolumn.grid(row=4, column=1, sticky="SW")
        columnspin = Spinbox(self.separationframe)
        columnspin.grid(row=5, column=1, sticky="NW")
        columnspin.delete(0, "end")
        columnspin.insert(0, 0)

        self.columnspin = columnspin
        self.LDspin = LDspin

        Voltagelabel = Label(self.separationframe, text="Voltage")
        Voltagelabel.grid(row=2, column=1, sticky="SW")
        Voltagespin = Spinbox(self.separationframe)
        Voltagespin.grid(row=3, column=1, sticky="NW")
        Voltagespin.delete(0, "end")
        Voltagespin.insert(0, 0)
        self.Vspin = Voltagespin
        self.peak_edit_first = True

        self.peak_edit(0, initial=True)
        # self.tree.grid()

    def on_resize(self, event):
        self.canvas.width = event.width
        self.canvas.height = event.height
        self.canvas.config(width=self.canvas.width, height=self.canvas.height)

    def separationstable(self):
        tree = Treeview(self.separationframe)

        # scrollbar = Scrollbar(self, orient="horizontal", command = tree.xview)
        # tree.configure(xscrollcommand=scrollbar.set)
        # scrollbar.grid(row = 3, column = 0, sticky = "NWE")
        # Define Columns
        tree["columns"] = ("ID", "Name", "Short Name",
                           "Buffer", "INJ Volume", "Plates")
        tree.column("ID", width=25)
        tree.column("Short Name", width=100)
        tree.column("INJ Volume", width=80)
        tree.column("Plates", width=50)
        tree.column("Buffer", width=110)
        tree.column("Name", width=225)
        tree.column("#0", width=125)
        # Define Headings
        # tree.heading("Date", text = "Date")
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Short Name", text="Short Name")
        tree.heading("Buffer", text="Buffer")
        tree.heading("INJ Volume", text="INJ V (nL)")
        tree.heading("Plates", text="Plates")
        # Define Event binding for selection
        tree.bind("<ButtonRelease-1>", self.separation_selection)
        # Call function to populate table
        tree.grid(sticky="NWS", rowspan=8)
        self.tree = tree
        self.fillseparationstable()

    def fillseparationstable(self):
        """Retrieve list of all unique separation dates,
        For each date create direcotry
            Within each directory add separation with matching date
        """
        # Clear previous separations
        self.clear_separation_tree()
        separationrows = {}
        dates = []
        session = self.session
        # print("Here?")
        for instance in session.query(db.Separation).filter(db.Separation.active.isnot(False)).order_by(
                db.Separation.date):
            separationrows[instance.id] = instance
            if dates.count(instance.date.isoformat()) == 0:
                # print(instance.id)
                # insert directory, label directory from datetime time isoform
                self.tree.insert("", 0, instance.date.isoformat(), text=instance.date.isoformat())
                dates.append(instance.date.isoformat())
            # Add values to the row
            # Retrieve buffer name
            if instance.buffer_id != None:
                buffername = session.query(db.Buffer).filter(db.Buffer.id == instance.buffer_id)
                buffername = buffername.first()
                buffername = buffername.name
            else:
                buffername = instance.buffer_id
                # declare values for the columns
            values = [instance.id, instance.name,
                      instance.shortname,
                      buffername, instance.injectionvolume]
            self.tree.insert(instance.date.isoformat(), END, instance.id,
                             text=str(instance.date.isoformat()),
                             values=values)
        if self.selection != 0:
            self.tree.item(self.selection, open=True)

    def export_separations(self):
        filename = dialog.asksaveasfilename()
        Fileconversion.ExportEgrams(self.peaksqueue, filename, self.session)

    def export_peaks(self):
        filename = dialog.asksaveasfilename()
        Fileconversion.ExportPeaks(self.peaksqueue, filename, self.engine)

    def newpeak(self):
        """Called to create a new peak
        Creates a new peak instance in db
        reloads peak tables"""
        sesh = self.session
        peak = db.Peak(name="New", run_id=self.instance.id)
        sesh.add(peak)
        sesh.commit()
        self.fillpeakstable(self.peaksqueue)

    def peakstable(self):

        tree = Treeview(self.peakframe)
        scrollbar = Scrollbar(self, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.grid(row=5, column=0, sticky="NWE")
        # self.peakcanvas.create_window((0,0),window = tree, anchor = "nw")

        # Define Columns
        tree["columns"] = ("ID", "Run", "Center",
                           "Width at 1/2H", "Corrected Area", "Corrected Area %", 'SNR',
                           "Resolution", "Plates", "Uep", "M2", "M3", "M4", "Max",)
        # Define Headings
        tree.column("ID", width=25)
        tree.column("Corrected Area", width=50)
        tree.column("Corrected Area %", width=50)
        tree.column("SNR",width = 50)
        tree.column("Width at 1/2H", width=50)
        tree.column("Center", width=50)
        tree.column("Plates", width=50)
        tree.column("Uep", width=50)
        tree.column("M2", width=40)
        tree.column("M4", width=40)
        tree.column("M3", width=40)
        tree.column("Max", width=50)
        tree.column("Run", width=125)
        tree.column("#0", width=150)
        # tree.column("Name", width = 100)
        tree.column("Resolution", width=50)
        tree.heading("Run", text="Run")

        # tree.heading("ID", text = "ID")
        # tree.heading("Short Name", text = "Short Name")
        # tree.heading("Separation", text = "Separation")
        tree.heading("Center", text="Tr")
        tree.heading("Plates", text="P")
        tree.heading("Uep", text="Uep (cm^2/(Vs))")
        tree.heading("M2", text="M2")
        tree.heading("M3", text="M3")
        tree.heading("M4", text="M4")
        tree.heading("Max", text="Max")
        tree.heading("Width at 1/2H", text="FWHM")
        tree.heading("Corrected Area", text="CA")
        tree.heading("Corrected Area %", text="CA%")
        tree.heading("SNR", text = 'SNR')
        tree.heading("Resolution", text="R")
        # tree.heading("Name", text = "Name")
        tree.heading("ID", text="ID")
        tree.heading("#0", text="Name")
        tree.grid(row=1, column=0, rowspan=4)
        # Bind event when item is selected
        tree.bind("<ButtonRelease-1>", self.peak_selection)
        # tree.config(scrollregion = ("left", "top", "right", "bottom"))
        # Call function to populate table
        self.treepeak = tree
        self.fillpeakstable()

        return tree

    def fillpeakstable(self, queue=[]):
        """
        Retrieve list of all unique peaks in selected separations,
        For each unique peak create a directory,
            Witin each directory add separation peak with matching peak
        """
        # clear old data
        self.clear_peak_tree()
        selectionlist = queue
        self.peaksqueue = queue  # preserve queue for reloading
        session = self.session
        peak = []
        if len(selectionlist) == 0:
            return
        for instance in session.query(db.Peak).filter(db.Peak.run_id.in_(selectionlist), db.Peak.active.isnot(False)):
            # print(instance.id, "is peak id", instance.name)
            if peak.count(instance.name) == 0:
                self.treepeak.insert("", END, instance.name, text=instance.name, open=True)
                peak.append(instance.name)
            runname = session.query(db.Separation).filter(db.Separation.id == instance.run_id)
            runname = runname.first()
            runname = runname.name
            kwds = self._get_kwds(instance)
            if not kwds:
                snr = 'NA'
            else:
                try:
                    snr = kwds['snr']
                except KeyError:
                    snr = 'NA'
            values = [instance.id, runname, instance.m1,
                      instance.fwhm, instance.correctedarea,
                      instance.correctedpercent, snr,  instance.resolution,
                      instance.plates, instance.apparentmobility,
                      instance.m2, instance.m3, instance.m4,
                      instance.maxtime]
            self.treepeak.insert(instance.name, 0, instance.id,
                                 text=str(instance.shortname),
                                 values=values, open=True)

        # set peak instance to None

        self.peakinstance = None

    def separation_selection(self, event):
        """ When List tree is clicked, highlighed rows will be used to obtain all
        separation id's for the higlighed rows"""
        selection = self.tree.selection()  # get selected rows
        queue = []
        # print("Selection is ", selection)
        first = True
        for item in selection:
            self.tree.item(item)
            # print(item)
            if first:
                try:
                    self.separation_edit(item)
                except:  # Keep track of our directories and keep them open when we want them to be open
                    if item == self.selection:
                        self.selection = 0
                    else:
                        self.selection = item  # Allow first selection item to be edited
            queue.append(item)  # append separation ID (from 2nd column) to queue
        # print("Queue is :" , queue)
        self.fillpeakstable(queue)  # Pass to load peaks
        self.load_separation(queue)  # Pass to load function that retrieves Time, RFu data

    def peak_selection(self, event):
        """ When List tree is clicked, highlighed rows will be used to obtain all
        separation id's for the higlighed rows"""
        selection = self.treepeak.selection()  # get selected rows
        queue = []
        # print("Selection is ", selection)
        first = True
        self.displayelectropherogram(self.data)
        for instance in self.session.query(db.Peak).filter(db.Peak.id.in_(selection)).order_by(db.Peak.area.desc()):
            item = instance.id
            # for item in selection:

            if first:
                self.peak_edit(item)  # Allow first selection item to be edited
            self.plot_area(item)
            queue.append(item)  # append separation ID (from 2nd column) to queue
        # self.fillpeakstable(queue)
        # print("Queue is :" , queue)
        # self.load_separation(queue) # Pass to load function that retrieves Time, RFu data

    def plot_area(self, peak_id):
        """ Gets peak instance, extracts starttime & stoptime, plots area under curve """
        query = self.session.query(db.Peak).filter(db.Peak.id == peak_id)
        instance = query.first()
        start = instance.starttime
        stop = instance.stoptime
        # X = np.arange(start,stop,0.25)
        """
        query = self.session.query(db.Separation).filter(db.Separation.id == instance.run_id)
        separation = query.first()
        Time,RFU = Fileconversion.Readfile(separation.filename,True,True,False,False)
        new_baseline = peaks.baseline(RFU)
        
            
        RFU = new_baseline.correctedrfu
        """
        name, Time, RFU = self.rfu_data[instance.run_id]
        time = np.asarray(Time)
        if start != None and stop != None:
            condition = np.all([time >= start, time <= stop], axis=0)
            color = self.colors[instance.run_id]
            try:
                name, time, base = self.rfu_data[-instance.run_id]
                # base = new_baseline.peakutils_baseline(eval(self.polyspin.get()),eval(self.skipspin.get()))
            except Exception as e:
                # print(e)
                base = 0
            self.plotsubplot.fill_between(Time, base, RFU, where=condition, interpolate=True, color=color)
        self.plotcanvas.draw()

    def separation_edit(self, sep_id):
        """ Retrieves info for the sep_id
        User can edit: Name, Short Name (Text box)
        Buffer (Combobox)
        INJ Volume (Popup window)
        Apparent mobility (spinboxes)
        """
        # Retrieve information
        sesh = self.session
        instance = sesh.query(db.Separation).filter(db.Separation.id == sep_id)
        instance = instance.first()
        self.instance = instance
        self.buffers = {}
        self.bufferids = {}

        # print(instance)
        for buffer in sesh.query(db.Buffer).order_by(db.Buffer.name):
            self.buffers[buffer.name] = buffer.id
            self.bufferids[buffer.id] = buffer.name
        self.volume = instance.injectionvolume

        # Create Widgets
        editframe = Frame(self.separationframe)
        editframe.grid(column=0, row=11, columnspan=2, sticky="NWE")
        namelabel = Label(editframe, text="Name: ")
        namelabel.grid(row=0, column=0)
        self.nameentry = Entry(editframe, text=instance.name)
        self.nameentry.grid(row=1, column=0)
        shortnamelabel = Label(editframe, text="Shortname: ")
        shortnamelabel.grid(row=0, column=1)
        self.shortnameentry = Entry(editframe, text=instance.shortname)
        self.shortnameentry.grid(row=1, column=1)
        bufferlabel = Label(editframe, text="Buffer: ")
        bufferlabel.grid(row=0, column=2)
        bufferlist = list(self.buffers.keys())
        bufferlist.sort()

        self.bufferbox = Combobox(editframe, values=bufferlist)
        self.bufferbox.grid(row=1, column=2)
        injectionbutton = Button(editframe, text='Set Injection Volume',
                                 command=self.get_injectionvolume)
        injectionbutton.grid(row=1, column=3)
        saveeditsbutton = Button(editframe, text="Save Edits",
                                 command=self.save_edits)
        saveeditsbutton.grid(row=1, column=4)
        deletesep = Button(editframe, text="Delete Separation",
                           command=self.delete_separation)
        deletesep.grid(row=0, column=4)

        # set the entry boxes to appropriate values
        self.nameentry.delete(0, "end")
        self.nameentry.insert(0, instance.name)

        self.shortnameentry.delete(0, "end")
        self.shortnameentry.insert(0, str(instance.shortname))

        if instance.buffer_id != None:
            self.bufferbox.set(self.bufferids[instance.buffer_id])

            buffer_instance = sesh.query(db.Buffer).filter(db.Buffer.id == instance.buffer_id)
            buffer_instance = buffer_instance.first()

            # Set the voltage to either Keword (first choice) or Buffer Voltage (second choice)
        if instance.kwds != None:
            # #print("here we are", instance.kwds)
            kwds = eval(instance.kwds)

            self.Vspin.delete(0, "end")
            self.Vspin.insert(0, eval(kwds["V"]))
            # print("and we changed", kwds)
            self.LDspin.delete(0, "end")
            self.LDspin.insert(0, eval(kwds["Ld"]))
            # print("To the end!!!")
            try:
                self.columnspin.delete(0, "end")
                self.columnspin.insert(0, eval(kwds["Lc"]))
            except:
                self.columnspin.delete(0, "end")
                self.columnspin.insert(0, 30)
            try:
                self.polyspin.delete(0, "end")
                self.polyspin.insert(0, eval(kwds["degree"]))
                self.poly_value.set(kwds["poly_value"])
                self.skipspin.delete(0, "end")
                self.skipspin.insert(0, eval(kwds["skip"]))

            except:
                self.poly_value.set(0)

    def peak_edit(self, peak_id, initial=False):
        """ Retrieves info for the sep_id
        User can edit: Name, Short Name (Text box)
        Buffer (Combobox)
        INJ Volume (Popup window)
        """

        # Retrieve information
        try:
            if self.peak_edit_first == True:
                self.textvar_peakshortname = StringVar()
                self.textvar_peakname = StringVar()
                self.peak_edit_first = False
                # Create Widgets
                self.editframe = editframe = Frame(self.peakframe)
                editframe.grid(column=0, row=0, sticky="NWE")
                namelabel = Label(editframe, text="Name: ")
                namelabel.grid(row=0, column=0)
                self.peaknameentry = Entry(editframe, textvariable=self.textvar_peakname)
                self.peaknameentry.grid(row=1, column=0)
                shortnamelabel = Label(editframe, text="Shortname: ")
                shortnamelabel.grid(row=0, column=1)

                self.peakshortnameentry = Entry(editframe, textvariable=self.textvar_peakshortname)
                self.peakshortnameentry.grid(row=1, column=1)

                # self.peakbaseline = Button(editframe, command = self.set_baseline)
                # self.peakbaseline.grid(row = 1, column = 2)
                widthbutton = Button(editframe, text='Set Width',
                                     command=self.set_width)
                widthbutton.grid(row=1, column=2)
                saveeditsbutton = Button(editframe, text="Save Edits",
                                         command=self.save_peakedits)
                saveeditsbutton.grid(row=1, column=4)

                self.peakdelete = Button(editframe, text="DELETE Peak", command=self.delete_peak)
                self.peakdelete.grid(row=0, column=4)

                # Polynomial Buttons
                try:
                    self.poly_value = IntVar(editframe)
                    self.poly_value.set(0)
                    poly_button = Checkbutton(editframe, text="Poly Baseline",
                                              variable=self.poly_value, command=self.cb)
                    poly_button.grid(row=0, column=5, columnspan=2)
                    polylabel = Label(editframe, text="Degree")
                    polylabel.grid(row=1, column=6)
                    self.polyspin = Spinbox(editframe, width=5)
                    self.polyspin.grid(row=1, column=5, sticky="E")
                    self.polyspin.delete(0, "end")
                    self.polyspin.insert(0, 3)

                    self.skipspin = Spinbox(editframe, width=5)
                    self.skipspin.grid(row=1, column=6, padx=5)
                    self.skipspin.insert(0, 0)
                    skiplabel = Label(editframe, text="First Data to Skip")
                    skiplabel.grid(row=1, column=7, sticky="W")

                except Exception as e:
                    print(e)
                """-
                #Index Buttons
                indexbutton=Button(editframe,text = "AutoPeaks",command = self.auto_peak)
                indexbutton.grid(row = 0, column = 7, columnspan = 1)
                self.threshspin = Spinbox(editframe,from_= 0 , to= 1,  width =5)
                self.threshspin.grid(row = 0, column = 8)
                threshlabel = Label(editframe,text = "Thresh(0-1)")
                threshlabel.grid(row = 0, column = 9)
                self.distspin = Spinbox(editframe, width = 5)
                self.distspin.grid(row=1,column =8)
                distlabel = Label(editframe, text = "Index Separation")
                distlabel.grid(row =1, column = 9)
                self.threshspin.delete(0,"end")
                self.distspin.delete(0,"end")
                self.threshspin.insert(0,0.5)
                self.distspin.insert(0,1)
                """




        except:
            print("Already have editframe")
        if initial:
            return
        sesh = self.session
        instance = sesh.query(db.Peak).filter(db.Peak.id == peak_id)
        instance = instance.first()
        separation = sesh.query(db.Separation).filter(db.Separation.id == instance.run_id)
        separation = separation.first()
        self.peakinstance = instance
        self.coords = [instance.starttime, instance.stoptime]

        # Create Widgets
        editframe = self.editframe
        self.peaknameentry
        shortnamelabel = Label(editframe, text="Shortname: ")
        shortnamelabel.grid(row=0, column=1)

        if instance.shortname != None:
            self.textvar_peakname.set(instance.name)
            self.textvar_peakshortname.set(instance.shortname)

            self.peakshortnameentry.delete(0, "end")
            # print(instance.shortname , "is the shortname")
            self.peakshortnameentry.insert(0, self.textvar_peakshortname.get())

            self.peaknameentry.delete(0, "end")
            self.peaknameentry.insert(0, self.textvar_peakname.get())

        # self.peakbaseline = Button(editframe, command = self.set_baseline)
        # self.peakbaseline.grid(row = 1, column = 2)
        """
        # set the entry boxes to appropriate values
        self.peaknameentry.delete(0,"end")
        self.peaknameentry.insert(0,instance.name)

        self.peakshortnameentry.delete(0,"end")
        self.peakshortnameentry.insert(0,str(instance.shortname))
        """

        return

    def cb(self):
        # print("this is value", self.poly_value.get())
        return

    def delete_peak(self):
        self.peakinstance.active = False
        # Reolaod peaks
        self.fillpeakstable(self, self.peaksqueue)

    def delete_separation(self):
        self.instance.active = False
        self.session.commit()
        # Reload separations
        self.fillseparationstable()

    def set_width(self):
        coords = [self.startd, self.stopd]
        coords.sort()
        self.coords = coords
        return

    def new_noise(self):
        # Get the electropherogram
        separation = self.instance
        Time, RFU = Fileconversion.Readfile(separation.filename)
        RFU  = peaks.baseline(RFU)
        # Get the coordinates
        coords = [self.startd, self.stopd]
        coords.sort()

        self.noise = peaks.noise_calc(RFU, Time, coords)

    def get_injectionvolume(self):

        # Grab the capillary volume
        length = self.columnspin.get()

        # Open dialog box to get injection volume
        self.volume = Injection.injectionwindow(length, self)

    def save_edits(self):
        # Make changes
        self.instance.name = self.nameentry.get()
        self.instance.shortname = self.shortnameentry.get()
        try:
            bufferid = self.buffers[self.bufferbox.get()]
            self.instance.buffer_id = bufferid
        except:
            pass
        self.instance.injectionvolume = self.volume
        kwds = {}
        kwds["Ld"] = self.LDspin.get()
        kwds["V"] = self.Vspin.get()
        kwds["Lc"] = self.columnspin.get()
        kwds["poly_value"] = self.poly_value.get()
        kwds["degree"] = self.polyspin.get()
        kwds["skip"] = self.skipspin.get()
        kwds["noise"] = self.noise
        self.instance.kwds = str(kwds)

        # Commit changes to database
        self.session.commit()
        # Clear Tree, Reload tree.
        self.clear_separation_tree()
        self.fillseparationstable()

    def clear_separation_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def clear_peak_tree(self):
        for row in self.treepeak.get_children():
            self.treepeak.delete(row)

    def load_separation(self, queue):
        """Queries filenames for each Separation ID
        For each filename:
            open file
            save shortname, Time, RFU to dictionary, with key set to separation ID"""
        if queue == []:  # saves costly db search for no sequence
            return
        sesh = self.session
        self.currentqueue = queue  # allows us to reload with this same queue after edits
        data = {}
        for instance in sesh.query(db.Separation).filter(db.Separation.id.in_(queue)):
            Time, RFU = Fileconversion.Readfile(instance.filename)
            new_baseline = peaks.baseline(RFU)
            poly_value = False
            # print(self.poly_value.get(), "IS POLY VLU")
            try:
                if instance.kwds != None:
                    # #print("here we are", instance.kwds)
                    kwds = eval(instance.kwds)
                    if kwds["poly_value"] == 1:
                        poly_value = 1
                        degree = eval(kwds["degree"])
                        skip = eval(kwds["skip"])
                    else:
                        poly_value = False

                    try:
                        self.noise = kwds['noise']
                    except KeyError:
                        self.noise = np.std(RFU[-20:])

            except Exception as e:
                # print(e)
                poly_value = False
            # print(type(poly_value),poly_value, "is recorded polyvalue")
            if poly_value == 1:
                baseline = new_baseline.peakutils_baseline(degree, skip)
                data[-instance.id] = [instance.shortname + 'BASELINE', Time, baseline]
            RFU = new_baseline.correctedrfu

            data[instance.id] = [instance.shortname, Time, RFU]
        self.rfu_data = data
        self.displayelectropherogram(data=data)  # Pass data to plot

    # print("Queue is still {} at load_separation".format(queue))
    # self.plotcanvas.draw()

    def plot_setup(self):
        """Plot setup at the __init__ stage"""
        # Set up canvas, and figure widgets
        plotframe = Frame(self.plotframe)
        plotframe.grid(column=0, row=0, sticky="NWE")
        plotfigure = Figure(figsize=(10, 5))
        self.plotsubplot = plotfigure.add_subplot(111)
        self.plotcanvas = FigureCanvasTkAgg(plotfigure, plotframe)
        self.plotcanvas.draw()
        self.plotcanvas.get_tk_widget().grid(column=0, row=0)
        plottool = tk.Frame(plotframe)
        plottool.grid(column=0, row=1, rowspan=1)
        toolbar = NavigationToolbar2Tk(self.plotcanvas, plottool)
        toolbar.update()
        plotfigure.canvas.mpl_connect('button_press_event', self.plotclick)
        # set flags for plotclick
        self.left_flag = True
        self.plotsubplot.clear()

    def displayelectropherogram(self, data, **kwargs):
        """Data = [separation_id's], from Data dictionary plot each separation time, RFU Data"""
        self.plotsubplot.clear()  # clear old data
        self.data = data
        colors = ['orange', 'lightslategray', 'indianred', 'seagreen', 'mediumorchid', 'lightcoral']
        pick = 0
        self.colors = {}
        first_baseline = True
        for separation in data:
            # Plot Time, RFU and give each line a label for a legend
            label = data[separation][0]
            if label == None:
                label = ""
            # print(separation, "is separatoin")
            try:
                if separation < 0 and first_baseline:
                    first_baseline = False
                elif separation < 0 and not first_baseline:
                    continue
            except Exception as e:
                pass
            self.colors[separation] = colors[pick]
            self.plotsubplot.plot(data[separation][1], data[separation][2], label=data[separation][0],
                                  color=colors[pick])
            pick += 1
            if pick == len(colors):
                pick = 0
        self.plotsubplot.legend()
        self.plotcanvas.draw()
        return

    def remove_lines(self):
        "Called when setting peak information"
        try:
            self.vline1.remove()
            self.vline2.remove()
        except:
            return
        try:
            v1, v2 = self.canvascoords['current']
            v1.remove()
            v2.remove()
        except:
            pass
            # print("no Lines")

    def auto_peak(self):
        sesh = self.session
        query = self.session.query(db.Separation).filter(db.Separation.id == self.instance.id)
        separation = query.first()
        data = Fileconversion.Readfile(separation.filename, True, True)

        baseline = peaks.baseline(data[1])

        peak = db.Peak(name="New", run_id=self.instance.id)
        sesh.add(peak)
        sesh.commit()
        self.fillpeakstable(self.peaksqueue)

    def save_peakedits(self):
        # print("Welcome to Peak edits save!")
        coords = self.coords
        inst = self.peakinstance
        inst.starttime = coords[0]
        inst.stoptime = coords[1]
        ymin, ymax = self.plotsubplot.get_ylim()
        self.remove_lines()
        # self.add_lines(coords,place)
        # Create a row for this peak in the datatable, calculate all peak statistics
        query = self.session.query(db.Separation).filter(db.Separation.id == inst.run_id)
        separation = query.first()
        data = Fileconversion.Readfile(separation.filename, True, True)
        # print(data)

        if self.poly_value.get() == 1:
            poly = eval(self.polyspin.get())
            skip = eval(self.skipspin.get())
        else:
            poly = False
            skip = 0



        peak = peaks.peakcalculations(data[0], data[1], coords[0], coords[1], poly=poly, skip=skip)

        # inst.('peaknumber',place)
        inst.name = self.peaknameentry.get()
        inst.shortname = self.peakshortnameentry.get()
        inst.starttime = peak.get_starttime()
        inst.stoptime = peak.get_stoptime()
        inst.m1 = round(peak.get_m1(), 2)
        inst.m2 = round(peak.get_m2(), 2)
        inst.m3 = round(peak.get_m3(), 4)
        inst.m4 = round(peak.get_m4(), 4)
        inst.fwhm = round(peak.get_fwhm(), 2)
        inst.area = peak.get_area()
        inst.correctedarea = peak.get_correctedarea()
        try:
            noise = self._get_kwds(separation)['noise']
            kwds = self._get_kwds(inst)
            if not kwds:
                kwds={}
            kwds['snr']= peak.get_snr(noise)
            inst.kwds=str(kwds)
        except KeyError:
            print("No noise has been recorded")
        # Calculate percent area and resolution and plates
        try:
            allpeak = peaks.allpeakcalculations(self.instance.id, self.session)
        except Exception as e:
            # pass
            # print("Not enough data for percent area and plates")
            # allpeak=peaks.allpeakcalculations(self.instance.id,self.session)
            print(e)
        # Add the row to the database
        self.session.commit()
        # Reload the plot
        self.plotcanvas.draw()
        # Reload the table
        self.fillpeakstable(self.peaksqueue)

    def plotclick(self, event):
        """When the user clicks on the graph it records information about where 
        they click and displays vertical lines on the click mark"""
        # print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f')
        # (event.button, event.x, event.y, event.xdata, event.ydata))
        ymin, ymax = self.plotsubplot.get_ylim()
        if self.left_flag:
            self.startd = event.xdata

            self.left_flag = False
            try:
                self.vline1.remove()
            except:
                self.vline1 = None
            self.vline1 = self.plotsubplot.vlines(event.xdata, ymax * .1, ymax * 0.9, color='b')

        else:
            self.stopd = event.xdata
            try:
                self.vline2.remove()
            except:
                self.vline2 = None
            self.vline2 = self.plotsubplot.vlines(event.xdata, ymax * .1, 0.9 * ymax, color='b')

            self.left_flag = True
        self.plotcanvas.draw()

    @staticmethod
    def _get_kwds(inst):
        """ Get kwds if exists, otherwise returns false"""
        if inst.kwds != None:
            return eval(inst.kwds)
        else:
            return False
