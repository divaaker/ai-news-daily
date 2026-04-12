#!/usr/bin/env python3
"""
AI News Daily Automation Pipeline
Fetches AI/tech news → Generates content via Claude → Posts to Notion
"""

import os
import json
import requests
from datetime import datetime
from anthropic import Anthropic
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Initialize clients
newsapi_key = os.getenv("NEWSAPI_KEY")
claude_api_key = os.getenv("CLAUDE_API_KEY")
notion_token = os.getenv("NOTION_TOKEN")
notion_db_id = os.getenv("NOTION_DB_ID")  # 91fd1aa2-22b3-492b-b517-e8d5dcd11281

client = Anthropic()

# Best AI/Tech news sources
NEWS_SOURCES = [
    "techcrunch",
    "the-verge",
    "hacker-news",
    "ars-technica",
    "wired"
]

class AINewsPipeline:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.output_dir = f"output/{self.timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def fetch_news(self):
        """Fetch top AI/tech story from NewsAPI"""
        print("📰 Fetching news from NewsAPI...")
        
        query = "artificial intelligence OR AI OR machine learning OR LLM OR ChatGPT OR Claude"
        sources = ",".join(NEWS_SOURCES)
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "sources": sources,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 5,
            "apiKey": newsapi_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            
            if not articles:
                print("⚠️  No articles found. Retrying with broader query...")
                params["q"] = "AI OR technology"
                response = requests.get(url, params=params, timeout=10)
                articles = response.json().get("articles", [])
            
            # Return top article
            if articles:
                story = articles[0]
                print(f"✅ Found: {story['title']}")
                return {
                    "title": story.get("title", ""),
                    "description": story.get("description", ""),
                    "source": story.get("source", {}).get("name", ""),
                    "url": story.get("url", ""),
                    "image": story.get("urlToImage", ""),
                    "content": story.get("content", "")
                }
            else:
                print("❌ No articles found")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching news: {e}")
            return None
    
    def generate_reddit_post(self, story):
        """Generate 200-300 word Reddit post via Claude"""
        print("✍️  Generating Reddit post...")
        
        prompt = f"""
You are a tech content creator for Reddit's AI community. 
Create a SHORT, PUNCHY Reddit post (200-300 words exactly) about this news:

Title: {story['title']}
Description: {story['description']}
Source: {story['source']}

Requirements:
- Start with an engaging hook (1 sentence)
- Explain the news in simple terms
- Add 2-3 key takeaways
- End with a thought-provoking question for engagement
- Use casual, conversational tone
- Include relevant emoji sparingly
- NO hashtags
- Make it sound like a real Redditor wrote it

Generate ONLY the post content, nothing else.
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-20250805",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            post = message.content[0].text.strip()
            print(f"✅ Reddit post generated ({len(post.split())} words)")
            return post
        except Exception as e:
            print(f"❌ Error generating Reddit post: {e}")
            return None
    
    def generate_instagram_caption(self, story):
        """Generate Instagram caption with hashtags"""
        print("📸 Generating Instagram caption...")
        
        prompt = f"""
Create a SHORT Instagram caption (50-80 words) for this AI/tech news:

Title: {story['title']}
Description: {story['description']}

