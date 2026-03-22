import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from repoauraapp import config, db

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Repo Aura",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme: dark background + neon glow palette
# ---------------------------------------------------------------------------

NEON_COLORS = [
    "#00f5ff",  # cyan
    "#ff00ff",  # magenta
    "#39ff14",  # neon green
    "#ff6600",  # orange
    "#bf5fff",  # purple
    "#ffff00",  # yellow
]

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0d0d0d;
        color: #999999;
    }
    [data-testid="stSidebar"] {
        background-color: #111111;
    }
    h1, h2, h3, h4 {
        color: #00f5ff;
        text-shadow: 0 0 8px #00f5ff66;
    }
    [data-testid="metric-container"] {
        background: #1a1a1a;
        border: 1px solid #00f5ff44;
        border-radius: 8px;
        padding: 12px;
    }
    div[data-baseweb="tab-list"] button {
        color: #aaa;
    }
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #00f5ff;
        border-bottom: 2px solid #00f5ff;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #2a2a2a !important;
        border-color: #444 !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #cc0000 !important;
        border-color: #cc0000 !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button {
        color: #aaaaaa !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
        fill: #aaaaaa !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] svg {
        fill: #aaaaaa !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] input {
        color: #999999 !important;
    }
    .block-container {
        padding-top: 2.5rem !important;
    }
    /* Override Streamlit white text throughout */
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stTextInput"] input,
    [data-testid="stForm"] label,
    .stButton button,
    [data-baseweb="input"] input,
    [data-testid="stCaption"] {
        color: #aaaaaa !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d0d0d",
    plot_bgcolor="#111111",
    font=dict(color="#999999"),
    title=dict(font=dict(color="#aaaaaa")),
    xaxis=dict(gridcolor="#1e1e1e", zerolinecolor="#1e1e1e", tickformat="%b %d"),
    yaxis=dict(gridcolor="#1e1e1e", zerolinecolor="#1e1e1e"),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(color="#555555", size=13), title=dict(font=dict(color="#aaaaaa"))),
    margin=dict(t=40, b=40, l=40, r=20),
)


def apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Password gate
# ---------------------------------------------------------------------------

def check_password() -> bool:
    if not config.DASHBOARD_PASSWORD:
        return True
    if st.session_state.get("authenticated"):
        return True

    with st.form("login"):
        st.markdown("## Repo Aura")
        st.markdown("Enter password to continue.")
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if pw == config.DASHBOARD_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar: repo + date filters
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    '<h2 style="color:#999999; text-shadow: 0 0 12px #00f5ff, 0 0 24px #00f5ff88; letter-spacing: 2px;">Repo Aura</h2>',
    unsafe_allow_html=True,
)

all_repos = db.get_all_repos()
visible_repos = [r for r in all_repos if r not in config.HIDDEN_REPOS]

if not visible_repos:
    st.warning("No data yet. Run the collector to populate the database.")
    st.stop()

repo_options = ["All repos"] + sorted(visible_repos)
selected = st.sidebar.multiselect(
    "Repositories",
    options=repo_options,
    default=["All repos"],
)

if not selected or "All repos" in selected:
    repos = visible_repos
else:
    repos = selected

today = date.today()
preset = st.sidebar.radio(
    "Time period",
    ["7 days", "30 days", "90 days", "1 year", "All time", "Custom"],
    index=1,
)

if preset == "Custom":
    col1, col2 = st.sidebar.columns(2)
    start_date = col1.date_input("From", value=today - timedelta(days=30))
    end_date = col2.date_input("To", value=today)
elif preset == "All time":
    start_date = date(2000, 1, 1)
    end_date = today
else:
    days_map = {"7 days": 7, "30 days": 30, "90 days": 90, "1 year": 365}
    start_date = today - timedelta(days=days_map[preset])
    end_date = today

