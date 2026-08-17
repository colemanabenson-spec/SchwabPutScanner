from scanner.fundamentals import check_fundamentals

stocks = ["AAPL", "CF", "BAC", "F", "AMD", "DVN", "PFE", "C"]

for ticker in stocks:

    result = check_fundamentals(ticker)

    market_cap = result["Market Cap"]

    if market_cap is not None:
        market_cap_display = f"${market_cap / 1_000_000_000:.2f}B"
    else:
        market_cap_display = "N/A"

    fcf_yield = result["FCF Yield"]

    if fcf_yield is not None:
        fcf_yield_display = f"{fcf_yield * 100:.2f}%"
    else:
        fcf_yield_display = "N/A"

    print("\n")
    print(f"{ticker} Analysis")
    print("-" * 40)

    print(f"Market Cap      {'✅' if result['Market Cap Pass'] else '❌'}  {market_cap_display}")
    print(f"Price           {'✅' if result['Price Pass'] else '❌'}  {result['Price']}")
    print(f"PE Ratio        {'✅' if result['PE Pass'] else '❌'}  {result['PE']}")
    print(f"PEG Ratio       ℹ️   {result['PEG']}")
    print(f"FCF Yield       {'✅' if result['FCF Pass'] else '❌'}  {fcf_yield_display}")
    print(f"Current Ratio   {'✅' if result['Current Ratio Pass'] else '❌'}  {result['Current Ratio']}")
    debt_equity = result["Debt/Equity"]

    if debt_equity is not None:
        debt_display = f"{debt_equity:.1f}%"
    else:
        debt_display = "N/A"

    print(f"Debt/Equity     {'✅' if result['Debt/Equity Pass'] else '❌'}  {debt_display}")
    print(f"Revenue Growth  {'✅' if result['Revenue Growth Pass'] else '❌'}  {result['Revenue Growth']}")

    print()
    print(f"Fundamental Score: {result['Fundamental Score']}/7")

    if result["Passes Fundamentals"]:
        print("OVERALL: PASS ✅")
    else:
        print("OVERALL: FAIL ❌")