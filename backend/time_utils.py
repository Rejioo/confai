from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def now_ist_naive():
    """
    Returns current IST time as naive datetime
    """
    return datetime.now(IST).replace(tzinfo=None)
