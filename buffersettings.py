class buffersettings(tk.Frame):
    """Buffer settings menu

    Menu
        1) New Buffer
        2) View Buffer details : Table of buffers
    Function1: Opens bufferproperties
    Function2: Opens bufferproperties for buffer X 
        """
    
class bufferproperties(tk.Frame):
    """
        Init(DB, Buffer ID)
        Menu
        0) Buffer Name
        1) Add chemical species
            a) chemicals in inventory
            b) add chemical to inventory

        2) Set pH
        4)Ohms plot
            a) if none request filename
        5) Manual
            a) set voltage
            b) set capillary id
            c) set capillary length
        6) View Separations using this buffer
    Function 1: Adds combobox + concentration spin box + new chemical button
    Function 2: spin box
    Function 4: Opens Ohmsplot with link to this buffer id
    Function 5: Adds spinbox, spinbox, spinbox, calculates Efield, returns.
    Function 6: Opens Separations table

    """
    
        
        
    
