# Bilibili视频内容多点采样缩略图提取系统配置文件

# Bilibili API相关配置
BILIBILI_COOKIE = ""  # 用户的Cookie，用于访问需要登录的接口

# 时间范围过滤
START_YEAR = "2026"  # 开始年份
START_MONTH = "1"    # 开始月份
START_DAY = "1"      # 开始日期
END_YEAR = "2026"    # 结束年份
END_MONTH = "12"     # 结束月份
END_DAY = "31"       # 结束日期

# 请求限制配置
MAX_QPS = 4  # 最大QPS（每秒查询率），建议设置为3-5
CONCURRENT_LIMIT = 5  # 并发请求限制

# 采样策略配置
MIN_VIDEO_DURATION = 10  # 最小视频时长（秒），低于此值的视频不处理

# 输出配置
OUTPUT_DIR = "./output/"  # 输出目录
IMAGE_FORMAT = "webp"  # 输出图片格式，当前支持webp

# 调试配置
LOG_LEVEL = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR