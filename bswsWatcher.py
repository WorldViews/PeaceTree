#!/usr/bin/env python3
"""
Bluesky Hashtag Monitor
Continuously polls Bluesky for posts containing #peace or #peacetree hashtags
"""

import time
import json
import requests
import os
import getpass
from datetime import datetime, timezone
from typing import Set, Dict, Tuple, Any, Optional
import logging
import paho.mqtt.client as mqtt
from ExpDecayRateEstimator import ExpDecayRateEstimator
from PeaceTreeAPI import PeaceTreeMQTTClient

BROKER = "takeoneworld.com"
TRANSPORT = "TCP"
PORT = 1883
API_TOPIC = "peacetreedev/api"  # topic being watched by WLED server
BLUESKY_TOPIC = "peacetreebsky" # topic posting bluesky info
USER = "dkimber1179"
PASSWORD = "d0cz3n0!2025"
DATA_LOG_FILE = "DATA_LOG.json"

wsclient = None
rateEst = ExpDecayRateEstimator(1/500.0)  # Example alpha value for decay rate
peaceTreeClient = None
recentPosts = []
RECENT_POSTS_FILE = "RECENT_POSTS.json"
MAX_NUM_RECENT_POSTS = 20

def startPeaceTreeClient():
    global peaceTreeClient
    peaceTreeClient = PeaceTreeMQTTClient(BROKER, PORT, API_TOPIC,
                                           username=USER, password=PASSWORD)
    
def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code:", rc)
    # Subscribe to the topic
    #client.subscribe(API_TOPIC)
    #print(f"Subscribed to topic: {API_TOPIC}")

def on_disconnect(client, userdata, disconnect_flags, rc, properties):
    print("Disconnected with result code:", rc)
    # do we need to initiate a new connect?

