import tkinter as tk
from tkinter import *
from tkinter.ttk import *
Volume = []
class injectionwindow():
    """This will output volumes
    Call start to open new window
    Volume will be stored after dialog as Volume"""
    def __init__(self, buffer_instance,parent):
        buffer_id = 3 #buffer_instance.id #buffer_instance.id
        self.capillarylength = 30 #buffer_instance.capillarylength#buffer_instance.capillarylength
        self.capillarylumen = 50 # buffer_instance.capillarylumen #buffer_instance.capillarylumen
        parent.volume = 9.9 # Standard volume for 50 um CID
        self.parent = parent
        self.start()
    def get_capillary_info(self):
        return [self.capillarylength,self.capillarylumen]
    def start(self):
        self.app = Injection_Volume(self)
        self.app.mainloop()
    def set_Volume(self,volume):
        self.volume=volume
    def close(self):
        self.parent.volume = self.volume
        self.app.destroy()
        return 
        
class Injection_Volume(tk.Tk):
    def __init__(self, parent,*args, **kwargs):
         # from kwargs
        
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        user = 'Brae'
# Populate all the main windows this program will display
        for F in (mainmenu,electrokinetic,hydrostatic):

            frame = F(container, self, parent)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(hydrostatic)
        
    def show_frame(self, cont):
        """Moves the frame of interest to the top"""

        frame = self.frames[cont]
        frame.tkraise()
class mainmenu(tk.Frame):
    def __init__(self, parent, controller,starter):
        
        tk.Frame.__init__(self,parent)
        Ecalc = Button(self, text = "Electrokinetic Injection",
                       command = lambda: controller.show_frame(electrokinetic))
        Ecalc.grid()

        Hcalc= Button(self, text = "Hydrodynamic Injection",
                      command = lambda: controller.show_frame(hydrostatic))
        Hcalc.grid()
    
class electrokinetic(tk.Frame):
    def __init__(self, parent, controller,starter):
        capillaryinfo = starter.get_capillary_info()
        """Asks Capillary length (cm),
        Capillary lumen,
        Temperature,
        EOF mobility (Standard 7e-8)
        Voltage (Standard 10 kV)
        time (Standard 5 s)
        solution viscosity (standard 0.00086)
        Calculate"""
        tk.Frame.__init__(self,parent)
        Length = Label(self, text = "Capillary Length (cm): ")
        Length.grid()
        self.Lengthedit= Spinbox(self)
        self.Lengthedit.grid()
        self.Lengthedit.bind('<FocusOut>', self.on_focusout)
        Lunit = Label(self, text = "cm")
        Lunit.grid()
        

        CL = Label(self, text = "Capillary Lumen (um): ")
        CL.grid()
        self.CLedit= Spinbox(self)
        self.CLedit.grid()
        self.CLedit.bind('<FocusOut>', self.on_focusout)
        CLunit= Label(self, text = "um")
        CLunit.grid()

        T= Label(self, text = "Temperature (C, integers 4-80): ")
        T.grid()
        self.Tedit = Spinbox(self)
        self.Tedit.grid()
        self.Tedit.bind('<FocusOut>', self.on_focusout)
        #self.Tedit.bind('<FocusOut>', viscositycalc)
        Tunit= Label ( self, text = "C")
        Tunit.grid()
    
        self.time= Label(self, text = "Time (s): ")
        self.time.grid()
        self.timeedit= Spinbox(self)
        self.timeedit.grid()
        self.timeedit.bind('<FocusOut>', self.on_focusout)
        timeunit = Label (self, text = "s")
        timeunit.grid()

        self.viscosity = Label(self, text = "Viscosity (Pa s): ")
        self.viscosity.grid()
        self.viscosityedit= Spinbox(self)
        self.viscosityedit.grid()
        self.viscosityedit.bind('<FocusOut>', self.on_focusout)
        visunit = Label(self, text = "Pa s")
        visunit.grid()

        EOF= Label(self, text = "EOF [m^2/(V s)]: ")
        EOF.grid()
        self.EOFedit= Entry(self)
        self.EOFedit.grid()
        self.EOFedit.bind('<FocusOut>', self.on_focusout)
        EOFunit= Label ( self, text = "x10^-8 [m^2/Vs]")
        EOFunit.grid()

        V= Label(self, text = "Voltage (V): ")
        V.grid()
        self.Vedit= Entry(self)
        self.Vedit.grid()
        self.Vedit.bind('<FocusOut>', self.on_focusout)
        Vunit = Label(self, text = "V")
        Vunit.grid()

        self.Lengthedit.delete(0,"end")
        self.Lengthedit.insert(0,capillaryinfo[0])

        self.CLedit.delete(0,"end")
        self.CLedit.insert(0,capillaryinfo[1])

        self.Tedit.delete(0,"end")
        self.Tedit.insert(0,25)

        self.timeedit.delete(0,"end")
        self.timeedit.insert(0,5)

        self.EOFedit.delete(0,"end")
        self.EOFedit.insert(0,6)

        self.Vedit.delete(0,"end")
        self.Vedit.insert(0,15000)

        self.Volume = Label(self)
        self.Volume.grid()

    def on_focusout(self,event):
        """Calculates Injection Volume"""
        L = self.Lengthedit.get()
        CL = self.CLedit.get()
        T = self.Tedit.get()
        EOF = self.EOFedit.get()
        V = self.Vedit.get()
        t = self.timeedit.get()
        vis = self.viscosityedit.get()
        V = calcelectrokinetic(float(V),float(t),float(L),float(CL)/2,float(EOF))
        self.Volume['text']='{} nL injected'.format(V)
