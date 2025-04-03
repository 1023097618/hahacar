from pydantic import BaseModel, Field
from typing import List, Optional

from sqlalchemy import JSON

from models.camera_line import CameraLine


class LabelRule(BaseModel):
    label_ids: List[str] = Field(..., alias="labelId",description="车辆类型规则：车辆类型id列表")
    label_line_id: str = Field(...,alias="cameraLineId",  description="指定用于车辆类型预警的检测线ID")
    class Config:
        allow_population_by_field_name = True

class LabelsEqualHold(BaseModel):
    """
    ***descripition**
    交通当量设置
    """
    labelId: str
    labelHoldNum: str

class CameraLineSchema(BaseModel):
    """
    ***descripition**
    摄像头检测线
    """
    cameraLineId: str
    isAll: bool

class LabelsEqualFlow(BaseModel):
    """
    ***descripition**
    交通当量设置
    """
    labelId: str
    labelEqualNum: str

class cameraStartLine(BaseModel):
    cameraLineId: str
    isAll: bool = Field(..., description="如果为true，则代表不设置某个起始检测线")
class cameraEndLine(BaseModel):
    cameraLineId: str
    isAll: bool = Field(..., description="如果为true，则代表不设置某个终止检测线")
class VehicleHold(BaseModel):
    maxVehicleHoldNum: str = Field(..., description="float类型的Num，因为一些大客车不能看成1，需要看成1.5之类的")
    maxContinuousTimePeriod: int = Field(..., description="")
    minVehicleHoldNum: str = Field(..., description="float类型的Num，因为一些大客车不能看成1，需要看成1.5之类的")
    minContinuousTimePeriod: int = Field(..., description="")
    LabelsEqual: Optional[List[LabelsEqualHold]] = Field(None, description="交通当量设置")
class VehicleFlow(BaseModel):
    maxVehicleFlowNum: str = Field(..., description="float类型的Num，因为一些大客车不能看成1，需要看成1.5之类的")
    maxContinuousTimePeriod: int = Field(..., description="")
    minVehicleFlowNum: str = Field(..., description="float类型的Num，因为一些大客车不能看成1，需要看成1.5之类的")
    minContinuousTimePeriod: int = Field(..., description="")
    LabelsEqual: List[LabelsEqualFlow] = Field(None, description="交通当量设置")
    cameraStartLine:Optional[CameraLineSchema] = Field(None, description="摄像头起始线，从哪个起始检测线驶入的车辆")
    cameraEndLine:Optional[CameraLineSchema] = Field(None, description="摄像头终止线，到哪个终止检测线驶入的车辆")

class GetLabelResponse(BaseModel):
    """
    **description**
    获取标签返回模型
    """
    labelId: str
    labelName: str
class CameraRuleUpdate(BaseModel):
    """
    **description**
    更新摄像头规则请求模型
    """
    rule_value: str = Field(..., alias="ruleValue", description="规则值，1表示车类型；2表示车拥堵情况；3表示车流量")   #Fileld(...)表示必填项
    label: Optional[LabelRule] #= Field(None, description="仅当规则值为1时必填，包含车辆类型id列表及预警检测线ID")
    VehicleHold: Optional[VehicleHold]      # Field(None, description="车拥堵情况，如果规则值是2，则必填。当连续maxContinuousTimePeriod秒的帧检测出来的交通当量都大于等于maxVihicleHoldNum辆的时候开始预警，将预警状态置为'正在发生'，此时，如果检测到交通当量小于等于minVihicleHoldNum且持续了minContinuousTimePeriod秒时，将预警状态置为‘已经发生’")
    VehicleFlow: Optional[VehicleFlow]      #= Field(None, description="车流流量，如果规则值是3，则必填.需要注意的是vehicleType为2计算的是一帧里面存有的车，但是vehicleType为3时需要计算的是画面中一秒里面经过的交通当量，这两个是不一样的，最简单的例子就是停车场，停车场里面每辆车都是静止的，那么每一帧里面可能都有10个交通当量，但是可能没有交通当量在一秒里面经过。预警的规则也和上方的是一样的")
    VehicleReserve: Optional[bool] #= Field(None, description="是否开启针对预约车辆的检测，仅当vehicleType为4时传输")
    eventDetect: Optional[bool] #= Field(None, description="是否开启事故预警，仅当vehicleType为5时传输")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class CameraRuleUpdateRequest(BaseModel):
    camera_id: str = Field(..., alias="cameraId")
    cameraRules: List[CameraRuleUpdate]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
