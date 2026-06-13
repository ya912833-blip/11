# Telegram 收支记录 Bot

这是一个基于 Python (`python-telegram-bot`) 和 SQLite 开发的个人收支记录 Telegram 机器人。

## ✨ 功能特性

- **基础收支记录**：记录日常收入和支出，支持金额、分类、备注。
- **报表统计**：提供日、周、月度报表，自动按分类汇总。
- **预算提醒**：可设置月度预算上限，接近（≥80%）或超支时自动提醒。
- **分类管理**：支持自定义收入和支出分类的增删查。
- **导出数据**：一键导出所有收支记录为 CSV 文件（UTF-8 BOM，Excel 兼容）。
- **Docker 部署**：支持一键容器化部署，非 root 用户运行，包含健康检查。

## 🚀 快速部署 (Docker)

推荐使用 Docker Compose 进行部署，过程非常简单。

### 1. 准备工作

确保你的服务器已安装 Docker 和 Docker Compose。

### 2. 获取代码并配置

```bash
# 克隆仓库
git clone <仓库地址>
cd telegram-finance-bot

# 复制配置文件模板
cp .env.example .env

# 编辑 .env 文件，填入你的 Bot Token
nano .env
```

`.env` 文件示例：

```
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

> Token 可通过 Telegram 中的 [@BotFather](https://t.me/BotFather) 获取。

### 3. 启动服务

在 `docker-compose.yml` 所在目录执行：

```bash
# 构建并后台运行容器
docker-compose up -d --build
```

### 4. 验证运行状态

```bash
# 查看容器状态
docker-compose ps

# 查看运行日志
docker-compose logs -f
```

数据库文件将自动持久化保存在当前目录下的 `./data/` 文件夹中。

## 🖥️ 本地开发运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 BOT_TOKEN

# 加载环境变量并启动
export $(cat .env | xargs) && python main.py
```

## 📖 使用指南

在 Telegram 中找到你的 Bot，发送 `/start` 开始使用。

### 快捷菜单

Bot 底部会显示快捷键盘，包含以下功能：

| 按钮 | 功能 |
|------|------|
| 💰 记录收入 | 按提示输入金额、选择分类并填写备注 |
| 💸 记录支出 | 按提示输入金额、选择分类并填写备注 |
| 📊 查看报表 | 选择查看今日、本周或本月的收支统计 |
| 💳 预算管理 | 设置或清除月度预算 |
| 📁 分类管理 | 查看、添加或删除自定义收支分类 |
| 📤 导出数据 | 获取包含所有记录的 CSV 文件 |

### 命令列表

| 命令 | 说明 |
|------|------|
| `/start` | 启动机器人并显示主菜单 |
| `/help` | 查看帮助信息 |
| `/income` | 记录收入 |
| `/expense` | 记录支出 |
| `/report` | 查看报表 |
| `/budget` | 预算管理 |
| `/categories` | 分类管理 |
| `/export` | 导出数据为 CSV |
| `/cancel` | 取消当前正在进行的操作 |

## 🗂️ 项目结构

```
telegram-finance-bot/
├── main.py              # 主程序入口，注册所有处理器
├── database.py          # 数据库模块（SQLite 操作）
├── states.py            # 对话状态常量
├── utils.py             # 工具函数（格式化、键盘构建等）
├── handlers/
│   ├── __init__.py
│   ├── common.py        # /start、/help、/cancel
│   ├── income.py        # 收入记录对话流程
│   ├── expense.py       # 支出记录对话流程
│   ├── report.py        # 报表查看
│   ├── budget.py        # 预算管理对话流程
│   ├── categories.py    # 分类管理对话流程
│   └── export.py        # CSV 数据导出
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 镜像构建文件
├── docker-compose.yml   # Docker Compose 配置
├── .env.example         # 环境变量模板
├── .gitignore
└── data/                # 数据库持久化目录（运行时自动创建）
```

## 🛠️ 技术栈

| 组件 | 版本/说明 |
|------|-----------|
| 语言 | Python 3.12 |
| 框架 | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21.6 |
| 数据库 | SQLite3（WAL 模式） |
| 容器化 | Docker & Docker Compose |

## 🔒 安全性说明

- 容器默认使用非 root 用户 (`botuser`) 运行，提升安全性。
- 数据库配置了 WAL 模式，提升并发读写性能。
- 资源限制：默认限制最大内存 256MB，CPU 0.5 核（可在 `docker-compose.yml` 中调整）。
- `.env` 文件已加入 `.gitignore`，Token 不会被意外提交到版本控制。

## 📋 默认分类

**收入分类**：工资、奖金、投资收益、兼职收入、其他收入

**支出分类**：餐饮、交通、购物、娱乐、医疗、住房、教育、其他支出

> 默认分类不可删除，但可以通过分类管理功能添加自定义分类。
