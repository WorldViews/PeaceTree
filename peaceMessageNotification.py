import paho.mqtt.client as mqtt
import time, json, random, datetime

# MQTT broker details
BROKER = "takeoneworld.com"
PORT = 1883
TOPIC = "peacetreebsky"
USER = "dkimber1179"
PASSWORD = "d0cz3n0!2025"

# List of 50 inspiring peace messages of one or two sentences each
#
PEACE_MESSAGES = [
    "Peace begins with a smile.",
    "Let us cultivate a peaceful world together.",
    "In the midst of chaos, there is always a place of peace.",
    "Peace is not the absence of conflict, but the presence of love.",
    "Every act of kindness brings us closer to peace.",
    "May peace be your guide in every step you take.",
    "Together, we can create a world filled with peace.",
    "Peace is the bridge between all people.",
    "Let your heart be filled with peace and your mind with love.",
    "In the garden of peace, we all can bloom.",
    "Peace is the light that guides us through the darkness.",
    "With each breath, let go of fear and embrace peace.",
    "Peace is a journey, not a destination.",
    "Let us be the change we wish to see in the world.",
    "In the silence of the heart, we find true peace.",
    "Peace is the melody of the soul.",
    "Together, we can weave a tapestry of peace.",
    "Let us walk the path of peace hand in hand.",
    "In the embrace of nature, we find peace.",
    "Peace is the greatest gift we can give to each other.",
    "Let us build bridges of understanding and compassion.",
    "In the face of adversity, choose peace.",
    "Peace is the language of the heart.",
    "Let us sow the seeds of peace in every interaction.",
    "In the stillness of the mind, we find peace.",
    "Peace is the foundation of a just society.",
    "Let us celebrate our differences and find common ground.",
    "In the warmth of community, we find peace.",
    "Peace is the heartbeat of humanity.",
    "Let us listen to the whispers of peace within us.",
    "In the dance of life, let peace lead the way.",
    "Peace is the compass that guides us home.",
    "Let us be the voice of peace in a noisy world.",
    "In the tapestry of life, peace is the thread that binds us.",
    "Peace is the gift we give to ourselves and others.",
    "Let us create a symphony of peace together.",
    "In the embrace of love, we find peace.",
    "Peace is the light that shines in the darkness.",
    "Let us be the architects of a peaceful future.",
    "In the journey of life, let peace be our companion.",
    "Peace is the essence of our shared humanity.",
    "Let us rise above division and embrace unity.",
    "In the heart of every conflict, there is a path to peace.",
    "Peace is the treasure we seek in our hearts.",
    "Let us be the stewards of peace in our communities.",
    "In the flow of life, let peace be our guide.",
    "Peace is the song that echoes in our souls.",
    "Let us paint the world with the colors of peace.",
    "In the stillness of the moment, we find peace.",
    "Peace is the promise of a better tomorrow.",
    "Let us nurture the seeds of peace in our hearts.",
    "In the embrace of forgiveness, we find peace.",
    "Peace is the journey we take together.",
    "Let us be the bearers of peace in a troubled world.",
    "In the light of understanding, we find peace.",
    "Peace is the foundation upon which we build our dreams.",
    "Let us walk the path of peace with courage and grace.",
    "In the heart of every person, there is a longing for peace.",
    "Peace is the gift we give to the world."
]

# choose a random peace message from the list, with random seed
# so that if we run script again it will get different messages
message = random.choice(PEACE_MESSAGES)

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
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    obj = {"type": "rtweb_post",
           "post": {
                "text": text,
                "createdAt": timestamp,
                "author": {
                    "displayName": "PeaceBot",
                    "handle": "peacebot"
                },
            }
        }
    
    print("sending", obj)
    rc = client.publish(TOPIC, json.dumps(obj))
    print("rc:", rc)
    # Disconnect
    client.disconnect()

if __name__ == "__main__":
    send_peace_message(message)

