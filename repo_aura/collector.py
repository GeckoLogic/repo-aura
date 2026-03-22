"""
Data collector — fetches GitHub stats and upserts them into the database.
Run standalone:  python -m repo_aura.collector
"""

import logging
from datetime import date, datetime, timezone
from github import Github, GithubException
from repo_aura import config, db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def collect_repo(repo) -> None:
    name = repo.full_name
    log.info("Collecting %s", name)

    # --- Traffic: views ---
    try:
        traffic = repo.get_views_traffic(per="day")
        views = traffic.views if hasattr(traffic, "views") else traffic.get("views", [])
        rows = [
            {"date": v.timestamp.date(), "total": v.count, "uniques": v.uniques}
            for v in views
        ]
        db.upsert_views(name, rows)
        log.info("  views: %d rows", len(rows))
    except GithubException as e:
        log.warning("  views failed: %s", e)

    # --- Traffic: clones ---
    try:
        traffic = repo.get_clones_traffic(per="day")
        clones = traffic.clones if hasattr(traffic, "clones") else traffic.get("clones", [])
        rows = [
            {"date": c.timestamp.date(), "total": c.count, "uniques": c.uniques}
            for c in clones
        ]
        db.upsert_clones(name, rows)
        log.info("  clones: %d rows", len(rows))
    except GithubException as e:
        log.warning("  clones failed: %s", e)

    # --- Referrers ---
    try:
        referrers = repo.get_top_referrers()
        rows = [
            {"referrer": r.referrer, "total": r.count, "uniques": r.uniques}
            for r in referrers
        ]
        db.upsert_referrers(name, rows)
        log.info("  referrers: %d rows", len(rows))
    except GithubException as e:
        log.warning("  referrers failed: %s", e)

    # --- Popular paths ---
    try:
        paths = repo.get_top_paths()
        rows = [
            {"path": p.path, "total": p.count, "uniques": p.uniques}
            for p in paths
        ]
        db.upsert_popular_paths(name, rows)
        log.info("  popular paths: %d rows", len(rows))
    except GithubException as e:
        log.warning("  popular paths failed: %s", e)

    # --- Commit activity (weekly) ---
    try:
        activity = repo.get_stats_commit_activity()
        if activity:
            def _to_date(val):
                if isinstance(val, datetime):
                    return val.date()
                return datetime.fromtimestamp(val, tz=timezone.utc).date()

            rows = [
                {
                    "week_start": _to_date(w.week),
                    "total": w.total,
                    "additions": 0,
                    "deletions": 0,
                }
                for w in activity
            ]
            # Enrich with additions/deletions from code_frequency stats
            try:
                freq = repo.get_stats_code_frequency()
                if freq:
                    freq_map = {
                        _to_date(f.week): f
                        for f in freq
                    }
                    for row in rows:
                        f = freq_map.get(row["week_start"])
                        if f:
                            row["additions"] = f.additions
                            row["deletions"] = abs(f.deletions)
            except GithubException:
                pass
            db.upsert_commit_activity(name, rows)
            log.info("  commit activity: %d rows", len(rows))
    except GithubException as e:
        log.warning("  commit activity failed: %s", e)

    # --- Contributors ---
    try:
        contribs = repo.get_stats_contributors()
        if contribs:
            rows = [
                {"author": c.author.login if c.author else "unknown", "total": c.total}
                for c in contribs
            ]
            db.upsert_contributors(name, rows)
            log.info("  contributors: %d rows", len(rows))
    except GithubException as e:
        log.warning("  contributors failed: %s", e)

    # --- Issues & PRs snapshot ---
    try:
        today = date.today()
        open_issues = repo.open_issues_count
        closed_issues = repo.get_issues(state="closed").totalCount
        open_prs = repo.get_pulls(state="open").totalCount
        merged_prs = repo.get_pulls(state="closed").totalCount
        db.upsert_issue_pr_stats(name, today, open_issues, closed_issues, open_prs, merged_prs)
        log.info("  issues/PRs: done")
    except GithubException as e:
        log.warning("  issues/PRs failed: %s", e)


def run() -> None:
    g = Github(config.GITHUB_TOKEN)
    user = g.get_user(config.GITHUB_USERNAME)
    repos = list(user.get_repos(type="owner"))
    log.info("Found %d repos for %s", len(repos), config.GITHUB_USERNAME)

    excluded = set(config.EXCLUDED_REPOS)
    for repo in repos:
        if repo.name in excluded or repo.full_name in excluded:
            log.info("Skipping excluded repo: %s", repo.full_name)
            continue
        try:
            collect_repo(repo)
        except Exception as e:
            log.error("Unexpected error collecting %s: %s", repo.full_name, e)

    log.info("Collection complete.")


if __name__ == "__main__":
    run()
