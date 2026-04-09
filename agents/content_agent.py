"""
PassiveFlow - Content Agent
============================
Generates high-quality, SEO-optimised blog posts for each niche.
Each post is affiliate-ready with link placeholders injected.
"""

import json
import re
from pathlib import Path
from datetime import datetime

from agents.base_agent import BaseAgent


SYSTEM_PROMPT = """You are an expert SEO content writer and affiliate marketer.
You write helpful, honest, reader-first content that also converts.

Your posts:
- Are 1200-1800 words (ideal for SEO)
- Have a clear structure with H2/H3 headings
- Include a compelling intro that hooks the reader
- Cover the topic thoroughly and honestly
- Include a clear, value-driven CTA with the affiliate link
- Are written in plain, conversational English (not salesy)
- Add genuine value — real tips, real comparisons, real advice
- Are formatted as clean HTML (no full page, just the article body)

NEVER fabricate statistics. If unsure, say "studies suggest" or omit.
ALWAYS disclose affiliate relationship in the post footer.
"""


class ContentAgent(BaseAgent):
    """Generates SEO blog post HTML for each configured niche."""

    POSTS_PER_RUN = 3  # Posts generated per weekly run

    def __init__(self):
        super().__init__("content_agent")
        self.niches = self._load_niches()
        self.affiliates = self._load_affiliates()
        self.output_dir = Path("site/posts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_niches(self) -> list:
        with open("config/niches.json") as f:
            return json.load(f)["niches"]

    def _load_affiliates(self) -> dict:
        with open("config/affiliates.json") as f:
            data = json.load(f)
        return {p["id"]: p for p in data["programs"]}

    def _pick_topics(self) -> list[dict]:
        """Pick POSTS_PER_RUN topics spread across niches."""
        topics = []
        niche_cycle = self.niches * 10  # repeat to have enough
        for i in range(self.POSTS_PER_RUN):
            niche = niche_cycle[i % len(self.niches)]
            keyword = niche["keywords"][i % len(niche["keywords"])]
            template = niche["post_templates"][i % len(niche["post_templates"])]
            year = datetime.now().year
            title = template.format(
                tool=niche["name"].split()[0],
                year=year,
                number=str(7 + i),
                category="Productivity",
                audience="Students",
                hosting="Hostinger",
                hosting1="Hostinger",
                hosting2="Namecheap",
                amount="$100"
            )
            topics.append({
                "niche_id": niche["id"],
                "niche_name": niche["name"],
                "keyword": keyword,
                "title": title,
                "affiliates": [self.affiliates[a] for a in niche["affiliates"] if a in self.affiliates]
            })
        return topics

    def _build_affiliate_context(self, affiliates: list) -> str:
        """Build a short description of affiliate links for the prompt."""
        lines = []
        for a in affiliates:
            lines.append(
                f"- {a['name']} ({a['category']}): Use placeholder [{a['link_placeholder']}]. "
                f"Commission: {a['commission']}. "
                f"Context: {a.get('notes', '')}"
            )
        return "\n".join(lines)

    def generate_post(self, topic: dict) -> dict:
        """Generate one full blog post and return metadata + HTML."""
        affiliate_ctx = self._build_affiliate_context(topic["affiliates"])

        prompt = f"""Write a complete SEO blog post with this target keyword: "{topic['keyword']}"

Suggested title: {topic['title']}
Niche: {topic['niche_name']}

Available affiliate links to naturally include in the post (use the EXACT placeholder text shown):
{affiliate_ctx}

Requirements:
1. Write the full post as clean HTML article body (use <h2>, <h3>, <p>, <ul>, <a href="PLACEHOLDER"> tags)
2. Naturally include 2-3 affiliate links using the exact placeholder shown in brackets
3. Make the CTAs feel genuinely helpful, not pushy
4. End with an <aside class="affiliate-disclosure"> that says "This post contains affiliate links..."
5. Target length: 1200-1600 words
6. Start with a <h1> tag for the title

Write the complete HTML now:"""

        html_content = self.call_claude(SYSTEM_PROMPT, prompt, max_tokens=3000)

        # Generate slug from title
        slug = re.sub(r'[^a-z0-9]+', '-', topic['title'].lower()).strip('-')
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{slug[:50]}.html"

        # Generate meta description
        meta_prompt = f"""Given this blog post title: "{topic['title']}"
Target keyword: "{topic['keyword']}"

Write a compelling meta description (150-160 chars) for Google search results.
Return ONLY the meta description text, nothing else."""

        meta_desc = self.call_claude(
            "You write SEO meta descriptions. Be concise and compelling.",
            meta_prompt,
            max_tokens=100
        )[:160]

        result = {
            "slug": slug,
            "filename": filename,
            "title": topic["title"],
            "keyword": topic["keyword"],
            "niche": topic["niche_id"],
            "meta_description": meta_desc,
            "html_content": html_content,
            "word_count": len(html_content.split()),
            "affiliates_used": [a["id"] for a in topic["affiliates"]],
            "status": "generated"
        }

        # Save the post HTML fragment
        post_path = self.output_dir / filename
        with open(post_path, "w") as f:
            f.write(html_content)

        self.logger.info(f"Generated post: {filename} ({result['word_count']} words)")
        return result

    def run(self):
        """Main run — generates POSTS_PER_RUN blog posts."""
        self.logger.info(f"ContentAgent starting. Generating {self.POSTS_PER_RUN} posts...")
        topics = self._pick_topics()
        generated = []

        for topic in topics:
            try:
                post = self.generate_post(topic)
                generated.append(post)
                self.log_result(post)
            except Exception as e:
                self.logger.error(f"Failed to generate post for '{topic['title']}': {e}")

        self.save_results()
        self.logger.info(f"ContentAgent done. {len(generated)}/{self.POSTS_PER_RUN} posts generated.")
        return generated
