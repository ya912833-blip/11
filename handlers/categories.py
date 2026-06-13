"""
分类管理处理器：支持查看、添加和删除自定义收支分类。
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

import database as db
import states
from utils import MAIN_KEYBOARD, build_delete_category_keyboard


CAT_TYPE_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("💰 收入分类", callback_data="cat_type:income"),
        InlineKeyboardButton("💸 支出分类", callback_data="cat_type:expense"),
    ],
    [InlineKeyboardButton("❌ 取消", callback_data="cancel")],
])


def _build_action_keyboard(cat_type: str) -> InlineKeyboardMarkup:
    """构建分类操作选项键盘（查看/添加/删除）。"""
    type_label = "收入" if cat_type == "income" else "支出"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"📋 查看{type_label}分类", callback_data=f"cat_action:view:{cat_type}"),
            InlineKeyboardButton(f"➕ 添加{type_label}分类", callback_data=f"cat_action:add:{cat_type}"),
        ],
        [
            InlineKeyboardButton(f"🗑 删除{type_label}分类", callback_data=f"cat_action:delete:{cat_type}"),
        ],
        [InlineKeyboardButton("❌ 取消", callback_data="cancel")],
    ])


async def categories_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """分类管理入口：选择分类类型。"""
    await update.message.reply_text(
        "📁 *分类管理*\n\n请选择要管理的分类类型：",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=CAT_TYPE_KEYBOARD,
    )
    return states.CATEGORY_TYPE


async def category_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理分类类型选择回调，展示操作选项。"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ 已取消分类管理。")
        return ConversationHandler.END

    cat_type = data.split(":")[1]
    context.user_data["cat_type"] = cat_type
    type_label = "收入" if cat_type == "income" else "支出"

    await query.edit_message_text(
        f"📁 *{type_label}分类管理*\n\n请选择操作：",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_build_action_keyboard(cat_type),
    )
    return states.CATEGORY_ACTION


async def category_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理分类操作选择回调（查看/添加/删除）。"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ 已取消分类管理。")
        return ConversationHandler.END

    parts = data.split(":")
    action = parts[1]
    cat_type = parts[2]
    context.user_data["cat_type"] = cat_type
    type_label = "收入" if cat_type == "income" else "支出"
    categories = db.get_categories(cat_type)

    if action == "view":
        if not categories:
            await query.edit_message_text(f"暂无{type_label}分类。")
        else:
            lines = [f"📋 *{type_label}分类列表：*\n"]
            for cat in categories:
                tag = "（默认）" if cat["is_default"] else "（自定义）"
                lines.append(f"  • {cat['name']} {tag}")
            await query.edit_message_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
            )
        return ConversationHandler.END

    elif action == "add":
        await query.edit_message_text(
            f"➕ 请输入要添加的{type_label}分类名称："
        )
        return states.CATEGORY_ADD_NAME

    elif action == "delete":
        custom_cats = [c for c in categories if c["is_default"] == 0]
        if not custom_cats:
            await query.edit_message_text(
                f"当前没有可删除的自定义{type_label}分类（默认分类不可删除）。"
            )
            return ConversationHandler.END
        keyboard = build_delete_category_keyboard(categories)
        await query.edit_message_text(
            f"🗑 请选择要删除的{type_label}分类（仅显示自定义分类）：",
            reply_markup=keyboard,
        )
        return states.CATEGORY_DELETE_SELECT

    return ConversationHandler.END


async def category_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """接收新分类名称并保存。"""
    name = update.message.text.strip()
    cat_type = context.user_data.get("cat_type", "expense")
    type_label = "收入" if cat_type == "income" else "支出"

    if not name or len(name) > 20:
        await update.message.reply_text(
            "❌ 分类名称不能为空且不超过 20 个字符，请重新输入："
        )
        return states.CATEGORY_ADD_NAME

    success = db.add_category(name, cat_type)
    if success:
        await update.message.reply_text(
            f"✅ {type_label}分类「{name}」添加成功！",
            reply_markup=MAIN_KEYBOARD,
        )
    else:
        await update.message.reply_text(
            f"❌ {type_label}分类「{name}」已存在，无需重复添加。",
            reply_markup=MAIN_KEYBOARD,
        )
    context.user_data.clear()
    return ConversationHandler.END


async def category_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理删除分类选择回调。"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ 已取消删除分类。")
        return ConversationHandler.END

    cat_id = int(data.split(":")[1])
    cat = db.get_category_by_id(cat_id)
    if not cat:
        await query.edit_message_text("❌ 分类不存在。")
        return ConversationHandler.END

    success = db.delete_category(cat_id)
    if success:
        await query.edit_message_text(f"✅ 分类「{cat['name']}」已删除。")
    else:
        await query.edit_message_text(
            f"❌ 分类「{cat['name']}」无法删除（该分类下存在收支记录）。"
        )
    return ConversationHandler.END


async def cancel_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消分类管理流程。"""
    context.user_data.clear()
    await update.message.reply_text("❌ 已取消分类管理。", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END
