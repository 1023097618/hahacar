from sqlalchemy import Column, String

from dependencies.database import Base

#目前没用
class PCU(Base):
    __tablename__ = "pcu"

    pcu_id = Column(String, primary_key=True, index=True)
    lable_id = Column(String, description="和vehicle_labels关联，作外键")
    label_num = Column(String)
    pcu_type = Column(String)