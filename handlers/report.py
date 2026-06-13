"""
报表处理器：提供今日、本周、本月三种维度的收支统计报表。
"""

from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import database as db
from utils import MAIN_KEYBOARD, format_report


def _get_week_range():
    """获取本周的起止日期（周一到今天）。"""
    today = date.today()
    start = today - timedelta(days=today.weekday())
    return start.isoformat(), today.isoformat()


def _get_month_range():
    """获取本月的起止日期（1日到今天）。"""
    today = date.today()
    start = today.replace(day=1)
    return start.isoformat(), today.isoformat()


REPORT_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📅 今日", callback_data="report:today"),
        InlineKeyboardButton("📆 本周", callback_data="report:week"),
        InlineKeyboardButton("🗓 本月", callback_data="report:month"),
    ],
    [InlineKeyboardButton("❌ 关闭", callback_data="cancel_report")],
])


async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """报表入口：显示报表时间范围选择键盘。"""
    await update.message.reply_text(
        "📊 *查看报表*\n\n请选择报表时间范围：",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=REPORT_KEYBOARD,
    )


async def report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理报表时间范围选择回调。"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    if data == "cancel_report":
        await query.edit_message_text("已关闭报表。")
        return

    if data == "report:today":
        today = date.today().isoformat()
        summary = db.get_summary_by_period(user_id, today, today)
        text = format_report("今日报表", summary)

    elif data == "report:week":
        start, end = _get_week_range()
        summary = db.get_summary_by_period(user_id, start, end)
        text = format_report(f"本周报表（{start} ~ {end}）", summary)

    elif data == "report:month":
        start, end = _get_month_range()
        summary = db.get_summary_by_period(user_id, start, end)
        text = format_report(f"本月报表（{start} ~ {end}）", summary)

    else:
        text = "❌ 未知的报表类型。"

    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
