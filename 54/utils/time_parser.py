import re
from datetime import timedelta

def parse_time(time_str: str) -> timedelta | None:
    if not time_str:
        return None
        
    pattern = r"(\d+)([smhd])"
    match = re.match(pattern, time_str.lower())
    
    if not match:
        return None
        
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    
    return None
