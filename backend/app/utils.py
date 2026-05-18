from datetime import datetime, timezone, timedelta

CHINA_TZ = timezone(timedelta(hours=8))


def format_datetime(dt):
    """将 datetime 格式化为东八区时间字符串，不带 T"""
    if dt is None:
        return None
    # 如果没有时区信息，假设是UTC时间
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # 转换为东八区
    dt = dt.astimezone(CHINA_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