components.html("""
<script>
(function() {
    function styleRadios() {
        const doc = window.parent.document;
        doc.querySelectorAll('[data-baseweb="radio"] [role="radio"]').forEach(el => {
            const checked = el.getAttribute('aria-checked') === 'true';
            el.style.setProperty('border-color', '#555555', 'important');
            el.style.setProperty('background-color', 'transparent', 'important');
            el.querySelectorAll('div').forEach((d, i) => {
                if (i === 0) {
                    d.style.setProperty('background-color', checked ? '#ff3333' : 'transparent', 'important');
                    d.style.setProperty('border-color', 'transparent', 'important');
                }
            });
        });
    }
    styleRadios();
    new MutationObserver(styleRadios).observe(window.parent.document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['aria-checked'] });
})();
</script>
""", height=0)

st.sidebar.markdown("---")
period_label = "all time" if preset == "All time" else f"{start_date} → {end_date}"
st.sidebar.caption(f"Showing {len(repos)} repo(s) · {period_label}")

# ---------------------------------------------------------------------------
# Helper: empty-state chart
# ---------------------------------------------------------------------------

def empty_chart(msg: str = "No data for selected period.") -> None:
    st.info(msg)


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown("# Repo Aura")

tab_traffic, tab_clones, tab_commits, tab_issues, tab_stars, tab_referrers, tab_contributors = st.tabs(
    ["Traffic", "Clones", "Commits", "Issues & PRs", "Stars", "Referrers", "Contributors"]
)

# ---------------------------------------------------------------------------
# Tab: Traffic (views)
# ---------------------------------------------------------------------------

with tab_traffic:
    st.markdown("### Page Views")
    data = db.get_views(repos, start_date, end_date)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        col1, col2 = st.columns(2)
        col1.metric("Total Views", int(df["total_views"].sum()))
        col2.metric("Unique Visitors", int(df["unique_visitors"].sum()))

        fig = px.line(
            df, x="date", y="total_views", color="repo",
            title="Views over time",
            labels={"total_views": "Views", "date": "Date"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig), width='stretch')

        fig2 = px.line(
            df, x="date", y="unique_visitors", color="repo",
            title="Unique visitors over time",
            labels={"unique_visitors": "Unique Visitors", "date": "Date"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig2), width='stretch')

# ---------------------------------------------------------------------------
# Tab: Clones
# ---------------------------------------------------------------------------

with tab_clones:
    st.markdown("### Clones")
    data = db.get_clones(repos, start_date, end_date)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        col1, col2 = st.columns(2)
        col1.metric("Total Clones", int(df["total_clones"].sum()))
        col2.metric("Unique Cloners", int(df["unique_cloners"].sum()))

        fig = px.line(
            df, x="date", y="total_clones", color="repo",
            title="Clones over time",
            labels={"total_clones": "Clones", "date": "Date"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig), width='stretch')

        fig2 = px.line(
            df, x="date", y="unique_cloners", color="repo",
            title="Unique cloners over time",
            labels={"unique_cloners": "Unique Cloners", "date": "Date"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig2), width='stretch')

# ---------------------------------------------------------------------------
# Tab: Commits
# ---------------------------------------------------------------------------

