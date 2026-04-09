"""
PassiveFlow - Deploy Agent
===========================
1. Builds the site index page from all generated posts
2. Commits all new content to Git
3. Pushes to GitHub — triggers automatic deployment to GitHub Pages / Vercel

Prerequisites:
- GitHub repo set up with GitHub Pages or Vercel connected
- Git credentials configured (done via GitHub Actions secrets)
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

from agents.base_agent import BaseAgent


class DeployAgent(BaseAgent):
    """Builds static site and deploys via Git push."""

    def __init__(self):
        super().__init__("deploy_agent")
        self.site_dir = Path("site")
        self.posts_dir = self.site_dir / "posts"
        self.site_url = os.environ.get("SITE_URL", "https://yourdomain.github.io")
        self.site_name = os.environ.get("SITE_NAME", "PassiveFlow Blog")

    def _load_all_posts(self) -> list[dict]:
        """Load all post metadata from content agent results."""
        results_file = Path("logs/content_agent_results.json")
        if not results_file.exists():
            return []
        with open(results_file) as f:
            return json.load(f)

    def build_index(self, posts: list[dict]) -> str:
        """
        Build the site's homepage (index.html) listing all blog posts.
        Styled, SEO-optimised, mobile-friendly.
        """
        # Sort by timestamp descending (newest first)
        sorted_posts = sorted(posts, key=lambda p: p.get("timestamp", ""), reverse=True)

        # Build post cards HTML
        cards_html = ""
        for post in sorted_posts[:20]:  # Show last 20 posts on homepage
            niche_badge = post.get("niche", "").replace("_", " ").title()
            cards_html += f"""
    <article class="post-card">
      <span class="badge">{niche_badge}</span>
      <h2><a href="/posts/{post['slug']}">{post['title']}</a></h2>
      <p class="meta">{post.get('meta_description', '')}</p>
      <a href="/posts/{post['slug']}" class="read-more">Read More →</a>
    </article>"""

        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{self.site_name} — Honest Reviews & Guides</title>
  <meta name="description" content="Honest reviews and guides on productivity tools, web hosting, freelancing, and online income. All recommendations are tested and verified.">
  <link rel="canonical" href="{self.site_url}">
  <link rel="stylesheet" href="/static/css/style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Blog",
    "name": "{self.site_name}",
    "url": "{self.site_url}",
    "description": "Honest reviews and guides on tools, hosting, and online income."
  }}
  </script>
</head>
<body>
  <header class="site-header">
    <nav>
      <a href="/" class="logo">{self.site_name}</a>
      <a href="/posts">All Posts</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <h1>Honest Guides. Real Results.</h1>
      <p>Reviews and guides on tools that actually help you work smarter and earn online.</p>
    </section>

    <section class="post-grid">
      {cards_html if cards_html else '<p class="empty">Posts coming soon. Check back shortly.</p>'}
    </section>
  </main>

  <footer class="site-footer">
    <p>© {datetime.now().year} {self.site_name}. All rights reserved.</p>
    <p><small>This site contains affiliate links. We earn a small commission when you purchase through our links, at no cost to you.</small></p>
  </footer>
</body>
</html>"""

        index_path = self.site_dir / "index.html"
        with open(index_path, "w") as f:
            f.write(index_html)

        self.logger.info(f"Built index.html with {len(sorted_posts)} posts")
        return str(index_path)

    def _run_git(self, *args) -> tuple[int, str, str]:
        """Run a git command and return (returncode, stdout, stderr)."""
        result = subprocess.run(
            ["git", *args],
            capture_output=True, text=True, cwd=Path.cwd()
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def git_deploy(self) -> bool:
        """
        Stage all changes, commit with timestamp, push to origin.
        GitHub Pages / Vercel will auto-deploy on push.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Configure git identity (for GitHub Actions)
        self._run_git("config", "user.email", "passiveflow-bot@users.noreply.github.com")
        self._run_git("config", "user.name", "PassiveFlow Bot")

        # Stage all site changes
        code, out, err = self._run_git("add", "site/", "logs/")
        if code != 0:
            self.logger.error(f"git add failed: {err}")
            return False

        # Check if there's anything to commit
        code, out, _ = self._run_git("status", "--porcelain")
        if not out:
            self.logger.info("Nothing to commit — no new posts generated this run.")
            return True

        # Commit
        commit_msg = f"auto: weekly content update {timestamp}"
        code, out, err = self._run_git("commit", "-m", commit_msg)
        if code != 0:
            self.logger.error(f"git commit failed: {err}")
            return False

        # Push
        code, out, err = self._run_git("push", "origin", "main")
        if code != 0:
            self.logger.error(f"git push failed: {err}")
            return False

        self.logger.info(f"Successfully pushed: {commit_msg}")
        return True

    def run(self):
        """Build site and deploy."""
        self.logger.info("DeployAgent starting...")
        posts = self._load_all_posts()

        # Build index
        self.build_index(posts)

        # Git deploy
        deployed = self.git_deploy()

        result = {"posts_indexed": len(posts), "deployed": deployed}
        self.log_result(result)
        self.save_results()

        if deployed:
            self.logger.info(f"DeployAgent done. Site live at: {self.site_url}")
        else:
            self.logger.warning("DeployAgent done but push failed — check git config.")

        return result
