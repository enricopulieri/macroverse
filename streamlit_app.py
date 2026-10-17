import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Macroverse — Global Economic Dashboard",
    page_icon="🌍",
    layout="wide",
)

WB_BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "GDP per Capita (USD)": "NY.GDP.PCAP.CD",
    "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation (%)": "FP.CPI.TOTL.ZG",
    "Public Debt (% GDP)": "GC.DOD.TOTL.GD.ZS",
    "Unemployment Rate (%)": "SL.UEM.TOTL.ZS",
    "Life Expectancy (years)": "SP.DYN.LE00.IN",
    "Trade Balance (% GDP)": "NE.RSB.GNFS.ZS",
    "Government Expenditure (% GDP)": "NE.CON.GOVT.ZS",
}

KPI_SET = [
    ("GDP per Capita (USD)", "${:,.0f}"),
    ("Inflation (%)", "{:.1f}%"),
    ("Public Debt (% GDP)", "{:.1f}%"),
    ("Unemployment Rate (%)", "{:.1f}%"),
    ("Life Expectancy (years)", "{:.1f}"),
]

# --------------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading country list...")
def load_countries():
    url = f"{WB_BASE}/country?format=json&per_page=400"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    rows = resp.json()[1]
    data = []
    for r in rows:
        if r["region"]["value"] == "Aggregates":
            continue
        data.append(
            {
                "iso_3": r["id"],
                "country": r["name"],
                "region": r["region"]["value"],
                "income_group": r["incomeLevel"]["value"],
            }
        )
    return pd.DataFrame(data)


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Fetching indicator data...")
def load_indicator(indicator_code, start_year=2000, end_year=2024):
    url = (
        f"{WB_BASE}/country/all/indicator/{indicator_code}"
        f"?format=json&per_page=20000&date={start_year}:{end_year}"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if len(payload) < 2 or payload[1] is None:
        return pd.DataFrame(columns=["iso_3", "year", "value"])
    rows = payload[1]
    data = [
        {"iso_3": r["countryiso3code"], "year": int(r["date"]), "value": r["value"]}
        for r in rows
        if r["countryiso3code"]
    ]
    return pd.DataFrame(data)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def load_all_indicators(countries_df):
    frames = []
    for label, code in INDICATORS.items():
        df_ind = load_indicator(code)
        df_ind["indicator"] = label
        frames.append(df_ind)
    long_df = pd.concat(frames, ignore_index=True)
    merged = countries_df.merge(long_df, on="iso_3", how="left")
    return merged


countries_df = load_countries()
full_df = load_all_indicators(countries_df)

# --------------------------------------------------------------------------
# SIDEBAR - FILTERS
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌍 Macroverse")
    st.caption("Global Economic Dashboard")
    st.divider()

    st.markdown("**YEARS**")
    all_years = list(range(2000, 2025))
    years_selected = st.multiselect(
        "Select years", all_years, default=list(range(2015, 2025)), label_visibility="collapsed"
    )

    st.markdown("**REGIONS**")
    all_regions = sorted(countries_df["region"].dropna().unique())
    regions_selected = st.multiselect(
        "Select regions", all_regions, default=all_regions, label_visibility="collapsed"
    )

    st.markdown("**INCOME LEVELS**")
    all_income = sorted(countries_df["income_group"].dropna().unique())
    income_selected = st.multiselect(
        "Select income levels", all_income, default=all_income, label_visibility="collapsed"
    )

    st.divider()
    st.caption("Source: World Bank Open Data API")

if not years_selected:
    years_selected = all_years
if not regions_selected:
    regions_selected = all_regions
if not income_selected:
    income_selected = all_income

df = full_df[
    full_df["region"].isin(regions_selected)
    & full_df["income_group"].isin(income_selected)
    & full_df["year"].isin(years_selected)
]
latest_year = max(years_selected)
n_countries = df["country"].nunique()

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
st.markdown("## GLOBAL ECONOMIC INTELLIGENCE DASHBOARD")
st.caption(
    f"{n_countries} countries selected · Period: {min(years_selected)}-{max(years_selected)} "
    f"· Latest year: {latest_year}"
)

# --------------------------------------------------------------------------
# KPI ROW
# --------------------------------------------------------------------------
kpi_cols = st.columns(len(KPI_SET))
df_latest = df[df["year"] == latest_year]
df_prev = df[df["year"] == latest_year - 1]

for col, (label, fmt) in zip(kpi_cols, KPI_SET):
    cur_vals = df_latest[df_latest["indicator"] == label]["value"].dropna()
    prev_vals = df_prev[df_prev["indicator"] == label]["value"].dropna()
    cur = cur_vals.mean() if not cur_vals.empty else None
    prev = prev_vals.mean() if not prev_vals.empty else None
    delta = f"{cur - prev:+.1f}" if cur is not None and prev is not None else None
    col.metric(
        label.upper(),
        fmt.format(cur) if cur is not None else "—",
        delta=delta,
    )

st.divider()

# --------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------
tab_map, tab_trends, tab_profile, tab_compare, tab_structure, tab_data = st.tabs(
    ["World Map", "Trends", "Country Profile", "Compare Countries", "Economic Structure", "Data"]
)

# ---- WORLD MAP -------------------------------------------------------
with tab_map:
    c1, c2 = st.columns([3, 1])
    with c1:
        map_indicator = st.selectbox("Indicator to map", list(INDICATORS.keys()), key="map_ind")
    with c2:
        map_year = st.selectbox("Reference year", sorted(years_selected, reverse=True), key="map_year")

    df_map = df[(df["indicator"] == map_indicator) & (df["year"] == map_year)]

    fig_map = px.choropleth(
        df_map,
        locations="iso_3",
        color="value",
        hover_name="country",
        hover_data={"value": True, "region": True, "income_group": True, "iso_3": False},
        color_continuous_scale="Viridis",
        projection="natural earth",
        labels={"value": map_indicator},
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=550)
    st.plotly_chart(fig_map, width="stretch")

# ---- TRENDS ------------------------------------------------------------
with tab_trends:
    trend_indicator = st.selectbox("Indicator", list(INDICATORS.keys()), key="trend_ind")
    default_countries = sorted(df["country"].dropna().unique())[:5]
    trend_countries = st.multiselect(
        "Countries to compare",
        sorted(df["country"].dropna().unique()),
        default=default_countries,
    )

    if trend_countries:
        df_ts = df[(df["indicator"] == trend_indicator) & (df["country"].isin(trend_countries))]
        fig_ts = px.line(
            df_ts.sort_values("year"),
            x="year",
            y="value",
            color="country",
            markers=True,
            labels={"value": trend_indicator, "year": "Year"},
        )
        fig_ts.update_layout(height=480)
        st.plotly_chart(fig_ts, width="stretch")
    else:
        st.info("Select at least one country.")

# ---- COUNTRY PROFILE ----------------------------------------------------
with tab_profile:
    country_sel = st.selectbox(
        "Select a country", sorted(df["country"].dropna().unique()), key="profile_country"
    )
    df_country = df[df["country"] == country_sel]

    profile_cols = st.columns(len(KPI_SET))
    for col, (label, fmt) in zip(profile_cols, KPI_SET):
        vals = df_country[(df_country["indicator"] == label) & (df_country["year"] == latest_year)]["value"]
        val = vals.iloc[0] if not vals.empty and pd.notna(vals.iloc[0]) else None
        col.metric(label.upper(), fmt.format(val) if val is not None else "—")

    st.markdown(f"#### Indicator trends — {country_sel}")
    indicator_pick = st.selectbox("Indicator", list(INDICATORS.keys()), key="profile_ind")
    df_pick = df_country[df_country["indicator"] == indicator_pick].sort_values("year")
    fig_profile = px.area(df_pick, x="year", y="value", labels={"value": indicator_pick, "year": "Year"})
    fig_profile.update_layout(height=400)
    st.plotly_chart(fig_profile, width="stretch")

# ---- COMPARE COUNTRIES ---------------------------------------------------
with tab_compare:
    compare_indicator = st.selectbox("Indicator", list(INDICATORS.keys()), key="compare_ind")
    compare_countries = st.multiselect(
        "Countries to compare",
        sorted(df["country"].dropna().unique()),
        default=sorted(df["country"].dropna().unique())[:8],
        key="compare_countries",
    )

    df_bar = df[
        (df["indicator"] == compare_indicator)
        & (df["year"] == latest_year)
        & (df["country"].isin(compare_countries))
    ].dropna(subset=["value"]).sort_values("value", ascending=False)

    fig_bar = px.bar(
        df_bar, x="country", y="value", color="value",
        color_continuous_scale="Viridis",
        labels={"value": compare_indicator, "country": "Country"},
    )
    fig_bar.update_layout(height=450)
    st.plotly_chart(fig_bar, width="stretch")

# ---- ECONOMIC STRUCTURE ---------------------------------------------------
with tab_structure:
    st.markdown("#### Relationship between two indicators")
    c1, c2 = st.columns(2)
    with c1:
        x_ind = st.selectbox("X-axis indicator", list(INDICATORS.keys()), index=0, key="x_ind")
    with c2:
        y_ind = st.selectbox("Y-axis indicator", list(INDICATORS.keys()), index=2, key="y_ind")

    df_x = df[(df["indicator"] == x_ind) & (df["year"] == latest_year)][["country", "region", "value"]].rename(columns={"value": "x"})
    df_y = df[(df["indicator"] == y_ind) & (df["year"] == latest_year)][["country", "value"]].rename(columns={"value": "y"})
    df_scatter = df_x.merge(df_y, on="country").dropna()

    fig_scatter = px.scatter(
        df_scatter, x="x", y="y", color="region", hover_name="country",
        labels={"x": x_ind, "y": y_ind},
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, width="stretch")

# ---- DATA ------------------------------------------------------------------
with tab_data:
    st.markdown("#### Raw data")
    data_indicator = st.selectbox("Indicator", list(INDICATORS.keys()), key="data_ind")
    df_table = (
        df[df["indicator"] == data_indicator][["country", "region", "income_group", "year", "value"]]
        .dropna(subset=["value"])
        .sort_values(["country", "year"])
        .rename(columns={"value": data_indicator})
        .reset_index(drop=True)
    )
    st.dataframe(df_table, width="stretch", height=450)

    csv = df_table.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download data (CSV)", csv, file_name=f"macroverse_{data_indicator}.csv")

st.divider()
st.caption("Source: World Bank Open Data API · Built with Streamlit · © 2026 Enrico Pulieri")