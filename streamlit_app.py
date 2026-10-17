import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Macroverse", layout="wide")

WB_BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation, Consumer Prices (%)": "FP.CPI.TOTL.ZG",
    "Central Government Debt / GDP (%)": "GC.DOD.TOTL.GD.ZS",
    "Unemployment (%)": "SL.UEM.TOTL.ZS",
    "GDP per Capita (current US$)": "NY.GDP.PCAP.CD",
}

# --------------------------------------------------------------------------
# DATA LOADING FROM WORLD BANK API
# --------------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading country list...")
def load_countries():
    url = f"{WB_BASE}/country?format=json&per_page=400"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    rows = resp.json()[1]
    data = []
    for r in rows:
        # exclude regional aggregates (not actual countries)
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


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Fetching data from the World Bank API...")
def load_indicator(indicator_code, start_year=2000, end_year=2025):
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


countries_df = load_countries()

# --------------------------------------------------------------------------
# SIDEBAR - FILTERS
# --------------------------------------------------------------------------
st.sidebar.title("Macroverse")
st.sidebar.caption("Live macroeconomic data — World Bank API")

metric_label = st.sidebar.selectbox("Indicator", list(INDICATORS.keys()))
indicator_code = INDICATORS[metric_label]

year = st.sidebar.slider("Year", min_value=2000, max_value=2025, value=2023)

regions = sorted(countries_df["region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

income_groups = sorted(countries_df["income_group"].dropna().unique())
selected_income = st.sidebar.multiselect(
    "Income Group", income_groups, default=income_groups
)

countries_filtered = countries_df[
    countries_df["region"].isin(selected_regions)
    & countries_df["income_group"].isin(selected_income)
]

indicator_df = load_indicator(indicator_code)
df = countries_filtered.merge(indicator_df, on="iso_3", how="left")
df_year = df[df["year"] == year]

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
st.title("🌍 Macroverse — Global Macroeconomic Dashboard")
st.markdown(f"**{metric_label}** · year **{year}** · source: World Bank Open Data API")

# --------------------------------------------------------------------------
# KPI ROW
# --------------------------------------------------------------------------
valid = df_year["value"].dropna()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Countries with data", valid.shape[0])
col2.metric("Mean", f"{valid.mean():.2f}" if not valid.empty else "—")
col3.metric("Median", f"{valid.median():.2f}" if not valid.empty else "—")
col4.metric("Std. deviation", f"{valid.std():.2f}" if not valid.empty else "—")

st.divider()

# --------------------------------------------------------------------------
# WORLD MAP
# --------------------------------------------------------------------------
st.subheader(f"World Map — {metric_label} ({year})")

fig_map = px.choropleth(
    df_year,
    locations="iso_3",
    color="value",
    hover_name="country",
    hover_data={"value": True, "region": True, "income_group": True, "iso_3": False},
    color_continuous_scale="Viridis",
    projection="natural earth",
    labels={"value": metric_label},
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
st.plotly_chart(fig_map, width="stretch")

st.divider()

# --------------------------------------------------------------------------
# TIME SERIES
# --------------------------------------------------------------------------
st.subheader(f"Trend Over Time — {metric_label}")

default_countries = (
    countries_filtered.sort_values("country")["country"].unique()[:5].tolist()
)
countries_sel = st.multiselect(
    "Select countries to compare",
    sorted(countries_filtered["country"].dropna().unique()),
    default=default_countries,
)

if countries_sel:
    df_ts = df[df["country"].isin(countries_sel)]
    fig_ts = px.line(
        df_ts.sort_values("year"),
        x="year",
        y="value",
        color="country",
        markers=True,
        labels={"value": metric_label, "year": "Year"},
    )
    fig_ts.update_layout(height=450)
    st.plotly_chart(fig_ts, width="stretch")
else:
    st.info("Select at least one country to see the historical trend.")

st.divider()

# --------------------------------------------------------------------------
# RANKING TABLE
# --------------------------------------------------------------------------
st.subheader(f"Country Ranking — {metric_label} ({year})")

df_rank = (
    df_year[["country", "region", "income_group", "value"]]
    .dropna(subset=["value"])
    .sort_values("value", ascending=False)
    .rename(columns={"value": metric_label})
    .reset_index(drop=True)
)
df_rank.index += 1
st.dataframe(df_rank, width="stretch")

csv = df_rank.to_csv(index=True).encode("utf-8")
st.download_button(
    "⬇️ Download Ranking (CSV)",
    csv,
    file_name=f"macroverse_{indicator_code}_{year}.csv",
)

st.caption("Data: World Bank Open Data API (api.worldbank.org). Some countries/years may not have data available.")