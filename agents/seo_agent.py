"""
PassiveFlow - SEO Agent
========================
Handles all SEO infrastructure:
- Generates sitemap.xml
- Injects meta tags into HTML pages
- Generates robots.txt
- Creates structured data (JSON-LD) for posts
- Tracks keyword rankings over time
"""

import json
import os
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from agents.base_agent import BaseAgent


class SEOAgent(BaseAgent):
    """Builds and maintains SEO infrastructure for the site."""

    def __init__(self):
        super().__init__("seo_agent")
        self.site_dir = Path("site")
        self.posts_dir = self.site_dir / "posts"
        self.site_url = os.environ.get("SITE_URL", "https://yourdomain.github.io")

    def _load_post_meta(self) -> list[dict]:
        """Load metadata for all generated posts from content agent results."""
        results_file = Path("logs/content_agent_results.json")
        if not results_file.exists():
            self.logger.warning("No content_agent_results.json found.")
            return []
        with open(results_file) as f:
            return json.load(f)

    def generate_sitemap(self, posts: list[dict]) -> str:
        """Generate a complete sitemap.xml."""
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

        # Homepage
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = self.site_url
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "1.0"
        ET.SubElement(url, "lastmod").text = datetime.now().strftime("%Y-%m-%d")

        # Posts
        for post in posts:
            url = ET.SubElement(urlset, "url")
            ET.SubElement(url, "loc").text = f"{self.site_url}/posts/{post['slug']}"
            ET.SubElement(url, "changefreq").text = "monthly"
            ET.SubElement(url, "priority").text = "0.8"
            ET.SubElement(url, "lastmod").text = post.get("timestamp", datetime.now().isoformat())[:10]

        tree = ET.ElementTree(urlset)
        ET.indent(tree, space="  ")
        sitemap_path = self.site_dir / "sitemap.xml"
        tree.write(sitemap_path, xml_declaration=True, encoding="utf-8")
        self.logger.info(f"Sitemap generated: {len(posts)+1} URLs")
        return str(sitemap_path)

    def generate_robots_txt(self):
        """Generate robots.txt."""
        content = f"""User-agent: *
Allow: /
Sitemap: {self.site_url}/sitemap.xml

# PassiveFlow - Automated SEO Blog
"""
        path = self.site_dir / "robots.txt"
        with open(path, "w") as f:
            f.write(content)
        self.logger.info("robots.txt generated")

    def generate_json_ld(self, post: dict) -> str:
        """Generate JSON-LD structured data for a blog post."""
        return json.dumps({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post["title"],
            "description": post.get("meta_description", ""),
            "author": {
                "@type": "Person",
                "name": os.environ.get("AUTHOR_NAME", "PassiveFlow")
            },
            "publisher": {
                "@type": "Organization",
                "name": os.environ.get("SITE_NAME", "PassiveFlow Blog"),
                "url": self.site_url
            },
            "datePublished": post.get("timestamp", datetime.now().isoformat())[:10],
            "dateModified": datetime.now().strftime("%Y-%m-%d"),
            "url": f"{self.site_url}/posts/{post['slug']}",
            "keywords": post.get("keyword", ""),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"{self.site_url}/posts/{post['slug']}"
            }
        }, indent=2)

    def inject_meta_tags(self, post: dict, html_content: str) -> str:
        """
        Wrap a post's HTML body content in a full page with proper meta tags.
        This transforms the article fragment into a complete, deployable HTML page.
        """
        json_ld = self.generate_json_ld(post)
        site_name = os.environ.get("SITE_NAME", "PassiveFlow Blog")
        site_url = self.site_url

        full_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{post['title']} | {site_name}</title>
  <meta name="description" content="{post.get('meta_description', '')}">
  <meta name="keywords" content="{post.get('keyword', '')}">
  <meta name="robots" content="index, follow">

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{post['title']}">
  <meta property="og:description" content="{post.get('meta_description', '')}">
  <meta property="og:url" content="{site_url}/posts/{post['slug']}">
  <meta property="og:site_name" content="{site_name}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{post['title']}">
  <meta name="twitter:description" content="{post.get('meta_description', '')}">

  <!-- Canonical -->
  <link rel="canonical" href="{site_url}/posts/{post['slug']}">

  <!-- Stylesheet -->
  <link rel="stylesheet" href="/static/css/style.css">

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>
  <header class="site-header">
    <nav>
      <a href="/" class="logo">{site_name}</a>
      <a href="/posts">All Posts</a>
    </nav>
  </header>

  <main class="post-container">
    <article class="post-content">
      {html_content}
    </article>
  </main>

  <footer class="site-footer">
    <p>© {datetime.now().year} {site_name}. All rights reserved.</p>
    <p><small>Some links on this site are affiliate links. We may earn a commission at no extra cost to you.</small></p>
  </footer>

  <!-- Analytics placeholder - add your Google Analytics / Plausible ID -->
  <!-- <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script> -->
</body>
</html>"""
        return full_page

    def build_full_pages(self, posts: list[dict]):
        """Convert all post HTML fragments into full deployable pages."""
        built = 0
        for post in posts:
            post_fragment_path = self.posts_dir / post["filename"]
            if not post_fragment_path.exists():
                self.logger.warning(f"Post fragment not found: {post['filename']}")
                continue

            with open(post_fragment_path) as f:
                html_fragment = f.read()

            full_page = self.inject_meta_tags(post, html_fragment)

            # Save as full page (same name but now complete HTML)
            output_path = self.posts_dir / post["filename"]
            with open(output_path, "w") as f:
                f.write(full_page)

            built += 1

        self.logger.info(f"Built {built} full HTML pages")

    def run(self):
        """Run all SEO tasks."""
        self.logger.info("SEOAgent starting...")
        posts = self._load_post_meta()

        # Build full HTML pages
        self.build_full_pages(posts)

        # Generate sitemap
        self.generate_sitemap(posts)

        # Generate robots.txt
        self.generate_robots_txt()

        self.log_result({"seo_tasks": "complete", "posts_processed": len(posts)})
        self.save_results()
        self.logger.info("SEOAgent done.")
        return posts
