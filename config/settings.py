"""
硬科技展会监控自动化系统 - 全局配置
所有敏感信息通过环境变量读取，不硬编码在代码中。
"""

import os

# ============================================================
# 领域关键词配置
# ============================================================
# 每个大类下列出的关键词，展会名称或简介中命中任意一个即算匹配
KEYWORD_GROUPS = {
    "半导体": [
        "半导体", "集成电路", "芯片", "晶圆", "封测", "封装测试",
        "半导体设备", "半导体材料", "光刻", "EDA", "IP核",
        "功率器件", "模拟芯片", "存储芯片", "传感器", "MEMS",
        "Chiplet", "SiC", "GaN", "化合物半导体", "eda",
    ],
    "人工智能": [
        "人工智能", "AI", "具身智能", "大模型", "LLM",
        "机器学习", "深度学习", "计算机视觉", "自然语言处理",
        "AIGC", "生成式AI", "智能驾驶", "自动驾驶", "智能终端",
        "智能体", "Agent", "RAG",
    ],
    "硬科技": [
        "机器人", "人形机器人", "工业机器人", "服务机器人",
        "量子计算", "量子通信", "量子技术",
        "航空航天", "商业航天", "卫星", "无人机", "低空经济",
        "新能源", "光伏", "储能", "氢能", "锂电池", "充电桩",
        "新材料", "碳纤维", "超导",
    ],
    "先进制造": [
        "先进制造", "智能制造", "工业互联网", "工业4.0",
        "高端装备", "数控机床", "3D打印", "增材制造",
        "工业自动化", "智能工厂", "精密制造",
    ],
    "数字经济": [
        "数字经济", "数字化转型", "大数据", "云计算",
        "物联网", "IoT", "区块链", "边缘计算",
        "5G", "6G", "元宇宙", "数字孪生", "数据要素",
    ],
}

# 汇总所有关键词的扁平列表（用于快速匹配）
ALL_KEYWORDS = []
for _keywords in KEYWORD_GROUPS.values():
    ALL_KEYWORDS.extend(_keywords)

# ============================================================
# 时间范围配置
# ============================================================
TIMEZONE = "Asia/Shanghai"

# ============================================================
# 数据源开关（可独立启用/禁用某个数据源）
# ============================================================
ENABLED_SOURCES = {
    "qufair": True,       # 去展网
    "cnena": True,        # CNENA 会展门户
    "ten_times": True,    # 10times.com
    "eventbrite": True,   # Eventbrite API
    "onezh": True,        # 第一展会网
}

# ============================================================
# 爬虫通用配置
# ============================================================
REQUEST_TIMEOUT = 15          # 单次请求超时（秒）
REQUEST_RETRY = 3             # 失败重试次数
REQUEST_DELAY = 2             # 同一数据源内请求间隔（秒），避免被封
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# ============================================================
# 推送配置
# ============================================================
# PushPlus token —— 通过环境变量 PUSHPLUS_TOKEN 传入
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
PUSHPLUS_URL = "http://www.pushplus.plus/send"

# Server酱 token（备用方案）—— 通过环境变量 SERVERCHAN_KEY 传入
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
SERVERCHAN_URL = "https://sctapi.ftqq.com/{key}.send"

# 推送方式选择：pushplus 或 serverchan
PUSH_METHOD = os.environ.get("PUSH_METHOD", "pushplus")

# ============================================================
# Eventbrite API 配置
# ============================================================
EVENTBRITE_API_KEY = os.environ.get("EVENTBRITE_API_KEY", "")
EVENTBRITE_API_URL = "https://www.eventbriteapi.com/v3/"