Requirements:
- Hook them in first line
- 1-2 sentences max
- Add relevant emojis
- End with 8-10 hashtags (#AI #MachineLearning #Tech #ArtificialIntelligence #Innovation #FutureOfAI #TechNews #AINews etc.)
- Make it shareable and engaging

Generate ONLY the caption with hashtags.
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-20250805",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            caption = message.content[0].text.strip()
            print(f"✅ Instagram caption generated")
            return caption
        except Exception as e:
            print(f"❌ Error generating Instagram caption: {e}")
            return None
    
    def generate_image(self, story):
        """Generate PNG image with news headline"""
        print("🎨 Generating PNG image...")
        
        try:
            # Create image with gradient-like background
            width, height = 1080, 1350  # Instagram post size
            
            # Create image with dark background
            img = Image.new('RGB', (width, height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # Try to use a nice font, fallback to default
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                source_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            except:
                title_font = text_font = source_font = ImageFont.load_default()
            
            # Add colored top bar
            draw.rectangle([(0, 0), (width, 150)], fill='#ff6b35')  # Orange
            
            # Title
            title = story['title']
            wrapped_title = textwrap.fill(title, width=25)
            draw.text((40, 200), wrapped_title, fill='#ffffff', font=title_font)
            
            # Source and date
            source_text = f"Source: {story['source']} | {self.timestamp}"
            draw.text((40, 700), source_text, fill='#888888', font=source_font)
            
            # AI quote at bottom
            ai_quote = "🤖 AI is reshaping the future, one innovation at a time."
            draw.text((40, 1200), ai_quote, fill='#ff6b35', font=text_font)
            
            # Save image
            image_path = f"{self.output_dir}/ai_news_image.png"
            img.save(image_path)
            print(f"✅ Image saved: {image_path}")
            return image_path
            
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            return None
    
    def write_to_notion(self, story, reddit_post, instagram_caption):
        """Write to Notion database"""
        print("📝 Writing to Notion...")
        
        try:
            headers = {
                "Authorization": f"Bearer {notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            data = {
                "parent": {"database_id": notion_db_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": story['title'][:100]}}]
                    },
                    "News_Source": {
                        "rich_text": [{"text": {"content": story['source']}}]
                    },
                    "Reddit_Post": {
                        "rich_text": [{"text": {"content": reddit_post}}]
                    },
                    "Instagram_Caption": {
                        "rich_text": [{"text": {"content": instagram_caption}}]
                    },
                    "Original_URL": {
                        "url": story['url']
                    },
                    "Date_Generated": {
                        "date": {"start": self.timestamp}
                    },
                    "Status": {
                        "select": {"name": "Ready to Post"}
                    }
                }
            }
            
            response = requests.post(
                f"https://api.notion.com/v1/pages",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Written to Notion successfully")
                return True
            else:
                print(f"⚠️  Notion write returned {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error writing to Notion: {e}")
            return False
    
    def save_local_files(self, story, reddit_post, instagram_caption):
        """Save all content to local files for easy access"""
        print("💾 Saving local files...")
        
        try:
            # Reddit post
            with open(f"{self.output_dir}/reddit_post.txt", "w") as f:
                f.write(f"Title: {story['title']}\n")
                f.write(f"Source: {story['source']}\n")
                f.write(f"URL: {story['url']}\n\n")
                f.write("---REDDIT POST---\n\n")
                f.write(reddit_post)
            
            # Instagram caption
            with open(f"{self.output_dir}/instagram_caption.txt", "w") as f:
                f.write(instagram_caption)
            
            # Summary JSON
            summary = {
                "date": self.timestamp,
                "title": story['title'],
                "source": story['source'],
                "url": story['url'],
                "reddit_words": len(reddit_post.split()),
                "instagram_chars": len(instagram_caption)
            }
            
            with open(f"{self.output_dir}/summary.json", "w") as f:
                json.dump(summary, f, indent=2)
            
            print(f"✅ Files saved to {self.output_dir}")
            
        except Exception as e:
            print(f"❌ Error saving local files: {e}")
    
    def run(self):
        """Execute the full pipeline"""
        print("\n🚀 Starting AI News Pipeline...")
        print("=" * 50)
        
        # Step 1: Fetch news
        story = self.fetch_news()
        if not story:
            print("❌ Pipeline failed: Could not fetch news")
            return False
        
        # Step 2: Generate content
        reddit_post = self.generate_reddit_post(story)
        if not reddit_post:
            print("❌ Pipeline failed: Could not generate Reddit post")
            return False
        
        instagram_caption = self.generate_instagram_caption(story)
        if not instagram_caption:
            print("❌ Pipeline failed: Could not generate Instagram caption")
            return False
        
        # Step 3: Generate image
        image_path = self.generate_image(story)
        
        # Step 4: Write to Notion
        self.write_to_notion(story, reddit_post, instagram_caption)
        
        # Step 5: Save local files
        self.save_local_files(story, reddit_post, instagram_caption)
        
        print("=" * 50)
        print("✅ Pipeline completed successfully!")
        print(f"📂 Output location: {self.output_dir}")
        return True


if __name__ == "__main__":
    pipeline = AINewsPipeline()
    pipeline.run()
