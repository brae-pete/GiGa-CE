import tkinter as tk
from tkinter import *
from tkinter.ttk import *
import database as db

class additive_window():
    """This class will add a new additive to a buffer """

    def __init__(self, buffer_id, session):
        self.buffer_id = buffer_id
        self.session = session
        self.start()

    def start(self):
        self.app = additive(self, self.session)
        self.app.mainloop()


class additive(tk.Tk):
    def __init__(self, parent,session, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)

        self.frames = {}
        self.session = session

        for key,F in zip(["newadditive","newchemical"],(newadditive,newchemical)):

            frame = F(container, self,session, parent)

            self.frames[key] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("newadditive")
        
    def show_frame(self, cont):
        """Moves the frame of interest to the top"""

        frame = self.frames[cont]
        frame.tkraise()
    
class newadditive(tk.Frame):
    def __init__(self, parent, controller,session, window):
        self.session = session
        self.controller = controller
        self.buffer_id = window.buffer_id
        tk.Frame.__init__(self,parent)

        chemicallabel = Label(self, text = "Chemical Name")
        chemicallabel.grid(row = 0, column = 0)
        
        
        self.chemicalbox = Combobox(self)
        self.chemicalbox.grid(row = 1, column = 0)
        self.load_chemicals()
        
        concentrationlabel = Label(self, text = "Concentration(mM)")
        concentrationlabel.grid(row = 0, column = 1)
        self.concentrationentry = Spinbox(self)
        self.concentrationentry.grid(row = 1, column = 1)

        addchemical = Button(self, text = "Add New Chemical \n to Inventory",
                             command = lambda: controller.show_frame\
                             ("newchemical"))
        addchemical.grid(row = 2, column = 0)

        saveadditive = Button(self, text = "Save Composition to buffer",\
                              command = self.save_additive)
        saveadditive.grid(row = 1, column = 2)
    def load_chemicals(self):
        chemicals,chemicalids = self.get_chemicals()
        self.chemicalbox['values']=list(chemicals.keys())
        
    def get_chemicals(self):
        chemicals={}
        chemicalids={}

        for instance in self.session.query(db.Chemical):
            chemicals[instance.name]=instance.id
            chemicalids[instance.id] = instance.name
        self.chemicals = chemicals
        self.chemicalids=chemicalids
        return chemicals, chemicalids
    def save_additive(self):
        sesh=self.session
        self.get_chemicals()
        chemical_id = self.chemicals[self.chemicalbox.get()]
        concentration = self.concentrationentry.get()
        # Insert calculate ionic strength here
        newadditive = db.Additive(chemical_id=chemical_id,
                                  bufferc_id = self.buffer_id,
                                  concentration = concentration)
        sesh.add(newadditive)
        sesh.commit()
        #Insert KILL command
        self.controller.destroy()
        

class newchemical(tk.Frame):
    def __init__(self, parent, controller,session,window):
        self.session = session
        self.controller = controller
        tk.Frame.__init__(self,parent)

        chemicallabel = Label(self, text = "Chemical Name")
        chemicallabel.grid(row = 0, column = 0)
        self.chemicalentry = Entry(self)
        self.chemicalentry.grid(row = 1, column= 0)
        

        chargelabel = Label(self, text = "Protonated Charge(z)")
        chargelabel.grid(row = 0, column = 1)
        self.chargeentry = Spinbox(self)
        self.chargeentry.grid(row = 1, column = 1)

        mwlabel = Label(self, text = "Molecular Weight(g/mol)")
        mwlabel.grid(row = 0, column = 2)
        self.mwentry = Spinbox(self)
        self.mwentry.grid(row = 1, column = 2)

        pkalabel = Label(self, text = "Pka")
        pkalabel.grid(row = 0, column = 3)
        self.pkaentry = Spinbox(self)
        self.pkaentry.grid( row = 1, column = 4)

        addchemical = Button(self, text = "Save Chemical to Inventory",
                             command =self.save_chemical)
        addchemical.grid(row = 1, column = 2)

        
    def save_chemical(self):
        """Adds a new chemical to the database,
        calls functions to reload the GUI"""
        sesh=self.session
        name = self.chemicalentry.get()
        charge = self.chargeentry.get()
        mw = self.mwentry.get()
        pka=self.pkaentry.get()
        # Insert calculate ionic strength here
        newchemical = db.Chemical(name = name,
                                  charge = charge,
                                  mw = mw,
                                  pka = pka)
        sesh.add(newchemical)
        sesh.commit()
        self.reload()
        self.controller.show_frame('newadditive')

        
    def reload(self):
        """Reloads the chemicalbox combobbox in gui after a chemical is added"""
        controller = self.controller
        frame = controller.frames['newadditive']
        frame.load_chemicals()
        


