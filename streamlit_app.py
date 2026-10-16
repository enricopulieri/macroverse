import streamlit as st

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MacroVerse | Global Economic Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# RESEARCH SECTIONS
# --------------------------------------------------

SECTIONS = [
    (
        "Global Economy",
        "🌍",
        "GDP, inflation, trade, employment",
        "Explore global macroeconomic indicators, "
        "compare countries and analyse historical trends."
    ),
    (
        "Sovereign Debt",
        "🏛️",
        "Debt, yields, fiscal sustainability",
        "Monitor government debt, sovereign bond yields, "
        "fiscal balances and debt sustainability."
    ),
    (
        "Climate Finance",
        "🌱",
        "Climate risks, damages, green bonds",
        "Investigate climate-related financial risks, "
        "economic damages and sustainable finance."
    ),
    (
        "Monetary Policy",
        "📈",
        "Interest rates, money supply, central banks",
        "Track policy rates, monetary aggregates "
        "and central bank developments."
    ),
    (
        "Econometrics Lab",
        "🧪",
        "OLS, FE, TWFE, DiD, forecasting",
        "Explore econometric methods, upload datasets "
        "and develop quantitative analyses."
    ),
    (
        "MacroVerse AI",
        "🧠",
        "AI-powered economic analysis",
        "A future AI assistant for exploring data, "
        "generating charts and supporting research."
    ),
]

# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    text-align: center;
    padding: 1.6rem 0 1.3rem;
}

.hero-title {
    font-size: clamp(2.5rem, 6vw, 4rem);
    font-weight: 800;
    letter-spacing: -0.055em;
    margin-bottom: .15rem;
}

.hero-subtitle {
    font-size: 1.3rem;
    font-weight: 500;
    margin-bottom: .4rem;
}

.hero-caption {
    color: #8b97a7;
    font-size: .95rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# NAVIGATION STATE
# --------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "Home"

PAGES = ["Home"] + [
    section[0] for section in SECTIONS
]

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("🌐 MacroVerse")
    st.caption("Global Economic Intelligence")

    st.divider()

    selected = st.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(st.session_state.page),
        key="sidebar_navigation"
    )

    if selected != st.session_state.page:
        st.session_state.page = selected
        st.rerun()

    st.divider()

    st.caption(
        "Explore · Analyse · Understand"
    )

# --------------------------------------------------
# HOMEPAGE
# --------------------------------------------------

if st.session_state.page == "Home":

    st.markdown("""
    <div class="hero">
        <div class="hero-title">
            🌐 MacroVerse
        </div>
        <div class="hero-subtitle">
            Explore the Global Economy
        </div>
        <div class="hero-caption">
            Global Economic Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("Explore MacroVerse")

    st.write(
        "Choose a research area to get started."
    )

    # Six interactive cards
    for start in range(0, len(SECTIONS), 2):

        columns = st.columns(
            2,
            gap="large"
        )

        for column, section in zip(
            columns,
            SECTIONS[start:start + 2]
        ):

            title, icon, description, details = section

            with column:

                with st.container(border=True):

                    st.markdown(
                        f"### {icon} {title}"
                    )

                    st.caption(description)

                    st.write(details)

                    if st.button(
                        "Explore →",
                        key=f"open_{title}",
                        use_container_width=True
                    ):
                        st.session_state.page = title
                        st.rerun()

    st.divider()

    st.caption(
        "MacroVerse | Research & Data Platform"
    )

# --------------------------------------------------
# INDIVIDUAL RESEARCH PAGES
# --------------------------------------------------

else:

    title, icon, description, details = next(
        section
        for section in SECTIONS
        if section[0] == st.session_state.page
    )

    st.title(
        f"{icon} {title}"
    )

    st.caption(description)

    st.write(details)

    st.info(
        "🚧 This section is under development. "
        "Interactive dashboards and research tools "
        "are coming soon."
    )

    if st.button("← Back to Home"):
        st.session_state.page = "Home"
        st.rerun()