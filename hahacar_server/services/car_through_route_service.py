from datetime import datetime

from models.CarThroughRoute import CarThroughRoute


def saveCarThroughFixedRoute(db, vehicle_no, vehicle_type, start_line, end_line, current_time, direction):
    """
    保存通过起止线车辆的相关信息
    参数:
        db: 数据库会话对象
        vehicle_no: 车辆编号（唯一标识）
        vehicle_type: 车辆类型（直接取检测记录中的 label）
        start_line: 车辆起始检测线ID
        end_line: 车辆终止检测线ID
        current_time: 当前检测时间（Unix时间戳，float型）
        direction: 车辆方向（"正向"、"逆向"或"未知"）
    """
    # 将 Unix 时间戳转换为 datetime 对象
    detection_time = datetime.datetime.fromtimestamp(current_time)

    car_route = CarThroughRoute(
        vehicle_no=vehicle_no,
        vehicle_type=vehicle_type,
        start_line=start_line,
        end_line=end_line,
        detection_time=detection_time,
        direction=direction
    )

    db.add(car_route)
    db.commit()
    db.refresh(car_route)
    print(
        f"已保存车辆 {vehicle_no} 的通行信息：类型 {vehicle_type}, 起线 {start_line}, 止线 {end_line}, 时间 {detection_time}, 方向 {direction}")