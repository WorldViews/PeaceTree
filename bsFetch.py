#!/usr/bin/env python3
"""
Bluesky Posts Scraper - Retrieve posts with #peace or #peacetree hashtags
from the last two months and save to JSONL format.
"""

import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Set, List, Dict, Any
import aiohttp
import time
import os
from pathlib import Path

# Install required packages:
# pip install atproto aiohttp

from atproto import Client, models


class BlueskyHashtagScraper:
    def __init__(self, username: str = None, password: str = None):
        """
        Initialize the Bluesky scraper.
        
        Args:
            username: Bluesky username (handle or email)
            password: Bluesky password or app password
        """
        self.client = Client()
        self.username = username
        self.password = password
        self.target_hashtags = {"peace", "peacetree"}
        self.posts_collected = set()  # To avoid duplicates
        
        # Calculate date range (last 2 months)
        self.end_date = datetime.now(timezone.utc)
        self.start_date = self.end_date - timedelta(days=60)
        
        print(f"Searching for posts from {self.start_date.date()} to {self.end_date.date()}")
        print(f"Target hashtags: {', '.join(f'#{tag}' for tag in self.target_hashtags)}")
    
    def authenticate(self):
        """Authenticate with Bluesky if credentials provided."""
        if self.username and self.password:
            try:
                self.client.login(self.username, self.password)
                print("✓ Successfully authenticated with Bluesky")
                return True
            except Exception as e:
                print(f"⚠ Authentication failed: {e}")
                print("Continuing without authentication (may have limited access)")
                return False
        else:
            print("No credentials provided, using unauthenticated access")
            return False
    
    def extract_hashtags(self, text: str) -> Set[str]:
        """Extract hashtags from post text."""
        if not text:
            return set()
        
        hashtags = set()
        words = text.split()
        for word in words:
            if word.startswith('#'):
                # Clean the hashtag (remove punctuation, convert to lowercase)
                hashtag = word[1:].lower().strip('.,!?;:"()[]{}')
                if hashtag:
                    hashtags.add(hashtag)
        return hashtags
    
    def is_within_date_range(self, created_at: str) -> bool:
        """Check if post creation date is within our target range."""
        try:
            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            return self.start_date <= post_date <= self.end_date
        except Exception as e:
            print(f"Error parsing date {created_at}: {e}")
            return False
    
    def has_target_hashtags(self, text: str, facets: List = None) -> bool:
        """Check if post contains target hashtags."""
        # Check in post text
        text_hashtags = self.extract_hashtags(text or "")
        if text_hashtags.intersection(self.target_hashtags):
            return True
        
        # Also check in facets (structured data for mentions, links, hashtags)
        if facets:
            for facet in facets:
                if hasattr(facet, 'features'):
                    for feature in facet.features:
                        if hasattr(feature, 'tag'):
                            tag = feature.tag.lower()
                            if tag in self.target_hashtags:
                                return True
        return False
    
    def serialize_object(self, obj) -> Any:
        """Convert Bluesky objects to JSON-serializable format."""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self.serialize_object(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self.serialize_object(v) for k, v in obj.items()}
        elif hasattr(obj, '__dict__'):
            # Convert object to dict, excluding private attributes
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    result[key] = self.serialize_object(value)
            return result
        else:
            # For other types, try to convert to string
            return str(obj)
    
    def format_post_data(self, post, author) -> Dict[str, Any]:
        """Format post data for JSON output."""
        return {
            'uri': str(post.uri) if post.uri else None,
            'cid': str(post.cid) if post.cid else None,
            'author': {
                'did': str(author.did) if author.did else None,
                'handle': str(author.handle) if author.handle else None,
                'display_name': str(getattr(author, 'display_name', '') or ''),
                'avatar': str(getattr(author, 'avatar', '') or ''),
                'description': str(getattr(author, 'description', '') or '')
            },
            'record': {
                'text': str(post.record.text) if post.record.text else '',
                'created_at': str(post.record.created_at) if post.record.created_at else None,
                'reply': self.serialize_object(getattr(post.record, 'reply', None)),
                'embed': self.serialize_object(getattr(post.record, 'embed', None)),
                'facets': self.serialize_object(getattr(post.record, 'facets', None))
            },
            'metrics': {
                'reply_count': int(getattr(post, 'reply_count', 0) or 0),
                'repost_count': int(getattr(post, 'repost_count', 0) or 0),
                'like_count': int(getattr(post, 'like_count', 0) or 0),
                'quote_count': int(getattr(post, 'quote_count', 0) or 0)
            },
            'scraped_at': datetime.now(timezone.utc).isoformat(),
            'hashtags_found': list(self.extract_hashtags(post.record.text))
        }
    
    async def search_posts_by_hashtag(self, hashtag: str, limit: int = 100) -> List[Dict]:
        """Search for posts containing a specific hashtag."""
        posts_found = []
        cursor = None
        
        print(f"Searching for #{hashtag}...")
        
        try:
            while len(posts_found) < limit:
                # Use the search API
                response = self.client.app.bsky.feed.search_posts(
                    params={
                        'q': f'#{hashtag}',
                        'limit': min(25, limit - len(posts_found)),
                        'cursor': cursor
                    }
                )
                
                if not response.posts:
                    print(f"No more posts found for #{hashtag}")
                    break
                
                for post in response.posts:
                    # Check if post is within date range
                    if not self.is_within_date_range(post.record.created_at):
                        continue
                    
                    # Check if post contains target hashtags
                    if not self.has_target_hashtags(post.record.text, 
                                                 getattr(post.record, 'facets', None)):
                        continue
                    
                    # Avoid duplicates
                    if post.uri in self.posts_collected:
                        continue
                    
                    self.posts_collected.add(post.uri)
                    formatted_post = self.format_post_data(post, post.author)
                    posts_found.append(formatted_post)
                    
                    print(f"Found post by @{post.author.handle}: {post.record.text[:100]}...")
                
                # Update cursor for pagination
                cursor = getattr(response, 'cursor', None)
                if not cursor:
                    break
                
                # Rate limiting
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"Error searching for #{hashtag}: {e}")
        
        return posts_found
    
    async def scrape_posts(self, output_file: str = "bluesky_peace_posts.jsonl", 
                          max_posts_per_hashtag: int = 500):
        """Main method to scrape posts and save to file."""
        
        # Authenticate if credentials provided
        self.authenticate()
        
        all_posts = []
        
        # Search for each target hashtag
        for hashtag in self.target_hashtags:
            posts = await self.search_posts_by_hashtag(hashtag, max_posts_per_hashtag)
            all_posts.extend(posts)
            
            print(f"Found {len(posts)} posts for #{hashtag}")
            await asyncio.sleep(2)  # Rate limiting between hashtags
        
        # Remove duplicates based on URI
        unique_posts = {}
        for post in all_posts:
            unique_posts[post['uri']] = post
        
        final_posts = list(unique_posts.values())
        
        # Sort by creation date (newest first)
        final_posts.sort(key=lambda x: x['record']['created_at'], reverse=True)
        
        # Save to JSONL file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            for post in final_posts:
                try:
                    json_line = json.dumps(post, ensure_ascii=False, default=str)
                    f.write(json_line + '\n')
                except Exception as e:
                    print(f"Warning: Failed to serialize post {post.get('uri', 'unknown')}: {e}")
                    # Try with more aggressive serialization
                    try:
                        simplified_post = self.serialize_object(post)
                        json_line = json.dumps(simplified_post, ensure_ascii=False, default=str)
                        f.write(json_line + '\n')
                    except Exception as e2:
                        print(f"Error: Could not serialize post at all: {e2}")
                        continue
        
        print(f"\n✓ Scraped {len(final_posts)} unique posts")
        print(f"✓ Saved to {output_path.absolute()}")
        
        # Print summary statistics
        hashtag_counts = {}
        for post in final_posts:
            for hashtag in post['hashtags_found']:
                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
        
        print("\nHashtag distribution:")
        for hashtag, count in sorted(hashtag_counts.items()):
            print(f"  #{hashtag}: {count} posts")
        
        return final_posts


async def main():
    """Main function to run the scraper."""
    
    # You can set credentials here or via environment variables
    username = os.getenv('BLUESKY_HANDLE')  # or your handle/email
    password = os.getenv('BLUESKY_PASSWORD')  # or app password
    
    # Initialize scraper
    scraper = BlueskyHashtagScraper(username, password)
    
    # Run the scraper
    try:
        posts = await scraper.scrape_posts(
            output_file="bluesky_peace_posts.jsonl",
            max_posts_per_hashtag=1000
        )
        
        print(f"\nScraping completed successfully!")
        print(f"Total posts collected: {len(posts)}")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Bluesky Peace Posts Scraper")
    print("=" * 30)
    
    # Check if required packages are installed
    try:
        import atproto
        print("✓ atproto package found")
    except ImportError:
        print("❌ Please install required packages:")
        print("   pip install atproto aiohttp")
        exit(1)
    
    # Run the scraper
    asyncio.run(main())