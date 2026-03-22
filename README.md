# Repo Aura

Monitor your GitHub repo traffic stats over time. Repo Aura collects and stores data continuously, then presents it as an interactive dashboard with visualized charts for views, clones, commits, referrers, and more. Deploy it to Streamlit Community Cloud and Supabase (both free, no credit card required) to access your data from anywhere.

## Background

### Problem

GitHub only retains 2 weeks of traffic data. After that, it's gone — there's no way to see how a repo performed a month ago, let alone over the past year. Checking stats also requires logging into GitHub and navigating per-repo, with no way to compare across repos or view trends over time from outside GitHub.

### Solution

Repo Aura uses the GitHub API to pull traffic and activity data on a schedule, storing it permanently in a PostgreSQL database. The collection runs as a cron job on Render, so your local machine never needs to be on. The dashboard is deployed as a web app (password-protected) so you can view and interact with your long-term stats from any device, anywhere.

## Architecture

- **Streamlit dashboard** — dark/neon UI with charts for views, clones, commits, issues, PRs, referrers, and contributors
- **GitHub Actions scheduled workflow** — runs the collector every 6 hours
- **Supabase PostgreSQL** — persistent storage for all historical data

## Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (free tier)
- A GitHub Personal Access Token with `repo` and `read:user` scopes
- A [Streamlit Community Cloud](https://streamlit.io/cloud) account (free, no credit card)
- A GitHub account (for Actions — free for public and private repos)

---

## Local Development

### 1. Install dependencies

```bash
pip install -e .
```

This installs the `repo_aura` package (defined in `pyproject.toml`) in editable mode along with all dependencies. Using a virtual environment per project is recommended to avoid package namespace conflicts.

### 2. Create a `.env` file

Copy `.env.example` to `.env` and fill in your values:

```env
# Direct connection (default — requires IPv6 support)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Transaction Pooler (use this if your network does not support IPv6)
# DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

GITHUB_TOKEN=ghp_yourtoken
GITHUB_USERNAME=yourusername
EXCLUDED_REPOS=repo-to-skip,another-repo
HIDDEN_REPOS=private-repo-hide-from-ui
DASHBOARD_PASSWORD=yourpassword
```

> **Note:** Supabase offers two connection methods under **Settings → Database → Connection string**.
> The **Direct connection** uses IPv6 and may not work on all local networks or ISPs.
> If you see connection timeouts, switch to the **Transaction Pooler** string instead — the URL format differs slightly (the project ref is appended to the username, and the port is `6543`).

### 3. Initialise the database

```bash
python scripts/init_db.py
```

### 4. Run the collector (populates initial data)

```bash
python -m repo_aura.collector
```

### 5. Start the dashboard

```bash
streamlit run repo_aura/dashboard.py
```

---

## Deployment

### Step 1: Create a Supabase database

1. Go to [supabase.com](https://supabase.com) and create a new project
2. From **Settings → Database**, copy the **Connection string** (URI format)
3. Run `python scripts/init_db.py` locally (with `DATABASE_URL` set) to create the schema

### Step 2: Deploy the dashboard to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app**, select this repo, and set the main file path to `repo_aura/dashboard.py`
4. Under **Advanced settings → Secrets**, add the following:

```toml
DATABASE_URL = "your-supabase-connection-string"
GITHUB_TOKEN = "ghp_yourtoken"
GITHUB_USERNAME = "yourusername"
EXCLUDED_REPOS = "repo-to-skip,another-repo"
HIDDEN_REPOS = "private-repo-hide-from-ui"
DASHBOARD_PASSWORD = "yourpassword"
```

5. Click **Deploy** — Streamlit Cloud will install dependencies from `requirements.txt` automatically

### Step 3: Set up the GitHub Actions collector

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Add the following repository secrets:
   - `DATABASE_URL` — your Supabase connection string
   - `GITHUB_TOKEN` — your GitHub PAT
   - `GITHUB_USERNAME` — your GitHub username
   - `EXCLUDED_REPOS` — comma-separated repo names to skip (optional)
3. The workflow at `.github/workflows/collect.yml` runs automatically every 6 hours
4. To trigger a manual run: go to **Actions → Collect GitHub Stats → Run workflow**

### Step 4: Verify

- Open the Streamlit Cloud app URL and log in
- Check the **Actions** tab in your GitHub repo after the first scheduled run to confirm data is being collected

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string |
| `GITHUB_TOKEN` | Yes | GitHub PAT with `repo` + `read:user` scopes |
| `GITHUB_USERNAME` | Yes | GitHub username to enumerate repos |
| `EXCLUDED_REPOS` | No | Comma-separated repos to skip during collection |
| `HIDDEN_REPOS` | No | Comma-separated repos to hide from the dashboard |
| `DASHBOARD_PASSWORD` | No | Password for the dashboard login gate |
| `COLLECTION_INTERVAL_HOURS` | No | Collection frequency hint (default: 6) |

---

## Dashboard Features

- **Traffic tab** — daily views and unique visitors over time
- **Clones tab** — daily clones and unique cloners over time
- **Commits tab** — weekly commits, additions, and deletions
- **Issues & PRs tab** — open/closed issues and open/merged PRs over time
- **Referrers tab** — top referring sites (latest snapshot)
- **Contributors tab** — commits per contributor (latest snapshot)

**Filters (sidebar):**
- Select individual repos, a subset, or all repos
- Time period presets: 7 days, 30 days, 90 days, 1 year, all time, or custom date range
