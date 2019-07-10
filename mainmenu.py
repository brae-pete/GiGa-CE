""" From Username with Username ID 
To buffersettings
instrumentsettings
analyze
"""
# import gui module
import tkinter as tk
# import custom classes
#import buffersettings
import ohms
import separations
import database as db

#This will be our main app, every window will be contained within this app
class UltraCEapp(tk.Tk):
    def __init__(self,User, *args, **kwargs):
        dbengine = db.database_engines(User)
        session=dbengine.get_session()
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
# Populate all the main windows this program will display
        titles=["mainmenu","ohmsmenu","ohmsview","separationsmenu","separationview",
                "ohmsmenu","ohmsview"]
        for key,F in zip(titles,(mainmenu,
                  #buffersettings.buffersettings,
                  #buffersettings.bufferproperties,
                  ohms.ohmsmenu,
                  #ohms.ohmsqueue,
                  ohms.ohmsview,
                  separations.separationsmenu,
                  separations.separationview)):

            frame = F(container, self, session, User)

            self.frames[key] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("separationview")
        
    def show_frame(self, cont):
        """Moves the frame of interest to the top"""

        frame = self.frames[cont]
        frame.tkraise()

class mainmenu(tk.Frame):
    def __init__(self, parent, controller, session,user):
        tk.Frame.__init__(self,parent) # initialize frame
        self.user = user # define user for database

        # Create buttons that will move between different windows

        bufferbutton=tk.Button(self, text = "Go to Buffer Settings"
                              )
        
        bufferbutton.grid()
        instrumentbutton=tk.Button(self, text = "Go to Instrument Settings"
                                )
        instrumentbutton.grid()
        ohmsbutton=tk.Button(self, text = "Go to Ohms Plots",
                                command = lambda: controller.show_frame\
                               ("ohmsmenu"))
        ohmsbutton.grid()
        separationbutton=tk.Button(self, text = "Go to Separations",
                                command = lambda: controller.show_frame\
                               ("separationsmenu"))
        separationbutton.grid()

        
    """New Main Menu
    MENU
        1) Buffers Settings
        2) Instrument Settings
        3) Ohms Plots
        4) Separations
    Function: Opens one of the menu options
    """


#app  = UltraCEapp()
#app.mainloop()

    
    
""" Old Start Menu
    def __init__(self, parent, controller,info):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Start Menu", font=LARGE_FONT)
        label.grid(pady=10,padx=10)

        button = ttk.Button(self, text="Load Batch Runs",
                            command=lambda: controller.show_frame(BatchSetup))
        button.grid(row = 1)
        
        button2 = ttk.Button(self, text="Analyze Run",
                            command=lambda: controller.show_frame(AnalyzeRun))
        button2.grid(row = 2)

        button3 = ttk.Button(self, text="Add Sample",
                            command=lambda: controller.show_frame(AddSample))
        button3.grid()
"""
