import datetime

def calculate_alarm_time(prep_time, commute_time, school_hour=9, school_minute=0):
    now = datetime.datetime.now()
    school_time = now.replace(hour=school_hour, minute=school_minute, second=0)

    wake_time = school_time - datetime.timedelta(minutes=(prep_time + commute_time))

    if wake_time < now:
        wake_time += datetime.timedelta(days=1)

    return wake_time.strftime("%H:%M")
