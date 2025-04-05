from sqlalchemy import Column, String, Integer, JSON, Float, DateTime
from dependencies.database import Base

#车的类型标签
class VehicleLabel(Base):
    __tablename__ = "vehicle_labels"

    label_id = Column(String, primary_key=True, index=True)
    label_name = Column(String, unique=True)
    default_equal = Column(String)
