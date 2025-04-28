from sqlalchemy import Column, String
from dependencies.database import Base

class Reserve(Base):
    __tablename__ = "reserve"
    reserveId      = Column("reserve_id", String, primary_key=True)
    licence        = Column(String, nullable=False)
    venueRoutesId  = Column("venue_routes_id", String, nullable=False)
    reserveTime    = Column("reserve_time", String, nullable=False)
    openId         = Column("open_id", String, nullable=False)