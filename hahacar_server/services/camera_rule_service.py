import json
from uuid import uuid4

from sqlalchemy.orm import Session

from models.camera_line import CameraLine
from models.camera_rule import CameraRule
from schemas.camera_rule_schema import *

#预警规则更新，根据camera_id
def updateCameraRule(db: Session, request: CameraRuleUpdateRequest):
    cameraId = request.camera_id
    rules_update = request.cameraRules

    for rule_update in rules_update:
        #先根据cameraid和rulevalue查询一下是否有对应的记录
        existing_rule = db.query(CameraRule).filter(CameraRule.camera_id == cameraId, CameraRule.rule_value == rule_update.rule_value).first()
        if existing_rule is None:
            existing_rule = CameraRule(
                id=str(uuid4()),  # 主键，可用UUID
                camera_id=cameraId,
                rule_value=rule_update.rule_value,
            )
            db.add(existing_rule)

        if rule_update.rule_value == '1':
           if rule_update.labelId:
               db.query(CameraRule).filter(CameraRule.camera_id == cameraId).update({
                   "label_ids":  json.dumps(rule_update.labelId)        #sqlite不支持存储list类型，所以要存储为json字符串
               })
               db.commit()
           else:
               return {"code": "400", "msg": "labelId is None", "data": {}}
        elif rule_update.rule_value == '2':
            if isinstance(rule_update.VehicleHold.LabelsEqual,str):
                labels_equal_hold = rule_update.VehicleHold.LabelsEqual #直接使用字符串存储
            else:
                labels_equal_hold = json.dumps([{"labelId": item.labelId, "labelHoldNum": item.labelHoldNum} for item in rule_update.VehicleHold.LabelsEqual])
            if rule_update.VehicleHold:
                db.query(CameraRule).filter(CameraRule.camera_id == cameraId).update({
                    "max_vehicle_hold_num": rule_update.VehicleHold.maxVehicleHoldNum,
                    "min_vehicle_hold_num": rule_update.VehicleHold.minVehicleHoldNum,
                    "max_continuous_time_period": rule_update.VehicleHold.maxContinuousTimePeriod,
                    "labels_equal_hold_ids": labels_equal_hold
                })
                db.commit()
            else:
                return {"code": "400", "msg": "VehicleHold is None", "data": {}}
        elif rule_update.rule_value == '3':
            if isinstance(rule_update.VehicleFlow.LabelsEqual,str):
                labels_equal_flow = rule_update.VehicleFlow.LabelsEqual #直接使用字符串存储
            else:
                labels_equal_flow = json.dumps([{"labelId": item.labelId, "labelEqualNum": item.labelEqualNum} for item in rule_update.VehicleFlow.LabelsEqual])
            if rule_update.VehicleFlow:
                update_data = {
                    "max_vehicle_flow_num": rule_update.VehicleFlow.maxVehicleFlowNum,
                    "min_vehicle_flow_num": rule_update.VehicleFlow.minVehicleFlowNum,
                    "max_continuous_time_period": rule_update.VehicleFlow.maxContinuousTimePeriod,
                    "labels_equal_flow_ids": labels_equal_flow
                }
                if rule_update.VehicleFlow.cameraStartLine and not rule_update.VehicleFlow.cameraStartLine.isAll:
                    update_data["camera_start_line_id"] = rule_update.VehicleFlow.cameraStartLine.cameraLineId
                if rule_update.VehicleFlow.cameraEndLine and not rule_update.VehicleFlow.cameraEndLine.isAll:
                        update_data["camera_end_line_id"] = rule_update.VehicleFlow.cameraEndLine.cameraLineId

                db.query(CameraRule).filter(CameraRule.camera_id == cameraId).update(update_data)
                db.commit()
            else:
                return {"code": "400", "msg": "VehicleFlow is None", "data": {}}
        else:
            return {"code": "400", "msg": "ruleValue is None or not in '1','2','3'", "data": {}}
    return {"code": "200", "msg": "success", "data": {}}


def getCameraRule(db: Session, cameraId: str):
    cameraRules = db.query(CameraRule).filter(CameraRule.camera_id == cameraId).all()

    if not cameraRules:  # 避免 None 和空列表
        return {"code": "400", "msg": "cameraRules is None", "data": {}}

    rules_data = []
    for rule in cameraRules:
        rule_data = {
            "ruleValue": str(rule.rule_value),  # 确保返回字符串
        }

        # 处理不同 rule_value 的规则
        if rule.rule_value == '1':
            if isinstance(rule.label_ids, list):
                rule_data["labelId"] = rule.label_ids       #如果是list类型，不需jsonloads处理，直接赋值
            else:
                rule_data["labelId"] = json.loads(rule.label_ids) if rule.label_ids else []

        elif rule.rule_value == '2':
            if isinstance(rule.labels_equal_hold_ids, list):
                LabelsEqual = rule.labels_equal_hold_ids
            else:
                LabelsEqual = json.loads(rule.labels_equal_hold_ids) if rule.labels_equal_hold_ids else []
            rule_data["VehicleHold"] = {
                "maxVehicleHoldNum": str(rule.max_vehicle_hold_num) if rule.max_vehicle_hold_num else "0",
                "maxContinuousTimePeriod": rule.max_continuous_time_period if rule.max_continuous_time_period else 0,
                "minVehicleHoldNum": str(rule.min_vehicle_hold_num) if rule.min_vehicle_hold_num else "0",
                "minContinuousTimePeriod": rule.min_continuous_time_period if rule.min_continuous_time_period else 0,
                "LabelsEqual": LabelsEqual
            }

        elif rule.rule_value == '3':
            if isinstance(rule.labels_equal_flow_ids, list):
                LabelsEqual = rule.labels_equal_flow_ids
            else:
                LabelsEqual = json.loads(rule.labels_equal_flow_ids) if rule.labels_equal_flow_ids else []
            rule_data["VehicleFlow"] = {
                "maxVehicleFlowNum": str(rule.max_vehicle_flow_num) if rule.max_vehicle_flow_num else "0",
                "maxContinuousTimePeriod": rule.max_continuous_time_period if rule.max_continuous_time_period else 0,
                "minVehicleFlowNum": str(rule.min_vehicle_flow_num) if rule.min_vehicle_flow_num else "0",
                "minContinuousTimePeriod": rule.min_continuous_time_period if rule.min_continuous_time_period else 0,
                "LabelsEqual": LabelsEqual,
                "cameraStartLine": {"cameraLineId": rule.camera_start_line_id,
                                    "isAll": False} if rule.camera_start_line_id else None,
                "cameraEndLine": {"cameraLineId": rule.camera_end_line_id,
                                  "isAll": True} if rule.camera_end_line_id else None
            }

        rules_data.append(rule_data)

    return {"code": "200", "msg": "查询成功", "data": {"cameraRules": rules_data}}