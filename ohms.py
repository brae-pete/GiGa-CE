"""From mainmenu 
   From buffersettings with buffer ID

"""
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
#import mainmenu

import additives
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as dialog
import numpy as np
import datetime as dt
import database as db
import Fileconversion
class ohmsmenu(tk.Frame):
    """Ohms Menu
    MENU
        1) Analyze multiple new ohms plots
            a) Requests directory
        2) Analyze single new ohms plot
            a) request filename
        3) View previous ohms plots
            a) export plots to excel
            b) export plots to jpeg

    Function1: opens multiple ohms plot queue window
    Function2: opens single ohms plot queue window
    Function3: opens table of buffers + ohms plot data
    """
    def __init__(self, parent, controller, session,user, *args):
        tk.Frame.__init__(self,parent) # initialize frame
        self.controller= controller # save to move between windows
        self.session=session
        self.user=user
        # Create buttons that will move between different windows

        bufferbutton=tk.Button(self, text = "Analyze New Ohms",
                               command = self.openohms)
        bufferbutton.grid()
        
        instrumentbutton=tk.Button(self, text = "View old separation",
                                )#command = self.queryseparations)
        
        mainmenubutton=tk.Button(self, text = "Go to Main Menu",
                                command = lambda: controller.show_frame\
                               (mainmenu.mainmenu))
        mainmenubutton.grid()
    def openohms(self):
        queue=dialog.askopenfilenames()
        
        session=self.session
        
        for file in queue:
            shortfile = file.split('/')
            print('Shortfile', shortfile[-1])
            
            newrun=db.Buffer(date = dt.date.today(), name = shortfile[-1])
            session.add(newrun)
            session.commit()
            newfile = self.filetype(file,new_id=newrun.id)
            newrun.ohmsfile = newfile
            session.commit()
            
        # convert queue?
        frame=self.controller.frames["ohmsview"]
        
        frame.clear_ohms_tree()
        frame.fillohmstable()# update frame
        self.controller.show_frame("ohmsview")
        
    def filetype(self, filename, new_id):
        " Determines the file type and calls appropriate conversion"
        last = filename[-3:].upper()

        if last == "ASC":
            newfile = Fileconversion.ASCconversion(filename,new_id,self.user,True)
            return newfile
        else:
            print('TXT conversion is not available')
            return
            #TXTconversion(filename, new_id)
        

