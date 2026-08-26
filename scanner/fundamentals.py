import math
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd


def is_missing(value):
    if value is None:
        return True

    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def score_metric(value, high, medium):
    if is_missing(value):
        return None
    if value > high:
        return 1.0

    if value >= medium:
        return 0.5

    return 0


def sum_scores(scores):
    return sum(score for score in scores if score is not None)


def score_coverage(scores):
    return sum(score is not None for score in scores)


def normalized_score(scores):
    valid_scores = [score for score in scores if score is not None]
    if not valid_scores:
        return None
    return sum(valid_scores) / len(valid_scores)


def is_financial_company(sector, industry):
    sector_name = (sector or "").lower()
    industry_name = (industry or "").lower()
    financial_keywords = (
        "bank",
        "insurance",
        "mortgage",
        "reit",
        "real estate investment trust",
    )
    return (
        "financial services" in sector_name
        and any(keyword in industry_name for keyword in financial_keywords)
    ) or (
        "real estate" in sector_name
        and any(keyword in industry_name for keyword in ("reit", "real estate investment trust"))
    )


def has_consecutive_quarters(series, count):
    if len(series) < count:
        return False

    periods = [
        date.tz_localize(None).to_period("Q")
        if getattr(date, "tzinfo", None) is not None
        else date.to_period("Q")
        for date in series.index[:count]
    ]
    return all(
        periods[index].ordinal - periods[index + 1].ordinal == 1
        for index in range(count - 1)
    )


def calculate_ttm_growth(series, min_denominator=0.10):
    if series is None:
        return None

    series = series.dropna().sort_index(ascending=False)
    if not has_consecutive_quarters(series, 8):
        return None

    current_ttm = series.iloc[:4].sum()
    prior_ttm = series.iloc[4:8].sum()

    if prior_ttm <= min_denominator:
        return None

    return (current_ttm / prior_ttm - 1) * 100


def calculate_annual_revenue_growth(series):
    if series is None:
        return None

    try:
        series = series.dropna().sort_index(ascending=False)
        if len(series) < 2:
            return None

        latest = series.iloc[0]
        prior = series.iloc[1]
        if prior <= 0:
            return None

        return (latest / prior - 1) * 100
    except (AttributeError, TypeError, ValueError, ZeroDivisionError):
        return None


def find_eps_row(frame):
    if frame is None or frame.empty:
        return None

    for row in frame.index:
        name = str(row).lower().strip()
        if "diluted eps" in name:
            return row

    for row in frame.index:
        name = str(row).lower().strip()
        if "eps" in name:
            return row

    return None


def normalize_eps_series(series):
    try:
        s = pd.to_numeric(series, errors="coerce").dropna()

        idx = pd.to_datetime(s.index, errors="coerce")
        valid = ~idx.isna()
        s = s[valid]
        idx = idx[valid]

        s.index = idx
        s = s.sort_index(ascending=False)
        return s
    except Exception:
        return pd.Series(dtype=float)


def calculate_eps_growth(quarterly_financials, annual_financials):
    """
    EPS Growth:
    1. Try TTM EPS growth using eight consecutive quarterly values when available.
    2. If unavailable, try annual EPS growth.
    3. Return (None, None) if neither can be calculated.
    """
    if quarterly_financials is not None and not quarterly_financials.empty:
        try:
            eps_row = find_eps_row(quarterly_financials)
            if eps_row is not None:
                eps = normalize_eps_series(quarterly_financials.loc[eps_row])

                if len(eps) >= 8 and has_consecutive_quarters(eps, 8):
                    current_ttm = eps.iloc[:4].sum()
                    prior_ttm = eps.iloc[4:8].sum()

                    if (
                        pd.notna(current_ttm)
                        and pd.notna(prior_ttm)
                        and prior_ttm > 0
                    ):
                        return (current_ttm / prior_ttm - 1) * 100, "TTM"
        except Exception:
            pass

    if annual_financials is not None and not annual_financials.empty:
        try:
            eps_row = find_eps_row(annual_financials)
            if eps_row is not None:
                eps = normalize_eps_series(annual_financials.loc[eps_row])

                if len(eps) >= 2:
                    latest = eps.iloc[0]
                    prior = eps.iloc[1]

                    if (
                        pd.notna(latest)
                        and pd.notna(prior)
                        and prior > 0
                    ):
                        return (latest / prior - 1) * 100, "Annual"
        except Exception:
            pass

    return None, None


def calculate_ttm_eps_growth(quarterly_financials):
    growth, _ = calculate_eps_growth(quarterly_financials, None)
    return growth


