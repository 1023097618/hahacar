from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies.database import get_db
from services.labels_service import getLabels

router = APIRouter(prefix="/api/label", tags=["Label"])

@router.get("/getLabels")
def getLabelsApi(db: Session = Depends(get_db)):
    labels = getLabels(db)
    return {
            "code": "200",
            "data": {
                "labels": [{"labelId":label.label_id, "labelName":label.label_name} for label in labels]
            }
            ,
            "msg": "Success"
        }