class hydrostatic(tk.Frame):
    def __init__(self, parent, controller,starter):
        self.starter=starter
        """Asks Capillary length (cm) (or pulls from instance)
        Asks temperature (standard 25)
        Asks Capillary Lumen diameter (pulls from instance)
        Asks Gravity ( leave blank if empty)
        Asks Pressure (in PSI, standard 5 s)
        Asks time ( standard 5 s)
        Solution viscosity (Standard 0.00086)
        Calulate"""
        capillaryinfo = starter.get_capillary_info()
        tk.Frame.__init__(self,parent) # initialize frame
        #self.user = user # define user for database

        Length = Label(self, text = "Capillary Length (cm): ")
        Length.grid()
        self.Lengthedit= Spinbox(self)
        self.Lengthedit.grid()
        self.Lengthedit.bind('<FocusOut>', self.on_focusout)
        Lunit = Label(self, text = "cm")
        Lunit.grid()

        self.Lengthedit.delete(0,"end")
        self.Lengthedit.insert(0,capillaryinfo[0])
        

        CL = Label(self, text = "Capillary Lumen (um): ")
        CL.grid()
        self.CLedit= Spinbox(self)
        self.CLedit.grid()
        self.CLedit.bind('<FocusOut>', self.on_focusout)
        CLunit= Label(self, text = "um")
        CLunit.grid()

        self.CLedit.delete(0,"end")
        self.CLedit.insert(0,capillaryinfo[1])

        T= Label(self, text = "Temperature (C, integers 4-80): ")
        T.grid()
        self.Tedit = Spinbox(self)
        self.Tedit.grid()
        
        self.Tedit.bind('<FocusOut>', self.on_focusout)
        self.Tedit.bind('<FocusOut>', self.viscosity_calc)
        Tunit= Label ( self, text = "C")
        Tunit.grid()

        self.Tedit.delete(0,"end")
        self.Tedit.insert(0,25)
        

        Pressure= Label(self, text = "Pressure  [PSI]: ")
        Pressure.grid()
        self.Pressureedit= Spinbox(self)
        self.Pressureedit.grid()
        self.Pressureedit.bind('<FocusOut>', self.on_focusout)
        Punit= Label (self, text = "PSI")
        Punit.grid()

        self.Pressureedit.delete(0,"end")
        self.Pressureedit.insert(0,0.5)

        Height= Label(self, text = "Height (cm), \n leave blank if pressure injection : ")
        Height.grid()
        self.Heightedit= Spinbox(self)
        self.Heightedit.grid()
        self.Heightedit.bind('<FocusOut>', self.on_focusout)
        Hunit=Label(self, text =" cm")
        Hunit.grid()

        self.Heightedit.delete(0,"end")
        

        self.time= Label(self, text = "Time (s): ")
        self.time.grid()
        self.timeedit= Spinbox(self)
        self.timeedit.grid()
        self.timeedit.bind('<FocusOut>', self.on_focusout)
        timeunit = Label (self, text = "s")
        timeunit.grid()

        self.timeedit.delete(0,"end")
        self.timeedit.insert(0,5)

        self.viscosity = Label(self, text = "Viscosity (Pa s): ")
        self.viscosity.grid()
        self.viscosityedit= Spinbox(self)
        self.viscosityedit.grid()
        self.viscosityedit.bind('<FocusOut>', self.on_focusout)
        visunit = Label(self, text = "Pa s")
        visunit.grid()

        self.viscosityedit.delete(0,"end")
        self.viscosityedit.insert(0,0.00086)

        self.Volume=Label(self)
        self.Volume.grid()

        self.submit=Button(self, text = "Submit Volume", command = starter.close)
        self.submit.grid()

        self.on_focusout(None)
    def on_focusout(self,event):
        """Calculates Injection Volume"""
        L = self.Lengthedit.get()
        CL = self.CLedit.get()
        T = self.Tedit.get()
        if self.Heightedit == '':
            P = 9.8 * float(self.heightedit.get())
        else:
            P = float(self.Pressureedit.get())
       
        t = self.timeedit.get()
        vis = self.viscosityedit.get()
        Vinj = calchydrodynamic(P,float(CL)/2,float(t),float(vis),float(L))
        self.starter.set_Volume(Vinj)
        self.Volume['text']='{} nL injected'.format(Vinj)
    def viscosity_calc(self,event):
        temp = float(self.Tedit.get())
        if temp > 80 or temp < 2 or temp%1>0:
            print ("Temperature is out of bounds or not integer")
            self.Tedit.set(0)
            return
        viscosity = table[temp]
        self.viscosityedit.delete(0,"end")
        self.viscosityedit.insert(0,viscosity)
        self.on_focusout(event)
        
            
