"""
支出记录处理器：引导用户完成支出记录的多步对话流程，并在完成后检查预算。
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

import database as db
import states
from utils import MAIN_KEYBOARD, build_category_keyboard, check_budget_warning, fmt_amount


async def expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """支出流程入口：提示用户输入金额。"""
    await update.message.reply_text(
        "💸 *记录支出*\n\n请输入支出金额（例如：88 或 88.50）：",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ 取消", callback_data="cancel")]]
        ),
    )
    return states.EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收金额输入，验证后展示分类选择。"""
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ 金额格式不正确，请输入正数（例如：88 或 88.50）："
        )
        return states.EXPENSE_AMOUNT

    context.user_data["expense_amount"] = amount
    categories = db.get_categories("expense")
    keyboard = build_category_keyboard(categories, "expense_cat")
    await update.message.reply_text(
        f"✅ 金额：¥{fmt_amount(amount)}\n\n请选择支出分类：",
        reply_markup=keyboard,
    )
    return states.EXPENSE_CATEGORY


async def expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收分类选择，提示输入备注。"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ 已取消记录支出。")
        await query.message.reply_text("操作已取消，返回主菜单。", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    cat_id = int(data.split(":")[1])
    cat = db.get_category_by_id(cat_id)
    if not cat:
        await query.edit_message_text("❌ 分类不存在，请重新选择。")
        return states.EXPENSE_CATEGORY

    context.user_data["expense_category_id"] = cat_id
    context.user_data["expense_category_name"] = cat["name"]

    await query.edit_message_text(
        f"✅ 分类：{cat['name']}\n\n请输入备注（可直接发送\u300c无\u300d跳过）："
    )
    return states.EXPENSE_NOTE


async def expense_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收备注，完成支出记录并检查预算提醒。"""
    note = update.message.text.strip()
    if note == "无":
        note = ""

    user_id = update.effective_user.id
    amount = context.user_data["expense_amount"]
    cat_id = context.user_data["expense_category_id"]
    cat_name = context.user_data["expense_category_name"]

    db.add_transaction(user_id, "expense", amount, cat_id, note)

    msg = (
        f"✅ *支出记录成功！*\n\n"
        f"💸 金额：¥{fmt_amount(amount)}\n"
        f"📂 分类：{cat_name}\n"
        f"📝 备注：{note or '无'}"
    )

    # 检查预算
    budget = db.get_budget(user_id)
    if budget:
        current_expense = db.get_current_month_expense(user_id)
        warning = check_budget_warning(budget, current_expense)
        msg += warning

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消支出记录流程。"""
    context.user_data.clear()
    await update.message.reply_text("❌ 已取消记录支出。", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END
