"""
收入记录处理器：引导用户完成收入记录的多步对话流程。
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

import database as db
import states
from utils import MAIN_KEYBOARD, build_category_keyboard, check_budget_warning, fmt_amount


async def income_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """收入流程入口：提示用户输入金额。"""
    await update.message.reply_text(
        "💰 *记录收入*\n\n请输入收入金额（例如：1500 或 1500.50）：",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ 取消", callback_data="cancel")]]
        ),
    )
    return states.INCOME_AMOUNT


async def income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收金额输入，验证后展示分类选择。"""
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ 金额格式不正确，请输入正数（例如：1500 或 1500.50）："
        )
        return states.INCOME_AMOUNT

    context.user_data["income_amount"] = amount
    categories = db.get_categories("income")
    keyboard = build_category_keyboard(categories, "income_cat")
    await update.message.reply_text(
        f"✅ 金额：¥{fmt_amount(amount)}\n\n请选择收入分类：",
        reply_markup=keyboard,
    )
    return states.INCOME_CATEGORY


async def income_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收分类选择，提示输入备注。"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ 已取消记录收入。")
        await query.message.reply_text("操作已取消，返回主菜单。", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    cat_id = int(data.split(":")[1])
    cat = db.get_category_by_id(cat_id)
    if not cat:
        await query.edit_message_text("❌ 分类不存在，请重新选择。")
        return states.INCOME_CATEGORY

    context.user_data["income_category_id"] = cat_id
    context.user_data["income_category_name"] = cat["name"]

    await query.edit_message_text(
        f"✅ 分类：{cat['name']}\n\n请输入备注（可直接发送\u300c无\u300d跳过）："
    )
    return states.INCOME_NOTE


async def income_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收备注，完成收入记录并检查预算。"""
    note = update.message.text.strip()
    if note == "无":
        note = ""

    user_id = update.effective_user.id
    amount = context.user_data["income_amount"]
    cat_id = context.user_data["income_category_id"]
    cat_name = context.user_data["income_category_name"]

    db.add_transaction(user_id, "income", amount, cat_id, note)

    msg = (
        f"✅ *收入记录成功！*\n\n"
        f"💰 金额：¥{fmt_amount(amount)}\n"
        f"📂 分类：{cat_name}\n"
        f"📝 备注：{note or '无'}"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消收入记录流程。"""
    context.user_data.clear()
    await update.message.reply_text("❌ 已取消记录收入。", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END
