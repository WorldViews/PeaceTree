import paho.mqtt.client as mqtt
import time, json, datetime

# MQTT broker details
BROKER = "takeoneworld.com"
PORT = 1883
TOPIC = "peacetreebsky"
USER = "dkimber1179"
PASSWORD = "d0cz3n0!2025"

message = "Let there be peace on earth!"

def send_peace_message(text):
    # Create MQTT client
    client = mqtt.Client(protocol=mqtt.MQTTv5,
                         callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    if USER and PASSWORD:
        client.username_pw_set(USER, PASSWORD)

    # Connect to broker
    client.connect(BROKER, PORT, 60)

    # Publish message
    # create timestamp string in iso format
    timestamp = datetime.datetime.now().isoformat()
    obj = {"type": "rtweb_post",
           "post": {
                "text": text,
                "createdAt": timestamp
            }
        }
    print("sending", obj)
    rc = client.publish(TOPIC, json.dumps(obj))
    print("rc:", rc)
    # Disconnect
    client.disconnect()

if __name__ == "__main__":
    send_peace_message(message)

