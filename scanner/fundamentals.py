import math
from datetime import datetime, timezone
import yfinance as yf


def is_missing(value):
    if value is None:
        return True

    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def score_metric(value, high, medium):
    if is_missing(value):
        return 0
    if value > high:
        return 1.0

    if value >= medium:
        return 0.5

    return 0


def upcoming_earnings_date(stock, info):
    now = datetime.now(timezone.utc)
    candidates = []

    earnings_timestamp = info.get("earningsTimestamp")
    if earnings_timestamp:
        try:
            candidates.append(
                datetime.fromtimestamp(
                    earnings_timestamp,
                    tz=timezone.utc
                )
            )
        except (TypeError, ValueError, OSError):
            pass

    if not candidates or candidates[0] < now:
        try:
            earnings_dates = stock.get_earnings_dates(limit=12)
            for earnings_date in earnings_dates.index:
                if hasattr(earnings_date, "to_pydatetime"):
                    earnings_date = earnings_date.to_pydatetime()

                if earnings_date.tzinfo is None:
                    earnings_date = earnings_date.replace(tzinfo=timezone.utc)
                else:
                    earnings_date = earnings_date.astimezone(timezone.utc)

                candidates.append(earnings_date)
        except (AttributeError, TypeError, ValueError, OSError):
            pass

    future_dates = [earnings_date for earnings_date in candidates if earnings_date >= now]
    return min(future_dates) if future_dates else None


