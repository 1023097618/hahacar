# schemas.py
from pydantic import BaseModel
from typing import List, Optional

class VenueRouteItem(BaseModel):
    venueRouteId: Optional[str]
    venueRouteSequence: int
    cameraLineId: str
    pointCloseToLine: Optional[List[float]]

    class Config:
        orm_mode = True

class RouteBundle(BaseModel):
    venueRoutes: List[VenueRouteItem]
    venueFromId: str
    venueToId: str
    venueRoutesId: str

    class Config:
        orm_mode = True

class GetVenueRoutesData(BaseModel):
    routes: List[RouteBundle]

class GetVenueRoutesResponse(BaseModel):
    code: str
    msg: str
    data: GetVenueRoutesData

class UpdateRoutesRequest(BaseModel):
    routes: List[RouteBundle]

class GetVenueRouteData(BaseModel):
    venueRoutes: List[VenueRouteItem]
    venueFromId: str
    venueToId: str
    venueRoutesId: str

class GetVenueRouteResponse(BaseModel):
    code: str
    msg: str
    data: GetVenueRouteData

class UpdateVenueRouteRequest(BaseModel):
    venueRoutes: List[VenueRouteItem]
    venueFromId: str
    venueToId: str
    venueRoutesId: str

class ReserveByPlateRequest(BaseModel):
    licence: str
    venueRoutesId: str
    reserveId: Optional[str]
    reserveTime: str
    openId: str

class GetReserveRequest(BaseModel):
    openId: str

class ReserveItem(BaseModel):
    licence: str
    venueRoutesId: str
    reserveId: str
    reserveTime: str
    openId: str

class GetReserveData(BaseModel):
    reserves: List[ReserveItem]

class GetReserveResponse(BaseModel):
    code: str
    msg: str
    data: GetReserveData

class ResponseModel(BaseModel):
    code: str
    msg: str
    data: dict = {}
