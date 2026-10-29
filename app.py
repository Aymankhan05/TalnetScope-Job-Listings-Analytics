
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
st.markdown("""
<style>
[data-testid="stSidebar"] {
    color: white;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "processed" / "job_listings_processed.csv"

st.set_page_config(
    page_title="TalentScope | Job Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Professional dashboard styling ----------
st.markdown(
    """
    <style>
    .stApp {
        background: #0b1120;
        color: #e5edf7;
    }
    [data-testid="stSidebar"] {
        background: #111a2c;
        border-right: 1px solid #26344a;
    }
    [data-testid="stMetric"] {
        background: #152238;
        border: 1px solid #293a52;
        padding: 18px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] {
        color: #9fb1c9;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9;
    }
    h1, h2, h3 {
        color: #f1f5f9;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #293a52;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path: str, modified: float) -> pd.DataFrame:
    """Load processed data; cache refreshes when the file changes."""
    del modified
    return pd.read_csv(path)


def clean_filter_values(series: pd.Series) -> list[str]:
    """Return sorted, non-empty filter choices."""
    values = series.dropna().astype(str).str.strip()
    return sorted(value for value in values.unique() if value)


def main() -> None:
    st.markdown(
    "<h1 style='color:#FFFFFF;'>📊 TalentScope</h1>",
    unsafe_allow_html=True,
)
    st.caption("Job Market Insights • Explore listings, employers, and locations")
    
    if not DATA_FILE.exists():
        st.error(
            "Processed dataset not found. Run "
            "`python run_pipeline.py` from your project root first."
        )
        st.stop()

    try:
        df = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Unable to load the dataset: {error}")
        st.stop()

    required = {"job_title", "company_name", "location"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {', '.join(sorted(missing))}")
        st.stop()

    # Normalize core fields for consistent filters and charts.
    for column in ["job_title", "company_name", "location"]:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()
        df.loc[df[column].eq(""), column] = "Unknown"

    # ---------- Sidebar filters ----------
    st.sidebar.title("Explore the data")
    st.sidebar.caption("Filters apply to all charts and the results table.")

    query = st.sidebar.text_input(
        "Search jobs",
        placeholder="e.g. Python, engineer, manager",
    ).strip().casefold()

    titles = clean_filter_values(df["job_title"])
    companies = clean_filter_values(df["company_name"])
    locations = clean_filter_values(df["location"])

    selected_titles = st.sidebar.multiselect(
        "Job titles", titles, placeholder="All job titles"
    )
    selected_companies = st.sidebar.multiselect(
        "Companies", companies, placeholder="All companies"
    )
    selected_locations = st.sidebar.multiselect(
        "Locations", locations, placeholder="All locations"
    )

    filtered = df.copy()

    if query:
        searchable = [
            c for c in [
                "job_title", "company_name", "location",
                "job_description",
            ] if c in filtered.columns
        ]
        mask = filtered[searchable].fillna("").astype(str).apply(
            lambda col: col.str.casefold().str.contains(
                query, regex=False
            )
        ).any(axis=1)
        filtered = filtered[mask]

    if selected_titles:
        filtered = filtered[filtered["job_title"].isin(selected_titles)]
    if selected_companies:
        filtered = filtered[
            filtered["company_name"].isin(selected_companies)
        ]
    if selected_locations:
        filtered = filtered[filtered["location"].isin(selected_locations)]

    st.sidebar.divider()
    st.sidebar.write(f"Matching listings: **{len(filtered):,}**")
    if st.sidebar.button("Reset all filters", use_container_width=True):
        st.rerun()

    # ---------- KPI cards ----------
    total = len(filtered)
    unique_titles = filtered["job_title"].nunique()
    unique_companies = filtered["company_name"].nunique()
    unique_locations = filtered["location"].nunique()

    st.subheader("📈 Overview at a Glance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Job listings", f"{total:,}")
    c2.metric("Unique titles", f"{unique_titles:,}")
    c3.metric("Companies", f"{unique_companies:,}")
    c4.metric("Locations", f"{unique_locations:,}")

    st.divider()

    if filtered.empty:
        st.warning("No jobs match these filters. Adjust your search.")
        st.stop()

    # ---------- Chart-ready summaries ----------
    title_counts = (
        filtered["job_title"].value_counts().head(10)
        .rename_axis("Job title").reset_index(name="Listings")
    )
    company_counts = (
        filtered["company_name"].value_counts().head(10)
        .rename_axis("Company").reset_index(name="Listings")
    )
    location_counts = (
        filtered["location"].value_counts().head(10)
        .rename_axis("Location").reset_index(name="Listings")
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Most common job titles")
        fig = px.bar(
            title_counts.sort_values("Listings"),
            x="Listings",
            y="Job title",
            orientation="h",
            text="Listings",
            color="Listings",
            color_continuous_scale=["#2563eb", "#38bdf8"],
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            height=430,
            margin=dict(l=10, r=15, t=20, b=10),
            coloraxis_showscale=False,
            xaxis_title="Number of listings",
            yaxis_title="",
            font=dict(color="#e5e7eb"),
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("📊 Job Market Analytics")
        st.subheader("Job title distribution")

    pie_data = title_counts.nlargest(6, "Listings").copy()

    other_count = int(title_counts["Listings"].sum() - pie_data["Listings"].sum())

    if other_count > 0:
        other_row = pd.DataFrame(
            [{"Job title": "Other job titles", "Listings": other_count}]
        )
        pie_data = pd.concat([pie_data, other_row], ignore_index=True)

    fig = px.pie(
        pie_data,
        names="Job title",
        values="Listings",
        hole=0.45,
        title="Share of listings by job title",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        height=450,
        margin=dict(l=10, r=10, t=60, b=10),
        legend_title_text="Job title",
        legend=dict(
        font=dict(color="#FFFFFF", size=14),
        title=dict(font=dict(color="#FFFFFF", size=15)),
        ),
        font=dict(color="#e5e7eb"),
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(color="#111827", size=14),
        marker=dict(line=dict(color="#0e1117", width=2)),
        hovertemplate="%{label}<br>Listings: %{value}<br>Share: %{percent}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Employers with the most listings")
        fig = px.bar(
            company_counts.sort_values("Listings"),
            x="Listings",
            y="Company",
            orientation="h",
            text="Listings",
            color="Listings",
            color_continuous_scale=["#0f766e", "#5eead4"],
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            height=430,
            margin=dict(l=10, r=15, t=20, b=10),
            coloraxis_showscale=False,
            xaxis_title="Number of listings",
            yaxis_title="",
            font=dict(color="#e5e7eb"),
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Listings by location")
    fig = px.bar(
        location_counts.sort_values("Listings"),
        x="Listings",
        y="Location",
        orientation="h",
        text="Listings",
        color="Listings",
        color_continuous_scale=["#7c3aed", "#c4b5fd"],
        
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        height=430,
        margin=dict(l=10, r=15, t=20, b=10),
        coloraxis_showscale=False,
        xaxis_title="Number of listings",
        yaxis_title="",
        font=dict(color="#ffffff", size=16, family="Arial"),
        xaxis=dict(
            title_font=dict(color="#ffffff", size=15),
            tickfont=dict(color="#ffffff", size=14),
            gridcolor="#d1d5db",
        ),
        yaxis=dict(
            title_font=dict(color="#ffffff", size=15),
            tickfont=dict(color="#ffffff", size=14),
        ),
    )
    fig.update_traces(
    textposition="outside",
    cliponaxis=False,
    textfont_color="white"
)
    
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Location distribution")

    pie_locations = location_counts.nlargest(6, "Listings").copy()

    other_locations = int(
        location_counts["Listings"].sum() - pie_locations["Listings"].sum()
    )

    if other_locations > 0:
        other_row = pd.DataFrame(
            [{"Location": "Other locations", "Listings": other_locations}]
        )
        pie_locations = pd.concat(
            [pie_locations, other_row], ignore_index=True
        )

    fig = px.pie(
        pie_locations,
        names="Location",
        values="Listings",
        hole=0.45,
        title="Share of listings by location",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        height=430,
        margin=dict(l=10, r=15, t=20, b=10),
        coloraxis_showscale=False,
        xaxis_title="Number of listings",
        yaxis_title="",
        font=dict(color="#FFFFFF", size=13),
        legend=dict(
        font=dict(color="#FFFFFF", size=14),
        title=dict(font=dict(color="#FFFFFF", size=15)),
        ),
    )

    fig.update_traces(
    textposition="inside",
    textinfo="percent",
    textfont=dict(
        color="#000000",
        size=18,
        family="Arial"
    ),
)

    st.plotly_chart(fig, use_container_width=True)

    # ---------- Data quality ----------
    st.divider()
    st.subheader("🔍 Data Quality Audit")

    q1, q2, q3 = st.columns(3)
    q1.metric("Missing cells", f"{int(filtered.isna().sum().sum()):,}")
    q2.metric("Duplicate rows", f"{int(filtered.duplicated().sum()):,}")
    q3.metric("Total columns", f"{len(filtered.columns):,}")

    st.caption(
        "A missing-value count of zero does not guarantee that every "
        "field is meaningful. Review the source data and application links."
    )

    # ---------- Searchable results and export ----------
    st.divider()
    st.subheader("📋 Job Listing Explorer")
    st.caption("Inspect the filtered records or download them as CSV.")

    display_columns = [
        c for c in [
            "job_title", "company_name", "location",
            "job_description", "apply_link",
            "description_length", "title_word_count",
        ] if c in filtered.columns
    ]

    st.dataframe(
    filtered[display_columns].style.set_properties(
        **{"color": "white", "background-color": "#0e1117"}
    ),
    use_container_width=True,
    hide_index=True,
    height=420,
)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇ Download filtered listings (CSV)",
        data=csv_bytes,
        file_name="filtered_job_listings.csv",
        mime="text/csv",
        use_container_width=False,
    )

    st.caption(
        "TalentScope · Job Listings Analytics · "
        "Source: practice job-listings dataset"
    )


if __name__ == "__main__":
    main()