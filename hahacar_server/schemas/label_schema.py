from pydantic import BaseModel


class LabelsResponse(BaseModel):
    labelId: str
    labelName: str