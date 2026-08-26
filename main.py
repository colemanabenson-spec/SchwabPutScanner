from scanner.fundamentals import analyze_stock


def status(score):
    if score is None:
        return "—"
    if score >= 1:
        return "✅"
    if score >= 0.5:
        return "⚠️"
    return "❌"


def percent(value):
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def number(value, decimals=2):
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


stocks = [
    "AAPL",
    "CF",
    "BAC",
    "F",
    "AMD",
    "DVN",
    "LHX",
    "C",
]


for ticker in stocks:
    try:
        result = analyze_stock(ticker)

        warnings = result.get("Data Warnings", [])
        warning_text = (
            "\n⚠️ DATA NOT FOUND\n"
            + "\n".join(f"• {warning}" for warning in warnings)
            if warnings
            else "\n✅ Data loaded successfully"
        )

        price = (
            f"${result['Price']:.2f}"
            if result["Price"] is not None
            else "N/A"
        )

        fcf_yield = (
            f"{result['FCF Yield'] * 100:.2f}%"
            if result["FCF Yield"] is not None
            else "N/A"
        )

        dma = (
            f"${result['200 DMA']:.2f}"
            if result["200 DMA"] is not None
            else "N/A"
        )

        roic_line = (
            f"ROIC {status(result['ROIC Score'])} "
            f"{percent(result['ROIC'])}\n"
            if result["ROIC"] is not None
            else ""
        )

        print(
            f"""
==============================
{result['Company Name']} ({ticker})
==============================

{warning_text}

Sector: {result['Sector'] or 'N/A'}
Industry: {result['Industry'] or 'N/A'}

COMPANY PROFILE
----------------------------------------
{result['Description'][:300] + '...' if result['Description'] else 'N/A'}

QUALITY
----------------------------------------
ROE {status(result['ROE Score'])} {percent(result['ROE'])}
{roic_line}Operating Margin {status(result['Operating Margin Score'])} {percent(result['Operating Margin'])}
Debt/Equity {percent(result['Debt/Equity'])}

Quality Score: {number(result['Quality Score'], 1)} (normalized {number(result['Quality Normalized'], 2)}, {result['Quality Coverage']}/{result['Quality Components']} available)

GROWTH
----------------------------------------
Revenue Growth ({result['Revenue Growth Source'] or 'N/A'}) {status(result['Revenue Growth Score'])} {percent(result['Revenue Growth'])}
Revenue CAGR {status(result['Revenue CAGR Score'])} {percent(result['Revenue CAGR'])}
EPS Growth ({result['EPS Growth Source'] or 'N/A'}) {status(result['EPS Growth Score'])} {percent(result.get('EPS Growth', result.get('TTM EPS Growth')))}
Historical EPS CAGR {status(result['EPS CAGR Score'])} {percent(result['EPS CAGR'])}

Growth Score: {number(result['Growth Score'], 1)} (normalized {number(result['Growth Normalized'], 2)}, {result['Growth Coverage']}/{result['Growth Components']} available)

VALUATION
----------------------------------------
Price {price}
PE Ratio {status(result['PE Score'])} {number(result['PE'], 1)}
Forward PE {number(result['Forward PE'], 1)}
PEG Ratio {status(result['PEG Score'])} {number(result['PEG'], 2)}
P/B Ratio {number(result['Price/Book'], 2)}
FCF Yield {status(result['FCF Score'])} {fcf_yield}

Valuation Score: {number(result['Valuation Score'], 1)} (normalized {number(result['Valuation Normalized'], 2)}, {result['Valuation Coverage']}/{result['Valuation Components']} available)

TECHNICALS
----------------------------------------
Above 200 DMA {'✅' if result['200 DMA Score'] else '❌'}
200 DMA: {dma}
RSI {status(result['RSI Score'])} {number(result['RSI'], 1)}
Relative Strength {status(result['Relative Strength Score'])} {percent(result['Relative Strength'])}

Technical Score: {number(result['Technical Score'], 1)} (normalized {number(result['Technical Normalized'], 2)}, {result['Technical Coverage']}/{result['Technical Components']} available)

SUMMARY
----------------------------------------
Quality Score: {number(result['Quality Score'], 1)} (normalized {number(result['Quality Normalized'], 2)}, {result['Quality Coverage']}/{result['Quality Components']} available)
Growth Score: {number(result['Growth Score'], 1)} (normalized {number(result['Growth Normalized'], 2)}, {result['Growth Coverage']}/{result['Growth Components']} available)
Valuation Score: {number(result['Valuation Score'], 1)} (normalized {number(result['Valuation Normalized'], 2)}, {result['Valuation Coverage']}/{result['Valuation Components']} available)
Technical Score: {number(result['Technical Score'], 1)} (normalized {number(result['Technical Normalized'], 2)}, {result['Technical Coverage']}/{result['Technical Components']} available)

TOTAL SCORE: {number(result['Total Score'], 1)} / 13.0
DATA QUALITY: {percent(result['Data Quality'] * 100)}
DATA STATUS: {result['Data Quality Status']}

NEXT EARNINGS
----------------------------------------
{result['Earnings Date'] if result['Earnings Date'] else 'N/A'}

VERDICT
----------------------------------------
{'✅ High Quality' if result['Quality Score'] is not None and result['Quality Score'] >= 2 else '⚠️ Below Target Quality'}
{'✅ Strong Growth' if result['Growth Score'] is not None and result['Growth Score'] >= 2.5 else ''}
{'✅ Attractive Valuation' if result['Valuation Score'] is not None and result['Valuation Score'] >= 2 else '⚠️ Expensive'}
{'✅ Positive Trend' if result['Technical Score'] is not None and result['Technical Score'] >= 1 else '❌ Below 200 Day Moving Average'}
"""
        )

    except Exception as error:
        print(f"Error analyzing ticker '{ticker}': {error}")