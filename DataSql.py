from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class Data(Base):
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True)
    separation_id = Column(Integer, ForeignKey('separation.id'))
    rfu = Column(Float)
    raw = Column(Float)
    time = Column(Float)
    current = Column(Float)
    voltage = Column(Float)

    def __repr__(self):
        return f"<Data(time={self.time},rfu={self.rfu})>"


class Separation(Base):
    __tablename__ = 'separation'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tags = Column(String)
    digital = Column(String)
    digital_arg1 = Column(Integer)
    digital_arg2 = Column(Float)
    noise = Column(Float)
    date = Column(DateTime)
    data = relationship("Data")

    def __repr__(self):
        return f"<Separation(name={self.name},tags={self.tags})>"


class Tags(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    separation_id = Column(Integer, ForeignKey('separation.id'))

    def __repr__(self):
        return f"<Tags(name={self.name}, ids={self.tags})"

class PeakLookUp(Base):
    __tablename__ = "peak_lookup"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    start = Column(Float)
    stop = Column(Float)
    center = Column(Float)
    deviation = Column(Float)
    buffer = Column(String)
    peaks = relationship("PeakData")

class PeakData(Base):
    __tablename__ = "peak_data"
    id = Column(Integer, primary_key=True)
    start = Column(Float)
    stop = Column(Float)
    m1 = Column(Float)
    m2 = Column(Float)
    m3 = Column(Float)
    m4 = Column(Float)
    area = Column(Float)
    corrected_area = Column(Float)
    max = Column(Float)
    start_idx = Column(Integer)
    stop_idx = Column(Integer)

    separation_id = Column(Integer, ForeignKey("separation.id"))
    peak_lut = Column(Integer, ForeignKey("peak_lookup.id"))

    def __repr__(self):
        return f"<PeakData<start:{self.start}, stop:{self.stop}, m1:{self.m1}, max:{self.max}, ca:{self.corrected_area}"
