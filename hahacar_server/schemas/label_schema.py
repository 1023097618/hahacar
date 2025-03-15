from pydantic import BaseModel


class LabelsResponse(BaseModel):
    label_id: str  # 修改字段名
    label_name: str

    class Config:
        orm_mode = True  # 允许 from_orm() 使用