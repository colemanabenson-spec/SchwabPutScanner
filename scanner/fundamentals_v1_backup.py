import yfinance as yf

def score_metric(value, high, medium):
    if value is None:
        return 0

    if value > high:
        return 1.0

    if value >= medium:
        return 0.5

    return 0

def analyze_stock(ticker):

    stock = yf.Ticker(ticker)
    info = stock.info

    price = info.get("currentPrice")
    pe = info.get("trailingPE")
    peg = info.get("pegRatio")
    market_cap = info.get("marketCap")
    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    free_cash_flow = info.get("freeCashflow")
    revenue_growth = info.get("revenueGrowth")
    company_name = info.get("longName")
    sector = info.get("sector")
    industry = info.get("industry")
    description = info.get("longBusinessSummary")
    roe = info.get("returnOnEquity")
    operating_margin = info.get("operatingMargins")
    eps_growth = info.get("earningsGrowth")

    if roe is not None:
        roe *= 100

    if operating_margin is not None:
        operating_margin *= 100

    if revenue_growth is not None:
        revenue_growth *= 100

    if eps_growth is not None:
        eps_growth *= 100

    roe_score = score_metric(
        roe,
        20,
        15
    )

    operating_margin_score = score_metric(
        operating_margin,
        20,
        10
    )

    revenue_growth_score = score_metric(
        revenue_growth,
        15,
        5
    )

    eps_growth_score = score_metric(
        eps_growth,
        15,
        5
    )

    if pe is None:
        pe_score = 0
    elif pe < 20:
        pe_score = 1
    elif pe <= 30:
        pe_score = 0.5
    else:
        pe_score = 0

    if peg is None:
        peg_score = 0
    elif peg < 1.5:
        peg_score = 1
    elif peg <= 2:
        peg_score = 0.5
    else:
        peg_score = 0

    # Calculate FCF Yield
    fcf_yield = None

    if market_cap and free_cash_flow:
        fcf_yield = free_cash_flow / market_cap

    # Individual Rule Checks
    market_cap_pass = (
        market_cap is not None
        and market_cap > 2_000_000_000
    )

    price_pass = (
        price is not None
        and price < 150
    )

    pe_pass = (
        pe is not None
        and pe < 25
    )

    fcf_pass = (
        fcf_yield is not None
        and fcf_yield > 0.04
    )

    current_ratio_pass = (
        current_ratio is not None
        and current_ratio > 0.75
    )

    # Assuming Yahoo Finance reports Debt/Equity as a percentage
    debt_to_equity_pass = (
        debt_to_equity is not None
        and debt_to_equity < 150
    )

    revenue_growth_pass = (
        revenue_growth is not None
        and revenue_growth > -0.05
    )

    quality_score = (
        roe_score
        + operating_margin_score
    )

    growth_score = (
        revenue_growth_score
        + eps_growth_score
    )

    valuation_score = (
        pe_score
        + peg_score
    )

    total_score = (
        quality_score
        + growth_score
        + valuation_score
    )

    # Fundamental Score
    score = 0

    if market_cap_pass:
        score += 1

    if price_pass:
        score += 1

    if pe_pass:
        score += 1

    if fcf_pass:
        score += 1

    if current_ratio_pass:
        score += 1

    if debt_to_equity_pass:
        score += 1

    if revenue_growth_pass:
        score += 1

    # Overall Pass/Fail
    passes = (
        market_cap_pass
        and price_pass
        and pe_pass
        and fcf_pass
        and current_ratio_pass
        and debt_to_equity_pass
        and revenue_growth_pass
    )

    return {
        "Ticker": ticker,
        "Price": price,
        "PE": pe,
        "PEG": peg,
        "FCF Yield": fcf_yield,
        "Current Ratio": current_ratio,
        "Market Cap": market_cap,
        "Debt/Equity": debt_to_equity,
        "Free Cash Flow": free_cash_flow,
        "Revenue Growth": revenue_growth,

        "Market Cap Pass": market_cap_pass,
        "Price Pass": price_pass,
        "PE Pass": pe_pass,
        "FCF Pass": fcf_pass,
        "Current Ratio Pass": current_ratio_pass,
        "Debt/Equity Pass": debt_to_equity_pass,
        "Revenue Growth Pass": revenue_growth_pass,

        "Fundamental Score": score,
        "Passes Fundamentals": passes,

        "Company Name": company_name,
        "Sector": sector,
        "Industry": industry,
        "Description": description,
        "ROE": roe,
        "ROE Score": roe_score,
        "Operating Margin": operating_margin,
        "Operating Margin Score": operating_margin_score,
        "EPS Growth": eps_growth,
        "EPS Growth Score": eps_growth_score,
        "Revenue Growth Score": revenue_growth_score,

        "Quality Score": quality_score,
        "Growth Score": growth_score,

        "Total Score": total_score,
        "PE Score": pe_score,
        "PEG Score": peg_score,
        "Valuation Score": valuation_score,
    }