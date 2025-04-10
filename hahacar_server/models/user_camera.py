from dependencies.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class UserCamera(Base):
    __tablename__ = "user_camera"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    camera_id = Column(String, ForeignKey("camera.id"), nullable=False)