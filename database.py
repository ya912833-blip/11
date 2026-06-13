"""
数据库模块：负责初始化 SQLite 数据库，提供所有数据访问操作。
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional, List, Tuple

DB_PATH = os.environ.get("DB_PATH", "./data/finance.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接，启用 WAL 模式和外键约束。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """初始化数据库，创建所有必要的表和默认分类数据。"""
    conn = get_connection()
    cursor = conn.cursor()

    # 创建分类表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            type     TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
            is_default INTEGER NOT NULL DEFAULT 0,
            UNIQUE(name, type)
        )
    """)

    # 创建收支记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
            amount      REAL    NOT NULL CHECK(amount > 0),
            category_id INTEGER NOT NULL REFERENCES categories(id),
            note        TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime'))
        )
    """)

    # 创建预算表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL UNIQUE,
            amount     REAL    NOT NULL CHECK(amount > 0),
            updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime'))
        )
    """)

    # 插入默认收入分类
    default_income = ["工资", "奖金", "投资收益", "兼职收入", "其他收入"]
    for name in default_income:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name, type, is_default) VALUES (?, 'income', 1)",
            (name,)
        )

    # 插入默认支出分类
    default_expense = ["餐饮", "交通", "购物", "娱乐", "医疗", "住房", "教育", "其他支出"]
    for name in default_expense:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name, type, is_default) VALUES (?, 'expense', 1)",
            (name,)
        )

    conn.commit()
    conn.close()


# ─────────────────────── 分类操作 ───────────────────────

def get_categories(cat_type: str) -> List[sqlite3.Row]:
    """获取指定类型的所有分类列表。"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM categories WHERE type = ? ORDER BY is_default DESC, name ASC",
        (cat_type,)
    ).fetchall()
    conn.close()
    return rows


def add_category(name: str, cat_type: str) -> bool:
    """添加自定义分类，若已存在则返回 False。"""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO categories (name, type, is_default) VALUES (?, ?, 0)",
            (name, cat_type)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def delete_category(cat_id: int) -> bool:
    """删除非默认分类，若为默认分类或存在关联记录则返回 False。"""
    conn = get_connection()
    row = conn.execute(
        "SELECT is_default FROM categories WHERE id = ?", (cat_id,)
    ).fetchone()
    if not row or row["is_default"] == 1:
        conn.close()
        return False
    # 检查是否有关联记录
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE category_id = ?", (cat_id,)
    ).fetchone()[0]
    if count > 0:
        conn.close()
        return False
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return True


def get_category_by_id(cat_id: int) -> Optional[sqlite3.Row]:
    """根据 ID 获取分类信息。"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
    conn.close()
    return row


# ─────────────────────── 收支记录操作 ───────────────────────

def add_transaction(user_id: int, trans_type: str, amount: float,
                    category_id: int, note: str = "") -> int:
    """新增一条收支记录，返回新记录的 ID。"""
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO transactions (user_id, type, amount, category_id, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, trans_type, amount, category_id, note)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_transactions_by_period(user_id: int, start: str, end: str) -> List[sqlite3.Row]:
    """获取指定时间段内的收支记录（start/end 格式：YYYY-MM-DD）。"""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT t.id, t.type, t.amount, t.note, t.created_at,
               c.name AS category_name
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ?
          AND DATE(t.created_at) BETWEEN ? AND ?
        ORDER BY t.created_at DESC
        """,
        (user_id, start, end)
    ).fetchall()
    conn.close()
    return rows


def get_all_transactions(user_id: int) -> List[sqlite3.Row]:
    """获取用户所有收支记录（用于导出）。"""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT t.id, t.type, t.amount, t.note, t.created_at,
               c.name AS category_name
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ?
        ORDER BY t.created_at DESC
        """,
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_summary_by_period(user_id: int, start: str, end: str) -> dict:
    """
    统计指定时间段内的收支汇总，返回结构：
    {
        'total_income': float,
        'total_expense': float,
        'income_by_category': [(category_name, total), ...],
        'expense_by_category': [(category_name, total), ...],
    }
    """
    conn = get_connection()

    def _query(trans_type: str):
        return conn.execute(
            """
            SELECT c.name AS category_name, SUM(t.amount) AS total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
              AND t.type = ?
              AND DATE(t.created_at) BETWEEN ? AND ?
            GROUP BY c.name
            ORDER BY total DESC
            """,
            (user_id, trans_type, start, end)
        ).fetchall()

    income_rows = _query("income")
    expense_rows = _query("expense")

    total_income = sum(r["total"] for r in income_rows)
    total_expense = sum(r["total"] for r in expense_rows)

    conn.close()
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "income_by_category": [(r["category_name"], r["total"]) for r in income_rows],
        "expense_by_category": [(r["category_name"], r["total"]) for r in expense_rows],
    }


# ─────────────────────── 预算操作 ───────────────────────

def set_budget(user_id: int, amount: float) -> None:
    """设置或更新用户月度预算。"""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO budgets (user_id, amount, updated_at)
        VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime'))
        ON CONFLICT(user_id) DO UPDATE SET
            amount = excluded.amount,
            updated_at = excluded.updated_at
        """,
        (user_id, amount)
    )
    conn.commit()
    conn.close()


def get_budget(user_id: int) -> Optional[float]:
    """获取用户月度预算，未设置则返回 None。"""
    conn = get_connection()
    row = conn.execute(
        "SELECT amount FROM budgets WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["amount"] if row else None


def clear_budget(user_id: int) -> None:
    """清除用户月度预算。"""
    conn = get_connection()
    conn.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_current_month_expense(user_id: int) -> float:
    """获取当前月份的总支出金额。"""
    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND type = 'expense'
          AND DATE(created_at) BETWEEN ? AND ?
        """,
        (user_id, start, end)
    ).fetchone()
    conn.close()
    return row["total"] if row else 0.0
