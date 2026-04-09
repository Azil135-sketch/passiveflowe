"""
PassiveFlow - Growth Agent
===========================
Autonomous channel growth without spamming.

Strategy:
1. Reddit — post genuinely helpful content to Indian subreddits,
   soft-mention Telegram channel at the end. High organic reach.
2. Pinterest — auto-create pins for every blog post. Pinterest
   is a search engine; pins drive traffic for years.
3. Blog CTA — inject Telegram join link into every post footer
   so SEO traffic converts to channel members.

Zero manual work. All autonomous.
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

from agents.base_agent import BaseAgent


# ── Subreddits to post in (genuine, relevant, Indian audience) ──
SUBREDDITS = [
    {"name": "india", "flair": None, "min_karma": 0},
    {"name": "IndiaInvestments", "flair": None, "min_karma": 0},
    {"name": "IndianStudents", "flair": None, "min_karma": 0},
    {"name": "Kerala", "flair": None, "min_karma": 0},
    {"name": "digitalnomad", "flair": None, "min_karma": 0},
    {"name": "povertyfinance", "flair": None, "min_karma": 0},
    {"name": "beermoney", "flair": None, "min_karma": 0},
]

# ── Reddit post templates ──────────────────────────────────────
REDDIT_SYSTEM = """You write helpful, genuine Reddit posts for Indian communities.
Posts are:
- Genuinely useful, not spammy
- Written in casual Indian English
- End with a SOFT mention of a Telegram channel (not pushy)
- First-person, relatable, honest
- 150-300 words total
- Never sound like marketing

You follow Reddit culture: no hard sells, give value first."""


class GrowthAgent(BaseAgent):
    """Autonomous growth: Reddit posts + Pinterest pins + blog CTAs."""

    def __init__(self):
        super().__init__("growth_agent")
        self.channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "@yourchannel")
        self.site_url = os.environ.get("SITE_URL", "https://yourdomain.github.io/passiveflow")
        self.reddit_token = None

        # Reddit credentials (optional — Reddit API is free)
        self.reddit_client_id = os.environ.get("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        self.reddit_username = os.environ.get("REDDIT_USERNAME")
        self.reddit_password = os.environ.get("REDDIT_PASSWORD")

        # Pinterest (optional)
        self.pinterest_token = os.environ.get("PINTEREST_ACCESS_TOKEN")
        self.pinterest_board_id = os.environ.get("PINTEREST_BOARD_ID")

    # ── Reddit ─────────────────────────────────────────────────

    def _reddit_login(self) -> bool:
        """Get Reddit OAuth token."""
        if not all([self.reddit_client_id, self.reddit_client_secret,
                    self.reddit_username, self.reddit_password]):
            self.logger.warning("Reddit credentials not set. Skipping Reddit posts.")
            return False

        try:
            resp = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.reddit_client_id, self.reddit_client_secret),
                data={
                    "grant_type": "password",
                    "username": self.reddit_username,
                    "password": self.reddit_password
                },
                headers={"User-Agent": "PassiveFlow/1.0"},
                timeout=15
            )
            data = resp.json()
            if "access_token" in data:
                self.reddit_token = data["access_token"]
                self.logger.info("Reddit login successful")
                return True
            else:
                self.logger.error(f"Reddit login failed: {data}")
                return False
        except Exception as e:
            self.logger.error(f"Reddit login error: {e}")
            return False

    def _generate_reddit_post(self, post: dict, subreddit: str) -> dict:
        """Generate a genuine Reddit post based on a blog article."""
        prompt = f"""Write a helpful Reddit post for r/{subreddit} based on this topic:

Blog article title: {post['title']}
Blog keyword: {post.get('keyword', '')}
Telegram channel: {self.channel_id}
Blog URL: {self.site_url}/posts/{post['slug']}

Write a genuine, helpful post that:
1. Shares the key insight from the article in your own words
2. Adds personal context ("as a student myself...")
3. Ends with ONE soft line like: "Also started a Telegram channel [{self.channel_id}] where I share deals/tips if that's useful"
4. Has a clear title (not clickbait)

Return as JSON with keys: "title" and "body"
"""
        result = self.call_claude_json(REDDIT_SYSTEM, prompt)
        return result

    def _post_to_reddit(self, subreddit: str, title: str, body: str) -> bool:
        """Submit a text post to Reddit."""
        if not self.reddit_token:
            return False

        try:
            resp = requests.post(
                "https://oauth.reddit.com/api/submit",
                headers={
                    "Authorization": f"bearer {self.reddit_token}",
                    "User-Agent": "PassiveFlow/1.0"
                },
                data={
                    "sr": subreddit,
                    "kind": "self",
                    "title": title,
                    "text": body,
                    "nsfw": False,
                    "spoiler": False,
                },
                timeout=15
            )
            data = resp.json()
            if data.get("success") or "url" in str(data):
                self.logger.info(f"Posted to r/{subreddit}: {title[:50]}...")
                return True
            else:
                self.logger.warning(f"Reddit post failed for r/{subreddit}: {data}")
                return False
        except Exception as e:
            self.logger.error(f"Reddit post error: {e}")
            return False

    def run_reddit_growth(self, posts: list[dict]) -> int:
        """Post one Reddit post per new blog article (spread across subreddits)."""
        if not self._reddit_login():
            return 0

        posted = 0
        # One post per article, rotate subreddits
        week = datetime.now().isocalendar()[1]

        for i, post in enumerate(posts[:2]):  # Max 2 Reddit posts per week
            subreddit_data = SUBREDDITS[(week + i) % len(SUBREDDITS)]
            subreddit = subreddit_data["name"]

            try:
                reddit_post = self._generate_reddit_post(post, subreddit)
                success = self._post_to_reddit(
                    subreddit,
                    reddit_post["title"],
                    reddit_post["body"]
                )
                if success:
                    posted += 1
                time.sleep(10)  # Reddit rate limit: 1 post per 10 min
            except Exception as e:
                self.logger.error(f"Reddit growth failed for post {post['title']}: {e}")

        self.logger.info(f"Reddit: {posted} posts published")
        return posted

    # ── Pinterest ───────────────────────────────────────────────

    def _create_pinterest_pin(self, post: dict) -> bool:
        """Create a Pinterest pin for a blog post."""
        if not self.pinterest_token or not self.pinterest_board_id:
            self.logger.warning("Pinterest credentials not set. Skipping.")
            return False

        # Generate pin description via Gemini
        prompt = f"""Write a Pinterest pin description (max 500 chars) for this blog post.
