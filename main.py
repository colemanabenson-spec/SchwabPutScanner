from scanner.fundamentals import analyze_stock


def status(score):

    if score >= 1:
        return "✅"

    elif score >= 0.5:
        return "⚠️"

    return "❌"


def format_percent(value):

    if value is None:
        return "N/A"

    return f"{value:.1f}%"


def format_number(value, decimals=2):

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
    "PFE",
    "C"
]


for ticker in stocks:

    result = analyze_stock(ticker)

    print()
    print("=" * 80)
    print(f"{result['Company Name']} ({ticker})")
    print("=" * 80)

    print()
    print(f"Sector: {result['Sector']}")
    print(f"Industry: {result['Industry']}")

    print()

    print("SUMMARY")
    print("-" * 40)

    print(
        f"Quality Score: "
        f"{result['Quality Score']:.1f}"
    )

    print(
        f"Growth Score: "
        f"{result['Growth Score']:.1f}"
    )

    print(
        f"Valuation Score: "
        f"{result['Valuation Score']:.1f}"
    )

    print(
        f"Technical Score: "
        f"{result['Technical Score']:.1f}"
    )

    print()

    print(
        f"TOTAL SCORE: "
        f"{result['Total Score']:.1f} / 10.0"
    )

    print()

    print("NEXT EARNINGS")
    print("-" * 40)

    if result.get("Earnings Date"):
        print(result["Earnings Date"])
    else:
        print("N/A")

    print()

    print("VERDICT")
    print("-" * 40)

    if result["Quality Score"] >= 1.5:
        print("✅ High Quality")
    else:
        print("⚠️ Below Target Quality")

    if result["Growth Score"] >= 2:
        print("✅ Strong Growth")

    if result["Valuation Score"] >= 2:
        print("✅ Attractive Valuation")
    else:
        print("⚠️ Expensive")

    if result["Technical Score"] >= 1:
        print("✅ Positive Trend")
    else:
        print("❌ Below 200 Day Moving Average")

    print()

    print("COMPANY PROFILE")
    print("-" * 40)

    if result["Description"]:
        print(result["Description"][:300] + "...")
    else:
        print("N/A")

    print()

    print("QUALITY")
    print("-" * 40)

    print(
        f"ROE "
        f"{status(result['ROE Score'])} "
        f"{format_percent(result['ROE'])}"
    )

    print(
        f"Operating Margin "
        f"{status(result['Operating Margin Score'])} "
        f"{format_percent(result['Operating Margin'])}"
    )

    print()

    print(
        f"Quality Score: "
        f"{result['Quality Score']:.1f}"
    )

    print()

    print("GROWTH")
    print("-" * 40)

    print(
        f"Revenue Growth "
        f"{status(result['Revenue Growth Score'])} "
        f"{format_percent(result['Revenue Growth'])}"
    )

    print(
        f"Revenue CAGR "
        f"{status(result['Revenue CAGR Score'])} "
        f"{format_percent(result['Revenue CAGR'])}"
    )

    print(
        f"EPS Growth "
        f"{status(result['EPS Growth Score'])} "
        f"{format_percent(result['EPS Growth'])}"
    )

    print(
        f"EPS CAGR "
        f"{status(result['EPS CAGR Score'])} "
        f"{format_percent(result['EPS CAGR'])}"
    )

    print()

    print(
        f"Growth Score: "
        f"{result['Growth Score']:.1f}"
    )

    print()

    print("VALUATION")
    print("-" * 40)

    if result["Price"] is not None:
        print(f"Price ${result['Price']:.2f}")
    else:
        print("Price N/A")

    print(
        f"PE Ratio "
        f"{status(result['PE Score'])} "
        f"{format_number(result['PE'], 1)}"
    )

    print(
        f"PEG Ratio "
        f"{status(result['PEG Score'])} "
        f"{format_number(result['PEG'], 2)}"
    )

    fcf_text = (
        f"{result['FCF Yield'] * 100:.2f}%"
        if result["FCF Yield"] is not None
        else "N/A"
    )

    print(
        f"FCF Yield "
        f"{status(result['FCF Score'])} "
        f"{fcf_text}"
    )

    print()

    print(
        f"Valuation Score: "
        f"{result['Valuation Score']:.1f}"
    )

    print()

    print("TECHNICALS")
    print("-" * 40)

    print(
        f"Above 200 DMA "
        f"{'✅' if result['200 DMA Score'] else '❌'}"
    )

    if result["200 DMA"] is not None:
        print(
            f"200 DMA: "
            f"${result['200 DMA']:.2f}"
        )
    else:
        print("200 DMA: N/A")

    print()

    print(
        f"Technical Score: "
        f"{result['Technical Score']:.1f}"
    )

    print()