class ohmsview(tk.Frame):
    """
    From ohmsmenu with none
    From ohmsqueue with ohms ID's
    From bufferproperties with ohm ID
    
    Function 1:List of all buffers with OHMS plots that have matching ID's
    Function3: Each filename is placed in table as buffer name,
    Function4: highlighed rows display ohms graph + voltage data + capillary info 
    Function5: button allows user to enter buffer properties information
    Function6: Checkboxes allow multiple plots to be viewed together
    Function7: Export to Excel/JPEG for all checkboxes
    """
   
    def __init__(self,parent, controller,session,user, *args, **kwargs):
        """Requires: User(Str)"""
        tk.Frame.__init__(self,parent) # initialize frame
        self.session=session
        #self.session=self.dbengine.get_session()
        self.ohmstable()
        
        self.plot_setup()# START HERE
        self.controller=controller

        mainmenu = Button(self, text = "Main Menu",
                          command = lambda: controller.show_frame("mainmenu"))
        mainmenu.grid()

        
        componentframe = Frame(self)
        self.componentframe=componentframe
        self.create_component_table(componentframe)
        self.ohms_edit()
        
        #self.tree.grid()

    def ohmstable(self):
        tree= Treeview(self)
        # Define Columns
        tree["columns"]=("ID","Name","pH",
                         "Ionicstrength", "Voltage", "Lumen", "Length")
        tree.column("ID", width = 25)
        tree.column("Length", width = 75)
        tree.column("Voltage", width = 50)
        tree.column("Lumen", width = 75)
        tree.column("Ionicstrength", width = 100)
        tree.column("Name", width = 125)
        tree.column("pH", width = 50)
        tree.column("#0", width = 150)
        # Define Headings
        #tree.heading("Date", text = "Date")
        tree.heading("ID", text = "ID")
        tree.heading("Name", text = "Name")
        tree.heading("Voltage", text = "Volts")
        tree.heading("Lumen", text = "Lumen(um)")
        tree.heading("Length", text = "Length(cm)")
        tree.heading("Ionicstrength", text = "mM")
        tree.heading("pH", text = "pH")
        # Define Event binding for selection
        tree.bind("<ButtonRelease-1>",self.ohms_selection)
        #Call function to populate table
        tree.grid(sticky = "NWE")
        self.tree = tree
        self.fillohmstable()

        button = Button(self, text = "Main Menu", command = lambda: self.controller.show_frame("mainmenu"))
        button.grid(column = 1)
    def fillohmstable(self):
        """Retrieve list of all unique separation dates,
        For each date create direcotry
            Within each directory add separation with matching date
        """
        ohmsrows={}
        dates=[]
        session = self.session
        self.clear_ohms_tree()
        for instance in session.query(db.Buffer).filter(db.Buffer.active.isnot(False)).order_by(db.desc(db.Buffer.date)):
            ohmsrows[instance.id]=instance
            if dates.count(instance.date.isoformat())==0:
                print(instance.id)
                #insert directory, label directory from datetime time isoform
                self.tree.insert("",0,instance.date.isoformat(),text = instance.date.isoformat())
                dates.append(instance.date.isoformat())
            #Add values to the row
           
                # declare values for the columns
            values=[instance.id, instance.name,instance.pH,
                    instance.ionicstrength,instance.ohmsvoltage, instance.capillarylumen,
                    instance.capillarylength]
            self.tree.insert(instance.date.isoformat(),END,instance.id,
                             text = str(instance.date.isoformat()),
                             values = values)
                     
    def ohms_selection(self,event):
        """ When List tree is clicked, highlighed rows will be used to obtain all
        separation id's for the higlighed rows"""
        selection = self.tree.selection() # get selected rows
        queue=[]
        print("Selection is ", selection)
        first = True
        for item in selection:
            #print(item)
            if first:
                self.reload_ohms_edit(item) # Allow first selection item to be edited
            queue.append(item) # append separation ID (from 2nd column) to queue
        #print("Queue is :" , queue)
        self.load_ohms(queue) # Pass to load function that retrieves Time, RFu data
    def additive_selection(self,event):
        """ When List tree is clicked, highlighed rows will be used to obtain all
        separation id's for the higlighed rows"""
        selection = self.componenttree.selection() # get selected rows
        queue=[]
        #print("Selection is ", selection)
        first = True
        for item in selection:
            #print(item)
            if first:
                self.additive_edit(item) # Allow first selection item to be edited
            queue.append(item) # append separation ID (from 2nd column) to queue
        #print("Queue is :" , queue)
        #self.load_separation(queue) # Pass to load function that retrieves Time, RFu data

    def additive_edit(self, additive_id):
        """Store Additive ID as class Field for deleting """
        
        sesh = self.session
        instance = sesh.query(db.Additive).filter(db.Additive.id == additive_id)
        instance = instance.first()
        self.additiveinstance = instance
        
    def ohms_edit(self):
        """ Retrieves info for the sep_id
        User can edit: Name, Short Name (Text box)
        Buffer (Combobox)
        INJ Volume (Popup window)
        """
        

        # create frame to place widgets in
        editframe=Frame(self)
        editframe.grid(column = 0, row = 1, sticky = "NWE")
        # Place componenet frame under this
        self.componentframe.grid(column = 0, row =2, sticky = "NWE")

        # Create Widgets
        namelabel = Label(editframe, text = "Name: ")
        
        namelabel.grid(row = 0, column = 0)
        self.nameentry= Entry(editframe)
        self.nameentry.grid(row = 1, column = 0)
        
        pHlabel = Label(editframe, text = "pH: ")
        pHlabel.grid(row = 0, column = 1)
        self.pHentry = Spinbox(editframe)
        self.pHentry.grid(row = 1, column = 1)
        
        Ventry = Label(editframe, text = "Voltage (V): ")
        Ventry.grid(row = 0, column = 2)
        self.Ventry = Spinbox(editframe)
        self.Ventry.grid(row = 1, column = 2)

        Lumenlabel = Label (editframe, text = " Capillary Lumen(um) " )
        Lumenlabel.grid(row = 0 , column = 3)
        self.Lumenentry = Spinbox(editframe)
        self.Lumenentry.grid(row = 1 , column = 3)
        

        Lengthlabel = Label ( editframe, text = "Capillary Length(cm)")
        Lengthlabel.grid( row = 0 , column = 4)
        self.Lentry= Spinbox(editframe)
        self.Lentry.grid(row = 1, column = 4)

        # SAVE Button 
        saveeditsbutton= Button (editframe, text = "Save Edits",
                                 command = self.save_edits)
        saveeditsbutton.grid(row = 1, column = 5)

        # Delete Button
        deletebutton= Button (editframe, text = "Delete Ohms",
                                 command = self.delete_ohms)
        deletebutton.grid(row = 0, column = 5)
        # Main Menu
        mainmenu = Button(editframe, text = "Main Menu",
                          command = lambda: self.controller.show_frame("mainmenu"))
        mainmenu.grid()

    def reload_ohms_edit(self, buffer_id):
        # Retrieve information
        sesh = self.session
        instance = sesh.query(db.Buffer).filter(db.Buffer.id == buffer_id)
        instance = instance.first()
        self.instance = instance
        
        # set the entry boxes to appropriate values
        self.nameentry.delete(0,"end")
        self.nameentry.insert(0,instance.name)

        self.pHentry.delete(0,"end")
        self.pHentry.insert(0,str(instance.pH))

        self.Ventry.delete(0,"end")
        self.Ventry.insert(0,str(instance.ohmsvoltage))

        self.Lumenentry.delete(0,"end")
        self.Lumenentry.insert(0,str(instance.capillarylumen))

        self.Lentry.delete(0,"end")
        self.Lentry.insert(0,str(instance.capillarylength))
        self.clear_component_table()
        self.set_component_table(instance.id)

    def set_component_table(self,buffer_id):
        sesh = self.session
        tree = self.componenttree
        # Query all additives with the matching buffer id
        for instance in sesh.query(db.Additive).filter(db.Additive.bufferc_id == buffer_id,
                                                       db.Additive.active.isnot(False)):
            query = sesh.query(db.Chemical).filter(db.Chemical.id == instance.chemical_id)
            chemical = query.first()
            name = chemical.name
            values=[instance.id, name,instance.concentration]
            tree.insert("",0,instance.id,
                             values = values)
        self.componenttree=tree # this may be redundant, I think objects go beyond global scope but to be safe I do this

        # 
    def create_component_table(self, frame):
        tree= Treeview(frame)
        # Define Columns
        tree["columns"]=("ID","Name","Concentration")
        tree.column("ID", width = 25)
        tree.column("Name", width = 125)
        tree.column("Concentration", width = 125)
        tree.column("#0", width = 5)
        # Define Headings
        #tree.heading("Date", text = "Date")
        tree.heading("ID", text = "ID")
        tree.heading("Name", text = "Name")
        tree.heading("Concentration", text = "Concentration [mM]")
        # Define Event binding for selection
        tree.bind("<ButtonRelease-1>",self.additive_selection)
        #Call function to populate table
        tree.grid(sticky = "NWE")
        # Add Buttons
        addbutton = Button(frame, text = "Add Additive", command = self.newadditive)
        addbutton.grid(sticky = "NE")
        deletebutton = Button(frame, text = "Delete Additive", command = self.delete_additive)
        deletebutton.grid(sticky= "NE")
        self.componenttree = tree
    def newadditive(self):
        """
        Create dialog window that asks for chemical (from box), concentration, or new chemical.
        Creates a new instance with that chemical concentration
        After return reload componenet table.
        """
        window = additives.additive_window(self.instance.id,self.session)
        # Destroys, or deltes all items in the componenet tree
        self.clear_component_table()
        self.set_component_table()
        
   
        # Reloads the component tree    
        
        
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
        starter = Injection.injectionwindow(buffer)
        # Store injection volume 
        self.volume = starter.volume
        return
    def save_edits(self):
        # Make changes, all additive changes are added when additives are saved
        self.instance.name = self.nameentry.get()
        self.instance.pH = self.pHentry.get()
        self.instance.ohmsvoltage = self.Ventry.get()
        self.instance.capillarylumen = self.Lumenentry.get()
        self.instance.capillarylength = self.Lentry.get()
        #calculate ionicstrength
        ion = ionicstrength(self.instance, self.session)
        print(ion.u, " is the ION u value at save_edits")
        self.instance.ionicstrength = ion.u
        
        #Commit changes to database
        self.session.commit()
        # Clear Tree, Reload tree.
        self.clear_ohms_tree()
        self.fillohmstable()
       
        
    def clear_ohms_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
    def clear_component_table(self):
        for row in self.componenttree.get_children():
            self.componenttree.delete(row)
    def load_ohms(self,queue):
        """Queries filenames for each Separation ID
        For each filename:
            open file
            save shortname, Time, RFU to dictionary, with key set to separation ID"""
        if queue == []: # saves costly db search for no sequence
            return
        sesh=self.session
        self.currentqueue=queue # allows us to reload with this same queue after edits
        data = {}
        for instance in sesh.query(db.Buffer).filter(db.Buffer.id.in_(queue)):
            Voltage,Current=Fileconversion.Readfile(instance.ohmsfile,
                                                    False, False, True, True)
            data[instance.id]=[instance.name,Voltage,Current]
        self.displayelectropherogram(data=data) # Pass data to plot
        print("Queue is still {} at load_separation".format(queue))
        self.plotcanvas.draw()
    
    def plot_setup(self):
        """Plot setup at the __init__ stage"""
    #Set up canvas, and figure widgets
        plotframe = Frame(self)
        plotframe.grid(column = 1, row = 0, rowspan = 2, sticky = "NWE")
        plotfigure= Figure()
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
        markers = ['.','o','v','*','h','s','1','2','4','8']
        marker = 0
        colors = ['r','g','b','y','c','m']
        color = 0
        for ohms in data:
            #Plot Time, RFU and give each line a label for a legend
            # Get average values
            #print("length of data", len(data[ohms][2]))
            x,y,sy = self.average_voltage(data[ohms][1],data[ohms][2])
            # Get line approximation
            lnx,lny = self.fit_line(x,y)
            #plot values
            self.plotsubplot.errorbar(x,y,sy, label = data[ohms][0], fmt = markers[marker], color = colors[color])
            self.plotsubplot.plot(lnx,lny,linestyle = '--', color = colors[color])

            #increment markers/colors
            marker +=1
            color +=1
            if marker == len(markers):
                marker = 0
            if color == len(colors):
                color = 0 
            
            
        #self.plotsubplot.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)    
        self.plotsubplot.legend(prop = {'size':6})
        self.plotcanvas.draw()
       
    def delete_ohms(self):
        self.instance.active = False
        self.session.commit()
        self.fillohmstable()

    def delete_additive(self):
        self.additiveinstance.active = False
        self.session.commit()
        
    def average_voltage(self,voltage, current,minimum = 59):
        voltage = np.asarray(voltage)
        # round voltage to nearest 500 place
        voltage = np.round_(voltage*2)/2
        #print(voltage[0:4], "first five values of voltage")
        voltage = list(voltage)
        avgC=[]
        avgV=[]
        stdC=[]
        for volt, amp in zip(voltage,current):
            X = volt
            Y = []
            #print(voltage.count(X),'this was count')
            while voltage.count(X)>0:
                index = voltage.index(X)
                #print(index, "this was index")
                voltage.pop(index)
                Y.append(current.pop(index))
            #print("this is length Y: ", len(Y))
            if len(Y)>minimum: # only averages with a minimum number of sample points
                Y = np.asarray(Y)
                avgC.append(Y.mean())
                stdC.append(Y.std())
                avgV.append(X)
        print(stdC)
        return avgV, avgC, stdC
    
    def fit_line(self, avgV, avgC):
        # create a line fit for first 4 points
        #print(avgV, avgC, 'Those were V and C values')
        polyfit= np.poly1d(np.polyfit(avgV[0:4],avgC[0:4],1))
        lnx=[avgV[0],max(avgV)]
        lny=[polyfit(lnx[0]),polyfit(lnx[1])]
        return lnx,lny
        
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
    def plotclick(self,event):
        """When the user clicks on the graph it records information about where 
        they click and displays vertical lines on the click mark"""
        print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f')
        #(event.button, event.x, event.y, event.xdata, event.ydata)) 
        ymin,ymax=self.plotsubplot.get_ylim()
        if self.left_flag:
            self.startd=event.xdata
            
            self.left_flag=False
            try:
                self.vline1.remove()
            except:
                self.vline1=None
            self.vline1=self.plotsubplot.vlines(event.xdata,ymin,ymax,color='b')  
            
        else:
            self.stopd=event.xdata
            try:
                self.vline2.remove()
            except:
                self.vline2=None
            self.vline2=self.plotsubplot.vlines(event.xdata,ymin,ymax,color='r')
            
            self.left_flag=True
        self.plotcanvas.draw()

        
