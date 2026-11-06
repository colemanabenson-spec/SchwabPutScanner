import math
from textwrap import dedent

import streamlit as st

from scanner.fundamentals import analyze_stock


def numeric_value(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def number(value, decimals=2, prefix="", suffix=""):
    value = numeric_value(value)
    if value is None:
        return "N/A"
    return f"{prefix}{value:.{decimals}f}{suffix}"


def percent(value, decimals=1, fractional=False):
    value = numeric_value(value)
    if value is None:
        return "N/A"
    if fractional:
        value *= 100
    return f"{value:.{decimals}f}%"


def status(score):
    score = numeric_value(score)
    if score is None:
        return "—"
    if score >= 1:
        return "✅"
    if score >= 0.5:
        return "⚠️"
    return "❌"


def score_summary(result, name):
    return (
        f"{number(result[f'{name} Score'], 1)} "
        f"(normalized {number(result[f'{name} Normalized'], 2)}, "
        f"{result[f'{name} Coverage']}/{result[f'{name} Components']} available)"
    )


def verdict(score, threshold, positive, negative):
    score = numeric_value(score)
    if score is None:
        return f"— {positive.split(' ', 1)[1]} unavailable"
    return positive if score >= threshold else negative


def build_report(result):
    description = " ".join((result["Description"] or "N/A").split())
    if len(description) > 300:
        description = f"{description[:300]}..."

    warnings = result["Data Warnings"]
    warning_text = (
        "⚠️ DATA NOT FOUND\n"
        + "\n".join(f"• {warning}" for warning in warnings)
        if warnings
        else "✅ Data loaded successfully"
    )
    warning_text = warning_text.replace("\n", "\n        ")

    return dedent(
        f"""
        ==============================
        {result['Company Name']} ({result['Ticker']})
        ==============================

        {warning_text}

        Sector: {result['Sector'] or 'N/A'}
        Industry: {result['Industry'] or 'N/A'}

        COMPANY PROFILE
        ----------------------------------------
        {description}

        QUALITY
        ----------------------------------------
        ROE {status(result['ROE Score'])} {percent(result['ROE'])}
        ROIC {status(result['ROIC Score'])} {percent(result['ROIC'])}
        Operating Margin {status(result['Operating Margin Score'])} {percent(result['Operating Margin'])}
        Debt/Equity {percent(result['Debt/Equity'])}

        Quality Score: {score_summary(result, 'Quality')}

        GROWTH
        ----------------------------------------
        Revenue Growth ({result['Revenue Growth Source'] or 'N/A'}) {status(result['Revenue Growth Score'])} {percent(result['Revenue Growth'])}
        Revenue CAGR {status(result['Revenue CAGR Score'])} {percent(result['Revenue CAGR'])}
        EPS Growth ({result['EPS Growth Source'] or 'N/A'}) {status(result['EPS Growth Score'])} {percent(result['EPS Growth'])}
        Historical EPS CAGR {status(result['EPS CAGR Score'])} {percent(result['EPS CAGR'])}

        Growth Score: {score_summary(result, 'Growth')}

        VALUATION
        ----------------------------------------
        Price {number(result['Price'], 2, prefix='$')}
        PE Ratio {status(result['PE Score'])} {number(result['PE'], 1)}
        Forward PE {number(result['Forward PE'], 1)}
        PEG Ratio {status(result['PEG Score'])} {number(result['PEG'], 2)}
        P/B Ratio {number(result['Price/Book'], 2)}
        FCF Yield {status(result['FCF Score'])} {percent(result['FCF Yield'], 2, fractional=True)}

        Valuation Score: {score_summary(result, 'Valuation')}

        TECHNICALS
        ----------------------------------------
        Above 200 DMA {status(result['200 DMA Score'])}
        200 DMA: {number(result['200 DMA'], 2, prefix='$')}
        RSI {status(result['RSI Score'])} {number(result['RSI'], 1)}
        Relative Strength {status(result['Relative Strength Score'])} {percent(result['Relative Strength'])}

        Technical Score: {score_summary(result, 'Technical')}

        SUMMARY
        ----------------------------------------
        Quality Score: {score_summary(result, 'Quality')}
        Growth Score: {score_summary(result, 'Growth')}
        Valuation Score: {score_summary(result, 'Valuation')}
        Technical Score: {score_summary(result, 'Technical')}

        TOTAL SCORE: {number(result['Total Score'], 1)} / 13.0
        DATA QUALITY: {percent(result['Data Quality'], fractional=True)}
        DATA STATUS: {result['Data Quality Status']}

        NEXT EARNINGS
        ----------------------------------------
        {result['Earnings Date'] or 'N/A'}

        VERDICT
        ----------------------------------------
        {verdict(result['Quality Score'], 2, '✅ High Quality', '⚠️ Below Target Quality')}
        {verdict(result['Growth Score'], 2.5, '✅ Strong Growth', '⚠️ Below Target Growth')}
        {verdict(result['Valuation Score'], 2, '✅ Attractive Valuation', '⚠️ Expensive')}
        {verdict(result['Technical Score'], 1, '✅ Positive Trend', '❌ Below 200 Day Moving Average')}
        """
    ).strip()


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
    st.write(result)
    st.text(build_report(result))