def viscosity_table():
    """Returns viscosity table in Pa*s"""
    fopen=open('viscosity.txt','r')
    data=fopen.readlines()
    data=data[1:]
    table={}
    for temp in data:
        temp=temp.split('\t')
        table[eval(temp[0])]=eval(temp[1])/1000
    return table
table = viscosity_table()
def pressure_convert(psi):
    """Returns pascals"""
    return psi*6894.76
def totalvolume (radius, length):
    "Returns L" 
    volume = ((radius)**2 )* 3.12159265359 * length *1e3
    print("total volume: ", volume)
    return volume

def calchydrodynamic(pressure,radius,time,viscosity,length):
    """pressure:psi, radius:um, time:s, temp:C, length:cm"""
    pressure=pressure_convert(pressure)
    length = length/100
    radius = radius*10**-6

    print('viscosity', viscosity)
    volume= pressure / (8 * viscosity * length ) * radius**4 * 3.1416 * time
    volume=volume*1e3 # to Liters
    volume = volume * 1e9 # to nL
    volume = round(volume,2)
    
    velocity = pressure / (8 * viscosity * length ) * radius**2
    print('velocity ', velocity)
    print(printvolume(volume,radius,length))
    return volume
          
def printvolume(volume,radius,length):
    "Returns L"
    totalv= totalvolume(radius,length)
    return print("Volume {} nL , percent injected {}".format(volume*1e9,volume /totalv*100 ) )

def calcelectrokinetic(Voltage,time,length,radius,ueof=6.0e-8):
    """Volume of sample (L) injected via electrokinetic injections"""
    volume = (ueof)*Voltage/length*(radius**2)*3.1416*time
    velocity = (ueof)*Voltage/length# length of capillary (m)
    #volume = length * 3.1416 * (radius**2) # m^3
    volume = volume* 1000  # 1000 L in 1 m^3 so (m^3 * 1000 L / m^3 = L)
    print(printvolume(volume,radius,length))
    print(velocity, 'Velocity')
    return volume

def gravity(height, time, radius,length=.40, temp=25):
    density = 997 #kg/m^3
    G = 9.8 #m/s^2
    viscosity = table[temp]
    volume = density * G * 3.1416 * (radius**4) * height * time /\
             8 / viscosity / length # m^3
    velocity = density * G  * (radius**2) * height /\
             8 / viscosity / length
    volume = volume * 1000 # 1000 L in 1 m^3 so (m^3 * 1000 L / m^3 = L)    
    print(printvolume(volume,radius,length))
    print(velocity, ' Velocity ')
    return volume

def ionic_strength():
    cont = 'y'
    u = 0
    while cont== 'y':
        cont == input("Add compound? y/n")
        if cont == 'y':
            concentration = float(input("What is the concentration?"))
            charge = int(input("What is the charge?"))
            u += (concentration * (charge**2))
    u=0.5 * u
    return print("ionic strength is {} ".format(u))

#app = Injection_Volume(capillaryinfo = [30,50])
#app.mainloop()