def calculate_cagr(series):
    series = series.dropna().sort_index(ascending=False)
    if len(series) < 2:
        return None

    latest = series.iloc[0]
    oldest = series.iloc[-1]
    years = (series.index[0] - series.index[-1]).days / 365.25

    if latest <= 0 or oldest <= 0 or years <= 0:
        return None

    return ((latest / oldest) ** (1 / years) - 1) * 100


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
    quarterly_financials = None
    balance_sheet = None
    quarterly_cashflow = None
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
    price_to_book = info.get("priceToBook")
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
    free_cash_flow = None
    revenue_growth = None
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
    eps_growth = None
    revenue_growth_source = None

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

    if is_missing(rsi):
        rsi_score = None
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

    revenue_cagr = None
    revenue_cagr_score = None
    eps_cagr_score = None

    try:
        financials = stock.income_stmt
        quarterly_financials = stock.quarterly_income_stmt
        balance_sheet = stock.balance_sheet
    except Exception as error:
        warnings.append(f"Financial statements not found: {error}")

    try:
        quarterly_cashflow = stock.quarterly_cashflow
    except Exception as error:
        warnings.append(f"Quarterly cash flow statement not found: {error}")

    if quarterly_cashflow is not None:
        if not is_financial_company(sector, industry):
            try:
                operating_cash_flow = (
                    quarterly_cashflow.loc["Operating Cash Flow"]
                    .dropna()
                    .sort_index(ascending=False)
                )

                capital_expenditure = (
                    quarterly_cashflow.loc["Capital Expenditure"]
                    .dropna()
                    .sort_index(ascending=False)
                )

                if has_consecutive_quarters(operating_cash_flow, 4) and has_consecutive_quarters(capital_expenditure, 4):
                    operating_cash_flow_ttm = operating_cash_flow.iloc[:4].sum()
                    capital_expenditure_ttm = capital_expenditure.iloc[:4].sum()
                    free_cash_flow = (
                        operating_cash_flow_ttm
                        - abs(capital_expenditure_ttm)
                    )

            except (IndexError, KeyError, TypeError, ValueError):
                pass

    try:
        revenue_series = quarterly_financials.loc["Total Revenue"]
        revenue_growth = calculate_ttm_growth(
            revenue_series,
            min_denominator=0.10,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        revenue_growth = None

    if revenue_growth is not None:
        revenue_growth_source = "TTM"

    if revenue_growth is None:
        try:
            revenue_growth = calculate_annual_revenue_growth(
                financials.loc["Total Revenue"]
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            revenue_growth = None

        if revenue_growth is not None:
            revenue_growth_source = "Annual"

    if revenue_growth is None:
        warnings.append("Revenue Growth not available")

    eps_growth, eps_growth_source = calculate_eps_growth(
        quarterly_financials,
        financials,
    )
    if eps_growth is None:
        warnings.append("EPS Growth not available")

    revenue_growth_score = score_metric(
        revenue_growth,
        15,
        5
    )

    eps_growth_score = score_metric(eps_growth, 15, 5)

    roic_score = None

    if (
        not is_financial_company(sector, industry)
        and
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
            tax_rate = min(max(tax_rate, 0), 0.35)

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
                revenue_cagr = calculate_cagr(revenue_series)
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
        eps_row = find_eps_row(financials)

        if eps_row is not None:
            eps_series = normalize_eps_series(financials.loc[eps_row])

            if len(eps_series) >= 2:
                latest = eps_series.iloc[0]
                oldest = eps_series.iloc[-1]

                if oldest > 0 and latest > 0:
                    eps_cagr = calculate_cagr(eps_series)
                    eps_cagr_score = score_metric(
                        eps_cagr,
                        10,
                        5
                    )
                else:
                    warnings.append("EPS CAGR not found")
            else:
                warnings.append("EPS CAGR not found")
        else:
            warnings.append("EPS CAGR not found")

    except Exception as error:
        warnings.append(f"EPS CAGR not found: {error}")

    growth_components = [
        revenue_growth_score,
        revenue_cagr_score,
        eps_growth_score,
        eps_cagr_score,
    ]
    growth_score = sum_scores(growth_components)
    growth_coverage = score_coverage(growth_components)
    growth_normalized = normalized_score(growth_components)

    dma_score = None

    if (
        price is not None
        and sma200 is not None
    ):
        dma_score = 1 if price > sma200 else 0

    if is_missing(pe):
        pe_score = None
    elif pe < 20:
        pe_score = 1
    elif pe <= 30:
        pe_score = 0.5
    else:
        pe_score = 0

    if peg is None:
        peg_score = None
    elif peg < 1.5:
        peg_score = 1
    elif peg <= 2:
        peg_score = 0.5
    else:
        peg_score = 0

    quality_components = [roe_score, roic_score, operating_margin_score]
    quality_score = sum_scores(quality_components)
    quality_coverage = score_coverage(quality_components)
    quality_normalized = normalized_score(quality_components)

    technical_components = [dma_score, rsi_score, relative_strength_score]
    technical_score = sum_scores(technical_components)
    technical_coverage = score_coverage(technical_components)
    technical_normalized = normalized_score(technical_components)

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

    valuation_components = [pe_score, peg_score]
    if not is_financial_company(sector, industry):
        valuation_components.append(fcf_score)
    valuation_score = sum_scores(valuation_components)
    valuation_coverage = score_coverage(valuation_components)
    valuation_normalized = normalized_score(valuation_components)

    weighted_categories = [
        (quality_normalized, 0.30),
        (growth_normalized, 0.30),
        (valuation_normalized, 0.20),
        (technical_normalized, 0.20),
    ]
    valid_categories = [
        (score, weight)
        for score, weight in weighted_categories
        if score is not None
    ]
    weight_total = sum(weight for _, weight in valid_categories)
    overall_normalized = (
        sum(score * weight for score, weight in valid_categories) / weight_total
        if weight_total
        else None
    )
    total_score = overall_normalized * 13 if overall_normalized is not None else None
    data_quality = sum(
        coverage / components
        for coverage, components in (
            (quality_coverage, len(quality_components)),
            (growth_coverage, len(growth_components)),
            (valuation_coverage, len(valuation_components)),
            (technical_coverage, len(technical_components)),
        )
    ) / 4
    data_quality_status = (
        "Insufficient Data"
        if data_quality < 0.80
        else "Sufficient Data"
    )

    if revenue_growth is not None and revenue_growth > 50:
        warnings.append(
            "Revenue growth unusually high: verify acquisition or cyclical effects"
        )

    if eps_growth is not None and eps_growth > 100:
        warnings.append(
            "EPS growth unusually high: verify denominator and one-time items"
        )

    fields = {
        "Price": price,
        "PE": pe,
        "Forward PE": forward_pe,
        "Price/Book": price_to_book,
        "PEG": peg,
        "ROE": roe,
        "Operating Margin": operating_margin,
        "Revenue CAGR": revenue_cagr,
        "EPS CAGR": eps_cagr,
    }

    if not is_financial_company(sector, industry):
        fields["Free Cash Flow"] = free_cash_flow

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
        "Price/Book": price_to_book,
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
        "Revenue Growth Source": revenue_growth_source,

        "Company Name": company_name,
        "Sector": sector,
        "Industry": industry,
        "Description": description,
        "ROE": roe,
        "ROE Score": roe_score,
        "Operating Margin": operating_margin,
        "Operating Margin Score": operating_margin_score,
        "EPS Growth": eps_growth,
        "EPS Growth Source": eps_growth_source,
        "TTM EPS Growth": eps_growth,
        "EPS Growth Score": eps_growth_score,
        "Revenue Growth Score": revenue_growth_score,
        "Revenue CAGR": revenue_cagr,
        "Revenue CAGR Score": revenue_cagr_score,

        "Quality Score": quality_score,
        "Quality Coverage": quality_coverage,
        "Quality Normalized": quality_normalized,
        "Growth Score": growth_score,
        "Growth Coverage": growth_coverage,
        "Growth Normalized": growth_normalized,
        "Quality Components": len(quality_components),
        "Growth Components": len(growth_components),

        "Total Score": total_score,
        "Overall Normalized": overall_normalized,
        "Data Quality": data_quality,
        "Data Quality Status": data_quality_status,
        "PE Score": pe_score,
        "PEG Score": peg_score,
        "Valuation Score": valuation_score,
        "Valuation Coverage": valuation_coverage,
        "Valuation Normalized": valuation_normalized,
        "Valuation Components": len(valuation_components),

        "200 DMA": sma200,
        "200 DMA Score": dma_score,
        "Technical Score": technical_score,
        "Technical Coverage": technical_coverage,
        "Technical Normalized": technical_normalized,
        "Technical Components": len(technical_components),
        "Earnings Date": earnings_date,

        "EPS CAGR": eps_cagr,
        "EPS CAGR Score": eps_cagr_score,
        "RSI": rsi,
        "RSI Score": rsi_score,
        "Relative Strength": relative_strength,
        "Relative Strength Score": relative_strength_score,
        "Data Warnings": list(dict.fromkeys(warnings)),
    }