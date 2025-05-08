import uuid
from sqlalchemy.orm import Session
from models.venues import Venue
from schemas.venues_schema import VenueCreate, VenueUpdate

def get_venues(db: Session, skip: int = 0, limit: int = 10):
    """
    **Description**
    分页获取可预约地点列表

    **Params**
    - `skip`: 跳过数量
    - `limit`: 限制数量

    **Returns**
    - Venue 列表
    """
    return db.query(Venue).offset(skip).limit(limit).all()

def create_venue(db: Session, venue_in: VenueCreate):
    """
    **Description**
    新增一个可预约地点

    **Params**
    - `venue_in`: 待创建地点信息

    **Returns**
    - 新建的 Venue 对象
    """
    newVenue = Venue(
        venueId      = str(uuid.uuid4()),
        venueName    = venue_in.venueName,
        venueType    = venue_in.venueType,
        venuePosition= venue_in.venuePosition,
    )
    db.add(newVenue)
    db.commit()
    db.refresh(newVenue)
    return newVenue

def update_venue(db: Session, venue_in: VenueUpdate):
    """
    **Description**
    更新可预约地点信息

    **Params**
    - `venue_in`: 包含 venueId 的更新数据

    **Returns**
    - 更新后的 Venue 对象；找不到时返回 None
    """
    dbVenue = db.query(Venue).filter(Venue.venueId == venue_in.venueId).first();
    if not dbVenue:
        return None
    dbVenue.venueName     = venue_in.venueName
    dbVenue.venueType     = venue_in.venueType
    dbVenue.venuePosition = venue_in.venuePosition
    db.commit()
    db.refresh(dbVenue)
    return dbVenue

def delete_venue(db: Session, venueId: str):
    """
    **Description**
    删除指定的可预约地点

    **Params**
    - `venueId`: 待删除地点ID

    **Returns**
    - None
    """
    db.query(Venue).filter(Venue.venueId == venueId).delete()
    db.commit()
