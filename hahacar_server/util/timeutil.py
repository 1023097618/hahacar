import datetime
from urllib.parse import unquote


def get_utc_datetime_from_timestamp(timestamp):
    """
    将 Unix 时间戳转换为 UTC 时间，并确保时间精确到秒
    如果传入的是 datetime 对象，则直接将 microsecond 置为 0

    参数:
        timestamp (Union[float, int, datetime.datetime]): Unix 时间戳或者 datetime 对象

    返回:
        datetime.datetime: 不包含微秒信息的 UTC 时间对象
    """
    if isinstance(timestamp, datetime.datetime):
        # 如果已经是 datetime 对象，则直接置为秒级别
        return timestamp.replace(microsecond=0)
    # 否则，将 Unix 时间戳转换为 datetime 对象
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    return dt.replace(microsecond=0)

def parse_frontend_time(time_str: str) -> datetime.datetime:
    """
    解析前端传入的时间字符串，先进行 URL 解码，然后统一返回不含微秒的 datetime 对象。

    函数流程：
      1. 使用 unquote 对传入的字符串进行解码
      2. 依次尝试两种时间格式进行解析：
         - "%Y-%m-%d %H:%M:%S"       —— 不带微秒
         - "%Y-%m-%d %H:%M:%S.%f"    —— 带微秒
      3. 返回解析后的 datetime 对象，并通过 replace 将 microsecond 设为 0

    参数:
      time_str (str): 前端传入的时间字符串，可能经过 URL 编码

    返回:
      datetime.datetime: 解析后的时间对象，精确到秒

    抛出:
      ValueError: 如果无法匹配上述任一时间格式，则抛出异常。
    """
    # 先进行 URL 解码
    decoded_time_str = unquote(time_str)

    # 尝试两种时间格式
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            dt = datetime.datetime.strptime(decoded_time_str, fmt)
            return dt.replace(microsecond=0)
        except ValueError:
            continue
    raise ValueError("时间字符串格式不符合预期，要求格式为 'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DD HH:MM:SS.%f'")