class ionicstrength():
    """This class calculates the ionic strength of a buffer from the database"""
    def __init__(self, instance, session):
        self.instance = instance
        self.session = session
        self.calculate()
        
# Start working here
    def get_chemical_info(self,chem_id):
        query = self.session.query(db.Chemical).filter(db.Chemical.id == chem_id)
        instance = query.first()
        charge = float(instance.charge)
        pka = float(instance.pka)
        mw = instance.mw
        return charge, pka, mw

    def get_concentrations(self, concentration, pH, pka):
        """ Calculates the acid and base concentration at a given pH
        acid = concentration/(10^(ph-pka)+1) """

        acid = concentration / (10**(pH-pka)+1)
        base = concentration - acid
        return acid, base
        

    def calculate(self):
        """ Run a for loop, sum various parts 0.5 * Sum(z_i^2 * c_i)"""
        sesh = self.session
        usum=0 
        for additive in sesh.query(db.Additive)\
            .filter(db.Additive.bufferc_id == self.instance.id, db.Additive.active.isnot(False)):
            charge, pka , mw = self.get_chemical_info(additive.chemical_id)
            acid, base = self.get_concentrations(float(additive.concentration),
                                                 float(self.instance.pH), pka)
            print("USUM is ", usum)
            usum += ((charge**2) * acid) + ((charge-1)**2 * base)
        u = 0.5 * usum
        self.u = u
    
            
            

    

        
        
