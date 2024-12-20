import json
import websocket

# Replace these with your actual API credentials
BLUESKY_API_URL = "wss://firehose.bluesky.api"  # Update to the actual Firehose endpoint
BLUESKY_API_URL = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
BLUESKY_API_TOKEN = "your_api_token_here"

def on_message(ws, message):
    """Callback function to handle incoming messages."""
    try:
        data = json.loads(message)
        #print("Received message:", data)
        """
        if "content" in data and "#peace" in data["content"]:
            print(f"Message containing #peace: {data['content']}")
        """
        if "commit" not in data:
            return
        commit = data["commit"]
        if "record" not in commit:
            return
        record = commit["record"]
        if "text" not in record:
            return
        text = record["text"]
        # if text doesn't contain #peace, return
        if "#peace" not in text:
            return
        print(f"text: {text}")

    except json.JSONDecodeError:
        print("Failed to decode message:", message)

def on_error(ws, error):
    """Callback function to handle errors."""
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    """Callback function when the connection is closed."""
    print("Connection closed:", close_msg)

def on_open(ws):
    """Callback function when the connection is opened."""
    print("Connection established. Listening for messages...")

def main():
    # Setup WebSocket
    print("Connecting to BlueSky Firehose...")
    print(f"API URL: {BLUESKY_API_URL}")
    ws = websocket.WebSocketApp(
        BLUESKY_API_URL,
        #header={"Authorization": f"Bearer {BLUESKY_API_TOKEN}"},
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.on_open = on_open
    
    # Run WebSocket
    ws.run_forever()

if __name__ == "__main__":
    main()
