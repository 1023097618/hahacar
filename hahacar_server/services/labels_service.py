from sqlalchemy.orm import Session

from models.vehicle_labels import VehicleLabel
from schemas.label_schema import LabelsResponse


def getLabels(db: Session):
    labels = db.query(VehicleLabel).filter(VehicleLabel.label_name != "").all()
    if not labels:
        return {
            "code": 200,
            "data": {
                "labels": []
            }
            ,
            "msg": "labels is not found"
        }
    return {
        "code": 200,
        "msg":"success",
        "data": {
            "labels":[
                {
                    "labelId": label.label_id,
                    "labelName": label.label_name
                }
                for label in labels
            ]
        }
    }