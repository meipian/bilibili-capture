# Bilibili 视频合集（/直播回放）快速预览

一个自动化的Bilibili视频缩略图获取工具，通过提取视频缩略图，实现对特定UP主视频集合的快速预览，支持自定义时间范围过滤及动态采样率。
（注：缩略图清晰度较低）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行主程序：
   ```bash
   python main.py
   ```

2. 获取Cookie：
   可通过插件（如`Cookie-Editor`获取）
   示例：
   
   <img width="637" height="668" alt="image" src="https://github.com/user-attachments/assets/5dd4ce50-82f2-4d46-9dd8-8ad2a55b3d01" />

4. 获取up主编号和合集编号：
   示例：
      1. 打开视频合集
         
      <img width="1620" height="454" alt="image" src="https://github.com/user-attachments/assets/fc4e8004-fe7f-45cb-9c91-e9ab44360519" />
      
      2. 第一项为**up主编号**，第二项为**合集编号**（编号为**纯数字**）
         
      <img width="1047" height="248" alt="image" src="https://github.com/user-attachments/assets/6982694a-9633-49d9-a7ac-dd642974af11" />

5. 填入UI配置中

## 安全说明

- 配置会自动保存到 `user_config.json` 文件中
- 请妥善保管个人Cookie信息，避免泄露

## 项目结构

```
bilibili-capture/
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
