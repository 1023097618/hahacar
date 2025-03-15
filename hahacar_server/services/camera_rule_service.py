import json

from sqlalchemy.orm import Session

from models.camera_line import CameraLine
from models.camera_rule import CameraRule
from schemas.camera_rule_schema import *

#预警规则更新，根据camera_id
def updateCameraRule(db: Session, rule_update: CameraRuleUpdate):
    if rule_update.ruleValue == '1':
       if rule_update.labelId:
           db.query(CameraRule).filter(CameraRule.camera_id == rule_update.cameraId).update({
               "label_ids": json.dumps([{"labelId": item.labelId} for item in rule_update.labelId])
           })
       else:
           return {"code": "400", "msg": "labelId is None", "data": {}}
    elif rule_update.ruleValue == '2':
        if rule_update.VehicleHold:
            db.query(CameraRule).filter(CameraRule.camera_id == rule_update.cameraId).update({
                "max_vehicle_hold_num": rule_update.VehicleHold.maxVehicleHoldNum,
                "min_vehicle_hold_num": rule_update.VehicleHold.minVehicleHoldNum,
                "max_continuous_time_period": rule_update.VehicleHold.maxContinuousTimePeriod,
                "labels_equal_hold_ids": json.dumps([{"labelId": item.labelId, "labelHoldNum": item.labelHoldNum} for item in rule_update.VehicleHold.LabelsEqual]),
            })
            db.commit()
        else:
            return {"code": "400", "msg": "VehicleHold is None", "data": {}}
    elif rule_update.ruleValue == '3':
        if rule_update.VehicleFlow:
            update_data = {
                "max_vehicle_flow_num": rule_update.VehicleFlow.maxVehicleFlowNum,
                "min_vehicle_flow_num": rule_update.VehicleFlow.minVehicleFlowNum,
                "max_continuous_time_period": rule_update.VehicleFlow.maxContinuousTimePeriod,
                "labels_equal_flow_ids": json.dumps([{"labelId": item.labelId, "labelFlowNum": item.labelFlowNum} for item in rule_update.VehicleFlow.LabelsEqual]),
            }
            if rule_update.VehicleFlow.cameraStartLine and not rule_update.VehicleFlow.cameraStartLine.isAll:
                update_data["camera_start_line_id"] = rule_update.VehicleFlow.cameraStartLine.cameraLineId
            if rule_update.VehicleFlow.cameraEndLine and not rule_update.VehicleFlow.cameraEndLine.isAll:
                    update_data["camera_end_line_id"] = rule_update.VehicleFlow.cameraEndLine.cameraLineId
            db.query(CameraRule).filter(CameraRule.camera_id == rule_update.cameraId).update(update_data)
            db.commit()
        else:
            return {"code": "400", "msg": "VehicleFlow is None", "data": {}}
    else:
        return {"code": "400", "msg": "ruleValue is None or not in '1','2','3'", "data": {}}
    return {"code": "200", "msg": "success", "data": {}}




def getCameraRule(db: Session, cameraId: str):
    cameraRules = db.query(CameraRule).filter(CameraRule.camera_id == cameraId).first()
    if cameraRules is None:
        return {"code": "400", "msg": "cameraRules is None", "data": {}}
    else:
        return {"code": "200", "msg": "success", "data": CameraRuleUpdate.from_orm(cameraRules).dict()}