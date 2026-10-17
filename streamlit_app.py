"""MacroVerse — interactive World Bank macroeconomic dashboard.

Run with: python -m streamlit run streamlit_app.py
"""
import io
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="MacroVerse | Global Economic Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

INDICATORS = {
    "GDP (current US$)": ("NY.GDP.MKTP.CD", "US$", "Economic output"),
    "GDP growth (annual %)": ("NY.GDP.MKTP.KD.ZG", "%", "Growth"),
    "GDP per capita (current US$)": ("NY.GDP.PCAP.CD", "US$", "Living standards"),
    "Inflation, consumer prices (%)": ("FP.CPI.TOTL.ZG", "%", "Prices"),
    "Unemployment (% of labour force)": ("SL.UEM.TOTL.ZS", "%", "Labour market"),
    "Government debt (% of GDP)": ("GC.DOD.TOTL.GD.ZS", "%", "Public finance"),
    "Government balance (% of GDP)": ("GC.BAL.CASH.GD.ZS", "%", "Public finance"),
    "Population": ("SP.POP.TOTL", "people", "Demographics"),
    "Trade (% of GDP)": ("NE.TRD.GNFS.ZS", "%", "External sector"),
    "FDI, net inflows (% of GDP)": ("BX.KLT.DINV.WD.GD.ZS", "%", "Investment"),
    "CO₂ emissions (tonnes per capita)": ("EN.GHG.CO2.PC.CE.AR5", "t/person", "Climate"),
    "Renewable electricity output (%)": ("EG.ELC.RNEW.ZS", "%", "Climate"),
}

st.markdown("""
<style>
.block-container {max-width: 1450px; padding-top: 1.15rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {background: #172334;}
[data-testid="stSidebar"] * {color: #f1f5f9;}
.mv-eyebrow {font-size: .78rem; text-transform: uppercase; letter-spacing: .13em; color: #698aaa; font-weight: 700;}
.mv-heading {font-size: 2.45rem; font-weight: 780; letter-spacing: -.05em; line-height: 1.1; margin: .15rem 0 .3rem;}
.mv-subtitle {color: #8392a9; font-size: .97rem; margin-bottom: 1rem;}
.mv-section {font-size: 1.16rem; font-weight: 700; margin: .35rem 0 .25rem;}
[data-testid="stMetric"] {border: 1px solid rgba(120,140,160,.24); border-radius: 12px; padding: 13px 17px; background: rgba(100,130,160,.06);}
[data-testid="stMetricLabel"] {font-size: .88rem;}
[data-testid="stMetricValue"] {font-size: 1.55rem;}
div[data-testid="stPlotlyChart"] {border: 1px solid rgba(120,140,160,.20); border-radius: 12px; padding: 6px;}
</style>
""", unsafe_allow_html=True)

API = "https://api.worldbank.org/v2"


def world_bank(path, params=None):
    options = {"format": "json", "per_page": 20000}
    options.update(params or {})
    response = requests.get(f"{API}/{path}", params=options, timeout=35)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError("The World Bank API did not return a valid dataset.")
    return payload[1]


@st.cache_data(ttl=86400, show_spinner=False)
def countries():
    raw = world_bank("country", {"per_page": 400})
    values = []
    for x in raw:
        region = x.get("region") or {}
        # World Bank uses NA for aggregate regions (not North America).
        if region.get("id") == "NA":
            continue
        iso3 = x.get("id")
        if iso3 and len(iso3) == 3:
            values.append({
                "iso3": iso3,
                "country": x.get("name", iso3),
                "region": region.get("value", "Other"),
                "income": (x.get("incomeLevel") or {}).get("value", "Unknown"),
            })
    if not values:
        raise ValueError("No country metadata found.")
    return pd.DataFrame(values)


@st.cache_data(ttl=43200, show_spinner=False)
def indicator_data(code, first_year=2000, last_year=2025):
    raw = world_bank(f"country/all/indicator/{code}", {"date": f"{first_year}:{last_year}"})
    rows = []
    for x in raw:
        value = x.get("value")
        if value is None:
            continue
        country = x.get("country") or {}