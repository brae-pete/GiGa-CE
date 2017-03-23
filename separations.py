""" From mainmenu
    From buffers with buffer id

"""
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
#import mainmenu
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
    def __init__(self, parent, controller, session,user, *args):
        tk.Frame.__init__(self,parent) # initialize frame
        self.controller= controller # save to move between windows
        self.session=session
        self.user=user
        # Create buttons that will move between different windows

        bufferbutton=tk.Button(self, text = "Analyze New Separations",
                               command = self.openseparations)
        bufferbutton.grid()
        
        instrumentbutton=tk.Button(self, text = "View old separation",
                                )#command = self.queryseparations)
        
        mainmenubutton=tk.Button(self, text = "Go to Main Menu",
                                command = lambda: controller.show_frame\
                               (mainmenu.mainmenu))
        mainmenubutton.grid()
    def openseparations(self):
        queue=dialog.askopenfilenames()
        session=self.session
        
        for file in queue:
            shortfile = file.split('/')
            print('Shortfile', shortfile[-1])
            
            newrun=db.Separation(date = dt.date.today(), name = shortfile[-1])
            session.add(newrun)
            session.commit()
            newfile = self.filetype(file,new_id=newrun.id)
            newrun.filename = newfile
            session.commit()
            
        # convert queue?
        frame=self.controller.frames["separationview"]
        
        frame.clear_separation_tree()
        frame.fillseparationstable()# update frame
        self.controller.show_frame("separationview")
        
    def filetype(self, filename, new_id):
        " Determines the file type and calls appropriate conversion"
        last = filename[-3:].upper()

        if last == "ASC":
            newfile = Fileconversion.ASCconversion(filename,new_id,self.user)
            return newfile
        else:
            print('TXT conversion is not available')
            return
            #TXTconversion(filename, new_id)
        
        
        

        
    
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
    Tree View
        Allows users to select multiple peaks to compare across separations (same short name)
        Allows users to select multiple separations to compare electropherograms and peak information
    Export
        Exports selected separations to csv for ORIGIN
        Exports selected separations+peak info for excel    
