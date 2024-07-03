from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Boxes(Base):
    __tablename__ = "boxes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    owner = Column(String)
    resource_tag = Column(String)
