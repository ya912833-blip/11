"""
工具函数：格式化输出、键盘构建等公共辅助函数。
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Tuple


# ─────────────────────── 主菜单键盘 ───────────────────────

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["💰 记录收入", "💸 记录支出"],
        ["📊 查看报表", "💳 预算管理"],
        ["📁 分类管理", "📤 导出数据"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


# ─────────────────────── 金额格式化 ───────────────────────

def fmt_amount(amount: float) -> str:
    """将金额格式化为带千分位的字符串，保留两位小数。"""
    return f"{amount:,.2f}"


# ─────────────────────── 报表格式化 ───────────────────────

def format_report(title: str, summary: dict) -> str:
    """
    将汇总数据格式化为可读的报表文本。

    参数：
        title: 报表标题（如"今日报表"）
        summary: get_summary_by_period 返回的字典
    """
    total_income = summary["total_income"]
    total_expense = summary["total_expense"]
    net = total_income - total_expense

    lines = [
        f"📊 *{title}*",
        "",
        f"💰 总收入：`¥{fmt_amount(total_income)}`",
        f"💸 总支出：`¥{fmt_amount(total_expense)}`",
        f"📈 净结余：`¥{fmt_amount(net)}`",
    ]

    if summary["income_by_category"]:
        lines.append("")
        lines.append("*收入明细：*")
        for cat, total in summary["income_by_category"]:
            lines.append(f"  • {cat}：¥{fmt_amount(total)}")

    if summary["expense_by_category"]:
        lines.append("")
        lines.append("*支出明细：*")
        for cat, total in summary["expense_by_category"]:
            lines.append(f"  • {cat}：¥{fmt_amount(total)}")

    if not summary["income_by_category"] and not summary["expense_by_category"]:
        lines.append("")
        lines.append("_该时段暂无收支记录。_")

    return "\n".join(lines)


# ─────────────────────── 分类内联键盘 ───────────────────────

def build_category_keyboard(categories, callback_prefix: str) -> InlineKeyboardMarkup:
    """
    根据分类列表构建内联键盘。

    参数：
        categories: 分类 Row 列表
        callback_prefix: 回调数据前缀，如 "income_cat" 或 "expense_cat"
    """
    buttons = []
    row = []
    for i, cat in enumerate(categories):
        row.append(InlineKeyboardButton(
            text=cat["name"],
            callback_data=f"{callback_prefix}:{cat['id']}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ 取消", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def build_delete_category_keyboard(categories) -> InlineKeyboardMarkup:
    """构建用于删除分类的内联键盘（仅显示非默认分类）。"""
    custom_cats = [c for c in categories if c["is_default"] == 0]
    if not custom_cats:
        return None
    buttons = []
    for cat in custom_cats:
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {cat['name']}",
            callback_data=f"del_cat:{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton("❌ 取消", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


# ─────────────────────── 预算提醒检查 ───────────────────────

def check_budget_warning(budget: float, current_expense: float) -> str:
    """
    检查预算使用情况，返回提醒文本（无需提醒则返回空字符串）。

    规则：
        - 使用率 >= 100%：超支警告
        - 使用率 >= 80%：接近预算警告
    """
    if budget <= 0:
        return ""
    ratio = current_expense / budget
    remaining = budget - current_expense
    if ratio >= 1.0:
        return (
            f"\n\n⚠️ *预算警告*：本月支出已超出预算！\n"
            f"预算：¥{fmt_amount(budget)}，"
            f"已支出：¥{fmt_amount(current_expense)}，"
            f"超出：¥{fmt_amount(-remaining)}"
        )
    elif ratio >= 0.8:
        return (
            f"\n\n⚠️ *预算提醒*：本月支出已达预算的 {ratio*100:.0f}%，请注意控制支出。\n"
            f"预算：¥{fmt_amount(budget)}，"
            f"剩余：¥{fmt_amount(remaining)}"
        )
    return ""
