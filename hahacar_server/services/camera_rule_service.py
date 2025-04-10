import json
import uuid
from uuid import uuid4

from sqlalchemy.orm import Session

from models.camera_rule import CameraRule, CameraRule1, CameraRule2, CameraRule3, CameraRule4, CameraRule5
from schemas.camera_rule_schema import CameraRuleUpdateRequest


def updateCameraRule(db: Session, request: CameraRuleUpdateRequest):
    cameraId = request.camera_id

    # 1. 查询该摄像头在数据库中的所有规则，并构造字典 {rule_id: rule}
    existing_rules = db.query(CameraRule).filter(CameraRule.camera_id == cameraId).all()
    existing_rule_dict = {rule.rule_id: rule for rule in existing_rules}

    # 2. 从请求中提取所有已有规则的 rule_id（新增规则时该字段应为 None）
    request_rule_ids = {rule_update.rule_id for rule_update in request.cameraRules if rule_update.rule_id}

    # 3. 删除数据库中存在但请求中未包含的规则，同时删除对应的分表数据
    for rule_id, rule in existing_rule_dict.items():
        if rule_id not in request_rule_ids:
            if rule.rule_value == "1":
                db.query(CameraRule1).filter(CameraRule1.rule_id == rule_id).delete()
            elif rule.rule_value == "2":
                db.query(CameraRule2).filter(CameraRule2.rule_id == rule_id).delete()
            elif rule.rule_value == "3":
                db.query(CameraRule3).filter(CameraRule3.rule_id == rule_id).delete()
            elif rule.rule_value == "4":
                db.query(CameraRule4).filter(CameraRule4.rule_id == rule_id).delete()
            elif rule.rule_value == "5":
                db.query(CameraRule5).filter(CameraRule5.rule_id == rule_id).delete()
            db.query(CameraRule).filter(CameraRule.rule_id == rule_id).delete()
    db.commit()  # 提交删除操作

    # 4. 遍历请求中的每条规则，进行更新或新增操作
    for rule_update in request.cameraRules:
        # 若传递了 rule_id 且数据库中存在该规则，则更新；否则视为新增规则
        if rule_update.rule_id and rule_update.rule_id in existing_rule_dict:
            rule_id = rule_update.rule_id

            # 更新主表中 rule_value（如有其它字段需要更新，可一并处理）
            db.query(CameraRule).filter(CameraRule.rule_id == rule_id).update({
                "rule_value": rule_update.rule_value
            })

            # 根据 rule_value 更新对应分表数据
            if rule_update.rule_value == "1" and rule_update.label:
                label_data = json.dumps(rule_update.label.dict(by_alias=True))
                db.query(CameraRule1).filter(CameraRule1.rule_id == rule_id).update({
                    "labels": label_data
                })
            elif rule_update.rule_value == "2" and rule_update.VehicleHold:
                vh = rule_update.VehicleHold
                labels_equal = json.dumps([item.dict() for item in vh.LabelsEqual]) if vh.LabelsEqual else None
                db.query(CameraRule2).filter(CameraRule2.rule_id == rule_id).update({
                    "max_vehicle_hold_num": vh.maxVehicleHoldNum,
                    "min_vehicle_hold_num": vh.minVehicleHoldNum,
                    "max_continuous_time_period": str(vh.maxContinuousTimePeriod),
                    "min_continuous_time_period": vh.minContinuousTimePeriod,
                    "Labels_equal": labels_equal
                })
            elif rule_update.rule_value == "3" and rule_update.VehicleFlow:
                vf = rule_update.VehicleFlow
                labels_equal = json.dumps([item.dict() for item in vf.LabelsEqual]) if vf.LabelsEqual else None
                camera_start_line = json.dumps(vf.cameraStartLine.dict()) if vf.cameraStartLine else None
                camera_end_line = json.dumps(vf.cameraEndLine.dict()) if vf.cameraEndLine else None
                db.query(CameraRule3).filter(CameraRule3.rule_id == rule_id).update({
                    "max_vehicle_flow_num": vf.maxVehicleFlowNum,
                    "max_continuous_time_period": str(vf.maxContinuousTimePeriod),
                    "min_vehicle_flow_num": vf.minVehicleFlowNum,
                    "min_continuous_time_period": str(vf.minContinuousTimePeriod),
                    "labels_equal": labels_equal,
                    "camera_start_line": camera_start_line,
                    "camera_end_line": camera_end_line
                })
            elif rule_update.rule_value == "4" and rule_update.VehicleReserve is not None:
                reserve_val = 1 if rule_update.VehicleReserve else 0
                db.query(CameraRule4).filter(CameraRule4.rule_id == rule_id).update({
                    "vehicle_reserve": reserve_val
                })
            elif rule_update.rule_value == "5" and rule_update.eventDetect is not None:
                event_detect_val = 1 if rule_update.eventDetect else 0
                db.query(CameraRule5).filter(CameraRule5.rule_id == rule_id).update({
                    "event_detect": event_detect_val
                })
        else:
            # 新规则：生成新的 rule_id，并插入主表和对应分表数据
            rule_id = str(uuid.uuid4())
            new_rule = CameraRule(rule_id=rule_id, camera_id=cameraId, rule_value=rule_update.rule_value)
            db.add(new_rule)

            if rule_update.rule_value == "1" and rule_update.label:
                label_data = json.dumps(rule_update.label.dict(by_alias=True))
                new_rule1 = CameraRule1(rule_id=rule_id, labels=label_data)
                db.add(new_rule1)
            elif rule_update.rule_value == "2" and rule_update.VehicleHold:
                vh = rule_update.VehicleHold
                labels_equal = json.dumps([item.dict() for item in vh.LabelsEqual]) if vh.LabelsEqual else None
                new_rule2 = CameraRule2(
                    rule_id=rule_id,
                    max_vehicle_hold_num=vh.maxVehicleHoldNum,
                    min_vehicle_hold_num=vh.minVehicleHoldNum,
                    max_continuous_time_period=str(vh.maxContinuousTimePeriod),
                    min_continuous_time_period=vh.minContinuousTimePeriod,
                    Labels_equal=labels_equal
                )
                db.add(new_rule2)
            elif rule_update.rule_value == "3" and rule_update.VehicleFlow:
                vf = rule_update.VehicleFlow
                labels_equal = json.dumps([item.dict() for item in vf.LabelsEqual]) if vf.LabelsEqual else None
                camera_start_line = json.dumps(vf.cameraStartLine.dict()) if vf.cameraStartLine else None
                camera_end_line = json.dumps(vf.cameraEndLine.dict()) if vf.cameraEndLine else None
                new_rule3 = CameraRule3(
                    rule_id=rule_id,
                    max_vehicle_flow_num=vf.maxVehicleFlowNum,
                    max_continuous_time_period=str(vf.maxContinuousTimePeriod),
                    min_vehicle_flow_num=vf.minVehicleFlowNum,
                    min_continuous_time_period=str(vf.minContinuousTimePeriod),
                    labels_equal=labels_equal,
                    camera_start_line=camera_start_line,
                    camera_end_line=camera_end_line
                )
                db.add(new_rule3)
            elif rule_update.rule_value == "4" and rule_update.VehicleReserve is not None:
                reserve_val = 1 if rule_update.VehicleReserve else 0
                new_rule4 = CameraRule4(rule_id=rule_id, vehicle_reserve=reserve_val)
                db.add(new_rule4)
            elif rule_update.rule_value == "5" and rule_update.eventDetect is not None:
                event_detect_val = 1 if rule_update.eventDetect else 0
                new_rule5 = CameraRule5(rule_id=rule_id, event_detect=event_detect_val)
                db.add(new_rule5)
    db.commit()  # 最后提交所有更新与插入操作
    from lifespan_manager import refresh_task
    refresh_task(cameraId)
    return True


