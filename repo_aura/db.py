import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from datetime import date, datetime
from repo_aura.config import DATABASE_URL


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Upserts (called by collector)
# ---------------------------------------------------------------------------

def upsert_views(repo: str, rows: list[dict]):
    """rows: [{'date': date, 'total': int, 'uniques': int}]"""
    if not rows:
        return
    sql = """
        INSERT INTO traffic_views (repo, date, total_views, unique_visitors)
        VALUES %s
        ON CONFLICT (repo, date) DO UPDATE
            SET total_views = EXCLUDED.total_views,
                unique_visitors = EXCLUDED.unique_visitors,
                collected_at = NOW()
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, sql, [(repo, r["date"], r["total"], r["uniques"]) for r in rows]
            )


def upsert_clones(repo: str, rows: list[dict]):
    """rows: [{'date': date, 'total': int, 'uniques': int}]"""
    if not rows:
        return
    sql = """
        INSERT INTO traffic_clones (repo, date, total_clones, unique_cloners)
        VALUES %s
        ON CONFLICT (repo, date) DO UPDATE
            SET total_clones = EXCLUDED.total_clones,
                unique_cloners = EXCLUDED.unique_cloners,
                collected_at = NOW()
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, sql, [(repo, r["date"], r["total"], r["uniques"]) for r in rows]
            )


def upsert_referrers(repo: str, rows: list[dict]):
    """rows: [{'referrer': str, 'total': int, 'uniques': int}]"""
    if not rows:
        return
    sql = """
        INSERT INTO referrers (repo, referrer, total_count, unique_count)
        VALUES %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, sql, [(repo, r["referrer"], r["total"], r["uniques"]) for r in rows]
            )


def upsert_popular_paths(repo: str, rows: list[dict]):
    """rows: [{'path': str, 'total': int, 'uniques': int}]"""
    if not rows:
        return
    sql = """
        INSERT INTO popular_paths (repo, path, total_count, unique_count)
        VALUES %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, sql, [(repo, r["path"], r["total"], r["uniques"]) for r in rows]
            )


def upsert_commit_activity(repo: str, rows: list[dict]):
    """rows: [{'week_start': date, 'total': int, 'additions': int, 'deletions': int}]"""
    if not rows:
        return
    sql = """
        INSERT INTO commit_activity (repo, week_start, total_commits, additions, deletions)
        VALUES %s
        ON CONFLICT (repo, week_start) DO UPDATE
            SET total_commits = EXCLUDED.total_commits,
                additions = EXCLUDED.additions,
                deletions = EXCLUDED.deletions
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, sql,
                [(repo, r["week_start"], r["total"], r["additions"], r["deletions"]) for r in rows]
            )


def upsert_contributors(repo: str, rows: list[dict]):
    """rows: [{'author': str, 'total': int}]"""
    if not rows:
        return
    sql = """
        INSERT INTO contributors (repo, author, total_commits)
        VALUES %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, sql, [(repo, r["author"], r["total"]) for r in rows]
            )


def upsert_star_stats(repo: str, snapshot_date: date, stars: int):
    sql = """
        INSERT INTO star_stats (repo, snapshot_date, stars)
        VALUES (%s, %s, %s)
        ON CONFLICT (repo, snapshot_date) DO UPDATE
            SET stars = EXCLUDED.stars
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (repo, snapshot_date, stars))


def upsert_issue_pr_stats(repo: str, snapshot_date: date, open_issues: int,
                           closed_issues: int, open_prs: int, merged_prs: int):
    sql = """
        INSERT INTO issue_pr_stats
            (repo, snapshot_date, open_issues, closed_issues, open_prs, merged_prs)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (repo, snapshot_date) DO UPDATE
            SET open_issues = EXCLUDED.open_issues,
                closed_issues = EXCLUDED.closed_issues,
                open_prs = EXCLUDED.open_prs,
                merged_prs = EXCLUDED.merged_prs
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (repo, snapshot_date, open_issues, closed_issues, open_prs, merged_prs))


# ---------------------------------------------------------------------------
# Queries (called by dashboard)
# ---------------------------------------------------------------------------

def _fetchall_df(sql: str, params=None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def get_views(repos: list[str], start: date, end: date) -> list[dict]:
    sql = """
        SELECT repo, date, total_views, unique_visitors
        FROM traffic_views
        WHERE repo = ANY(%s) AND date BETWEEN %s AND %s
        ORDER BY date
    """
    return _fetchall_df(sql, (repos, start, end))


def get_clones(repos: list[str], start: date, end: date) -> list[dict]:
    sql = """
        SELECT repo, date, total_clones, unique_cloners
        FROM traffic_clones
        WHERE repo = ANY(%s) AND date BETWEEN %s AND %s
        ORDER BY date
    """
    return _fetchall_df(sql, (repos, start, end))


def get_commit_activity(repos: list[str], start: date, end: date) -> list[dict]:
    sql = """
        SELECT repo, week_start, total_commits, additions, deletions
        FROM commit_activity
        WHERE repo = ANY(%s) AND week_start BETWEEN %s AND %s
        ORDER BY week_start
    """
    return _fetchall_df(sql, (repos, start, end))


def get_star_stats(repos: list[str], start: date, end: date) -> list[dict]:
    sql = """
        SELECT repo, snapshot_date, stars
        FROM star_stats
        WHERE repo = ANY(%s) AND snapshot_date BETWEEN %s AND %s
        ORDER BY snapshot_date
    """
    return _fetchall_df(sql, (repos, start, end))


def get_issue_pr_stats(repos: list[str], start: date, end: date) -> list[dict]:
    sql = """
        SELECT repo, snapshot_date, open_issues, closed_issues, open_prs, merged_prs
        FROM issue_pr_stats
        WHERE repo = ANY(%s) AND snapshot_date BETWEEN %s AND %s
        ORDER BY snapshot_date
    """
    return _fetchall_df(sql, (repos, start, end))


def get_referrers(repos: list[str]) -> list[dict]:
    """Returns the most recent snapshot of referrers for the given repos."""
    sql = """
        SELECT DISTINCT ON (repo, referrer) repo, referrer, total_count, unique_count, collected_at
        FROM referrers
        WHERE repo = ANY(%s)
        ORDER BY repo, referrer, collected_at DESC
    """
    return _fetchall_df(sql, (repos,))


def get_popular_paths(repos: list[str]) -> list[dict]:
    """Returns the most recent snapshot of popular paths for the given repos."""
    sql = """
        SELECT DISTINCT ON (repo, path) repo, path, total_count, unique_count, collected_at
        FROM popular_paths
        WHERE repo = ANY(%s)
        ORDER BY repo, path, collected_at DESC
    """
    return _fetchall_df(sql, (repos,))


def get_contributors(repos: list[str]) -> list[dict]:
    """Returns the most recent snapshot of contributors for the given repos."""
    sql = """
        SELECT DISTINCT ON (repo, author) repo, author, total_commits, collected_at
        FROM contributors
        WHERE repo = ANY(%s)
        ORDER BY repo, author, collected_at DESC
    """
    return _fetchall_df(sql, (repos,))


def get_all_repos() -> list[str]:
    sql = "SELECT DISTINCT repo FROM traffic_views ORDER BY repo"
    rows = _fetchall_df(sql)
    return [r["repo"] for r in rows]