""" 
    def __init__(self,parent, controller,session,user, *args, **kwargs):
        """Requires: User(Str)"""
        tk.Frame.__init__(self,parent) # initialize frame
        self.session=session
        self.selection = 0
        #self.session=self.dbengine.get_session()
        self.separationstable()
        self.peakstable()
       
        self.plot_setup()

        Addpeakbutton = Button(self,text = "Add Peak", command = self.newpeak)
        Addpeakbutton.grid(row = 2, column =2, sticky = "W")
        self.controller=controller
        frame = Frame(self)
        frame.grid(row = 4,column = 0, columnspan = 2)
        button = Button(frame, text = "Main Menu", command = lambda: self.controller.show_frame("mainmenu"))
        button.grid(column = 0)
        button2 = Button(frame, text = "Export Electropherograms", command = self.export_separations)
        button2.grid(column = 1)
        

        button2 = Button(self, text = "Export Electropherograms", command = self.export_separations)
        button2.grid(column = 2)
        #self.tree.grid()

    def separationstable(self):
        tree= Treeview(self)
        # Define Columns
        tree["columns"]=("ID","Name","Short Name",
                         "Buffer", "INJ Volume", "Plates")
        tree.column("ID", width = 25)
        tree.column("Short Name", width = 75)
        tree.column("INJ Volume", width = 80)
        tree.column("Plates", width = 50)
        tree.column("Buffer", width = 100)
        tree.column("Name", width = 125)
        tree.column("#0", width = 150)
        # Define Headings
        #tree.heading("Date", text = "Date")
        tree.heading("ID", text = "ID")
        tree.heading("Name", text = "Name")
        tree.heading("Short Name", text = "Short Name")
        tree.heading("Buffer", text = "Buffer")
        tree.heading("INJ Volume", text = "INJ V (nL)")
        tree.heading("Plates", text = "Plates")
        # Define Event binding for selection
        tree.bind("<ButtonRelease-1>",self.separation_selection)
        #Call function to populate table
        tree.grid(sticky = "NWE")
        self.tree = tree
        self.fillseparationstable()
        
    def fillseparationstable(self):
        """Retrieve list of all unique separation dates,
        For each date create direcotry
            Within each directory add separation with matching date
        """
        # Clear previous separations
        self.clear_separation_tree()
        separationrows={}
        dates=[]
        session = self.session
        print("Here?")
        for instance in session.query(db.Separation).filter(db.Separation.active.isnot(False)).order_by(db.desc(db.Separation.date)):
            separationrows[instance.id]=instance
            if dates.count(instance.date.isoformat())==0:
                print(instance.id)
                #insert directory, label directory from datetime time isoform
                self.tree.insert("",0,instance.date.isoformat(),text = instance.date.isoformat())
                dates.append(instance.date.isoformat())
            #Add values to the row
                # Retrieve buffer name
            if instance.buffer_id != None:
                buffername = session.query(db.Buffer).filter(db.Buffer.id == instance.buffer_id)
                buffername = buffername.first()
                buffername = buffername.name
            else:
                buffername=instance.buffer_id
                # declare values for the columns
            values=[instance.id, instance.name,
                    instance.shortname,
                    buffername, instance.injectionvolume]
            self.tree.insert(instance.date.isoformat(),END,instance.id,
                             text = str(instance.date.isoformat()),
                             values = values)
        if self.selection != 0 :
            self.tree.item(self.selection, open = True)

    def export_separations(self):
        filename = dialog.asksaveasfilename()
        Fileconversion.ExportEgrams(self.peaksqueue,filename,self.session)
    def newpeak(self):
        """Called to create a new peak
        Creates a new peak instance in db
        reloads peak tables"""
        sesh = self.session
        peak=db.Peak(name = "New", run_id= self.instance.id)
        sesh.add(peak)
        sesh.commit()
        self.fillpeakstable(self.peaksqueue)
        
    def peakstable(self):
        
        tree= Treeview(self)
        scrollbar = Scrollbar(self, orient="horizontal", command = self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.grid(row = 3, column = 0, sticky = "NWE")
        #self.peakcanvas.create_window((0,0),window = tree, anchor = "nw")
        
        #Define Columns
        tree["columns"]=("ID","Run", "Center",
                         "Width at 1/2H", "Corrected Area", "Corrected Area %",
                         "Resolution", "Plates", "M2", "M3", "M4", "Max",)
        #Define Headings
        tree.column("ID", width = 25)
        tree.column("Corrected Area", width = 50)
        tree.column("Corrected Area %", width = 50)
        tree.column("Width at 1/2H", width = 50)
        tree.column("Center", width = 50)
        tree.column("Plates", width = 50)
        tree.column("M2", width = 40)
        tree.column("M4", width = 40)
        tree.column("M3", width = 40)
        tree.column("Max", width = 50)
        tree.column("Run", width = 125)
        tree.column("#0", width = 150)
        #tree.column("Name", width = 100)
        tree.column("Resolution", width = 50)
        tree.heading("Run", text = "Run")
        
        #tree.heading("ID", text = "ID")
        #tree.heading("Short Name", text = "Short Name")
        #tree.heading("Separation", text = "Separation")
        tree.heading("Center", text = "Tr")
        tree.heading("Plates", text = "P")
        tree.heading("M2", text = "M2")
        tree.heading("M3", text = "M3")
        tree.heading("M4", text = "M4")
        tree.heading("Max", text = "Max")
        tree.heading("Width at 1/2H", text = "FWHM")
        tree.heading("Corrected Area", text = "CA")
        tree.heading("Corrected Area %", text = "CA%")
        tree.heading("Resolution", text = "R")
        #tree.heading("Name", text = "Name")
        tree.heading("ID", text = "ID")
        tree.heading("#0", text = "Name")
        tree.grid(row = 2, column =0)
        # Bind event when item is selected
        tree.bind("<ButtonRelease-1>",self.peak_selection)
        #tree.config(scrollregion = ("left", "top", "right", "bottom"))
        #Call function to populate table
        self.treepeak = tree
        self.fillpeakstable()
        
        return tree

    def fillpeakstable(self,queue=[]):
        """
        Retrieve list of all unique peaks in selected separations,
        For each unique peak create a directory,
            Witin each directory add separation peak with matching peak
        """
        # clear old data
        self.clear_peak_tree()
        selectionlist=queue
        self.peaksqueue=queue # preserve queue for reloading
        session = self.session
        peak = []
        if len(selectionlist)==0 :
            return
        for instance in session.query(db.Peak).filter(db.Peak.run_id.in_(selectionlist),db.Peak.active.isnot(False)):
            print(instance.id, "is peak id", instance.name)
            if peak.count(instance.name) == 0:
                self.treepeak.insert("",END,instance.name,text = instance.name, open=True)
                peak.append(instance.name)
            runname = session.query(db.Separation).filter(db.Separation.id == instance.run_id)
            runname = runname.first()
            runname = runname.name

            values = [ instance.id, runname, instance.m1,
                       instance.fwhm, instance.correctedarea,
                       instance.correctedpercent, instance.resolution,
                       instance.plates,
                       instance.m2, instance.m3, instance.m4,
                       instance.maxtime]
            self.treepeak.insert(instance.name,0,instance.id,
                                 text = str(instance.shortname),
                                 values = values, open = True)

        #set peak instance to None

        self.peakinstance = None
        
                     
    def separation_selection(self,event):
        """ When List tree is clicked, highlighed rows will be used to obtain all
        separation id's for the higlighed rows"""
        selection = self.tree.selection() # get selected rows
        queue=[]
        #print("Selection is ", selection)
        first = True
        for item in selection:
            self.tree.item(item)
            #print(item)
            if first:
                try:
                    self.separation_edit(item)
                except: # Keep track of our directories and keep them open when we want them to be open
                    if item == self.selection:
                        self.selection = 0
                    else:
                        self.selection = item# Allow first selection item to be edited
            queue.append(item) # append separation ID (from 2nd column) to queue
        #print("Queue is :" , queue)
        self.fillpeakstable(queue) # Pass to load peaks
        self.load_separation(queue)# Pass to load function that retrieves Time, RFu data
    def peak_selection(self,event):
        """ When List tree is clicked, highlighed rows will be used to obtain all
        separation id's for the higlighed rows"""
        selection = self.treepeak.selection() # get selected rows
        queue=[]
        print("selection is ::" , selection)
        #print("Selection is ", selection)
        first = True
        self.displayelectropherogram(self.data)
        for instance in self.session.query(db.Peak).filter(db.Peak.id.in_(selection)).order_by(db.Peak.area.desc()):
            item = instance.id
        #for item in selection:
            print(item)
            if first:
                self.peak_edit(item) # Allow first selection item to be edited
            self.plot_area(item)
            queue.append(item) # append separation ID (from 2nd column) to queue
        #self.fillpeakstable(queue)
        #print("Queue is :" , queue)
        #self.load_separation(queue) # Pass to load function that retrieves Time, RFu data
    def plot_area(self, peak_id):
        """ Gets peak instance, extracts starttime & stoptime, plots area under curve """
        query = self.session.query(db.Peak).filter(db.Peak.id == peak_id)
        instance = query.first()
        start = instance.starttime
        stop = instance.stoptime
        #X = np.arange(start,stop,0.25)
        query = self.session.query(db.Separation).filter(db.Separation.id == instance.run_id)
        separation = query.first()
        Time,RFU = Fileconversion.Readfile(separation.filename,True,True,False,False)
        time = np.asarray(Time)
        if start != None and stop != None:
            condition = np.all([time >=start, time<=stop],axis = 0 )
            color = self.colors[separation.id]
            self.plotsubplot.fill_between(Time,0,RFU, where =condition,interpolate = True, color =color)
        self.plotcanvas.draw()
        
    def separation_edit(self, sep_id):
        """ Retrieves info for the sep_id
        User can edit: Name, Short Name (Text box)
        Buffer (Combobox)
        INJ Volume (Popup window)
        """
        # Retrieve information
        sesh = self.session
        instance = sesh.query(db.Separation).filter(db.Separation.id == sep_id)
        instance = instance.first()
        self.instance = instance
        self.buffers = {}
        self.bufferids={}
    
        print(instance)
        for buffer in sesh.query(db.Buffer):
            self.buffers[buffer.name]=buffer.id
            self.bufferids[buffer.id]=buffer.name
        self.volume = instance.injectionvolume

        # Create Widgets
        editframe=Frame(self)
        editframe.grid(column = 0, row = 1, sticky = "NWE")
        namelabel = Label(editframe, text = "Name: ")
        namelabel.grid(row = 0, column = 0)
        self.nameentry= Entry(editframe, text = instance.name)
        self.nameentry.grid(row = 1, column = 0)
        shortnamelabel = Label(editframe, text = "Shortname: ")
        shortnamelabel.grid(row = 0, column = 1)
        self.shortnameentry = Entry(editframe, text = instance.shortname)
        self.shortnameentry.grid(row = 1, column = 1)
        bufferlabel = Label(editframe, text = "Buffer: ")
        bufferlabel.grid(row = 0, column = 2)
        self.bufferbox = Combobox(editframe, values = list(self.buffers.keys()))
        self.bufferbox.grid(row = 1, column = 2)
        injectionbutton= Button(editframe, text = 'Set Injection Volume',
                                command = self.get_injectionvolume)
        injectionbutton.grid(row = 1, column = 3)
        saveeditsbutton= Button (editframe, text = "Save Edits",
                                 command = self.save_edits)
        saveeditsbutton.grid(row = 1, column = 4)
        deletesep = Button(editframe, text = "Delete Separation",
                           command =self.delete_separation)
        deletesep.grid(row = 0, column = 4)

        # set the entry boxes to appropriate values
        self.nameentry.delete(0,"end")
        self.nameentry.insert(0,instance.name)

        self.shortnameentry.delete(0,"end")
        self.shortnameentry.insert(0,str(instance.shortname))
        if instance.buffer_id != None:
            self.bufferbox.set(self.bufferids[instance.buffer_id])
    def peak_edit(self, peak_id):
        """ Retrieves info for the sep_id
        User can edit: Name, Short Name (Text box)
        Buffer (Combobox)
        INJ Volume (Popup window)
        """
        
        # Retrieve information
        try:
            self.editframe.destroy()
        except:
            flag=True
        sesh = self.session
        instance = sesh.query(db.Peak).filter(db.Peak.id == peak_id)
        instance = instance.first()
        print("peak_id is ", peak_id)
        separation = sesh.query(db.Separation).filter(db.Separation.id == instance.run_id)
        separation = separation.first()
        self.peakinstance = instance
        # set width
        
        self.coords=[instance.starttime,instance.stoptime]
        
        print(instance)
        
        # Create Widgets
        self.editframe=editframe=Frame(self)
        editframe.grid(column = 1, row = 2, sticky = "NWE")
        namelabel = Label(editframe, text = "Name: ")
        namelabel.grid(row = 0, column = 0)
        self.peaknameentry= Entry(editframe, text = instance.name)
        self.peaknameentry.grid(row = 1, column = 0)
        shortnamelabel = Label(editframe, text = "Shortname: ")
        shortnamelabel.grid(row = 0, column = 1)
        self.peakshortnameentry = Entry(editframe, text = instance.shortname)
        self.peakshortnameentry.grid(row = 1, column = 1)
       
        #self.peakbaseline = Button(editframe, command = self.set_baseline)
        #self.peakbaseline.grid(row = 1, column = 2)
        widthbutton= Button(editframe, text = 'Set Width',
                                command = self.set_width)
        widthbutton.grid(row = 1, column = 2)
        saveeditsbutton= Button (editframe, text = "Save Edits",
                                 command = self.save_peakedits)
        saveeditsbutton.grid(row = 1, column = 4)


        # set the entry boxes to appropriate values
        self.peaknameentry.delete(0,"end")
        self.peaknameentry.insert(0,instance.name)

        self.peakshortnameentry.delete(0,"end")
        self.peakshortnameentry.insert(0,str(instance.shortname))

        self.peakdelete= Button(editframe, text = "DELETE Peak", command = self.delete_peak)
        self.peakdelete.grid(row =0, column = 4)
    
        
        return
    def delete_peak(self):
        self.peakinstance.active = False
        #Reolaod peaks
        self.fillpeakstable(self,self.peaksqueue)
        
    def delete_separation(self):
        self.instance.active = False
        # Reload separations
        self.fillseparationstable()
        
    def set_width(self):
        coords=[self.startd,self.stopd]
        coords.sort()
        self.coords=coords
        return 
        
    def get_injectionvolume(self):
    
        # Grab Buffer information which holds capillary information
        bufferid = self.buffers[self.bufferbox.get()]
        buffer = self.session.query(db.Buffer).filter(db.Buffer.id==bufferid)
        buffer = buffer.first()

        # Open dialog box to get injection volume
        self.volume = 0
        starter = Injection.injectionwindow(buffer, self)
      
    def save_edits(self):
        # Make changes
        self.instance.name = self.nameentry.get()
        self.instance.shortname = self.shortnameentry.get()
        bufferid = self.buffers[self.bufferbox.get()]
        self.instance.buffer_id = bufferid
        self.instance.injectionvolume = self.volume
        
        #Commit changes to database
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
            
    

        
    def load_separation(self,queue):
        """Queries filenames for each Separation ID
        For each filename:
            open file
            save shortname, Time, RFU to dictionary, with key set to separation ID"""
        if queue == []: # saves costly db search for no sequence
            return
        sesh=self.session
        self.currentqueue=queue # allows us to reload with this same queue after edits
        data = {}
        for instance in sesh.query(db.Separation).filter(db.Separation.id.in_(queue)):
            Time,RFU=Fileconversion.Readfile(instance.filename)
            data[instance.id]=[instance.shortname,Time,RFU]
        self.displayelectropherogram(data=data) # Pass data to plot
        print("Queue is still {} at load_separation".format(queue))
        self.plotcanvas.draw()
    
    def plot_setup(self):
        """Plot setup at the __init__ stage"""
    #Set up canvas, and figure widgets
        plotframe = Frame(self)
        plotframe.grid(column = 1, row = 0, rowspan = 2, sticky = "NWE")
        plotfigure= Figure(figsize=(6.25,3))
        self.plotsubplot=plotfigure.add_subplot(111)
        self.plotcanvas = FigureCanvasTkAgg(plotfigure, plotframe)
        self.plotcanvas.show()
        self.plotcanvas.get_tk_widget().grid(column = 0 ,row = 0)
        plottool=tk.Frame(plotframe)
        plottool.grid(column = 0, row = 1, rowspan = 1)
        toolbar=NavigationToolbar2TkAgg(self.plotcanvas,plottool)
        toolbar.update()
        plotfigure.canvas.mpl_connect('button_press_event',self.plotclick)
        # set flags for plotclick
        self.left_flag = True
        self.plotsubplot.clear()
    def displayelectropherogram(self,data, **kwargs):
        """Data = [separation_id's], from Data dictionary plot each separation time, RFU Data"""
        self.plotsubplot.clear() # clear old data
        self.data = data
        colors = ['orange','lightslategray','indianred','seagreen','mediumorchid','lightcoral']
        pick = 0
        self.colors={}
        for separation in data:
            #Plot Time, RFU and give each line a label for a legend
            label = data[separation][0]
            if label == None:
                label = ""
            self.colors[separation]=colors[pick]
            self.plotsubplot.plot(data[separation][1],data[separation][2],label = data[separation][0], color = colors[pick])
            pick +=1
            if pick == len(colors):
                pick = 0 
        self.plotsubplot.legend()
        self.plotcanvas.draw()
        return
    def remove_lines(self):
        "Called when setting peak information"
        self.vline1.remove()
        self.vline2.remove()
        try:
            v1,v2=self.canvascoords['current']
            v1.remove()
            v2.remove()
        except:
            print("no Lines")
    def save_peakedits(self):
        print("Welcome to Peak edits save!")
        coords=self.coords
        inst = self.peakinstance
        inst.starttime=coords[0]
        inst.stoptime=coords[1]
        ymin,ymax=self.plotsubplot.get_ylim()
        self.remove_lines()
        #self.add_lines(coords,place)
        #Create a row for this peak in the datatable, calculate all peak statistics
        query = self.session.query(db.Separation).filter(db.Separation.id == inst.run_id)
        separation = query.first()
        data = Fileconversion.Readfile(separation.filename,True,True)
        #print(data)
        peak=peaks.peakcalculations(data[0],data[1],coords[0],coords[1])
        #inst.('peaknumber',place)
        inst.name = self.peaknameentry.get()
        inst.shortname= self.peakshortnameentry.get()
        inst.starttime=peak.get_starttime()
        inst.stoptime=peak.get_stoptime()
        inst.m1=round(peak.get_m1(),2)
        inst.m2=round(peak.get_m2(),2)
        inst.m3=round(peak.get_m3(),4)
        inst.m4=round(peak.get_m4(),4)
        inst.fwhm=round(peak.get_fwhm(),2)
        inst.area=round(peak.get_area(),2)
        inst.correctedarea=round(peak.get_correctedarea(),2)
        # Calculate percent area and resolution and plates
        allpeak=peaks.allpeakcalculations(self.instance.id,self.session)
        
        
        #Add the row to the database 
        self.session.commit()
        # Reload the plot
        self.plotcanvas.draw()
        # Reload the table
        self.fillpeakstable(self.peaksqueue)
    def plotclick(self,event):
        """When the user clicks on the graph it records information about where 
        they click and displays vertical lines on the click mark"""
        #print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f')
        #(event.button, event.x, event.y, event.xdata, event.ydata)) 
        ymin,ymax=self.plotsubplot.get_ylim()
        if self.left_flag:
            self.startd=event.xdata
            
            self.left_flag=False
            try:
                self.vline1.remove()
            except:
                self.vline1=None
            self.vline1=self.plotsubplot.vlines(event.xdata,ymax*.1,ymax*0.9,color='b')  
            
        else:
            self.stopd=event.xdata
            try:
                self.vline2.remove()
            except:
                self.vline2=None
            self.vline2=self.plotsubplot.vlines(event.xdata,ymax*.1,0.9*ymax,color='b')
            
            self.left_flag=True
        self.plotcanvas.draw()
    
        
