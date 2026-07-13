# 硬科技展会监控自动化系统

每天自动抓取互联网上的硬科技展会/峰会/论坛信息，筛选出下周举办的活动，推送到微信。

## 监控领域

- **半导体**: 材料、设备、设计、制造、封测等全产业链
- **人工智能**: AI、具身智能、大模型、AIGC、智能驾驶
- **硬科技**: 机器人、量子计算、航空航天、新能源、新材料
- **先进制造**: 智能制造、工业互联网、工业4.0、3D打印
- **数字经济**: 大数据、云计算、物联网、5G/6G、区块链

## 项目结构

```
hardtech-expo-monitor/
├── main.py                         # 主程序入口
├── requirements.txt                # Python 依赖
├── .gitignore
├── config/
│   └── settings.py                 # 全局配置（关键词、数据源、推送等）
├── models/
│   └── exhibition.py               # 展会数据模型
├── scrapers/                       # 爬虫模块
│   ├── base.py                     # 爬虫基类（HTTP封装、重试、UA轮换）
│   ├── qufair.py                   # 去展网 (qufair.com)
│   ├── cnena.py                    # CNENA会展门户 (cnena.com)
│   ├── ten_times.py                # 10times.com
│   ├── eventbrite.py               # Eventbrite API
│   └── onezh.py                    # 第一展会网 (onezh.com)
├── filters/                        # 筛选模块
│   ├── keyword_filter.py           # 关键词匹配
│   └── time_filter.py              # 时间过滤 + 去重
├── notify/
│   └── wechat_push.py              # 微信推送（PushPlus / Server酱）
├── utils/
│   ├── date_utils.py               # 日期计算与解析
│   └── logger.py                   # 日志配置
└── .github/
    └── workflows/
        └── daily-expo.yml          # GitHub Actions 定时任务
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置推送 Token

支持两种推送渠道，任选其一：

#### 方式一：PushPlus（推荐）
1. 访问 [PushPlus 官网](http://www.pushplus.plus/)
2. 微信扫码登录，获取你的 `token`
3. 设置环境变量：
```bash
# Linux / macOS
export PUSHPLUS_TOKEN="你的token"

# Windows PowerShell
$env:PUSHPLUS_TOKEN="你的token"
```

#### 方式二：Server酱
1. 访问 [Server酱](https://sct.ftqq.com/)，GitHub 登录
2. 获取 `SendKey`
3. 设置环境变量：
```bash
export SERVERCHAN_KEY="你的key"
export PUSH_METHOD="serverchan"
```

### 3. （可选）配置 Eventbrite API

1. 访问 [Eventbrite API](https://www.eventbrite.com/platform/api)
2. 注册获取 API Key
3. 设置环境变量：
```bash
export EVENTBRITE_API_KEY="你的key"
```

### 4. 本地运行

```bash
python main.py
```

## GitHub Actions 部署

### 1. 上传到 GitHub

```bash
git init
git add .
git commit -m "硬科技展会监控自动化系统"
git branch -M main
git remote add origin https://github.com/你的用户名/hardtech-expo-monitor.git
git push -u origin main
```

### 2. 配置 Secrets

进入 GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret，添加：

| Secret 名称 | 值 | 必填 |
|---|---|---|
| `PUSHPLUS_TOKEN` | PushPlus 的 token | 是（使用 PushPlus 时） |
| `SERVERCHAN_KEY` | Server酱的 SendKey | 是（使用 Server酱 时） |
| `PUSH_METHOD` | `pushplus` 或 `serverchan` | 否（默认 pushplus） |
| `EVENTBRITE_API_KEY` | Eventbrite API Key | 否（不填则跳过该数据源） |

### 3. 启用 Actions

- GitHub 仓库 → Actions 页面 → 确认 workflow 已启用
- 点击 "Run workflow" 可手动触发测试
- 系统每周一北京时间 09:00 自动运行

## 工作流程

```
GitHub Actions 定时触发 (每周一 09:00)
         │
         ▼
   多源数据抓取 (5个数据源)
         │
         ▼
   关键词筛选 (半导体/AI/硬科技/制造/数字经济)
         │
         ▼
   时间筛选 (只保留下周举办的展会)
         │
         ▼
   多源去重
         │
         ▼
   格式化 + 微信推送
```

## 数据源说明

| 数据源 | 类型 | 覆盖范围 | 获取方式 |
|---|---|---|---|
| 去展网 (qufair.com) | 国内展会聚合 | 国内外全行业 | HTML 爬虫 |
| CNENA会展门户 (cnena.com) | 国内展会门户 | 国内全行业 | HTML 爬虫 |
| 10times.com | 全球展会数据库 | 全球全行业 | HTML 爬虫 |
| Eventbrite API | 全球活动平台 | 全球科技活动 | REST API |
| 第一展会网 (onezh.com) | 国内展会排期 | 国内全行业 | HTML 爬虫 |

## 自定义配置

编辑 `config/settings.py`：

- **关键词**: 修改 `KEYWORD_GROUPS` 字典，添加/删除/修改各领域关键词
- **数据源开关**: 修改 `ENABLED_SOURCES` 字典，启用/禁用特定数据源
- **请求参数**: 调整 `REQUEST_TIMEOUT`、`REQUEST_RETRY`、`REQUEST_DELAY`
- **推送渠道**: 通过环境变量 `PUSH_METHOD` 切换 PushPlus / Server酱

## 技术栈

- Python 3.11+
- requests / beautifulsoup4 / lxml（爬虫与 HTML 解析）
- pytz / python-dateutil（时区与日期处理）
- PushPlus / Server酱（微信推送）
- GitHub Actions（定时调度）

## License

MIT
