# -*- coding: utf-8 -*-
"""
This module is for the Database Classes.
Created on Sat Jul  9 12:21:44 2016

@author: Alyssa
Tested : 3/8/2017
"""
import os
from sqlalchemy import create_engine
from sqlalchemy import desc
        
di=os.getcwd()
print('directory is di', di)
engine = create_engine('sqlite:///{}\\simplyCE1.db'.format(di))

#### Declare the base so we can start mapping
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

#### IF you want to access the database you need to use a session!
#Use the sessionmaker to make a session. Be sure to complete the transaction quickly!

from sqlalchemy.orm import sessionmaker
#Session = sessionmaker(bind=engine)
#session=Session()
##### Create Classes to map
"""There are the following classes:
Run- has one to many relationship with peaks
     has many to one relationship with buffers
     has many to one relationship with samples
     has many to one relationship with instruments
     
     has project field
     has subproject field
     has date/time field - from CSV import
     has voltage field
     has preamp field
     has capillary id
     
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship

#
from sqlalchemy import distinct
import datetime as dt
class Separation(Base):
    __tablename__='separations'
    id = Column(Integer, primary_key=True)
    active = Column(String)
    project=Column(String)
    date=Column(Date) #as datetime.time(yr,mo,day)
    name=Column(String)
    shortname=Column(String)
    injectiontype=Column(String)
    injectionvolume=Column(Integer)
    filename=Column(String)
    kwds=Column(String) #[Ld:(cm), V:(V)]
    ##relationships
    #one to many
    runpeaks=relationship("Peak",back_populates='run',cascade="all, delete, delete-orphan")
    #many to one
    buffer_id= Column(Integer, ForeignKey('buffers.id'))
    buffer=relationship("Buffer",back_populates='runb')
    def __repr__(self):
        return """<Run(project={},date={},name={},
        file={},injectiontype={},injectionvolume={},kwds={})>""".format(\
        self.project,self.date,self.name,
        self.shortname, self.filename,self.injectiontype,
        self.injectionvolume,self.kwds)


"""Peaks-has many to one relationship with runs
        -has many to one with samples
        
        has starttime
        has stoptime
        has maxtime
        has m1 retetion time
        has m2
        has m3
        has m4
        has FWHM
        has area
        has corrected area
        has corrected area %
"""
        
class Peak(Base):
    __tablename__='peaks'
    id= Column(Integer, primary_key=True)
    name = Column(String)
    active = Column(String)
    shortname = Column(String)
    peaknumber=Column(Integer)
    starttime=Column(Integer)
    stoptime=Column(Integer)
    maxtime=Column(Integer)
    m1=Column(Integer)
    m2=Column(Integer)
    m3=Column(Integer)
    m4=Column(Integer)
    fwhm=Column(Integer)
    area=Column(Integer)
    areapercent=Column(Integer)
    correctedarea=Column(Integer)
    correctedpercent=Column(Integer)
    apparentmobility=Column(Integer)
    resolution=Column(String)
    detectordistance=Column(Integer)
    plates = Column(String)
    kwds=Column(String)#cm
    
    #relationships
    
    #many to one
    run_id=Column(Integer, ForeignKey('separations.id'))
    run=relationship("Separation",back_populates="runpeaks")

    
    def __repr__(self):
        return "<Peak(startime={},stoptime={},maxtime={},m1={},m2={},m3={},m4={},fwhm={},area={},correctedarea={},correctedpercent={},apparetmobility={})>"\
        .format(self.starttime,self.stoptime,self.maxtime,self.m1,self.m2,self.m3,\
        self.m4,self.fwhm,self.area,self.correctedarea,self.correctedpercent\
        ,self.apparentmobility)    
class Additive(Base):
    __tablename__='additives'
    id = Column(Integer,primary_key=True)
    concentration = Column(Integer)#Molar
    kwds= Column(String)
    active = Column(String)
    bufferc_id= Column(Integer, ForeignKey('buffers.id'))
    bufferc=relationship("Buffer",back_populates='composition')

    chemical_id= Column(Integer, ForeignKey('chemicals.id'))
    chemical=relationship("Chemical",back_populates='use')    
"""Buffers- has one to many with runs
         
        - has ohmsfile
        - has name
        - has ionicstrength
        - has EOflow
        - has ohmsvoltage # 4%
        - has pH
        - has additive
        - has additivevolume
        - has additive2
        - has additivevolume2
"""
class Buffer(Base):
    __tablename__='buffers'

    id=Column(Integer,primary_key=True)
    name=Column(String)
    active = Column(String)
    date = Column(Date)
    ohmsfile=Column(String)
    ionicstrength=Column(Integer)
    eoflow=Column(Integer)
    ohmsvoltage=Column(Integer)
    pH=Column(Integer)
    capillarylumen=Column(Integer)#Microns
    capillarylength=Column(Integer)#cm
    percentile = Column(Integer) # # of values to count when calulating the average
    kwds = Column(String)
    #relationships
    runb=relationship("Separation",back_populates='buffer')
    composition = relationship("Additive", back_populates='bufferc')
    
    def __repr__(self):
        return "<Buffer(name={},ohsfile={},ionicstrength={},eoflow={}>"\
        .format(self.name,self.ohmsfile,self.ionicstrength,self.eoflow)
class Chemical(Base):
    __tablename__='chemicals'
    id = Column(Integer,primary_key=True)
    name = Column(String)
    active = Column(String)
    charge = Column(Integer)
    mw = Column(Integer)
    pka= Column(Integer)
    kwds= Column(String)

    use = relationship("Additive", back_populates='chemical')


    
####  Database Functions for the Simply CE program
""" Database functions are as follows:
You need to create an engine before you create 
a transaction. 

