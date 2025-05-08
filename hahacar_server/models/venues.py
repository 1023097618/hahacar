from sqlalchemy import Column, String
from dependencies.database import Base
from sqlalchemy.orm import relationship

class Venue(Base):
    __tablename__ = "venues"
    venueId = Column("venue_id", String, primary_key=True)              # 地点主键
    venueName = Column("venue_name", String, nullable=False)            # 地点名称
    venueType = Column("venue_type", String, nullable=False)            # 地点类型
    venuePosition = Column("venue_position", String, nullable=False)    # 经纬度位置

    # 反向关系
    outgoingRoutes = relationship(
        "VenueRoutes",
        foreign_keys="[VenueRoutes.venueFromId]",
        back_populates="fromVenue",
        cascade="all, delete-orphan"
    )
    incomingRoutes = relationship(
        "VenueRoutes",
        foreign_keys="[VenueRoutes.venueToId]",
        back_populates="toVenue",
        cascade="all, delete-orphan"
    )