Include 5 relevant hashtags at the end.
Title: {post['title']}
Keyword: {post.get('keyword', '')}
Return only the description text with hashtags."""

        description = self.call_claude(
            "You write Pinterest pin descriptions for Indian audiences.",
            prompt, max_tokens=150
        )

        try:
            resp = requests.post(
                "https://api.pinterest.com/v5/pins",
                headers={
                    "Authorization": f"Bearer {self.pinterest_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "board_id": self.pinterest_board_id,
                    "title": post["title"][:100],
                    "description": description,
                    "link": f"{self.site_url}/posts/{post['slug']}",
                    "media_source": {
                        "source_type": "image_url",
                        # Default OG image — replace with a real image generator later
                        "url": "https://via.placeholder.com/735x1102/1a1a2e/00e676?text=Read+More"
                    }
                },
                timeout=15
            )
            if resp.status_code in [200, 201]:
                self.logger.info(f"Pinterest pin created: {post['title'][:50]}")
                return True
            else:
                self.logger.warning(f"Pinterest failed: {resp.status_code} {resp.text[:100]}")
                return False
        except Exception as e:
            self.logger.error(f"Pinterest error: {e}")
            return False

    # ── Blog CTA Injection ──────────────────────────────────────

    def inject_telegram_cta(self, posts_dir: Path = Path("site/posts")):
        """
        Inject a Telegram join CTA into the footer of every blog post.
        This converts SEO visitors (Google traffic) into channel members.
        """
        cta_html = f"""
<aside class="telegram-cta" style="
  margin: 3rem 0 1rem;
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, #0a2a1a, #0a1a2a);
  border: 1px solid #1a4020;
  border-radius: 12px;
  text-align: center;
">
  <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📱</div>
  <div style="font-weight: 700; font-size: 1rem; color: #00e676; margin-bottom: 0.4rem;">
    Join the Telegram for Free Deals & Tips
  </div>
  <div style="font-size: 0.87rem; color: #888; margin-bottom: 1rem;">
    Weekly deals, study resources, and earning tips for Indian students. Free to join.
  </div>
  <a href="https://t.me/{self.channel_id.lstrip('@')}"
     style="display:inline-block; background:#00e676; color:#000; font-weight:700;
            padding:0.6rem 1.5rem; border-radius:8px; text-decoration:none; font-size:0.9rem;">
    Join {self.channel_id} →
  </a>
</aside>"""

        injected = 0
        for html_file in posts_dir.glob("*.html"):
            with open(html_file) as f:
                content = f.read()

            # Don't inject twice
            if "telegram-cta" in content:
                continue

            # Inject before </article>
            if "</article>" in content:
                content = content.replace("</article>", cta_html + "\n</article>")
            elif "</main>" in content:
                content = content.replace("</main>", cta_html + "\n</main>")
            else:
                content += cta_html

            with open(html_file, "w") as f:
                f.write(content)

            injected += 1

        self.logger.info(f"Telegram CTA injected into {injected} posts")
        return injected

    # ── Main Run ────────────────────────────────────────────────

    def run(self, posts: list[dict] = None):
        """Full growth run."""
        self.logger.info("GrowthAgent starting...")

        if not posts:
            results_file = Path("logs/content_agent_results.json")
            if results_file.exists():
                with open(results_file) as f:
                    posts = json.load(f)
            else:
                posts = []

        results = {}

        # 1. Inject Telegram CTA into all blog posts
        cta_count = self.inject_telegram_cta()
        results["telegram_cta_injected"] = cta_count

        # 2. Reddit posts (needs credentials in GitHub Secrets)
        reddit_posts = self.run_reddit_growth(posts)
        results["reddit_posts"] = reddit_posts

        # 3. Pinterest pins (needs credentials in GitHub Secrets)
        pinterest_pins = 0
        for post in posts[:3]:
            if self._create_pinterest_pin(post):
                pinterest_pins += 1
            time.sleep(2)
        results["pinterest_pins"] = pinterest_pins

        self.log_result(results)
        self.save_results()
        self.logger.info(f"GrowthAgent done: {results}")
        return results
