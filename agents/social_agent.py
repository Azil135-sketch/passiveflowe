"""
PassiveFlow - Social Agent
===========================
Posts affiliate content to Telegram channel using your existing bot.
Asil already has Telegram bot infrastructure from deal-bot — this plugs in directly.

Also supports posting teaser threads for new blog posts.
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

from agents.base_agent import BaseAgent


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class SocialAgent(BaseAgent):
    """Posts content and deals to Telegram channel."""

    def __init__(self):
        super().__init__("social_agent")
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
        self.site_url = os.environ.get("SITE_URL", "https://yourdomain.github.io")

    def _send_message(self, text: str, parse_mode: str = "HTML",
                      disable_preview: bool = False) -> dict:
        """Send a message to the Telegram channel."""
        if not self.bot_token or not self.channel_id:
            self.logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not set. Skipping.")
            return {"ok": False, "description": "Missing credentials"}

        url = TELEGRAM_API.format(token=self.bot_token, method="sendMessage")
        payload = {
            "chat_id": self.channel_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = resp.json()
            if data.get("ok"):
                self.logger.info(f"Telegram message sent (message_id: {data['result']['message_id']})")
            else:
                self.logger.error(f"Telegram error: {data.get('description')}")
            return data
        except requests.RequestException as e:
            self.logger.error(f"Telegram request failed: {e}")
            return {"ok": False, "error": str(e)}

    def _generate_post_teaser(self, post: dict) -> str:
        """Use Claude to generate a punchy Telegram teaser for a blog post."""
        prompt = f"""Write a short, engaging Telegram post (max 250 chars) that teases this blog article.
Make it feel useful and natural, not spammy. Add 2-3 relevant emojis.

Article title: {post['title']}
Keyword: {post.get('keyword', '')}
URL: {self.site_url}/posts/{post['slug']}

Format: One short hook sentence. Then the link. End with a relevant emoji.
Return ONLY the Telegram post text."""

        teaser = self.call_claude(
            "You write punchy, high-converting Telegram post teasers.",
            prompt,
            max_tokens=150
        )
        return teaser

    def _generate_affiliate_deal(self, affiliate_id: str) -> str:
        """Generate a deal post for a specific affiliate program."""
        with open("config/affiliates.json") as f:
            data = json.load(f)
        programs = {p["id"]: p for p in data["programs"]}

        if affiliate_id not in programs:
            return ""

        prog = programs[affiliate_id]
        link_env = f"AFFILIATE_{affiliate_id.upper()}_URL"
        link = os.environ.get(link_env, prog.get("signup_url", "#"))

        prompt = f"""Write a short Telegram deal post (max 280 chars) for this affiliate offer.
Be honest and helpful. Frame it as a useful resource, not an ad.

Product: {prog['name']}
Category: {prog['category']}
Commission context (DON'T mention this to reader): {prog['commission']}
What it does: {prog.get('notes', '')}
Link: {link}

Add 2-3 emojis. Return ONLY the Telegram post text."""

        post_text = self.call_claude(
            "You write authentic, helpful Telegram posts about useful tools and services.",
            prompt,
            max_tokens=150
        )
        return post_text

    def post_new_articles(self, posts: list[dict]):
        """Post teasers for all newly generated articles."""
        posted = 0
        for post in posts:
            try:
                teaser = self._generate_post_teaser(post)
                result = self._send_message(teaser)
                if result.get("ok"):
                    posted += 1
                time.sleep(3)  # Rate limit: 1 msg per 3 seconds
            except Exception as e:
                self.logger.error(f"Failed to post teaser for {post['title']}: {e}")

        self.logger.info(f"Posted {posted}/{len(posts)} article teasers to Telegram")
        return posted

    def post_weekly_deal(self):
        """Post one affiliate deal per week (rotates through programs)."""
        # Determine which affiliate to feature this week (rotate by week number)
        week_num = datetime.now().isocalendar()[1]
        with open("config/affiliates.json") as f:
            programs = json.load(f)["programs"]

        featured = programs[week_num % len(programs)]
        self.logger.info(f"Weekly deal: {featured['name']}")

        deal_text = self._generate_affiliate_deal(featured["id"])
        if deal_text:
            result = self._send_message(deal_text)
            if result.get("ok"):
                self.logger.info(f"Weekly deal posted: {featured['name']}")
                return True
        return False

    def post_custom(self, text: str):
        """Post a custom message to the channel."""
        return self._send_message(text)

    def run(self, posts: list[dict] = None):
        """Full social agent run."""
        self.logger.info("SocialAgent starting...")

        if not posts:
            results_file = Path("logs/content_agent_results.json")
            if results_file.exists():
                with open(results_file) as f:
                    posts = json.load(f)
            else:
                posts = []

        # Post article teasers (only if we have posts)
        if posts:
            posted = self.post_new_articles(posts)
        else:
            posted = 0
            # Still send a welcome/status message so you know the bot works
            self.logger.info("No posts yet — sending channel intro message")
            site_url = self.site_url
            channel = self.channel_id
            intro = (
                f"👋 Welcome to {channel}!\n\n"
                f"This channel shares weekly deals, earning tips, and free resources for students in India.\n\n"
                f"New posts drop every Monday. Stay tuned 📚"
            )
            self._send_message(intro)

        # Always post weekly affiliate deal
        time.sleep(3)
        self.post_weekly_deal()

        result = {"posts_teased": posted, "weekly_deal": True}
        self.log_result(result)
        self.save_results()
        self.logger.info("SocialAgent done.")
        return result
