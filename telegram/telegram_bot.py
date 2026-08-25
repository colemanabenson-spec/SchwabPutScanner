import sys
import os

# Allow Python to find the scanner folder
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

from scanner.fundamentals import analyze_stock

BOT_TOKEN = "8829569608:AAGeIHl3vBs_nC6OL9EM1yOHcq2_XdV6slA"


def percent(value):

    if value is None:
        return "N/A"

    return f"{value:.1f}%"


def number(value, decimals=2):

    if value is None:
        return "N/A"

    return f"{value:.{decimals}f}"


def status(score):

    if score >= 1:
        return "✅"

    elif score >= 0.5:
        return "⚠️"

    return "❌"


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    ticker = (
        update.message.text
        .upper()
        .strip()
    )

    try:

        result = analyze_stock(ticker)

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

        earnings = (
            result["Earnings Date"]
            if result["Earnings Date"]
            else "N/A"
        )

        warnings = result.get("Data Warnings", [])

        warning_text = (
            "\n⚠️ DATA NOT FOUND\n"
            + "\n".join(f"• {warning}" for warning in warnings)
            if warnings
            else "\n✅ Data loaded successfully"
        )

        roic_line = (
            f"ROIC {status(result['ROIC Score'])} "
            f"{percent(result['ROIC'])}\n"
            if result["ROIC"] is not None
            else ""
        )

        reply = f"""
==============================
{result['Company Name']} ({ticker})
==============================

{warning_text}

Sector: {result['Sector']}
Industry: {result['Industry']}

COMPANY PROFILE
----------------------------------------
{result['Description'][:300] + '...' if result['Description'] else 'N/A'}

QUALITY
----------------------------------------
ROE {status(result['ROE Score'])} {percent(result['ROE'])}
{roic_line}Operating Margin {status(result['Operating Margin Score'])} {percent(result['Operating Margin'])}
Debt/Equity {percent(result['Debt/Equity'])}

Quality Score: {result['Quality Score']:.1f}

GROWTH
----------------------------------------
Revenue Growth {status(result['Revenue Growth Score'])} {percent(result['Revenue Growth'])}
Revenue CAGR {status(result['Revenue CAGR Score'])} {percent(result['Revenue CAGR'])}
EPS Growth {status(result['EPS Growth Score'])} {percent(result['EPS Growth'])}
EPS CAGR {status(result['EPS CAGR Score'])} {percent(result['EPS CAGR'])}

Growth Score: {result['Growth Score']:.1f}

VALUATION
----------------------------------------
Price {price}
PE Ratio {status(result['PE Score'])} {number(result['PE'], 1)}
Forward PE {number(result['Forward PE'], 1)}
PEG Ratio {status(result['PEG Score'])} {number(result['PEG'], 2)}
FCF Yield {status(result['FCF Score'])} {fcf_yield}

Valuation Score: {result['Valuation Score']:.1f}

TECHNICALS
----------------------------------------
Above 200 DMA {'✅' if result['200 DMA Score'] else '❌'}
200 DMA: {dma}
RSI {status(result['RSI Score'])} {number(result['RSI'], 1)}
Relative Strength {status(result['Relative Strength Score'])} {percent(result['Relative Strength'])}

Technical Score: {result['Technical Score']:.1f}

SUMMARY
----------------------------------------
Quality Score: {result['Quality Score']:.1f}
Growth Score: {result['Growth Score']:.1f}
Valuation Score: {result['Valuation Score']:.1f}
Technical Score: {result['Technical Score']:.1f}

TOTAL SCORE: {result['Total Score']:.1f} / 13.0

NEXT EARNINGS
----------------------------------------
{result['Earnings Date'] if result['Earnings Date'] else 'N/A'}

VERDICT
----------------------------------------
{'✅ High Quality' if result['Quality Score'] >= 2 else '⚠️ Below Target Quality'}
{'✅ Strong Growth' if result['Growth Score'] >= 2.5 else ''}
{'✅ Attractive Valuation' if result['Valuation Score'] >= 2 else '⚠️ Expensive'}
{'✅ Positive Trend' if result['Technical Score'] >= 1 else '❌ Below 200 Day Moving Average'}

"""

        await update.message.reply_text(
            reply
        )

    except Exception as e:

        await update.message.reply_text(
            f"Error analyzing ticker '{ticker}'\n\n{e}"
        )


app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("Bot is running...")

app.run_polling()