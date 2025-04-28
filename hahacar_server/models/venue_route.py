from sqlalchemy import Column, String, Integer, ForeignKey
from dependencies.database import Base
from sqlalchemy.orm import relationship

class VenueRoute(Base):
    __tablename__ = "venue_route"
    venueRouteId       = Column("venue_route_id", String, primary_key=True)
    venueRouteSequence = Column("venue_route_sequence", Integer, nullable=False)
    cameraLineId       = Column("camera_line_id", String, ForeignKey("camera_lines.camera_line_id"), nullable=False)
    venueRoutesId      = Column("venue_routes_id", String, nullable=False)
    
    # 1. 建立与 CameraLine 的关系
    cameraLine = relationship(
        "CameraLine",
        back_populates="venueRoutes",
        lazy="joined"
    )

    @property
    def pointCloseToLine(self):
        """
        **Description**
        通过 cameraLineId 关联到 CameraLine 表，动态返回对应的 [经度, 纬度]

        **Returns**
        - 返回 CameraLine.point_close_to_line 字段
        """
        # 如果没加载上来，.cameraLine 可能是 None，要做好空值检查
        return self.cameraLine.point_close_to_line if self.cameraLine else None