from models.venue_route import VenueRoute
from models.venue_routes import VenueRoutes
from models.reserve import Reserve
from schemas.route_schema import *
from services.route_service import *
import uuid
from sqlalchemy.orm import Session

def get_venue_route(db: Session,
                    venueRoutesId: Optional[str] = None,
                    venueFromId: Optional[str] = None,
                    venueToId: Optional[str] = None,
                    skip: int = 0,
                    limit: int = 10):
    # 找到一条符合条件的路线
    query = db.query(VenueRoutes)
    if venueRoutesId:
        query = query.filter(VenueRoutes.venueRoutesId == venueRoutesId)
    elif venueFromId and venueToId:
        query = query.filter(
            VenueRoutes.venueFromId == venueFromId,
            VenueRoutes.venueToId == venueToId
        )
    route = query.offset(skip).limit(limit).first()
    if not route:
        return None, None
    # 查询所有节点，并按 sequence 排序
    nodes = db.query(VenueRoute)\
        .filter(VenueRoute.venueRoutesId == route.venueRoutesId)\
        .order_by(VenueRoute.venueRouteSequence)\
        .all()
    return route, nodes

def update_venue_route(db: Session, req: UpdateVenueRouteRequest):
    # 先更新主表
    vr = db.query(VenueRoutes)\
        .filter(VenueRoutes.venueRoutesId == req.venueRoutesId)\
        .first()
    if not vr:
        # 如果不存在则新建
        vr = VenueRoutes(
            venueRoutesId=req.venueRoutesId,
            venueFromId=req.venueFromId,
            venueToId=req.venueToId
        )
        db.add(vr)
    else:
        vr.venueFromId = req.venueFromId
        vr.venueToId = req.venueToId
    # 处理节点的增删改
    existing = {
        node.venueRouteId: node
        for node in db.query(VenueRoute)
            .filter(VenueRoute.venueRoutesId == req.venueRoutesId)
            .all()
    }
    seen = set()
    for item in req.venueRoutes:
        if not item.venueRouteId:
            # 新增
            new_id = str(uuid.uuid4())
            nr = VenueRoute(
                venueRouteId=new_id,
                venueRoutesId=req.venueRoutesId,
                venueRouteSequence=item.venueRouteSequence,
                cameraLineId=item.cameraLineId,
                pointCloseToLine=item.pointCloseToLine
            )
            db.add(nr)
        else:
            seen.add(item.venueRouteId)
            node = existing.get(item.venueRouteId)
            if node:
                node.venueRouteSequence = item.venueRouteSequence
                node.cameraLineId = item.cameraLineId
                node.pointCloseToLine = item.pointCloseToLine
    # 删除多余节点
    for vid, node in existing.items():
        if vid not in seen:
            db.delete(node)
    db.commit()

def reserve_by_plate(db: Session, req: ReserveByPlateRequest):
    if req.reserveId:
        r = db.query(Reserve)\
            .filter(Reserve.reserveId == req.reserveId)\
            .first()
        if r:
            r.licence = req.licence
            r.venueRoutesId = req.venueRoutesId
            r.reserveTime = req.reserveTime
            r.openId = req.openId
            db.commit()
            return
    # 新建
    new_id = str(uuid.uuid4())
    r = Reserve(
        reserveId=new_id,
        licence=req.licence,
        venueRoutesId=req.venueRoutesId,
        reserveTime=req.reserveTime,
        openId=req.openId
    )
    db.add(r)
    db.commit()

def get_reserve_by_openid(db: Session, openId: str):
    return db.query(Reserve)\
        .filter(Reserve.openId == openId)\
        .all()


