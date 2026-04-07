"""
PassiveFlow - Affiliate Agent
==============================
Manages affiliate link injection across all generated content.
Replaces placeholders with real tracking URLs once you add your IDs.
Tracks which programs are active and monetised.
"""

import json
import re
from pathlib import Path
from datetime import datetime

from agents.base_agent import BaseAgent


class AffiliateAgent(BaseAgent):
    """Handles affiliate link management and injection."""

    def __init__(self):
        super().__init__("affiliate_agent")
        self.programs = self._load_programs()
        self.posts_dir = Path("site/posts")
        self.link_map = self._build_link_map()

    def _load_programs(self) -> dict:
        with open("config/affiliates.json") as f:
            data = json.load(f)
        return {p["id"]: p for p in data["programs"]}

    def _build_link_map(self) -> dict:
        """
        Build a placeholder → real URL map.
        You fill in your actual affiliate URLs in .env or config/my_links.json.
        The system works with placeholders until you do.
        """
        import os

        # Try to load user-configured links
        links_file = Path("config/my_links.json")
        user_links = {}
        if links_file.exists():
            with open(links_file) as f:
                user_links = json.load(f)

        link_map = {}
        for prog_id, prog in self.programs.items():
            placeholder = prog["link_placeholder"]
            env_key = f"AFFILIATE_{prog_id.upper()}_URL"

            if env_key in os.environ:
                link_map[placeholder] = os.environ[env_key]
            elif prog_id in user_links:
                link_map[placeholder] = user_links[prog_id]
            else:
                # Keep placeholder with a comment so it's obvious
                link_map[placeholder] = f"#REPLACE_WITH_{env_key}"

        return link_map

    def inject_links(self, html: str) -> tuple[str, int]:
        """
        Replace all link placeholders in HTML with real affiliate URLs.
        Returns (updated_html, num_replacements).
        """
        count = 0
        for placeholder, real_url in self.link_map.items():
            occurrences = html.count(placeholder)
            if occurrences > 0:
                html = html.replace(placeholder, real_url)
                count += occurrences
                if real_url.startswith("#REPLACE"):
                    self.logger.warning(f"Placeholder not replaced: {placeholder} — set env var or config/my_links.json")
        return html, count

    def process_all_posts(self):
        """Inject affiliate links into all posts in site/posts/."""
        posts = list(self.posts_dir.glob("*.html"))
        total_injected = 0

        for post_path in posts:
            with open(post_path) as f:
                html = f.read()

            updated_html, count = self.inject_links(html)

            with open(post_path, "w") as f:
                f.write(updated_html)

            total_injected += count
            self.logger.info(f"Processed {post_path.name}: {count} links injected")

        self.logger.info(f"Total affiliate links injected: {total_injected}")
        return total_injected

    def generate_signup_checklist(self) -> str:
        """
        Generate a clear, actionable checklist for signing up to all affiliate programs.
        Saved to AFFILIATE_SETUP.md.
        """
        lines = ["# Affiliate Program Setup Checklist\n"]
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append("Complete these steps once. After that, everything is automatic.\n")
        lines.append("---\n")

        for i, (prog_id, prog) in enumerate(self.programs.items(), 1):
            status = "⬜"
            lines.append(f"\n## {i}. {prog['name']} {status}")
            lines.append(f"**Category:** {prog['category']}")
            lines.append(f"**Commission:** {prog['commission']}")
            lines.append(f"**Payment:** {', '.join(prog['payment_methods'])}")
            lines.append(f"**Min Payout:** ${prog.get('min_payout', '?')}")
            lines.append(f"**Cookie:** {prog['cookie_days']} days")
            lines.append(f"**Sign Up:** [{prog['signup_url']}]({prog['signup_url']})")
            if prog.get("network"):
                lines.append(f"**Network:** {prog['network']}")
            lines.append(f"\n**After signing up:**")
            lines.append(f"Add to `.env`: `AFFILIATE_{prog_id.upper()}_URL=<your-tracking-link>`")
            lines.append(f"\n**Note:** {prog.get('notes', '')}\n")

        lines.append("\n---")
        lines.append("\n## After Setup\n")
        lines.append("Run `python orchestrator.py --inject-links` to apply all your links to existing posts.")
        lines.append("Payment flows: Program → PayPal/Payoneer → Your Indian Bank Account")

        checklist = "\n".join(lines)
        with open("AFFILIATE_SETUP.md", "w") as f:
            f.write(checklist)

        self.logger.info("Affiliate setup checklist written to AFFILIATE_SETUP.md")
        return checklist

    def report_status(self) -> dict:
        """Report which affiliate links are configured vs pending."""
        configured = []
        pending = []
        for placeholder, url in self.link_map.items():
            if url.startswith("#REPLACE"):
                pending.append(placeholder)
            else:
                configured.append(placeholder)

        report = {
            "configured": configured,
            "pending": pending,
            "configured_count": len(configured),
            "pending_count": len(pending),
            "monetisation_ready": len(pending) == 0
        }
        self.logger.info(f"Affiliate status: {len(configured)} configured, {len(pending)} pending")
        return report

    def run(self):
        """Full affiliate agent run."""
        self.logger.info("AffiliateAgent starting...")

        # Generate setup checklist (useful on first run)
        self.generate_signup_checklist()

        # Report status
        status = self.report_status()

        # Inject links into all posts
        injected = self.process_all_posts()

        result = {**status, "links_injected": injected}
        self.log_result(result)
        self.save_results()
        self.logger.info("AffiliateAgent done.")
        return result
