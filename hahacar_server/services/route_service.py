from models.venue_route import VenueRoute
from models.venue_routes import VenueRoutes
from models.reserve import Reserve
from models.camera_line import CameraLine
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
    if venueFromId:
        query = query.filter(VenueRoutes.venueFromId == venueFromId)
    if venueToId:
        query = query.filter(VenueRoutes.venueToId == venueToId)
    routes = query.offset(skip).limit(limit).all()
    results = []
    for r in routes:
        nodes = (
            db.query(VenueRoute)
            .filter(VenueRoute.venueRoutesId == r.venueRoutesId)
            .order_by(VenueRoute.venueRouteSequence)
            .all()
        )
        results.append((r, nodes))
    return results

#实现增加了routes表，但没在route表里增加路线
def update_venue_route(db: Session, req: UpdateRoutesRequest):
    for bundle in req.routes:
        # upsert 路线主表
        vr = (
            db.query(VenueRoutes)
            .filter(VenueRoutes.venueRoutesId == bundle.venueRoutesId)
            .first()
        )
        if not vr:
            vr = VenueRoutes(
                venueRoutesId=bundle.venueRoutesId,
                venueFromId=bundle.venueFromId,
                venueToId=bundle.venueToId
            )
            db.add(vr)
        else:
            vr.venueFromId = bundle.venueFromId
            vr.venueToId = bundle.venueToId

        # 节点增删改
        existing = {
            node.venueRouteId: node
            for node in db.query(VenueRoute)
                          .filter(VenueRoute.venueRoutesId == bundle.venueRoutesId)
                          .all()
        }
        seen = set()
        for item in bundle.venueRoutes:
            isNew = (not item.venueRouteId) or (item.venueRouteId not in existing)
            if isNew:
                new_id = item.venueRouteId or str(uuid.uuid4())
                db.add(
                    VenueRoute(
                        venueRouteId=new_id,
                        venueRoutesId=bundle.venueRoutesId,
                        venueRouteSequence=item.venueRouteSequence,
                        cameraLineId=item.cameraLineId,
                    )
                )
                seen.add(new_id)
            else:
                seen.add(item.venueRouteId)
                node = existing[item.venueRouteId]
                node.venueRouteSequence = item.venueRouteSequence
                node.cameraLineId       = item.cameraLineId

        # 删除那些 existing 里但不在 seen 里的
        for old_id, node in existing.items():
            if old_id not in seen:
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


