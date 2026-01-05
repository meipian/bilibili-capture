import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import sys
import logging
from datetime import datetime
import aiohttp

# 导入项目模块
from indexer import VideoIndexer
from sampler import SamplingEngine
from extractor import ThumbnailExtractor
from config import *
from config_manager import load_user_config, save_user_config

# 配置日志
if DEBUG_MODE:
    log_level = logging.DEBUG
else:
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bb_capture.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BilibiliCaptureUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bilibili视频内容多点采样缩略图提取系统")
        self.root.geometry("800x700")
        
        # 添加停止标志
        self.stop_flag = threading.Event()
        
        # 加载用户配置
        user_config = load_user_config()
        
        # 存储配置
        self.config = {
            'cookie': tk.StringVar(value=user_config['cookie']),
            'target_up_id': tk.StringVar(value=user_config['target_up_id']),
            'favorite_list_id': tk.StringVar(value=user_config['favorite_list_id']),
            'start_year': tk.StringVar(value=str(user_config['start_year'])),
            'start_month': tk.StringVar(value=str(user_config['start_month'])),
            'start_day': tk.StringVar(value=str(user_config['start_day'])),
            'end_year': tk.StringVar(value=str(user_config['end_year'])),
            'end_month': tk.StringVar(value=str(user_config['end_month'])),
            'end_day': tk.StringVar(value=str(user_config['end_day'])),
            'max_qps': tk.IntVar(value=user_config['max_qps']),
            'concurrent_limit': tk.IntVar(value=user_config['concurrent_limit']),
            'output_dir': tk.StringVar(value=user_config['output_dir']),
            'image_format': tk.StringVar(value=user_config['image_format']),
            'debug_mode': tk.BooleanVar(value=user_config['debug_mode'])
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置信息", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Cookie输入
        ttk.Label(config_frame, text="Cookie:").grid(row=0, column=0, sticky=tk.W, pady=2)
        cookie_entry = tk.Entry(config_frame, textvariable=self.config['cookie'], width=80)
        cookie_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        # UP主编号输入
        ttk.Label(config_frame, text="UP主编号:").grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Entry(config_frame, textvariable=self.config['target_up_id'], width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 合集编号输入
        ttk.Label(config_frame, text="合集编号:").grid(row=2, column=0, sticky=tk.W, pady=2)
        tk.Entry(config_frame, textvariable=self.config['favorite_list_id'], width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 开始时间选择
        ttk.Label(config_frame, text="开始时间:").grid(row=3, column=0, sticky=tk.W, pady=2)
        start_time_frame = ttk.Frame(config_frame)
        start_time_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 开始时间年份下拉框
        start_years = [str(year) for year in range(2000, 2030)]
        start_year_combo = ttk.Combobox(start_time_frame, textvariable=self.config['start_year'], 
                                       values=start_years, width=6, state="readonly")
        start_year_combo.grid(row=0, column=0, padx=(0, 5))
        
        # 开始时间月份下拉框
        start_months = [str(i) for i in range(1, 13)]
        start_month_combo = ttk.Combobox(start_time_frame, textvariable=self.config['start_month'], 
                                        values=start_months, width=4, state="readonly")
        start_month_combo.grid(row=0, column=1, padx=(0, 5))
        
        # 开始时间日期下拉框
        start_days = [str(i) for i in range(1, 32)]
        start_day_combo = ttk.Combobox(start_time_frame, textvariable=self.config['start_day'], 
                                      values=start_days, width=4, state="readonly")
        start_day_combo.grid(row=0, column=2)
        
        # 结束时间选择
        ttk.Label(config_frame, text="结束时间:").grid(row=4, column=0, sticky=tk.W, pady=2)
        end_time_frame = ttk.Frame(config_frame)
        end_time_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 结束时间年份下拉框
        end_years = [str(year) for year in range(2000, 2030)]
        end_year_combo = ttk.Combobox(end_time_frame, textvariable=self.config['end_year'], 
                                    values=end_years, width=6, state="readonly")
        end_year_combo.grid(row=0, column=0, padx=(0, 5))
        
        # 结束时间月份下拉框
        end_months = [str(i) for i in range(1, 13)]
        end_month_combo = ttk.Combobox(end_time_frame, textvariable=self.config['end_month'], 
                                     values=end_months, width=4, state="readonly")
        end_month_combo.grid(row=0, column=1, padx=(0, 5))
        
        # 结束时间日期下拉框
        end_days = [str(i) for i in range(1, 32)]
        end_day_combo = ttk.Combobox(end_time_frame, textvariable=self.config['end_day'], 
                                   values=end_days, width=4, state="readonly")
        end_day_combo.grid(row=0, column=2)
        
        # QPS和并发限制
        ttk.Label(config_frame, text="最大QPS:").grid(row=6, column=0, sticky=tk.W, pady=2)
        tk.Spinbox(config_frame, from_=1, to=10, textvariable=self.config['max_qps'], width=10).grid(row=6, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(config_frame, text="并发限制:").grid(row=7, column=0, sticky=tk.W, pady=2)
        tk.Spinbox(config_frame, from_=1, to=20, textvariable=self.config['concurrent_limit'], width=10).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # 输出目录
        ttk.Label(config_frame, text="输出目录:").grid(row=8, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(config_frame)
        output_frame.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=2)
        tk.Entry(output_frame, textvariable=self.config['output_dir'], width=50).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_dir).grid(row=0, column=1, padx=(5, 0))
        
        # 图片格式选择
        ttk.Label(config_frame, text="图片格式:").grid(row=9, column=0, sticky=tk.W, pady=2)
        format_combo = ttk.Combobox(config_frame, textvariable=self.config['image_format'], values=["webp"], width=10, state="readonly")
        format_combo.grid(row=9, column=1, sticky=tk.W, pady=2)
        
        # 调试模式
        ttk.Checkbutton(config_frame, text="调试模式", variable=self.config['debug_mode']).grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 配置框架列权重
        config_frame.columnconfigure(1, weight=1)
        
        # 控制按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始提取", command=self.start_capture)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 主框架权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.config['output_dir'].set(directory)
            
    def start_capture(self):
        # 更新配置
        self.update_config_from_ui()
        
        # 保存配置
        current_config = {
            'cookie': self.config['cookie'].get(),
            'target_up_id': self.config['target_up_id'].get(),
            'favorite_list_id': self.config['favorite_list_id'].get(),
            'start_year': self.config['start_year'].get(),
            'start_month': self.config['start_month'].get(),
            'start_day': self.config['start_day'].get(),
            'end_year': self.config['end_year'].get(),
            'end_month': self.config['end_month'].get(),
            'end_day': self.config['end_day'].get(),
            'max_qps': self.config['max_qps'].get(),
            'concurrent_limit': self.config['concurrent_limit'].get(),
            'output_dir': self.config['output_dir'].get(),
            'image_format': self.config['image_format'].get(),
            'debug_mode': self.config['debug_mode'].get()
        }
        save_user_config(current_config)
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 清除停止标志
        self.stop_flag.clear()
        
        # 启动提取任务
        def run_async():
            asyncio.run(self._run_capture_async())
        
        self.capture_thread = threading.Thread(target=run_async)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
    def stop_capture(self):
        # 设置停止标志
        self.stop_flag.set()
        self.log_message("停止请求已发送...")
        # 禁用停止按钮，启用开始按钮将在任务完成后进行
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        
    def update_config_from_ui(self):
        # 更新全局配置
        global BILIBILI_COOKIE, TARGET_UP_ID, FAVORITE_LIST_ID
        global START_YEAR, START_MONTH, START_DAY, END_YEAR, END_MONTH, END_DAY
        global MAX_QPS, CONCURRENT_LIMIT, OUTPUT_DIR
        global IMAGE_FORMAT, DEBUG_MODE
        
        BILIBILI_COOKIE = self.config['cookie'].get()
        TARGET_UP_ID = self.config['target_up_id'].get()
        FAVORITE_LIST_ID = self.config['favorite_list_id'].get()
        START_YEAR = self.config['start_year'].get()
        START_MONTH = self.config['start_month'].get()
        START_DAY = self.config['start_day'].get()
        END_YEAR = self.config['end_year'].get()
        END_MONTH = self.config['end_month'].get()
        END_DAY = self.config['end_day'].get()
        MAX_QPS = self.config['max_qps'].get()
        CONCURRENT_LIMIT = self.config['concurrent_limit'].get()
        OUTPUT_DIR = self.config['output_dir'].get()
        IMAGE_FORMAT = self.config['image_format'].get()
        DEBUG_MODE = self.config['debug_mode'].get()
        
    async def _run_capture_async(self):
        try:
            # 创建输出目录
            os.makedirs(self.config['output_dir'].get(), exist_ok=True)
            
            # 构建时间字符串
            start_time_str = f"{self.config['start_year'].get()}-{self.config['start_month'].get().zfill(2)}-{self.config['start_day'].get().zfill(2)} 00:00:00"
            end_time_str = f"{self.config['end_year'].get()}-{self.config['end_month'].get().zfill(2)}-{self.config['end_day'].get().zfill(2)} 23:59:59"
            
            # 创建全局会话
            connector = aiohttp.TCPConnector(
                limit=10,             # 严格限制并发连接数
                ttl_dns_cache=300,    # 缓存 DNS
                use_dns_cache=True,
                force_close=False     # 强制保持长连接 (Keep-Alive)
            )
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://space.bilibili.com/',
                'Cookie': self.config['cookie'].get(),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                # 初始化组件，传递运行时配置和全局会话
                self.log_message(f"初始化提取组件...")
                indexer = VideoIndexer(session=session, cookie=self.config['cookie'].get(), qps=self.config['max_qps'].get())
                sampler = SamplingEngine()
                extractor = ThumbnailExtractor(session=session, cookie=self.config['cookie'].get())
                
                # 执行提取流程
                self.log_message(f"开始获取UP主 {self.config['target_up_id'].get()} 的视频列表...")
                
                # 构建时间字符串和时间对象
                from datetime import datetime
                start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                
                # 检查停止标志
                if self.stop_flag.is_set():
                    self.log_message("任务已取消，停止获取视频列表")
                    return
                
                # 获取视频列表（带重试机制）
                video_list = None
                for attempt in range(2):  # 最多重试一次
                    video_list = await indexer.get_videos_by_up_id(
                        up_id=self.config['target_up_id'].get(),
                        start_time=start_dt,
                        end_time=end_dt
                    )
                    
                    # 如果获取成功，跳出重试循环
                    if video_list is not None:
                        break
                    
                    if attempt == 0:  # 第一次失败，进行重试
                        self.log_message("获取视频列表失败，正在重试...")
                        await asyncio.sleep(2)  # 等待2秒再重试
                    else:  # 重试也失败
                        self.log_message("获取视频列表失败，请检查Cookie或其他配置")
                        return
                
                self.log_message(f"获取到 {len(video_list)} 个视频")
                
                # 遍历视频列表
                for idx, video in enumerate(video_list):
                    # 检查停止标志
                    if self.stop_flag.is_set():
                        self.log_message("任务已取消，停止处理视频")
                        return
                        
                    self.log_message(f"处理视频: {video['bvid']} - {video['title']}")
                    
                    # 计算采样点
                    sample_times = sampler.calculate_sample_points(video['duration'])
                    self.log_message(f"计算出 {len(sample_times)} 个采样点: {sample_times}")
                    
                    # 提取缩略图
                    for sample_idx, sample_time in enumerate(sample_times):
                        # 检查停止标志
                        if self.stop_flag.is_set():
                            self.log_message("任务已取消，停止提取缩略图")
                            return
                            
                        try:
                            # 生成输出文件名
                            output_filename = f"{video['bvid']}_{int(sample_time)}.{self.config['image_format'].get()}"
                            output_path = os.path.join(self.config['output_dir'].get(), output_filename)
                            
                            # 提取缩略图（带重试机制）
                            success = False
                            for attempt in range(2):  # 最多重试一次
                                success = await extractor.extract_thumbnail_at_time(
                                    bvid=video['bvid'],
                                    time_in_seconds=sample_time,
                                    output_path=output_path
                                )
                                
                                if success:
                                    break
                                
                                if attempt == 0:  # 第一次失败，进行重试
                                    self.log_message(f"提取缩略图失败，正在重试: {output_filename}")
                                    await asyncio.sleep(1)  # 等待1秒再重试
                                else:  # 重试也失败
                                    self.log_message(f"提取缩略图失败，请检查Cookie或其他配置: {output_filename}")
                            
                            if success:
                                self.log_message(f"成功提取缩略图: {output_filename}")
                            else:
                                self.log_message(f"提取缩略图失败: {output_filename}")
                        except Exception as e:
                            self.log_message(f"处理采样点时出错: {str(e)}")
                            
                self.log_message("提取任务完成！")
                
        except Exception as e:
            self.log_message(f"提取过程中出错: {str(e)}")
            logger.exception("提取过程异常")
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # 在主线程中更新UI
        self.root.after(0, lambda: self._update_log_text(formatted_message))
    
    def _update_log_text(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = BilibiliCaptureUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()