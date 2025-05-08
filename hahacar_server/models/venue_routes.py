from sqlalchemy import Column, String , ForeignKey
from sqlalchemy.orm import relationship
from dependencies.database import Base

class VenueRoutes(Base):
    __tablename__ = "venue_routes"
    venueRoutesId = Column("venue_routes_id", String, primary_key=True)
    venueFromId   = Column("venue_from_id", String, ForeignKey("venues.venue_id"), nullable=False)
    venueToId     = Column("venue_to_id", String, ForeignKey("venues.venue_id"), nullable=False)


     # ORM 关联
    fromVenue = relationship(
        "Venue",
        foreign_keys=[venueFromId],
        back_populates="outgoingRoutes",
        lazy="joined"
    )
    toVenue = relationship(
        "Venue",
        foreign_keys=[venueToId],
        back_populates="incomingRoutes",
        lazy="joined"
    )