import paho.mqtt.client as mqtt
import os, time

class PeaceTreeMQTTClient:
    def __init__(self, broker_url, broker_port, topic, username=None, password=None):
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.topic = topic
        transport = "tcp"  # Default transport
        print("*******  Getting MQTT Client - transport:", transport, broker_url,
              broker_port, topic, username, password )
        self.client = mqtt.Client(protocol=mqtt.MQTTv5,
                                  callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                                  transport = transport)
        if username and password:
            print("Authenticating User:", username)
            self.client.username_pw_set(username, password)
        else:
            print("No authentication being used.")
        # setup handler for connect and disconnect
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.reconnect_delay_set(min_delay=1, max_delay=120)
        self.client.connect(self.broker_url, self.broker_port, 60)
        print("connected to broker.  starting loop")
        self.client.loop_start()
        time.sleep(1)  # Allow time for connection to establish

    def on_connect(self, client, userdata, flags, rc, properties):
        print("Connected with result code:", rc)

    def on_disconnect(self, client, userdata, disconnect_flags, rc, properties):
        print("Disconnected with result code:", rc)

    def send_message(self, message: str):
        print(f"Sending message: {message} to topic: {self.topic}")
        result = self.client.publish(self.topic, message, retain=True)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def disconnect(self):
        print("Disconnecting from MQTT broker.")
        self.client.loop_stop()
        self.client.disconnect()

    def set_post_rate(self, rate):
        f = rate/10.0
        n = math.floor(f)
        if n < 0:
            n = 0
        if n > 5:
            n = 5
        ps = 21 + n
        print("set_post_rate:", rate, f, n, ps)
        self.send_message(f'{{"ps": {ps}}}')

# write functon test1 that gets username and password from BLUESKY_HANDLE
# and BLUESKY_PASSWORD environment variables.   It sends messages to set
# presets '{"ps": 21}', '{"ps": 22}', '{"ps": 23}'
# spaced apart by 5 seconds.
import math
def test1():
    #username = os.getenv("MQTT_USERNAME")
    #password = os.getenv("MQTT_PASSWORD")
    username = "dkimber1179"
    password = "d0cz3n0!2025"
    topic = "peacetreedev/api"
    client = PeaceTreeMQTTClient("takeoneworld.com", 1883, topic,
                                 username=username, password=password)
    for i in range(21, 27):
        client.send_message(f'{{"ps": {i}}}')
        time.sleep(5)
    client.disconnect()

if __name__ == "__main__":
    test1()

