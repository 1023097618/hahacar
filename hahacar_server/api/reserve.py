from fastapi import APIRouter, Depends, HTTPException, Header, Query, Body
from schemas.venues_schema import *
from services.venues_service import *
from dependencies.database import get_db
from core.security import verify_jwt_token
from schemas.route_schema import *
from services.route_service import *

router = APIRouter(prefix="/api/reserve", tags=["reserve"])

@router.get("/getVenues", response_model=GetVenuesResponse)
def api_get_venues(
    pageNum: Optional[int] = Query(None, alias="pageNum"),
    pageSize: Optional[int] = Query(None, alias="pageSize"),
    db: Session = Depends(get_db),
):
    """
    **Description**
    获取可以选择的预约地点

    **Params**
    - `pageNum`: 页码，可选
    - `pageSize`: 每页数量，可选

    **Returns**
    - `venues`: 地点列表
    """
    skip  = (pageNum - 1) * pageSize if pageNum and pageSize else 0
    limit = pageSize or 10
    vs = get_venues(db, skip=skip, limit=limit)
    return {"code": "200", "msg": "success", "data": {"venues": vs}}

@router.post("/addVenue", response_model=ResponseModel)
def api_add_venue(
    token: str           = Header(..., alias="X-HAHACAR-TOKEN"),
    venue: VenueCreate   = Depends(),
    db: Session          = Depends(get_db),
):
    """
    **Description**
    增添一个可选的预约地点

    **Params**
    - `venueName`: 地点名称
    - `venueType`: 地点类型
    - `venuePosition`: 经纬度

    **Returns**
    - 空对象
    """
    # TODO: 在此校验 token 合法性
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return verify_jwt_token(token)

    create_venue(db, venue)
    return {"code": "200", "msg": "success", "data": {}}

@router.post("/updateVenue", response_model=ResponseModel)
def api_update_venue(
    token: str            = Header(..., alias="X-HAHACAR-TOKEN"),
    venue: VenueUpdate    = Depends(),
    db: Session           = Depends(get_db),
):
    """
    **Description**
    修改一个可用的预约地点

    **Params**
    - `venueId`: 地点 ID
    - `venueName`: 地点名称
    - `venueType`: 地点类型
    - `venuePosition`: 经纬度

    **Returns**
    - 空对象
    """
    updated = update_venue(db, venue)
    if not updated:
        raise HTTPException(status_code=404, detail="Venue not found")
    return {"code": "200", "msg": "success", "data": {}}

@router.delete("/deleteVenue", response_model=ResponseModel)
def api_delete_venue(
    token: str                 = Header(..., alias="X-HAHACAR-TOKEN"),
    body: DeleteVenueRequest   = Depends(),
    db: Session                = Depends(get_db),
):
    """
    **Description**
    删除一个可用的预约地点

    **Params**
    - `venueId`: 地点 ID

    **Returns**
    - 空对象
    """
    delete_venue(db, body.venueId)
    return {"code": "200", "msg": "success", "data": {}}


@router.get("/getVenueRoute", response_model=GetVenueRoutesResponse)
def api_get_venue_route(
    pageNum: Optional[int] = Query(None),
    pageSize: Optional[int] = Query(None),
    venueIdFrom: Optional[str] = Query(None, alias="venueIdFrom"),
    venueIdTo: Optional[str] = Query(None, alias="venueIdTo"),
    venueRoutesId: Optional[str] = Query(None, alias="venueRoutesId"),
    db: Session = Depends(get_db)
):
    skip = (pageNum - 1) * pageSize if pageNum and pageSize else 0
    limit = pageSize or 10
    records = get_venue_route(
        db,
        venueRoutesId=venueRoutesId,
        venueFromId=venueIdFrom,
        venueToId=venueIdTo,
        skip=skip,
        limit=limit
    )
    if not records:
        raise HTTPException(status_code=404, detail="no routes found")
    bundles = []
    for route, nodes in records:
        bundles.append(
            RouteBundle(
                venueRoutes=[node for node in nodes],
                venueFromId=route.venueFromId,
                venueToId=route.venueToId,
                venueRoutesId=route.venueRoutesId
            )
        )
    data = GetVenueRoutesData(routes=bundles)
    return {"code": "200", "msg": "success", "data": data}

@router.post("/updateVenueRoute", response_model=ResponseModel)
def api_update_venue_route(
    token: str = Header(..., alias="X-HAHACAR-TOKEN"),
    req: UpdateRoutesRequest = Body(...),
    db: Session = Depends(get_db)
):
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return verify_jwt_token(token)
    update_venue_route(db, req)
    return {"code": "200", "msg": "success", "data": {}}

@router.post("/reserveByPlate", response_model=ResponseModel)
def api_reserve_by_plate(
    req: ReserveByPlateRequest = Body(...),
    db: Session = Depends(get_db)
):
    reserve_by_plate(db, req)
    return {"code": "200", "msg": "success", "data": {}}

@router.get("/getReserve", response_model=GetReserveResponse)
def api_get_reserve(
    openId: str = Query(..., alias="openId"),
    db: Session = Depends(get_db)
):
    recs = get_reserve_by_openid(db, openId)
    items = [
        ReserveItem(
            licence=r.licence,
            venueRoutesId=r.venueRoutesId,
            reserveId=r.reserveId,
            reserveTime=r.reserveTime,
            openId=r.openId
        )
        for r in recs
    ]
    data = GetReserveData(reserves=items)
    return {"code": "200", "msg": "success", "data": data}