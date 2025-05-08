from pydantic import BaseModel
from typing import List, Optional

class VenueBase(BaseModel):
    venueName: str
    venueType: str
    venuePosition: str

    class Config:
        orm_mode = True

class VenueCreate(VenueBase):
    pass

class VenueUpdate(VenueBase):
    venueId: str

class DeleteVenueRequest(BaseModel):
    venueId: str

class VenueOut(VenueBase):
    venueId: str

class GetVenuesData(BaseModel):
    venues: List[VenueOut]

class ResponseModel(BaseModel):
    code: str
    msg: str
    data: dict = {}

class GetVenuesResponse(ResponseModel):
    data: GetVenuesData
