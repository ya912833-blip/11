"""
主程序入口：初始化数据库，注册所有命令处理器和对话流程，启动 Bot。
"""

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

import database as db
import states
from handlers.common import start, help_command, cancel, unknown_message
from handlers.income import (
    income_start, income_amount, income_category, income_note, cancel_income
)
from handlers.expense import (
    expense_start, expense_amount, expense_category, expense_note, cancel_expense
)
from handlers.report import report_start, report_callback
from handlers.budget import (
    budget_start, budget_callback, budget_set_amount, cancel_budget
)
from handlers.categories import (
    categories_start, category_type_callback, category_action_callback,
    category_add_name, category_delete_callback, cancel_categories
)
from handlers.export import export_data

# ─────────────────────── 日志配置 ───────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """初始化并启动 Telegram Bot。"""
    # 初始化数据库
    db.init_db()
    logger.info("数据库初始化完成。")

    # 读取 Bot Token
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("环境变量 BOT_TOKEN 未设置，请在 .env 文件中配置。")

    app = Application.builder().token(token).build()

    # ── 收入记录对话流程 ──
    income_conv = ConversationHandler(
        entry_points=[
            CommandHandler("income", income_start),
            MessageHandler(filters.Regex("^💰 记录收入$"), income_start),
        ],
        states={
            states.INCOME_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, income_amount)
            ],
            states.INCOME_CATEGORY: [
                CallbackQueryHandler(income_category, pattern=r"^income_cat:|^cancel$")
            ],
            states.INCOME_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, income_note)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_income),
            MessageHandler(filters.COMMAND, cancel_income),
        ],
        allow_reentry=True,
    )

    # ── 支出记录对话流程 ──
    expense_conv = ConversationHandler(
        entry_points=[
            CommandHandler("expense", expense_start),
            MessageHandler(filters.Regex("^💸 记录支出$"), expense_start),
        ],
        states={
            states.EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)
            ],
            states.EXPENSE_CATEGORY: [
                CallbackQueryHandler(expense_category, pattern=r"^expense_cat:|^cancel$")
            ],
            states.EXPENSE_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_note)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_expense),
            MessageHandler(filters.COMMAND, cancel_expense),
        ],
        allow_reentry=True,
    )

    # ── 预算管理对话流程 ──
    budget_conv = ConversationHandler(
        entry_points=[
            CommandHandler("budget", budget_start),
            MessageHandler(filters.Regex("^💳 预算管理$"), budget_start),
        ],
        states={
            states.BUDGET_SET: [
                CallbackQueryHandler(budget_callback, pattern=r"^budget:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, budget_set_amount),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_budget),
            MessageHandler(filters.COMMAND, cancel_budget),
        ],
        allow_reentry=True,
    )

    # ── 分类管理对话流程 ──
    categories_conv = ConversationHandler(
        entry_points=[
            CommandHandler("categories", categories_start),
            MessageHandler(filters.Regex("^📁 分类管理$"), categories_start),
        ],
        states={
            states.CATEGORY_TYPE: [
                CallbackQueryHandler(category_type_callback, pattern=r"^cat_type:|^cancel$")
            ],
            states.CATEGORY_ACTION: [
                CallbackQueryHandler(category_action_callback, pattern=r"^cat_action:|^cancel$")
            ],
            states.CATEGORY_ADD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_add_name)
            ],
            states.CATEGORY_DELETE_SELECT: [
                CallbackQueryHandler(category_delete_callback, pattern=r"^del_cat:|^cancel$")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_categories),
            MessageHandler(filters.COMMAND, cancel_categories),
        ],
        allow_reentry=True,
    )

    # ── 注册所有处理器 ──
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(income_conv)
    app.add_handler(expense_conv)
    app.add_handler(budget_conv)
    app.add_handler(categories_conv)

    # 报表（无状态，直接回调）
    app.add_handler(CommandHandler("report", report_start))
    app.add_handler(MessageHandler(filters.Regex("^📊 查看报表$"), report_start))
    app.add_handler(CallbackQueryHandler(report_callback, pattern=r"^report:|^cancel_report$"))

    # 导出数据
    app.add_handler(CommandHandler("export", export_data))
    app.add_handler(MessageHandler(filters.Regex("^📤 导出数据$"), export_data))

    # 全局 cancel 命令
    app.add_handler(CommandHandler("cancel", cancel))

    # 未识别消息（放在最后）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    logger.info("Bot 启动中...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