with tab_commits:
    st.markdown("### Commit Activity")
    data = db.get_commit_activity(repos, start_date, end_date)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df["week_start"] = pd.to_datetime(df["week_start"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Commits", int(df["total_commits"].sum()))
        col2.metric("Additions", int(df["additions"].sum()))
        col3.metric("Deletions", int(df["deletions"].sum()))

        fig = px.line(
            df, x="week_start", y="total_commits", color="repo",
            title="Commits over time",
            labels={"total_commits": "Commits", "week_start": "Week"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig), width='stretch')

        fig = px.bar(
            df, x="week_start", y="total_commits", color="repo",
            title="Weekly commits",
            labels={"total_commits": "Commits", "week_start": "Week"},
            color_discrete_sequence=NEON_COLORS,
            barmode="group",
        )
        st.plotly_chart(apply_theme(fig), width='stretch')

        fig_add = px.line(
            df, x="week_start", y="additions", color="repo",
            title="Lines added over time",
            labels={"additions": "Lines Added", "week_start": "Week"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig_add), width='stretch')

        fig_del = px.line(
            df, x="week_start", y="deletions", color="repo",
            title="Lines removed over time",
            labels={"deletions": "Lines Removed", "week_start": "Week"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig_del), width='stretch')

        fig3 = px.bar(
            df, x="week_start", y=["additions", "deletions"], color="repo",
            title="Additions & Deletions per week",
            labels={"week_start": "Week", "value": "Lines"},
            color_discrete_sequence=NEON_COLORS,
            barmode="group",
        )
        st.plotly_chart(apply_theme(fig3), width='stretch')

# ---------------------------------------------------------------------------
# Tab: Issues & PRs
# ---------------------------------------------------------------------------

with tab_issues:
    st.markdown("### Issues & Pull Requests")
    data = db.get_issue_pr_stats(repos, start_date, end_date)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])

        latest = df.sort_values("snapshot_date").groupby("repo").last().reset_index()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Open Issues", int(latest["open_issues"].sum()))
        col2.metric("Closed Issues", int(latest["closed_issues"].sum()))
        col3.metric("Open PRs", int(latest["open_prs"].sum()))
        col4.metric("Merged PRs", int(latest["merged_prs"].sum()))

        fig = px.line(
            df, x="snapshot_date", y=["open_issues", "closed_issues"], color="repo",
            title="Issues over time",
            labels={"snapshot_date": "Date", "value": "Count"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig), width='stretch')

        fig2 = px.line(
            df, x="snapshot_date", y=["open_prs", "merged_prs"], color="repo",
            title="Pull requests over time",
            labels={"snapshot_date": "Date", "value": "Count"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig2), width='stretch')

# ---------------------------------------------------------------------------
# Tab: Stars
# ---------------------------------------------------------------------------

with tab_stars:
    st.markdown("### Stars")
    data = db.get_star_stats(repos, start_date, end_date)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])

        latest = df.sort_values("snapshot_date").groupby("repo").last().reset_index()
        st.metric("Total Stars", int(latest["stars"].sum()))

        fig = px.line(
            df, x="snapshot_date", y="stars", color="repo",
            title="Stars over time",
            labels={"stars": "Stars", "snapshot_date": "Date"},
            color_discrete_sequence=NEON_COLORS,
        )
        st.plotly_chart(apply_theme(fig), width='stretch')

# ---------------------------------------------------------------------------
# Tab: Referrers
# ---------------------------------------------------------------------------

with tab_referrers:
    st.markdown("### Top Referring Sites")
    st.caption("Most recent snapshot per repository.")
    data = db.get_referrers(repos)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df = df.sort_values("total_count", ascending=False)

        fig = px.bar(
            df, x="referrer", y="total_count", color="repo",
            title="Top referrers",
            labels={"total_count": "Views", "referrer": "Referrer"},
            color_discrete_sequence=NEON_COLORS,
            barmode="group",
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(apply_theme(fig), width='stretch')

        st.dataframe(
            df[["repo", "referrer", "total_count", "unique_count"]].rename(columns={
                "repo": "Repo", "referrer": "Referrer",
                "total_count": "Views", "unique_count": "Unique"
            }),
            width='stretch',
            hide_index=True,
        )

# ---------------------------------------------------------------------------
# Tab: Contributors
# ---------------------------------------------------------------------------

with tab_contributors:
    st.markdown("### Contributors")
    st.caption("Most recent snapshot per repository.")
    data = db.get_contributors(repos)
    if not data:
        empty_chart()
    else:
        df = pd.DataFrame(data)
        df = df.sort_values("total_commits", ascending=False)

        fig = px.bar(
            df, x="author", y="total_commits", color="repo",
            title="Commits by contributor",
            labels={"total_commits": "Commits", "author": "Author"},
            color_discrete_sequence=NEON_COLORS,
            barmode="group",
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(apply_theme(fig), width='stretch')

        st.dataframe(
            df[["repo", "author", "total_commits"]].rename(columns={
                "repo": "Repo", "author": "Author", "total_commits": "Commits"
            }),
            width='stretch',
            hide_index=True,
        )
