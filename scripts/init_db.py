"""
One-time database schema initialisation.
Run once after creating your Supabase project:

    python scripts/init_db.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from repoauraapp.config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS traffic_views (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    date DATE NOT NULL,
    total_views INT,
    unique_visitors INT,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repo, date)
);

CREATE TABLE IF NOT EXISTS traffic_clones (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    date DATE NOT NULL,
    total_clones INT,
    unique_cloners INT,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repo, date)
);

CREATE TABLE IF NOT EXISTS referrers (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    referrer TEXT NOT NULL,
    total_count INT,
    unique_count INT,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS popular_paths (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    path TEXT NOT NULL,
    total_count INT,
    unique_count INT,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS commit_activity (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    week_start DATE NOT NULL,
    total_commits INT,
    additions INT,
    deletions INT,
    UNIQUE(repo, week_start)
);

CREATE TABLE IF NOT EXISTS contributors (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    author TEXT NOT NULL,
    total_commits INT,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS issue_pr_stats (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    open_issues INT,
    closed_issues INT,
    open_prs INT,
    merged_prs INT,
    UNIQUE(repo, snapshot_date)
);

CREATE TABLE IF NOT EXISTS star_stats (
    id SERIAL PRIMARY KEY,
    repo TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    stars INT,
    UNIQUE(repo, snapshot_date)
);
"""

if __name__ == "__main__":
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        conn.commit()
        print("Database schema created successfully.")
    finally:
        conn.close()
