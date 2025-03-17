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
               "label_ids":  json.dumps(rule_update.labelId)        #sqlite不支持存储list类型，所以要存储为json字符串
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




# def getCameraRule(db: Session, cameraId: str):
#     cameraRules = db.query(CameraRule).filter(CameraRule.camera_id == cameraId).all()
#     if cameraRules is None:
#         return {"code": "400", "msg": "cameraRules is None", "data": {}}
#     # 处理 JSON 解析错误
#     rules_data = []
#     for rule in cameraRules:
#         rule_data = CameraRuleUpdate.from_orm(rule).dict()
#
#         # 解析 JSON 字段，确保其是 Python 数据类型
#         json_fields = ["label_ids", "labels_equal_hold_ids", "labels_equal_flow_ids"]
#         for field in json_fields:
#             if field in rule_data and rule_data[field]:
#                 try:
#                     rule_data[field] = json.loads(rule_data[field])  # 转换 JSON 数据
#                 except (TypeError, json.JSONDecodeError):
#                     pass  # 防止异常导致崩溃
#
#         rules_data.append(rule_data)  # 添加到结果列表
#
#     return {"code": "200", "msg": "success", "data": rules_data}


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
                "maxVihicleHoldNum": str(rule.max_vehicle_hold_num) if rule.max_vehicle_hold_num else "0",
                "maxContinuousTimePeriod": rule.max_continuous_time_period if rule.max_continuous_time_period else 0,
                "minVihicleHoldNum": str(rule.min_vehicle_hold_num) if rule.min_vehicle_hold_num else "0",
                "minContinuousTimePeriod": rule.min_continuous_time_period if rule.min_continuous_time_period else 0,
                "LabelsEqual": LabelsEqual
            }

        elif rule.rule_value == '3':
            if isinstance(rule.labels_equal_flow_ids, list):
                LabelsEqual = rule.labels_equal_flow_ids
            else:
                LabelsEqual = json.loads(rule.labels_equal_flow_ids) if rule.labels_equal_flow_ids else []
            rule_data["VehicleFlow"] = {
                "maxVihicleFlowNum": str(rule.max_vehicle_flow_num) if rule.max_vehicle_flow_num else "0",
                "maxContinuousTimePeriod": rule.max_continuous_time_period if rule.max_continuous_time_period else 0,
                "minVihicleFlowNum": str(rule.min_vehicle_flow_num) if rule.min_vehicle_flow_num else "0",
                "minContinuousTimePeriod": rule.min_continuous_time_period if rule.min_continuous_time_period else 0,
                "LabelsEqual": LabelsEqual,
                "cameraStartLine": {"cameraLineId": rule.camera_start_line_id,
                                    "isAll": False} if rule.camera_start_line_id else None,
                "cameraEndLine": {"cameraLineId": rule.camera_end_line_id,
                                  "isAll": True} if rule.camera_end_line_id else None
            }

        rules_data.append(rule_data)

    return {"code": "200", "msg": "查询成功", "data": {"cameraRules": rules_data}}