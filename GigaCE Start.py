""" From: start
    To: mainmenu
    
"""
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
import mainmenu as mm
class username(tk.Frame):
    """Username Prompt
    Select USERNAME
       1) Username List
    Create New User
        1) Text Field + Submit
        *Will this be a normal process? No. Only happens once per database.

    Function: returns database object with username
    Function: opens mainmenu
    """


class User_window():
    """This class will prompt for a user """

    def __init__(self):
        self.start()
        self.user = "Default"

    def start(self):
        value = user(self)

class user(tk.Tk):
    def __init__(self, parent, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)

        self.frames = {}
        

        for key,F in zip(["adduser"],[adduser]):

            frame = F(container, self, parent)

            self.frames[key] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("adduser")
        
    def show_frame(self, cont):
        """Moves the frame of interest to the top"""

        frame = self.frames[cont]
        frame.tkraise()
    
class adduser(tk.Frame):
    def __init__(self, parent, controller, window):
        #self.session = session
        self.controller = controller
        self.window = window
        tk.Frame.__init__(self,parent)
        self.parent = parent
        chemicallabel = Label(self, text = "Enter User Name")
        chemicallabel.grid(row = 0, column = 0)
        
        
        self.entry = Entry(self)
        self.entry.grid()
        

        saveadditive = Button(self, text = "Start GigaCE",\
                              command = self.start_giga)
        saveadditive.grid(row = 1, column = 2)
    def start_giga(self):
        user = self.entry.get()
        app  = mm.UltraCEapp(user)
        self.destroy()
        self.controller.destroy()
        #self.parent.destroy()
        app.mainloop()
        
app = User_window()

