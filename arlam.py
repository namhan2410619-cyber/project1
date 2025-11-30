import datetime
# IoT 메시지 전송(MQTT)
import paho.mqtt.client as mqtt

def send_alarm_signal():
    client = mqtt.Client()
    client.connect("broker.hivemq.com", 1883)
    client.publish("iot/alarm", "wake_up")
    client.disconnect()

def calculate_alarm_time(prep, commute):
    now = datetime.datetime.now()
    school_time = now.replace(hour=9, minute=0, second=0)

    wake_time = school_time - datetime.timedelta(minutes=(prep + commute))

    if wake_time < now:
        wake_time += datetime.timedelta(days=1)  # 다음날 시간으로 보정

    send_alarm_signal()  # IoT 알람 전송
    return wake_time.strftime("%H:%M")
