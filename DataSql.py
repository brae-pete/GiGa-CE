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