def analyze_stock(ticker):
    warnings = []
    financials = None
    balance_sheet = None
    eps_cagr = None
    roic = None

    stock = yf.Ticker(ticker)

    info = {}
    hist = None

    try:
        info = stock.info or {}
    except Exception as error:
        warnings.append(f"Company data not found: {error}")

    try:
        hist = stock.history(period="1y")
    except Exception as error:
        warnings.append(f"Price history not found: {error}")

    sma200 = None

    if hist is not None and not hist.empty and len(hist) >= 200:
        sma200 = hist["Close"].rolling(window=200).mean().iloc[-1]
    else:
        warnings.append("200-day moving average not found")

    price = info.get("currentPrice")
    pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    eps_ttm = info.get("trailingEps")

    if (
        not is_missing(price)
        and not is_missing(eps_ttm)
        and eps_ttm > 0
    ):
        calculated_pe = price / eps_ttm

        if (
            is_missing(pe)
            or pe > calculated_pe * 2
            or pe < calculated_pe / 2
        ):
            pe = calculated_pe

    peg = info.get("pegRatio")
    market_cap = info.get("marketCap")
    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    free_cash_flow = info.get("freeCashflow")
    revenue_growth = info.get("revenueGrowth")
    company_name = (
        info.get("longName")
        or info.get("shortName")
        or ticker
    )
    sector = info.get("sector")
    industry = info.get("industry")
    description = info.get("longBusinessSummary")
    roe = info.get("returnOnEquity")
    operating_margin = info.get("operatingMargins")
    eps_growth = info.get("earningsGrowth")
    earnings_date = upcoming_earnings_date(stock, info)

    if earnings_date:
        earnings_date = earnings_date.strftime("%Y-%m-%d")
    else:
        warnings.append("Earnings date not found")

    rsi = info.get("rsi")
    
    relative_strength = None

    rsi_score = None

    if hist is not None and not hist.empty:
        try:
            delta = hist["Close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
        except Exception as error:
            warnings.append(f"RSI not found: {error}")

    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")

        if (
            hist is not None
            and not hist.empty
            and spy_hist is not None
            and not spy_hist.empty
        ):
            stock_return = hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1
            spy_return = (
                spy_hist["Close"].iloc[-1]
                / spy_hist["Close"].iloc[0]
                - 1
            )
            relative_strength = (stock_return - spy_return) * 100
        else:
            warnings.append("Relative strength not found")

    except Exception as error:
        warnings.append(f"Relative strength not found: {error}")

    if roe is not None:
        roe *= 100

    if operating_margin is not None:
        operating_margin *= 100

    if revenue_growth is not None:
        revenue_growth *= 100

    if eps_growth is not None:
        eps_growth *= 100


    if is_missing(rsi):
        rsi_score = 0
        warnings.append("RSI not found")
    elif 40 <= rsi <= 70:
        rsi_score = 1
    elif 30 <= rsi <= 80:
        rsi_score = 0.5
    else:
        rsi_score = 0

    relative_strength_score = score_metric(
        relative_strength,
        10,
        0
    )

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

    revenue_cagr = None
    revenue_cagr_score = 0
    eps_cagr_score = 0
    eps_growth_score = score_metric(eps_growth, 15, 5)

    try:
        financials = stock.financials
        balance_sheet = stock.balance_sheet
    except Exception as error:
        warnings.append(f"Financial statements not found: {error}")

    roic_score = 0

    if (
        financials is not None
        and balance_sheet is not None
        and "Operating Income" in financials.index
    ):
        try:
            operating_income = financials.loc[
                "Operating Income"
            ].iloc[0]
            tax_provision = financials.loc[
                "Tax Provision"
            ].iloc[0]
            pretax_income = financials.loc[
                "Pretax Income"
            ].iloc[0]

            total_debt = balance_sheet.loc[
                "Total Debt"
            ].iloc[0]
            equity = balance_sheet.loc[
                "Stockholders Equity"
            ].iloc[0]
            cash = balance_sheet.loc[
                "Cash And Cash Equivalents"
            ].iloc[0]

            tax_rate = (
                tax_provision / pretax_income
                if pretax_income > 0
                else 0.21
            )

            nopat = operating_income * (1 - tax_rate)
            invested_capital = total_debt + equity - cash

            if invested_capital > 0:
                roic = nopat / invested_capital * 100
                roic_score = score_metric(roic, 12, 8)

        except (KeyError, IndexError, TypeError, ValueError):
            pass

    try:
        revenue_series = financials.loc["Total Revenue"].dropna()

        if len(revenue_series) >= 2:
            latest = revenue_series.iloc[0]
            oldest = revenue_series.iloc[-1]
            years = len(revenue_series) - 1

            if oldest > 0 and latest > 0:
                revenue_cagr = (
                    (latest / oldest) ** (1 / years) - 1
                ) * 100
                revenue_cagr_score = score_metric(
                    revenue_cagr,
                    10,
                    5
                )
            else:
                warnings.append("Revenue CAGR not found")
        else:
            warnings.append("Revenue CAGR not found")

    except Exception as error:
        warnings.append(f"Revenue CAGR not found: {error}")

    try:
        eps_series = financials.loc["Diluted EPS"].dropna()

        if len(eps_series) >= 2:
            latest = eps_series.iloc[0]
            oldest = eps_series.iloc[-1]
            years = len(eps_series) - 1

            if oldest > 0 and latest > 0:
                eps_cagr = (
                    (latest / oldest) ** (1 / years) - 1
                ) * 100
                eps_cagr_score = score_metric(
                    eps_cagr,
                    10,
                    5
                )
            else:
                warnings.append("EPS CAGR not found")
        else:
            warnings.append("EPS CAGR not found")

    except Exception as error:
        warnings.append(f"EPS CAGR not found: {error}")

    growth_score = (
        revenue_growth_score
        + revenue_cagr_score
        + eps_growth_score
        + eps_cagr_score
    )

    dma_score = 0

    if (
        price is not None
        and sma200 is not None
    ):
        dma_score = 1 if price > sma200 else 0

    if is_missing(pe):
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

    quality_score = (
        roe_score
        + roic_score
        + operating_margin_score
    )

    technical_score = (
        dma_score
        + rsi_score
        + relative_strength_score
    )

    # Calculate FCF Yield
    fcf_yield = None

    if (
        market_cap is not None
        and free_cash_flow is not None
        and market_cap != 0
    ):
        fcf_yield = free_cash_flow / market_cap

    fcf_score = score_metric(
        fcf_yield * 100 if fcf_yield is not None else None,
        5,
        2
    )

    valuation_score = (
        pe_score
        + peg_score
        + fcf_score
    )

    total_score = (
        quality_score
        + growth_score
        + valuation_score
        + technical_score
    )

    fields = {
        "Price": price,
        "PE": pe,
        "Forward PE": forward_pe,
        "PEG": peg,
        "ROE": roe,
        "Operating Margin": operating_margin,
        "Revenue Growth": revenue_growth,
        "Revenue CAGR": revenue_cagr,
        "EPS Growth": eps_growth,
        "EPS CAGR": eps_cagr,
        "Free Cash Flow": free_cash_flow,
    }

    for name, value in fields.items():
        if is_missing(value):
            warnings.append(f"{name} not found")

    for name, value in {
        "Company Name": info.get("longName") or info.get("shortName"),
        "Sector": sector,
        "Industry": industry,
        "Description": description,
    }.items():
        if is_missing(value) or value == "":
            warnings.append(f"{name} not found")

    return {
        "Ticker": ticker,
        "Price": price,
        "PE": pe,
        "Forward PE": forward_pe,
        "PEG": peg,
        "ROIC": roic,
        "ROIC Score": roic_score,
        "FCF Yield": fcf_yield,
        "FCF Score": fcf_score,
        "Current Ratio": current_ratio,
        "Market Cap": market_cap,
        "Debt/Equity": debt_to_equity,
        "Free Cash Flow": free_cash_flow,
        "Revenue Growth": revenue_growth,

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
        "Revenue CAGR": revenue_cagr,
        "Revenue CAGR Score": revenue_cagr_score,

        "Quality Score": quality_score,
        "Growth Score": growth_score,

        "Total Score": total_score,
        "PE Score": pe_score,
        "PEG Score": peg_score,
        "Valuation Score": valuation_score,

        "200 DMA": sma200,
        "200 DMA Score": dma_score,
        "Technical Score": technical_score,
        "Earnings Date": earnings_date,

        "EPS CAGR": eps_cagr,
        "EPS CAGR Score": eps_cagr_score,
        "RSI": rsi,
        "RSI Score": rsi_score,
        "Relative Strength": relative_strength,
        "Relative Strength Score": relative_strength_score,
        "Data Warnings": list(dict.fromkeys(warnings)),
    }