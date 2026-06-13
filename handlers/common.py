"""
通用命令处理器：/start、/help、/cancel 等基础命令。
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from utils import MAIN_KEYBOARD

HELP_TEXT = """
📖 *收支记录 Bot 使用帮助*

*快捷菜单功能：*
• 💰 记录收入 — 按步骤输入金额、分类和备注
• 💸 记录支出 — 按步骤输入金额、分类和备注
• 📊 查看报表 — 选择今日/本周/本月统计
• 💳 预算管理 — 设置或清除月度预算
• 📁 分类管理 — 查看、添加或删除自定义分类
• 📤 导出数据 — 获取 CSV 格式的全部记录

*命令列表：*
• /start — 启动机器人并显示主菜单
• /help — 查看此帮助信息
• /income — 记录收入
• /expense — 记录支出
• /report — 查看报表
• /budget — 预算管理
• /categories — 分类管理
• /export — 导出数据为 CSV
• /cancel — 取消当前正在进行的操作

*使用提示：*
在任意流程中发送 /cancel 可随时取消当前操作并返回主菜单。
""".strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令，发送欢迎信息并显示主菜单。"""
    user = update.effective_user
    name = user.first_name or "用户"
    await update.message.reply_text(
        f"👋 你好，{name}！欢迎使用*收支记录 Bot*。\n\n"
        "使用底部快捷菜单或命令开始记录你的收支吧！\n"
        "发送 /help 可查看完整帮助。",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KEYBOARD,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /help 命令，发送帮助文本。"""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KEYBOARD,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理 /cancel 命令，终止当前对话流程并返回主菜单。"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ 当前操作已取消，返回主菜单。",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理未识别的文本消息，提示用户使用菜单。"""
    await update.message.reply_text(
        "❓ 不明白你的意思，请使用底部菜单或发送 /help 查看帮助。",
        reply_markup=MAIN_KEYBOARD,
    )
