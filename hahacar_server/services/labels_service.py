from sqlalchemy.orm import Session

from models.vehicle_labels import VehicleLabel
from schemas.label_schema import LabelsResponse


def getLabels(db: Session):
    labels = db.query(VehicleLabel).filter(VehicleLabel.label_name != "").all()
    return labels