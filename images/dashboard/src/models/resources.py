from sqlalchemy import Column, String, Integer
from database import Base

class Resources(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String)
    cpu = Column(Integer)
    ram = Column(Integer)