def getCameraRule(db: Session, cameraId: str) -> dict:
    # 查询主表中属于指定摄像头的预警规则
    cameraRules = db.query(CameraRule).filter(CameraRule.camera_id == cameraId).all()

    result = {
        "cameraRules": []
    }

    for rule in cameraRules:
        # 返回时增加 rule_id 便于前端后续更新时使用
        rule_dict = {"rule_id": rule.rule_id, "ruleValue": rule.rule_value}

        if rule.rule_value == "1":
            # 根据 rule_id 查询 CameraRule1 表数据
            r1 = db.query(CameraRule1).filter(CameraRule1.rule_id == rule.rule_id).first()
            if r1:
                try:
                    label_obj = json.loads(r1.labels)
                except Exception:
                    label_obj = r1.labels
                rule_dict["label"] = label_obj

        elif rule.rule_value == "2":
            r2 = db.query(CameraRule2).filter(CameraRule2.rule_id == rule.rule_id).first()
            if r2:
                try:
                    labels_equal = json.loads(r2.Labels_equal) if r2.Labels_equal else []
                except Exception:
                    labels_equal = r2.Labels_equal
                rule_dict["VehicleHold"] = {
                    "maxVehicleHoldNum": r2.max_vehicle_hold_num,
                    "maxContinuousTimePeriod": r2.max_continuous_time_period,
                    "minVehicleHoldNum": r2.min_vehicle_hold_num,
                    "minContinuousTimePeriod": r2.min_continuous_time_period,
                    "LabelsEqual": labels_equal
                }

        elif rule.rule_value == "3":
            r3 = db.query(CameraRule3).filter(CameraRule3.rule_id == rule.rule_id).first()
            if r3:
                try:
                    labels_equal = json.loads(r3.labels_equal) if r3.labels_equal else []
                except Exception:
                    labels_equal = r3.labels_equal
                try:
                    camera_start_line = json.loads(r3.camera_start_line) if r3.camera_start_line else {}
                except Exception:
                    camera_start_line = r3.camera_start_line
                try:
                    camera_end_line = json.loads(r3.camera_end_line) if r3.camera_end_line else {}
                except Exception:
                    camera_end_line = r3.camera_end_line
                rule_dict["VehicleFlow"] = {
                    "maxVehicleFlowNum": r3.max_vehicle_flow_num,
                    "maxContinuousTimePeriod": r3.max_continuous_time_period,
                    "minVehicleFlowNum": r3.min_vehicle_flow_num,
                    "minContinuousTimePeriod": r3.min_continuous_time_period,
                    "LabelsEqual": labels_equal,
                    "cameraStartLine": camera_start_line,
                    "cameraEndLine": camera_end_line
                }

        elif rule.rule_value == "4":
            r4 = db.query(CameraRule4).filter(CameraRule4.rule_id == rule.rule_id).first()
            if r4:
                rule_dict["VehicleReserve"] = bool(r4.vehicle_reserve)

        elif rule.rule_value == "5":
            r5 = db.query(CameraRule5).filter(CameraRule5.rule_id == rule.rule_id).first()
            if r5:
                rule_dict["eventDetect"] = bool(r5.event_detect)

        result["cameraRules"].append(rule_dict)
    return result
