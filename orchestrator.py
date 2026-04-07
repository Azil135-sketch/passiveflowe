"""
PassiveFlow Orchestrator
=========================
The main controller. Runs all agents in sequence.
Run this manually or via GitHub Actions (weekly cron).

Usage:
  python orchestrator.py              # Full weekly run
  python orchestrator.py --inject     # Only re-inject affiliate links
  python orchestrator.py --deploy     # Only rebuild and deploy
  python orchestrator.py --status     # Print income/affiliate status
"""

import sys
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Load env vars from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # In GitHub Actions, env vars are set directly


# ─── Setup Logging ───────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | ORCHESTRATOR | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/swarm.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("orchestrator")


# ─── Agent Imports ────────────────────────────────────────────────────────────
from agents.content_agent import ContentAgent
from agents.seo_agent import SEOAgent
from agents.affiliate_agent import AffiliateAgent
from agents.social_agent import SocialAgent
from agents.deploy_agent import DeployAgent


# ─── Orchestrator ────────────────────────────────────────────────────────────

def run_full_swarm():
    """
    Full pipeline:
    1. Content Agent  → generates 3 SEO blog posts
    2. SEO Agent      → builds full pages, sitemap, meta
    3. Affiliate Agent → injects links, generates setup checklist
    4. Social Agent   → posts teasers to Telegram
    5. Deploy Agent   → builds index, git push → auto-deploy
    """
    log.info("=" * 60)
    log.info("PASSIVEFLOW SWARM STARTING")
    log.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    results = {}
    start = time.time()

    # ── Step 1: Content Generation ──────────────────────────────────────────
    log.info("\n[1/5] ContentAgent — Generating blog posts...")
    try:
        content = ContentAgent()
        posts = content.run()
        results["content"] = {"posts_generated": len(posts), "status": "ok"}
        log.info(f"✓ ContentAgent: {len(posts)} posts generated")
    except Exception as e:
        log.error(f"✗ ContentAgent failed: {e}")
        results["content"] = {"status": "error", "error": str(e)}
        posts = []

    time.sleep(2)

    # ── Step 2: SEO ──────────────────────────────────────────────────────────
    log.info("\n[2/5] SEOAgent — Building pages + sitemap...")
    try:
        seo = SEOAgent()
        seo.run()
        results["seo"] = {"status": "ok"}
        log.info("✓ SEOAgent: Pages built, sitemap generated")
    except Exception as e:
        log.error(f"✗ SEOAgent failed: {e}")
        results["seo"] = {"status": "error", "error": str(e)}

    time.sleep(2)

    # ── Step 3: Affiliate Link Injection ─────────────────────────────────────
    log.info("\n[3/5] AffiliateAgent — Injecting links + checking status...")
    try:
        affiliate = AffiliateAgent()
        aff_result = affiliate.run()
        results["affiliate"] = aff_result
        if aff_result.get("pending_count", 0) > 0:
            log.warning(f"⚠ {aff_result['pending_count']} affiliate links not yet configured.")
            log.warning("  → Check AFFILIATE_SETUP.md to sign up and add your links.")
        else:
            log.info("✓ AffiliateAgent: All links injected")
    except Exception as e:
        log.error(f"✗ AffiliateAgent failed: {e}")
        results["affiliate"] = {"status": "error", "error": str(e)}

    time.sleep(2)

    # ── Step 4: Social Media ──────────────────────────────────────────────────
    log.info("\n[4/5] SocialAgent — Posting to Telegram...")
    try:
        social = SocialAgent()
        social_result = social.run(posts=posts)
        results["social"] = social_result
        log.info(f"✓ SocialAgent: {social_result.get('posts_teased', 0)} teasers posted")
    except Exception as e:
        log.error(f"✗ SocialAgent failed: {e}")
        results["social"] = {"status": "error", "error": str(e)}

    time.sleep(2)

    # ── Step 5: Deploy ────────────────────────────────────────────────────────
    log.info("\n[5/5] DeployAgent — Building index + deploying...")
    try:
        deploy = DeployAgent()
        deploy_result = deploy.run()
        results["deploy"] = deploy_result
        if deploy_result.get("deployed"):
            log.info("✓ DeployAgent: Site deployed successfully")
        else:
            log.warning("⚠ DeployAgent: Build done but git push may have failed")
    except Exception as e:
        log.error(f"✗ DeployAgent failed: {e}")
        results["deploy"] = {"status": "error", "error": str(e)}

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - start
    summary = {
        "run_at": datetime.now().isoformat(),
        "duration_seconds": round(elapsed, 1),
        "results": results
    }

    with open("logs/income_report.json", "w") as f:
        json.dump(summary, f, indent=2)

    log.info("\n" + "=" * 60)
    log.info("SWARM COMPLETE")
    log.info(f"Duration: {elapsed:.1f}s")
    log.info(f"Posts generated: {results.get('content', {}).get('posts_generated', 0)}")
    log.info(f"Deployed: {results.get('deploy', {}).get('deployed', False)}")
    log.info("=" * 60)

    return summary


def run_inject_only():
    """Only re-inject affiliate links (useful after adding new affiliate IDs)."""
    log.info("Affiliate link injection only...")
    affiliate = AffiliateAgent()
    result = affiliate.run()
    log.info(f"Done: {result}")


def run_deploy_only():
    """Only rebuild index and deploy."""
    log.info("Deploy only...")
    deploy = DeployAgent()
    result = deploy.run()
    log.info(f"Done: {result}")


def print_status():
    """Print current income/affiliate status."""
    report_path = Path("logs/income_report.json")
    if report_path.exists():
        with open(report_path) as f:
            report = json.load(f)
        print("\n=== PassiveFlow Status ===")
        print(f"Last run: {report.get('run_at', 'Never')}")
        print(f"Duration: {report.get('duration_seconds', '?')}s")
        results = report.get("results", {})
        print(f"Posts generated (last run): {results.get('content', {}).get('posts_generated', 0)}")
        aff = results.get("affiliate", {})
        print(f"Affiliate links configured: {aff.get('configured_count', '?')}")
        print(f"Affiliate links pending: {aff.get('pending_count', '?')} → see AFFILIATE_SETUP.md")
        print(f"Site deployed: {results.get('deploy', {}).get('deployed', False)}")
    else:
        print("No runs yet. Run: python orchestrator.py")

    # Also show affiliate checklist status
    affiliate = AffiliateAgent()
    status = affiliate.report_status()
    print(f"\nMonetisation ready: {status['monetisation_ready']}")
    if status["pending"]:
        print("Still needed:")
        for p in status["pending"]:
            print(f"  → {p}")


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PassiveFlow Swarm Orchestrator")
    parser.add_argument("--inject", action="store_true", help="Only re-inject affiliate links")
    parser.add_argument("--deploy", action="store_true", help="Only rebuild and deploy")
    parser.add_argument("--status", action="store_true", help="Print current status")
    args = parser.parse_args()

    if args.inject:
        run_inject_only()
    elif args.deploy:
        run_deploy_only()
    elif args.status:
        print_status()
    else:
        run_full_swarm()
