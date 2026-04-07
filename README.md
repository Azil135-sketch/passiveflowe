# PassiveFlow — Halal Multi-Agent Income System

**Multi-agent swarm. Fully automated. Real money to your Payoneer → Indian bank.**

---

## ⚠️ Why Kimi's Plan Didn't Work

| Problem | Fix |
|---|---|
| Amazon Associates doesn't load in India | Replaced with 7 programs that work in India + pay via Payoneer |
| Placeholder code, nothing actually runs | Every file is production-grade, tested logic |
| No real traffic strategy | SEO-optimised content + Telegram integration |
| Required a server/crontab | Runs free on GitHub Actions |
| Vague earnings projections | Realistic timelines based on affiliate EPCs |

---

## 💰 Income Streams (All Halal)

### Stream 1: Affiliate Blog (SEO → Commissions)
Auto-generated SEO blog posts targeting buyer-intent keywords.
Readers find via Google → click affiliate link → you earn commission.

**Programs (India-compatible, Payoneer-supported):**

| Program | Commission | Cookie | Notes |
|---|---|---|---|
| Hostinger | Up to 60% (~$50-150/sale) | 30 days | Highest EPC in hosting |
| Grammarly | $0.20 free / $20 premium | 90 days | High volume, student audience |
| Canva | 80% first + 25% recurring | 30 days | Recurring = passive |
| Fiverr | $15-150 CPA | 30 days | Payoneer direct |
| NordVPN | 100% first + 30% recurring | 30 days | Privacy = halal |
| Coursera | 10-45% | 30 days | Education = 100% halal |
| Namecheap | 20-35% | 30 days | Pairs with hosting content |

### Stream 2: Telegram Channel (Immediate)
Your existing bot posts weekly affiliate deals + article teasers.
**This earns from Day 1** once you have affiliate links.

### Stream 3: Compounding (Month 3+)
As posts rank, organic traffic → passive commissions. No ongoing work.

---

## 🕐 Realistic Timeline

| Period | What Happens | Expected Monthly |
|---|---|---|
| Week 1-2 | Setup, sign up for 2-3 programs | $0 (setup phase) |
| Week 3-4 | First posts live, Telegram active | $5-30 (Telegram clicks) |
| Month 2 | 10+ posts live, Google indexing | $20-100 |
| Month 3 | Long-tail keywords start ranking | $50-300 |
| Month 6 | 70+ posts, established site | $200-800 |
| Month 12 | Authority site, recurring commissions | $500-2000+ |

*Note: These are conservative estimates based on realistic affiliate site performance. Results depend on niche competition and traffic. Nothing is "guaranteed" in passive income — but these programs have decade-long track records and pay reliably.*

---

## 🚀 Setup (One-Time, ~90 Minutes)

### Step 1: Fork & Clone This Repo (5 min)

```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/passiveflow
cd passiveflow
pip install -r requirements.txt
```

### Step 2: Copy .env and Add Your Keys (10 min)

```bash
cp .env.example .env
# Edit .env and add:
# - ANTHROPIC_API_KEY (your existing key)
# - TELEGRAM_BOT_TOKEN (your existing bot from deal-bot)
# - TELEGRAM_CHANNEL_ID (your channel)
# - SITE_URL (after Step 4)
```

### Step 3: Sign Up for Affiliate Programs (45 min)

Run this to get your personalised checklist:
```bash
python orchestrator.py --status
```
This generates `AFFILIATE_SETUP.md` with direct signup links.

**Sign up order (prioritise highest commission first):**
1. **Grammarly** via Impact — easiest approval, pays fast
2. **Canva** via Impact — recurring income
3. **Fiverr** — Payoneer direct, fast approval
4. **Hostinger** — highest per-sale value
5. Others as you go

After each signup, add your tracking URL to `.env`:
```
AFFILIATE_GRAMMARLY_URL=https://grammarly.go2cloud.org/aff_c?offer_id=...
```

### Step 4: Deploy to GitHub Pages (10 min)

```bash
# First run locally to generate initial content:
python orchestrator.py

# Then push to GitHub:
git add .
git commit -m "initial deployment"
git push origin main
```

In your GitHub repo settings:
- Go to **Settings → Pages**
- Set source to: **main branch, /site folder**
- Your site will be live at: `https://YOUR_USERNAME.github.io/passiveflow`

Update `SITE_URL` in `.env` and in GitHub Secrets.

### Step 5: Add GitHub Secrets (10 min)

Go to: **GitHub repo → Settings → Secrets → Actions**

Add all your `.env` variables as repository secrets. The GitHub Action uses these to run the swarm weekly without exposing your keys.

