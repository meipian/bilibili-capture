# Bilibili 提取缩略图实现视频内容快速预览

一个自动化的Bilibili视频缩略图获取工具，通过提取视频缩略图，实现对特定UP主视频集合的快速预览，支持自定义时间范围过滤及动态采样率。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行主程序：
   ```bash
   python main.py
   ```

2. 在UI界面中填写配置信息：
   - Cookie：Bilibili登录Cookie（重要：需要从浏览器获取自己的Cookie）
   - UP主编号：目标UP主的ID
   - 合集编号：视频合集ID（可选）
   - 时间范围：选择开始和结束时间
   - 其他配置：QPS、并发限制、输出目录等

3. 点击"开始提取"按钮启动提取任务

4. 在日志区域查看详细的处理信息

## 安全说明

- 项目会自动保存配置到 `user_config.json` 文件中
- 请妥善保管个人Cookie信息，避免泄露

## 项目结构

```
bb-capture/
├── main.py                 # 主程序入口，包含UI界面
├── config.py               # 配置文件
├── config_manager.py       # 配置保存和加载管理器
├── indexer.py              # 视频索引器
├── sampler.py              # 采样引擎
├── extractor.py            # 图像提取器
├── utils.py                # 工具函数
├── requirements.txt        # 依赖包
├── user_config.example.json # 安全的配置示例文件
└── README.md               # 项目说明文档
```