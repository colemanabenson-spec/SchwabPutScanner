import sys
import os

# Allow Python to find the scanner folder
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from scanner.fundamentals import check_fundamentals

BOT_TOKEN = "8829569608:AAGeIHl3vBs_nC6OL9EM1yOHcq2_XdV6slA"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    ticker = update.message.text.upper().strip()

    try:

        result = check_fundamentals(ticker)

        market_cap = result["Market Cap"]
        market_cap_display = (
            f"${market_cap / 1_000_000_000:.2f}B"
            if market_cap is not None
            else "N/A"
        )

        fcf_yield = result["FCF Yield"]
        fcf_yield_display = (
            f"{fcf_yield * 100:.2f}%"
            if fcf_yield is not None
            else "N/A"
        )

        revenue_growth = result["Revenue Growth"]
        revenue_growth_display = (
            f"{revenue_growth * 100:.1f}%"
            if revenue_growth is not None
            else "N/A"
        )

        debt_equity = result["Debt/Equity"]
        debt_equity_display = (
            f"{debt_equity:.1f}%"
            if debt_equity is not None
            else "N/A"
        )

        reply = f"""
{ticker} Analysis
----------------------------------------

Market Cap      {'✅' if result['Market Cap Pass'] else '❌'}  {market_cap_display}
Price           {'✅' if result['Price Pass'] else '❌'}  ${result['Price']}
PE Ratio        {'✅' if result['PE Pass'] else '❌'}  {result['PE']}
PEG Ratio       ℹ️  {result['PEG']}
FCF Yield       {'✅' if result['FCF Pass'] else '❌'}  {fcf_yield_display}
Current Ratio   {'✅' if result['Current Ratio Pass'] else '❌'}  {result['Current Ratio']}
Debt/Equity     {'✅' if result['Debt/Equity Pass'] else '❌'}  {debt_equity_display}
Revenue Growth  {'✅' if result['Revenue Growth Pass'] else '❌'}  {revenue_growth_display}

Fundamental Score: {result['Fundamental Score']}/7

OVERALL: {'✅ PASS' if result['Passes Fundamentals'] else '❌ FAIL'}
"""

        await update.message.reply_text(reply)

    except Exception as e:

        await update.message.reply_text(
            f"Error analyzing ticker '{ticker}'\n\n{e}"
        )


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

print("Bot is running...")

app.run_polling()