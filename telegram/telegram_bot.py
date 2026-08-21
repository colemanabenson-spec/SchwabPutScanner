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

        reply = f"""
📊 {result['Company Name']} ({ticker})

Sector: {result['Sector']}
Industry: {result['Industry']}

━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━

Quality Score: {result['Quality Score']:.1f}
Growth Score: {result['Growth Score']:.1f}
Valuation Score: {result['Valuation Score']:.1f}
Technical Score: {result['Technical Score']:.1f}

🏆 TOTAL SCORE:
{result['Total Score']:.1f} / 10.0

📅 Next Earnings:
{earnings}

━━━━━━━━━━━━━━━━━━
QUALITY
━━━━━━━━━━━━━━━━━━

ROE
{status(result['ROE Score'])}
{percent(result['ROE'])}

Operating Margin
{status(result['Operating Margin Score'])}
{percent(result['Operating Margin'])}

━━━━━━━━━━━━━━━━━━
GROWTH
━━━━━━━━━━━━━━━━━━

Revenue Growth
{status(result['Revenue Growth Score'])}
{percent(result['Revenue Growth'])}

Revenue CAGR
{status(result['Revenue CAGR Score'])}
{percent(result['Revenue CAGR'])}

EPS Growth
{status(result['EPS Growth Score'])}
{percent(result['EPS Growth'])}

EPS CAGR
{status(result['EPS CAGR Score'])}
{percent(result['EPS CAGR'])}

━━━━━━━━━━━━━━━━━━
VALUATION
━━━━━━━━━━━━━━━━━━

Price
{price}

PE Ratio
{status(result['PE Score'])}
{number(result['PE'], 1)}

PEG Ratio
{status(result['PEG Score'])}
{number(result['PEG'], 2)}

FCF Yield
{status(result['FCF Score'])}
{fcf_yield}

━━━━━━━━━━━━━━━━━━
TECHNICALS
━━━━━━━━━━━━━━━━━━

Above 200 DMA
{'✅' if result['200 DMA Score'] else '❌'}

200 DMA
{dma}
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