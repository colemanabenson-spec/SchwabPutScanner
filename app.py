import streamlit as st
from scanner.fundamentals import analyze_stock

st.set_page_config(
    page_title="CAB Stock Scanner",
    page_icon="📈"
)

st.title("📈 CAB Stock Scanner")

ticker = st.text_input(
    "Enter Ticker",
    value="AAPL"
)

if st.button("Analyze"):

    result = analyze_stock(ticker.upper())

    st.header(
        f"{result['Company Name']} ({result['Ticker']})"
    )

    def show_metrics(metrics):
        st.dataframe(
            [{"Metric": name, "Value": result[name]} for name in metrics],
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Company Overview")
    st.write(f"Sector: {result['Sector'] or 'N/A'}")
    st.write(f"Industry: {result['Industry'] or 'N/A'}")
    st.write(f"Earnings Date: {result['Earnings Date'] or 'N/A'}")
    st.write(result["Description"] or "Description not available.")

    st.subheader("Quality")
    show_metrics([
        "ROE",
        "ROIC",
        "Operating Margin",
    ])
    st.metric("Quality Score", result["Quality Score"])

    st.subheader("Growth")
    show_metrics([
        "Revenue Growth",
        "Revenue Growth Source",
        "Revenue CAGR",
        "EPS Growth",
        "TTM EPS Growth",
        "EPS Growth Source",
        "EPS CAGR",
    ])
    st.metric("Growth Score", result["Growth Score"])

    st.subheader("Valuation")
    show_metrics([
        "Price",
        "PE",
        "Forward PE",
        "PEG",
        "Price/Book",
        "Free Cash Flow",
        "FCF Yield",
    ])
    st.metric("Valuation Score", result["Valuation Score"])
    st.caption("Additional fundamentals (not included in the valuation score)")
    show_metrics([
        "Market Cap",
        "Current Ratio",
        "Debt/Equity",
    ])

    st.subheader("Technical")
    show_metrics([
        "200 DMA",
        "RSI",
        "Relative Strength",
    ])
    st.metric("Technical Score", result["Technical Score"])

    st.subheader("Overall")
    show_metrics([
        "Total Score",
        "Overall Normalized",
        "Data Quality",
        "Data Quality Status",
    ])

    warnings = result["Data Warnings"]
    if warnings:
        st.subheader("Data Warnings")
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("All available analysis data loaded.")
