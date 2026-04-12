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
claude_api_key = os.getenv("CLAUDE_API_KEY")
notion_token = os.getenv("NOTION_TOKEN")
notion_db_id = os.getenv("NOTION_DB_ID")

client = Anthropic(api_key=claude_api_key)

# HackerNews API (free, no authentication needed)
HACKERNEWS_API = "https://hacker-news.firebaseio.com/v0"
AI_KEYWORDS = ["AI", "machine learning", "LLM", "ChatGPT", "Claude", "neural", "algorithm", "data science", "GPT"]

class AINewsPipeline:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.output_dir = f"output/{self.timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def clean_text(self, text):
        """Remove markdown formatting for Notion"""
        # Remove ** bold markers
        text = text.replace("**", "")
        # Remove ### headers
        text = text.replace("#
