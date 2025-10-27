"""
Class Schedule Data for MBTA Prediction

"""

STANDARD_PATTERNS = [
    # Type A - 50 minute classes
    {"days": "MWF", "start": "09:05", "end": "09:55", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "10:10", "end": "11:00", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "12:20", "end": "13:10", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "13:25", "end": "14:15", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "14:30", "end": "15:20", "duration_min": 50, "type": "A"},
    {"days": "MWF", "start": "16:40", "end": "17:30", "duration_min": 50, "type": "A"},
    
    # Type B - 2:45 classes
    {"days": "MTWRF", "start": "08:00", "end": "10:45", "duration_min": 165, "type": "B"},
    {"days": "F", "start": "11:15", "end": "14:00", "duration_min": 165, "type": "B"},
    {"days": "TR", "start": "12:30", "end": "15:15", "duration_min": 165, "type": "B"},
    {"days": "MWF", "start": "14:30", "end": "17:15", "duration_min": 165, "type": "B"},
    {"days": "TR", "start": "15:30", "end": "18:15", "duration_min": 165, "type": "B"},
    {"days": "MTWRF", "start": "18:30", "end": "21:15", "duration_min": 165, "type": "B"},
    
    # Type C - 1:15 classes
    {"days": "TR", "start": "08:00", "end": "09:15", "duration_min": 75, "type": "C"},
    {"days": "TR", "start": "09:30", "end": "10:45", "duration_min": 75, "type": "C"},
    {"days": "TR", "start": "11:00", "end": "12:15", "duration_min": 75, "type": "C"},
    {"days": "TR", "start": "12:30", "end": "13:45", "duration_min": 75, "type": "C"},
    {"days": "TR", "start": "14:00", "end": "15:15", "duration_min": 75, "type": "C"},
    {"days": "TR", "start": "15:30", "end": "16:45", "duration_min": 75, "type": "C"},
    {"days": "TR", "start": "17:00", "end": "18:15", "duration_min": 75, "type": "C"},
    
    # Type D - 1:45 classes
    {"days": "MWF", "start": "08:00", "end": "09:45", "duration_min": 105, "type": "D"},
    {"days": "MWF", "start": "10:10", "end": "11:55", "duration_min": 105, "type": "D"},
    {"days": "MWF", "start": "12:20", "end": "14:05", "duration_min": 105, "type": "D"},
    {"days": "MWF", "start": "14:30", "end": "16:15", "duration_min": 105, "type": "D"},
    {"days": "MWF", "start": "16:30", "end": "18:15", "duration_min": 105, "type": "D"},
    {"days": "TR", "start": "09:00", "end": "10:45", "duration_min": 105, "type": "D"},
    {"days": "TR", "start": "13:30", "end": "15:15", "duration_min": 105, "type": "D"},
    {"days": "TR", "start": "15:30", "end": "17:15", "duration_min": 105, "type": "D"},
    
    # Type E - 50 minute classes (daily)
    {"days": "MTWRF", "start": "08:00", "end": "08:50", "duration_min": 50, "type": "E"},
    {"days": "MTWRF", "start": "11:15", "end": "12:05", "duration_min": 50, "type": "E"},
    {"days": "MTWRF", "start": "15:35", "end": "16:25", "duration_min": 50, "type": "E"},
]


def get_class_starts_at_time(hour: int, minute: int, day_of_week: int) -> int:
    """
    Returns the number of classes starting at a given time on a given day.
    
    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)
        day_of_week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        
    Returns:
        Number of classes starting at that time
    """
    # Map day to letter
    day_map = {
        0: 'M',  # Monday
        1: 'T',  # Tuesday
        2: 'W',  # Wednesday
        3: 'R',  # Thursday
        4: 'F',  # Friday
    }
    
    if day_of_week not in day_map:
        return 0  # No classes on weekends
    
    day_letter = day_map[day_of_week]
    time_str = f"{hour:02d}:{minute:02d}"
    
    # Check each pattern
    count = 0
    for pattern in STANDARD_PATTERNS:
        if day_letter in pattern['days'] and pattern['start'] == time_str:
            count += 1
    
    return count


def get_class_starts_in_window(start_hour: int, start_minute: int, 
                                end_hour: int, end_minute: int, 
                                day_of_week: int) -> int:
    """
    Returns the number of classes starting in a time window on a given day.
    
    Args:
        start_hour, start_minute: Start of time window
        end_hour, end_minute: End of time window
        day_of_week: 0=Monday, 1=Tuesday, etc.
        
    Returns:
        Total number of classes starting in that window
    """
    total = 0
    current_minute = start_minute
    
    # Iterate through each minute in the window
    for h in range(start_hour, end_hour + 1):
        end_m = end_minute if h == end_hour else 60
        
        while current_minute < end_m:
            total += get_class_starts_at_time(h, current_minute, day_of_week)
            current_minute += 1
        
        current_minute = 0
    
    return total


def get_peak_class_times(day_of_week: int = None) -> list:
    """
    Returns a list of peak class start times for a given day.
    
    Args:
        day_of_week: Optional, if None returns for all weekdays
        
    Returns:
        List of tuples (hour, minute, count)
    """
    peak_times = []
    days = [day_of_week] if day_of_week is not None else range(5)  # Monday-Friday
    
    for day in days:
        for pattern in STANDARD_PATTERNS:
            if day_of_week is None or any(day_map[day] in pattern['days'] 
                                          for day_map in [{0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F'}]):
                start_time = pattern['start']
                hour, minute = map(int, start_time.split(':'))
                count = get_class_starts_at_time(hour, minute, day if day_of_week is not None else day)
                peak_times.append((hour, minute, count))
    
    return sorted(peak_times)


if __name__ == '__main__':
    # Example: Get class starts for Monday at 10:10 AM
    print("Classes starting Monday 10:10 AM:", get_class_starts_at_time(10, 10, 0))
    print("Classes starting Tuesday 8:00-9:00 AM:", get_class_starts_in_window(8, 0, 9, 0, 1))
    print("\nPeak class start times (Monday):")
    for hour, minute, count in get_peak_class_times(day_of_week=0):
        if count > 0:
            print(f"{hour:02d}:{minute:02d} - {count} classes starting")
