import json
import paho.mqtt.client as mqtt

BROKER = "takeoneworld.com"
TRANSPORT = "TCP"
PORT = 1883
TOPICS = ["peacetreedev/#", "peacetreebsky"]
USER = "dkimber1179"
PASSWORD = "d0cz3n0!2025"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    for topic in TOPICS:
        print("Subscribing to", topic)
        client.subscribe(topic)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received on {msg.topic}: {data}")
    except json.JSONDecodeError:
        print(f"Received invalid JSON: {msg.payload.decode()}")

print("Getting client - Transport:", TRANSPORT)
client = mqtt.Client(transport=TRANSPORT)  # Use WebSockets

client.on_connect = on_connect
client.on_message = on_message
print(f"User: {USER} Host: {BROKER} Port: {PORT} Topic: {TOPICS}")
if USER:
    client.username_pw_set(USER, PASSWORD)
client.connect(BROKER, PORT, 60)
client.loop_forever()
