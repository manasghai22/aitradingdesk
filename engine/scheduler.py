from datetime import datetime
import time

def is_market_open() -> bool:
    """Check if time is between 09:15 and 15:30 IST and is a weekday."""
    now_time = datetime.now().time()
    open_t = datetime.strptime("09:15:00", "%H:%M:%S").time()
    close_t = datetime.strptime("15:30:00", "%H:%M:%S").time()
    
    if datetime.now().weekday() >= 5: # Sat or Sun
        return False
        
    return open_t <= now_time <= close_t

def is_square_off_time() -> bool:
    """Trigger at 15:20 to exit intraday positions."""
    now_time = datetime.now().time()
    sq_t = datetime.strptime("15:20:00", "%H:%M:%S").time()
    close_t = datetime.strptime("15:30:00", "%H:%M:%S").time()
    return sq_t <= now_time <= close_t
