import paho.mqtt.client as mqtt
import sys, time, json, random, datetime

# MQTT broker details
BROKER = "takeoneworld.com"
PORT = 1883
TOPIC = "peacetreebsky"
USER = "dkimber1179"
PASSWORD = "d0cz3n0!2025"

def send_instagram_estimate(rate):
    # Create MQTT client
    client = mqtt.Client(protocol=mqtt.MQTTv5,
                         callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    if USER and PASSWORD:
        client.username_pw_set(USER, PASSWORD)

    # Connect to broker
    client.connect(BROKER, PORT, 60)

    text = f"Instagram Peace Post Estimate: {rate} posts per minute."
    # Publish message
    # create timestamp string in iso format
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # uri is a bit bogus, but is unique
    uri = "igscraper:peace_post_estimate_" + str(time.time())
    obj = {"type": "instagram_peace_post_estimate",
           "post": {
                "uri": uri,
                "text": text,
                "rate": rate,
                "createdAt": timestamp,
                "author": {
                    "displayName": "Instagram Bot",
                    "handle": "instagram_bot",
                },
            }
        }
    
    print("sending", obj)
    rc = client.publish(TOPIC, json.dumps(obj))
    print("rc:", rc)
    # Disconnect
    client.disconnect()

if __name__ == "__main__":
    rate = random.randint(1, 10)  # Example rate
    if sys.argv and len(sys.argv) > 1:
        rate = float(sys.argv[1])
    send_instagram_estimate(rate)


