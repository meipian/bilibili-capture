# Bilibili 视频合集（/直播回放）快速预览

一个自动化的Bilibili视频缩略图获取工具，通过提取视频缩略图，实现对特定UP主视频集合的快速预览，支持自定义时间范围过滤及动态采样率。
（注：缩略图清晰度较低）

## 界面展示

<img width="866" height="399" alt="image" src="https://github.com/user-attachments/assets/dda59751-ed57-40cb-9ed1-84b0a5a5ab0c" />

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
   
 

3. 获取合集链接：
   以**直播回放**为例
   
   <img width="1429" height="80" alt="image" src="https://github.com/user-attachments/assets/95f269d2-343f-477c-868c-fc46543052df" />

   **合集链接**类似这样：

   <img width="561" height="42" alt="image" src="https://github.com/user-attachments/assets/788b59e3-b0fb-40fb-849c-85e6b0707be0" />


## 安全说明

- 配置会自动保存到 `user_config.json` 文件中
- 请妥善保管个人Cookie信息，避免泄露