Transactions require session inputs from engines.

Multiple instances of the database_instances
 are required if you want to add multiple rows
 to the database. 
"""
        
        
class database_engines():
    """Setsup the database for the user
    IFT: 7/9/16"""
    def __init__(self,name):
        self.name=name
        self.get_engine()
        self.get_sessionmaker()
        self.create_mapping()
    def get_directory(self):
        return os.getcwd()
    def get_engine(self):
        directory=self.get_directory()
        name = self.name
        engine = create_engine('sqlite:///{}\\DB-{}.db'.format(di,name))
        self.engine=engine
    def get_sessionmaker(self):
        self.session=sessionmaker(bind=self.engine)
        #self.Base=declarative_base()
    def create_mapping(self):
        Base.metadata.create_all(self.engine)  
    def get_session(self):
        return self.session()

    
class database_instance():
    """Modifies and carries instances,a seperate object
    is necessary for multiple isntances
    IFT 7/9/2016"""
    def __init__(self,inst):
        """enter table, Run for Run()"""
        self.inst=inst()
    def change_instance(self,attr,info):
        """Attr is the field you want to change"""
        setattr(self.inst,attr,info)
    def get_instance(self):
        return self.inst     
    def set_instance(self,instance):
        self.inst=instance
class database_transactions():
    """Performs transactions with a session
    IFT 7/9/2016"""
    def __init__(self,session):
        self.session=session
    def add_instance(self,inst):
        self.session.add(inst)
        self.session.commit()
        return inst.id
        
    def get_samplebygroup(self,group):
        """Returns samples shortnames by in the same group"""
        query=self.get_query(Sample)
        query=self.equals(query,Sample,'group',group)
        items=self.attrquery(query,Sample,'shortname')
        return items
    def get_sampleid(self,group,shortname):
        query=self.get_query(Sample)
        query=self.equals(query,Sample,'group',group)
        query=self.equals(query,Sample,'shortname',shortname)
        ids=self.attrquery(query,Sample,'id')
        return ids[0]
    def get_query(self,table):
        query=self.session.query(table)
        return query
    def unique_fields(self,table,column):
        unique=[]
        attr=getattr(table,column)
        for row in self.session.query(distinct(attr)):
            if row[0] != None:
                unique.append(row[0])
        return unique
    def equals(self,query,table,column,info):
        """table = Run, column = 'id' for Run.id"""
        attr = getattr(table,column)
        query = query.filter(attr == info ) 
        return query
    def distinct(self,query,table,column):
        """table = Run, column = 'id' for Run.id"""
        attr = getattr(table,column)
        query=query.distinct(attr)
        return query
    def listquery(self,query):
        items = []
        for item in query:
            items.append(item)
        return items
    def attrquery(self,query,table,column):
        """table = Run, column = 'id' for Run.id"""
        items = []
        for item in query:
            item = getattr(item,column)
            items.append(item)
        return items
    def returnid(self,table,column,match):
        """Returns the first id that matches a query
        for the table and column """
        attr=getattr(table,column)
        sesh=self.session
        ids=[]
        for i in sesh.query(table).filter(attr==match):
            ids.append(i.id)
        if len(ids)<1:
            return -1
        else:
            return ids[0]
    def get_valuebyid(self,table,rowid,column):
        sesh=self.session
        for i in sesh.query(table).filter(table.id==rowid):
            value=getattr(i,column)
        return value
    def get_total_CA(self,runid):
        sesh=self.session
        total=0
        for i in sesh.query(Peak).filter(Peak.run_id == runid):
            total+=float(i.correctedarea)
        return total
    def set_percent_area(self,runid):
        sesh=self.session
        total=self.get_total_CA(runid)
        placeCA={}
        for i in sesh.query(Peak).filter(Peak.run_id == runid):
            i.correctedpercent=float(i.correctedarea)/total*100
            placeCA[i.peaknumber]=i.correctedpercent
        sesh.commit()
        return placeCA
            
class table_information():
    def __init__(self,table):
        self.table=table
    def get_keys(self):
        information=getattr(self.table,'__table__')
        self.columns = information.columns.keys()
        return self.columns
        
Base.metadata.create_all(engine)
sesh = sessionmaker(bind = engine)
run1=Separation(project='AKT', date = dt.date(2015,6,22))
#run2=Run(project='AKT',subproject='mRNA', date = dt.date(2015,6,24),voltage=1205,preamp=150,laserhv=488,capillaryid=50,cellline='AKT',file='Dunno',injection='Hydrodynamic',injectiontime='160',injectionpressure='5psi',injectionvoltage='10kv')
        
if __name__ == "__main__":
    dbengine=database_engines("David")
    sesh=dbengine.get_session()

