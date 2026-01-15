# Bilibili 视频合集（/直播回放）快速预览

一个自动化的Bilibili视频缩略图获取工具，通过提取视频缩略图，实现对特定UP主视频集合的快速预览，支持自定义时间范围过滤及动态采样率。
（注：缩略图清晰度较低）

## 界面展示

<img width="701" height="336" alt="image" src="https://github.com/user-attachments/assets/48d673dc-15c7-41e7-b429-936c3adc0cfb" />

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

3. 获取合集链接：

## 安全说明

- 配置会自动保存到 `user_config.json` 文件中
- 请妥善保管个人Cookie信息，避免泄露
