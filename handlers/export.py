"""
导出处理器：将用户所有收支记录导出为 CSV 文件并发送。
"""

import csv
import io
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

import database as db
from utils import MAIN_KEYBOARD


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """导出所有收支记录为 CSV 文件并通过 Telegram 发送给用户。"""
    user_id = update.effective_user.id
    rows = db.get_all_transactions(user_id)

    if not rows:
        await update.message.reply_text(
            "📤 当前没有任何收支记录可以导出。",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    # 使用内存缓冲区生成 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "类型", "金额(¥)", "分类", "备注", "记录时间"])

    for row in rows:
        trans_type = "收入" if row["type"] == "income" else "支出"
        writer.writerow([
            row["id"],
            trans_type,
            f"{row['amount']:.2f}",
            row["category_name"],
            row["note"] or "",
            row["created_at"],
        ])

    output.seek(0)
    csv_bytes = output.getvalue().encode("utf-8-sig")  # 带 BOM，Excel 兼容

    filename = f"finance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    bio = io.BytesIO(csv_bytes)
    bio.name = filename

    await update.message.reply_document(
        document=bio,
        filename=filename,
        caption=f"📤 已导出 {len(rows)} 条收支记录。",
        reply_markup=MAIN_KEYBOARD,
    )