def startWSClient():
    global wsclient
    print("*******  Getting MQTT Client - transport:", TRANSPORT)
    wsclient = mqtt.Client(transport=TRANSPORT,
                           protocol=mqtt.MQTTv5,
                           callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    if USER:
        print("Authenticating User:", USER)
        wsclient.username_pw_set(USER, PASSWORD)
    else:
        print("No authentication being used.")
    # setup handler for connect and disconnect
    wsclient.on_connect = on_connect
    wsclient.on_disconnect = on_disconnect
    wsclient.reconnect_delay_set(min_delay=1, max_delay=120)  # 1-120 second delays
    wsclient.connect(BROKER, PORT, 60)
    #wsclient.loop_start()
    #time.sleep(1)  # Allow time for connection to establish

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def post_peace_message():
    print("********** post_peace_message ******************")
    url = "https://www.reachandteach.com/peacetreelive.php"
    # form-encoded payload
    payload = {
        "message": "Peace in the Blue Sky"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        print("🕊️  Peace message posted successfully!")
    except requests.exceptions.RequestException as err:
        print(f"❌  Failed to post peace message: {err}")

# Bluesky monitoring class for scraping posts
class BlueskyMonitor:
    def __init__(self, poll_interval: int = 30):
        self.base_url = "https://bsky.social"
        self.api_url = f"{self.base_url}/xrpc"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BlueskyHashtagMonitor/1.0',
            'Accept': 'application/json'
        })
        
        # Authentication
        self.access_token = None
        self.refresh_token = None
        
        # Track seen posts to avoid duplicates
        self.seen_posts: Set[str] = set()
        self.last_post_time = None  # UTC of the last post

        # Polling configuration
        self.poll_interval = poll_interval
        self.hashtags = ['#peace', '#peacetree']
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests

        # Cursor for pagination
        self.cursor: Optional[str] = None
        
    def authenticate(self, handle: str, password: str) -> bool:
        """Authenticate with Bluesky using handle and password"""
        try:
            auth_data = {
                "identifier": handle,
                "password": password
            }
            
            response = self.session.post(
                f"{self.api_url}/com.atproto.server.createSession",
                json=auth_data,
                timeout=30
            )
            response.raise_for_status()
            
            auth_response = response.json()
            self.access_token = auth_response.get('accessJwt')
            self.refresh_token = auth_response.get('refreshJwt')
            logger.info(f"access_token: {self.access_token}")
            logger.info(f"refresh_token: {self.refresh_token}")
            if self.access_token:
                self.session.headers['Authorization'] = f'Bearer {self.access_token}'
                logger.info(f"Successfully authenticated as {handle}")
                return True
            else:
                logger.error("Authentication failed: No access token received")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """Refresh the authentication session"""
        if not self.refresh_token:
            logger.warning("refresh_session: no refresh_token")
            return False
            
        try:
            response = self.session.post(
                f"{self.api_url}/com.atproto.server.refreshSession",
                headers={'Authorization': f'Bearer {self.refresh_token}'},
                timeout=30
            )
            response.raise_for_status()
            
            auth_response = response.json()
            self.access_token = auth_response.get('accessJwt')
            self.refresh_token = auth_response.get('refreshJwt')
            
            if self.access_token:
                self.session.headers['Authorization'] = f'Bearer {self.access_token}'
                logger.info("Successfully refreshed session")
                return True
            else:
                logger.error("Session refresh failed: No access token received")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Session refresh failed: {e}")
            return False
    
    def rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def search_posts(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search for posts using the AT Protocol search endpoint"""
        self.rate_limit()
        
        params = {
            'q': query,
            'limit': limit
        }
        
        if self.cursor:
            params['cursor'] = self.cursor
            
        try:
            response = self.session.get(
                f"{self.api_url}/app.bsky.feed.searchPosts",
                params=params,
                timeout=30
            )
            
            # Handle 401 errors by attempting to refresh session
            if response.status_code == 401:
                logger.info("Received 401, attempting to refresh session...")
                if self.refresh_session():
                    # Retry the request with refreshed token
                    response = self.session.get(
                        f"{self.api_url}/app.bsky.feed.searchPosts",
                        params=params,
                        timeout=30
                    )
                else:
                    logger.error("Failed to refresh session")
                    return {}
            
            # Handle 400 errors by attempting to refresh session
            if response.status_code == 400:
                logger.info("Received 401, attempting to refresh session...")
                if self.refresh_session():
                    # Retry the request with refreshed token
                    response = self.session.get(
                        f"{self.api_url}/app.bsky.feed.searchPosts",
                        params=params,
                        timeout=30
                    )
                else:
                    logger.error("Failed to refresh session")
                    return {}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {}
    
    def extract_post_info(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant information from a post"""
        try:
            record = post.get('record', {})
            author = post.get('author', {})
            
            # Get post text
            text = record.get('text', '')
            
            # Check if post contains our target hashtags
            text_lower = text.lower()
            if not any(hashtag.lower() in text_lower for hashtag in self.hashtags):
                return None
                
            # Extract post info
            post_info = {
                'uri': post.get('uri', ''),
                'cid': post.get('cid', ''),
                'author': {
                    'handle': author.get('handle', ''),
                    'displayName': author.get('displayName', ''),
                },
                'text': text,
                'createdAt': record.get('createdAt', ''),
                'replyCount': post.get('replyCount', 0),
                'repostCount': post.get('repostCount', 0),
                'likeCount': post.get('likeCount', 0),
            }
            
            return post_info
            
        except Exception as e:
            logger.error(f"Error extracting post info: {e}")
            return None
    
    def format_post_output(self, post_info: Dict[str, Any]) -> str:
        """Format post information for display"""
        author = post_info['author']
        display_name = author['displayName'] or author['handle']
        
        # Parse and format timestamp
        try:
            created_at = datetime.fromisoformat(post_info['createdAt'].replace('Z', '+00:00'))
            formatted_time = created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = post_info['createdAt']
        
        # Create post URL (approximate)
        handle = author['handle']
        post_id = post_info['uri'].split('/')[-1] if post_info['uri'] else 'unknown'
        post_url = f"https://bsky.app/profile/{handle}/post/{post_id}"
        
        output = f"""
{'-'*60}
👤 {display_name} (@{author['handle']})
🕐 {formatted_time}
📝 {post_info['text']}
📊 ❤️ {post_info['likeCount']} | 🔄 {post_info['repostCount']} | 💬 {post_info['replyCount']}
🔗 {post_url}
{'-'*60}
"""
        return output
    
    def process_search_results(self, results: Dict[str, Any]) -> int:
        """Process search results and print new posts"""
        if not results or 'posts' not in results:
            return 0
        
        new_posts_count = 0
        posts = results['posts']
        
        # sort posts by timestamps determined from 'createdAt' fields
        # in ascending order
        posts.sort(key=lambda p: p['record']['createdAt'], reverse=False)

        for post in posts:
            post_info = self.extract_post_info(post)
            if not post_info:
                continue
            
            # Use URI as unique identifier
            post_id = post_info['uri']
            
            if post_id not in self.seen_posts:
                self.seen_posts.add(post_id)
                print("="*70)
                print(f"Total posts: {len(self.seen_posts)}")
                # get t as UTC float
                # post creation time
                pt = datetime.fromisoformat(post_info['createdAt'].replace('Z', '+00:00')).timestamp()
                ct = time.time()
                delay = ct - pt
                print(f"Delay: {delay} seconds")
                # print time elapsed since previous post
                if self.last_post_time:
                    elapsed = pt - self.last_post_time
                    # Print elapsed time in seconds
                    print(f"Time since previous post: {elapsed} seconds")
                self.last_post_time = pt
                bonus = 0
                if post_info['text'].find("peacedance") >= 0:
                    bonus = 8
                    post_peace_message()
                msg = {'post': post_info,
                       'pt': pt,
                       'ct': ct,
                       'delay': ct - pt}
                if rateEst:
                    print("Updating rate estimate", pt, 1+bonus)
                    rateEst.update(pt, 1+bonus)
                    msg['rate'] = rateEst.get_rate(pt)* 3600  # convert to events/hour
                    print(f"Rate estimate: {msg['rate']:.4f} events/hour")
                print(self.format_post_output(post_info))
                if DATA_LOG_FILE:
                    print("Logging post message")
                    f = open(DATA_LOG_FILE, "a")
                    f.write(json.dumps(msg) + "\n")
                    f.close()
                if recentPosts != None:
                    recentPosts.append(post_info)
                    if len(recentPosts) > MAX_NUM_RECENT_POSTS:
                        recentPosts.pop(0)
                    f = open(RECENT_POSTS_FILE, "w")
                    rpobj = {'posts':recentPosts}
                    if rateEst:
                        rpobj['rate'] = rateEst.get_rate(pt)* 3600  # convert to events/hour
                    f.write(json.dumps(rpobj) + "\n")
                    f.close()
                if wsclient:
                    rc = wsclient.publish(API_TOPIC, json.dumps(msg))
                    print(f"Published to {API_TOPIC}")
                new_posts_count += 1

        
        # Update cursor for next request
        self.cursor = results.get('cursor')
        
        return new_posts_count
    
    def cleanup_seen_posts(self, max_size: int = 10000):
        """Clean up seen_posts set to prevent memory issues"""
        if len(self.seen_posts) > max_size:
            # Keep only the most recent half
            posts_list = list(self.seen_posts)
            self.seen_posts = set(posts_list[-max_size//2:])
            logger.info(f"Cleaned up seen_posts cache, now tracking {len(self.seen_posts)} posts")
    

#    def get_credentials(self) -> tuple[str, str]:
    def get_credentials(self) -> Tuple[str, str]:
        """Get Bluesky credentials from environment variables or user input"""
        # Try environment variables first
        handle = os.getenv('BLUESKY_HANDLE')
        password = os.getenv('BLUESKY_PASSWORD')
        
        if handle and password:
            logger.info(f"Using credentials from environment variables for {handle}")
            return handle, password
        
        # Fall back to user input
        print("Bluesky credentials required for API access")
        handle = input("Enter your Bluesky handle (e.g., username.bsky.social): ").strip()
        password = getpass.getpass("Enter your Bluesky password: ").strip()
        return handle, password
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting Bluesky hashtag monitor...")
        
        # Get credentials and authenticate
        handle, password = self.get_credentials()
        if not self.authenticate(handle, password):
            logger.error("Authentication failed. Exiting.")
            return
        
        logger.info(f"Monitoring hashtags: {', '.join(self.hashtags)}")
        logger.info(f"Poll interval: {self.poll_interval} seconds")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                # Search for posts with our hashtags
                # We'll search for each hashtag separately to be more thorough
                total_new_posts = 0
                
                for hashtag in self.hashtags:
                    #logger.info(f"Searching for posts with {hashtag}...")
                    results = self.search_posts(hashtag)
                    
                    if results:
                        new_posts = self.process_search_results(results)
                        total_new_posts += new_posts
                        if new_posts:
                            logger.info(f"Found {new_posts} new posts for {hashtag}")
                    else:
                        logger.warning(f"No results for {hashtag}")
                    
                    # Small delay between hashtag searches
                    time.sleep(2)
                
                if total_new_posts:
                    logger.info(f"Total new posts this cycle: {total_new_posts}")
                
                # Reset error counter on successful cycle
                consecutive_errors = 0
                
                # Periodic cleanup
                self.cleanup_seen_posts()
                
                if wsclient:
                    ct = time.time()
                    msg = {"type": "heartbeat", "ct": ct}
                    if rateEst:
                        msg['rate'] = rateEst.get_rate(ct) * 3600
                        print(f"Heartbeat rate estimate: {msg['rate']:.4f} events/hour")
                    wsclient.publish(API_TOPIC, json.dumps(msg))
                    print(f"Published heartbeat to {API_TOPIC}")
                    if peaceTreeClient:
                        peaceTreeClient.set_post_rate(msg['rate'])
                # Wait before next poll
                logger.info(f"Waiting {self.poll_interval} seconds before next poll...")
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in main loop (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, shutting down...")
                    break
                
                # Exponential backoff on errors
                error_delay = min(20, 2 ** consecutive_errors)
                logger.info(f"Waiting {error_delay} seconds before retry...")
                time.sleep(error_delay)

def main():
    """Main function"""
    # Configuration
    poll_interval = 15  # Poll every 60 seconds
    
    print("Bluesky Hashtag Monitor")
    print("=" * 50)
    print("This script monitors Bluesky for posts with #peace or #peacetree hashtags.")
    print("You'll need to provide your Bluesky credentials for API access.")
    print()
    print("You can set environment variables to avoid entering credentials each time:")
    print("export BLUESKY_HANDLE=your_handle.bsky.social")
    print("export BLUESKY_PASSWORD=your_password")
    print()

    startWSClient()
    startPeaceTreeClient()

    # Create and run monitor
    monitor = BlueskyMonitor(poll_interval=poll_interval)
    monitor.run()

if __name__ == "__main__":
    main()