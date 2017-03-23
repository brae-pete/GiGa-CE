import tkinter as tk
from tkinter import *
from tkinter.ttk import *

class UltraCEapp(tk.Tk):
    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        user = 'Brae'
# Populate all the main windows this program will display
        for F in (mainmenu,mainmenu):

            frame = F(container, self, user)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(mainmenu)
        
    def show_frame(self, cont):
        """Moves the frame of interest to the top"""

        frame = self.frames[cont]
        frame.tkraise()

class mainmenu(tk.Frame):
    def __init__(self, parent, controller, user):
        tk.Frame.__init__(self,parent) # initialize frame
        self.user = user # define user for database

        # Create buttons that will move between different windows

        bufferbutton=Button(self, text = "Go to Buffer Settings")                              
        
        bufferbutton.grid()
        instrumentbutton=Button(self, text = "Go to Instrument Settings")
        instrumentbutton.grid()
        ohmsbutton=Button(self, text = "Go to Ohms Plots")
        ohmsbutton.grid()
        separationbutton=Button(self, text = "Go to Separations")

        tree= Treeview(self)
        tree["columns"]=("Date","User")
        tree.column("Date", width = 100)
        tree.column("User", width = 100)
        tree.heading("Date", text = "Date")
        tree.heading("User", text = "User")

        tree.insert("",0,text = "Line 1", values = ("March","Brae"))
        # Directory number 1
        id2 = tree.insert("", 1, "dir2", text="Dir 2")
        tree.insert(id2, "end", "dir 2", text="sub dir 2", values=("2A","2B"))
        # Directory number 2
        tree.insert("", 3, "dir3", text="Dir 3")
        tree.insert("dir3", 3, text=" sub dir 3",values=("3A"," 3B"))
        
        tree.grid()
        self.tree = tree
        tree.bind("<Button-1>", self.selected)
    def selected (self,event):
        k = self.tree.selection()
        for item in k:
            l= self.tree.item(item,'values')
            print(l)
        

app = UltraCEapp()
app.mainloop()
