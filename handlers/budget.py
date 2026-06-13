"""
预算管理处理器：支持设置、查看和清除月度预算。
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

import database as db
import states
from utils import MAIN_KEYBOARD, fmt_amount, check_budget_warning


BUDGET_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✏️ 设置预算", callback_data="budget:set"),
        InlineKeyboardButton("🗑 清除预算", callback_data="budget:clear"),
    ],
    [InlineKeyboardButton("❌ 关闭", callback_data="budget:close")],
])


async def budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """预算管理入口：显示当前预算信息和操作选项。"""
    user_id = update.effective_user.id
    budget = db.get_budget(user_id)
    current_expense = db.get_current_month_expense(user_id)

    if budget:
        remaining = budget - current_expense
        ratio = current_expense / budget * 100
        status = (
            f"💳 *月度预算管理*\n\n"
            f"预算金额：¥{fmt_amount(budget)}\n"
            f"本月已支出：¥{fmt_amount(current_expense)}\n"
            f"剩余预算：¥{fmt_amount(remaining)}\n"
            f"使用率：{ratio:.1f}%"
        )
    else:
        status = "💳 *月度预算管理*\n\n当前未设置月度预算。"

    await update.message.reply_text(
        status,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=BUDGET_KEYBOARD,
    )
    return states.BUDGET_SET


async def budget_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理预算操作选择回调。"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    data = query.data
    if data == "budget:close":
        await query.edit_message_text("已关闭预算管理。")
        return ConversationHandler.END

    elif data == "budget:clear":
        db.clear_budget(user_id)
        await query.edit_message_text("✅ 月度预算已清除。")
        return ConversationHandler.END

    elif data == "budget:set":
        await query.edit_message_text(
            "✏️ 请输入月度预算金额（例如：5000）："
        )
        return states.BUDGET_SET

    return ConversationHandler.END


async def budget_set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收预算金额输入并保存。"""
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ 金额格式不正确，请输入正数（例如：5000）："
        )
        return states.BUDGET_SET

    user_id = update.effective_user.id
    db.set_budget(user_id, amount)

    current_expense = db.get_current_month_expense(user_id)
    warning = check_budget_warning(amount, current_expense)

    msg = f"✅ 月度预算已设置为 ¥{fmt_amount(amount)}。{warning}"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


async def cancel_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消预算管理流程。"""
    await update.message.reply_text("❌ 已取消预算管理。", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END
