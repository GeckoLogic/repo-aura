# Repo Aura

Monitor your GitHub repo traffic stats over time — stored permanently and visualized in an interactive dashboard.

---

## Background

### Problem

GitHub only retains 2 weeks of traffic data. After that, it's gone — there's no way to see how a repo performed a month ago, let alone over the past year. Checking stats also requires logging into GitHub and navigating per-repo, with no way to compare across repos or view trends over time.

### Solution

Repo Aura uses the GitHub API to pull traffic and activity data on a schedule, storing it permanently in a PostgreSQL database. The collection runs as a scheduled GitHub Actions workflow, so your local machine never needs to be on. The dashboard is deployed as a web app (password-protected) so you can view and interact with your long-term stats from any device, anywhere.

---

## Features

| Feature | Description |
|---|---|
| **Traffic** | Daily views and unique visitors over time, with cumulative totals |
| **Clones** | Daily clones and unique cloners over time, with cumulative totals |
| **Commits** | Weekly commits, lines added, and lines removed per repo |
| **Issues & PRs** | Open/closed issues and open/merged pull requests over time |
| **Stars** | Cumulative star counts over time |
| **Referrers** | Top referring sites (latest snapshot) |
| **Contributors** | Commits per contributor (latest snapshot) |
| **Repo & date filters** | Select individual repos or all; presets for 7d, 30d, 90d, 1y, all time, or custom range |

---

## Tech Stack

| Technology | Role |
|---|---|
| **Python** | Core language for the collector and dashboard |
| **Streamlit** | Interactive web dashboard with dark/neon UI |
| **Plotly** | Charts and data visualizations |
| **PostgreSQL (Supabase)** | Persistent storage for all historical data |
| **GitHub API (PyGithub)** | Source of traffic, commit, star, and contributor data |
| **GitHub Actions** | Scheduled workflow that runs the collector every 6 hours |

---

## Architecture

```
┌─────────────────────────────────────┐
│         GitHub Actions              │
│   Scheduled collector (6h cron)     │
│   python -m repoauraapp.collector   │
└─────────────────┬───────────────────┘
                  │ GitHub API
┌─────────────────▼───────────────────┐
│         Supabase PostgreSQL         │
│   traffic_views, traffic_clones,    │
│   commit_activity, star_stats, …    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│      Streamlit Community Cloud      │
│   Password-protected dashboard      │
│   repoauraapp/dashboard.py          │
└─────────────────────────────────────┘
```

---

## Setup

### Local Development

#### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (free tier)
- A GitHub Personal Access Token with `repo` and `read:user` scopes

#### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/GeckoLogic/repo-aura.git
   cd repo-aura
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[app]"
   ```
   This installs the `repoauraapp` package in editable mode with all dependencies, including Streamlit and Plotly. Using a virtual environment is recommended.

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Then fill in your values:
   ```env
   # Direct connection (default — requires IPv6 support)
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

   # Transaction Pooler (use this if your network does not support IPv6)
   # DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

   GH_TOKEN=ghp_yourtoken
   GH_USERNAME=yourusername
   EXCLUDED_REPOS=repo-to-skip,another-repo
   HIDDEN_REPOS=private-repo-hide-from-ui
   DASHBOARD_PASSWORD=yourpassword
   ```
   > **Note:** Supabase offers two connection methods under **Settings → Database → Connection string**.
   > The **Direct connection** uses IPv6 and may not work on all local networks or ISPs.
   > If you see connection timeouts, switch to the **Transaction Pooler** string instead — the URL format differs slightly (the project ref is appended to the username, and the port is `6543`).

4. Initialise the database schema:
   ```bash
   python scripts/init_db.py
   ```

5. Run the collector to populate initial data:
   ```bash
   python -m repoauraapp.collector
   ```

6. Start the dashboard:
   ```bash
   streamlit run repoauraapp/dashboard.py
   ```

---

### Remote Deployment

#### Prerequisites

- A [Supabase](https://supabase.com) project with the schema already initialised (see Local Development step 4)
- This repository pushed to GitHub
- A [Streamlit Community Cloud](https://streamlit.io/cloud) account (free, no credit card required)
- A GitHub Personal Access Token with `repo` and `read:user` scopes
- A GitHub account (for Actions — free for public and private repos)

#### Deployment

**Step 1: Deploy the dashboard to Streamlit Community Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app**, select this repo, and set the main file path to `repoauraapp/dashboard.py`
3. Under **Advanced settings → Secrets**, add:
   ```toml
   DATABASE_URL = "your-supabase-connection-string"
   HIDDEN_REPOS = "private-repo-hide-from-ui"
   DASHBOARD_PASSWORD = "yourpassword"
   ```
4. Click **Deploy** — Streamlit Cloud will install dependencies from `pyproject.toml` automatically

**Step 2: Set up the GitHub Actions collector**

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Add the following repository secrets:
   - `DATABASE_URL` — your Supabase connection string
   - `GH_TOKEN` — your GitHub PAT
   - `GH_USERNAME` — your GitHub username
   - `EXCLUDED_REPOS` — comma-separated repo names to skip (optional)
3. The workflow at `.github/workflows/collect.yml` runs automatically every 6 hours
4. To trigger a manual run: go to **Actions → Collect GitHub Stats → Run workflow**

**Step 3: Verify**

- Open the Streamlit Cloud app URL and log in with your `DASHBOARD_PASSWORD`
- Check the **Actions** tab in your GitHub repo after the first scheduled run to confirm data is being collected

---

## Configuration

| Variable | Required | Required by | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | Dashboard + Collector | Supabase PostgreSQL connection string |
| `GH_TOKEN` | Yes | Collector | GitHub PAT with `repo` + `read:user` scopes |
| `GH_USERNAME` | Yes | Collector | GitHub username to enumerate repos |
| `EXCLUDED_REPOS` | No | Collector | Comma-separated repo names to skip during collection |
| `HIDDEN_REPOS` | No | Dashboard | Comma-separated repo names to hide from the UI |
| `DASHBOARD_PASSWORD` | No | Dashboard | Password for the login gate (leave blank to disable) |

---

## Project Structure

```
repo-aura/
├── repoauraapp/
│   ├── collector.py      # Fetches data from the GitHub API and upserts into the DB
│   ├── dashboard.py      # Streamlit dashboard
│   ├── db.py             # Database helpers (upserts and queries)
│   └── config.py         # Environment variable loading
├── scripts/
│   └── init_db.py        # Creates the database schema
├── .github/
│   └── workflows/
│       └── collect.yml   # Scheduled GitHub Actions collector
├── .env.example          # Environment variable template
└── pyproject.toml        # Package definition and dependencies
```

---

## Scripts

```bash
streamlit run repoauraapp/dashboard.py   # Start the dashboard locally
python -m repoauraapp.collector          # Run the collector manually
python scripts/init_db.py               # Initialise the database schema
```
