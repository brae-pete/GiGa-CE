# GiGa-CE
A SQLAlchemy Database and GUI for analyzing and storing Electropherograms. 


## Installation

GigaCE runs on python version 3.6.

Download the repository to the PC. Install the following packages:
Numpy, Scipy, Matplotlib, Pandas, Sqlalchemy, and peakutils. 

If you are using Miniconda or Anaconda, open the anaconda terminal. Activate your environment (optional): 

~~~
conda install numpy scipy matplotlib pandas sqlalchemy peakutils
~~~

followed by: 

~~~
python -m pip install peakutils
~~~

Run GigaCE by entering the following (assuming your are in the GigaCE directory)
~~~
python main.py 
~~~

## Database & Data storage
GigaCE stores all the data in a database and a file tree within the GigaCE folder. Currently there is no way to combine 
databases, but if you wish to install an old database on a new computer copy the matching .db and file folder and paste 
it into the new GigaCE folder.

It is not intended that a user manually looks at or modifies chromatograms inside the filefolder. 
Instead use the export electropherograms option, this will preserve the long-name of the separation and 
prevent the database links to electropherograms from being corrupted. 