### Step 6: Enable GitHub Actions (2 min)

- Go to **Actions tab** in your GitHub repo
- Click "Enable Actions"
- The workflow runs every Monday at 8:00 AM UTC (1:30 PM IST)
- Or trigger manually anytime from the Actions tab

**Done. The swarm runs itself from here.**

---

## 🤖 How the Swarm Works

```
Every Monday at 1:30 PM IST:

orchestrator.py
├── [1] ContentAgent
│   └── Calls Claude API → generates 3 SEO blog posts
│       └── Saves to site/posts/
│
├── [2] SEOAgent
│   └── Wraps posts in full HTML pages
│   └── Generates sitemap.xml + robots.txt
│   └── Injects structured data (JSON-LD)
│
├── [3] AffiliateAgent
│   └── Injects your affiliate links into all posts
│   └── Warns if any links still unset
│
├── [4] SocialAgent
│   └── Posts article teasers to your Telegram channel
│   └── Posts weekly affiliate deal
│
└── [5] DeployAgent
    └── Builds index.html from all posts
    └── Git commit + push → GitHub Pages auto-deploys
```

---

## 💳 Getting Paid

### Payoneer → Indian Bank (You Already Have Payoneer)

All 7 programs support PayPal or Payoneer. Here's the flow:

```
Affiliate Program
  → Pays to PayPal or Payoneer
  → Transfer to your Payoneer account
  → Withdraw to your Indian bank (SBI/HDFC etc.)
  → INR credited to your account
```

Payoneer withdrawal to Indian bank: ₹500 fee flat, 1-3 business days.

### Payment Schedules
- Grammarly (Impact): Net-30 after approval threshold
- Canva (Impact): Net-30
- Fiverr: Net-30
- Hostinger: Monthly, min $100
- NordVPN: Monthly
- Coursera (Rakuten): Monthly

---

## 🔧 Manual Commands

```bash
# Full weekly run (generates content + deploys)
python orchestrator.py

# Re-inject affiliate links after adding new ones
python orchestrator.py --inject

# Rebuild index + deploy only (no new content)
python orchestrator.py --deploy

# Check current status
python orchestrator.py --status
```

---

## 📁 Project Structure

```
passiveflow/
├── orchestrator.py          ← Main controller — RUN THIS
├── requirements.txt
├── .env.example             ← Copy to .env and fill in
├── .gitignore
├── AFFILIATE_SETUP.md       ← Auto-generated signup checklist
│
├── agents/
│   ├── base_agent.py        ← Retry logic, Claude API, logging
│   ├── content_agent.py     ← Generates blog posts via Claude
│   ├── seo_agent.py         ← Meta tags, sitemap, structured data
│   ├── affiliate_agent.py   ← Link injection + program management
│   ├── social_agent.py      ← Telegram posting
│   └── deploy_agent.py      ← Git push → GitHub Pages
│
├── config/
│   ├── affiliates.json      ← All 7 affiliate programs
│   ├── niches.json          ← Content topics + keywords
│   └── my_links.json        ← (Optional) Your affiliate URLs here
│
├── site/
│   ├── index.html           ← Auto-generated homepage
│   ├── sitemap.xml          ← Auto-generated
│   ├── robots.txt           ← Auto-generated
│   ├── posts/               ← All blog posts (auto-generated)
│   └── static/css/style.css ← Blog stylesheet
│
├── logs/
│   ├── swarm.log            ← Full run log
│   ├── income_report.json   ← Latest swarm results
│   └── *_results.json       ← Per-agent results
│
└── .github/workflows/
    └── weekly_swarm.yml     ← GitHub Actions cron job
```

---

## ❓ FAQ

**Is this halal?**
Yes. All products promoted are legitimate software services (writing tools, hosting, education, privacy, freelancing platform). No interest, no speculation, no haram products. Affiliate marketing = commission for referral = halal.

**Do I need a server?**
No. GitHub Actions runs the swarm for free. GitHub Pages hosts the site for free. Total infrastructure cost: $0.

**What does it cost to run?**
Only the Anthropic API calls for content generation. At 3 posts/week using Claude Haiku: ~$0.05-0.15/week. Less than ₹15/week.

**What if a post ranks but the affiliate link is wrong?**
Run `python orchestrator.py --inject` after updating your `.env`. It re-processes all posts.

**Can I add more affiliate programs?**
Yes. Add to `config/affiliates.json` and add the env var. The affiliate agent picks it up automatically.

**Can I change posting frequency?**
Edit `.github/workflows/weekly_swarm.yml` cron expression. Edit `ContentAgent.POSTS_PER_RUN` for more posts per run.
