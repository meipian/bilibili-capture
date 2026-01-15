"""
主窗口UI模块
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import asyncio
import os
import re
from datetime import datetime
import aiohttp

# 导入项目模块
from core.indexer import VideoIndexer
from core.sampler import SamplingEngine
from core.extractor import ThumbnailExtractor
from style import StyleManager
from config.config_manager import load_user_config, save_user_config


class BilibiliCaptureUI:
    """Bilibili缩略图提取器主界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("Bilibili缩略图提取器")
        # 设置最小高度，只显示配置信息和控制按钮
        self.root.minsize(600, 300)
        self.root.geometry("700x300")

        # 添加停止标志
        self.stop_flag = threading.Event()

        # 初始化样式管理器
        self.style_manager = StyleManager(root)
        self.style_manager.apply_root_style()

        # 加载用户配置
        user_config = load_user_config()

        # 存储配置
        self.config = {
            'url': tk.StringVar(value=user_config.get('url', '')),
            'cookie': tk.StringVar(value=user_config['cookie']),
            'start_year': tk.StringVar(value=str(user_config['start_year'])),
            'start_month': tk.StringVar(value=str(user_config['start_month'])),
            'start_day': tk.StringVar(value=str(user_config['start_day'])),
            'end_year': tk.StringVar(value=str(user_config['end_year'])),
            'end_month': tk.StringVar(value=str(user_config['end_month'])),
            'end_day': tk.StringVar(value=str(user_config['end_day'])),
            'max_qps': tk.IntVar(value=user_config['max_qps']),
            'concurrent_limit': tk.IntVar(value=user_config['concurrent_limit']),
            'output_dir': tk.StringVar(value=user_config['output_dir']),
            'image_format': tk.StringVar(value=user_config['image_format'])
        }

        self.setup_ui()

        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self._on_window_configure)

    def _on_window_configure(self, event):
        """窗口大小变化时更新最小高度"""
        # 只在主窗口上触发，避免子组件触发
        if event.widget == self.root:
            current_height = self.root.winfo_height()
            if current_height > 300:
                self.root.minsize(600, current_height)
            else:
                self.root.minsize(600, 300)

    def _get_target_height(self):
        """根据当前展开状态计算目标窗口高度"""
        base_height = 320
        advanced_height = 170
        log_height = 270

        total_height = base_height
        if self.advanced_visible:
            total_height += advanced_height
        if self.log_visible:
            total_height += log_height

        return total_height

    def _resize_window(self):
        """调整窗口大小到正确的尺寸"""
        target_height = self._get_target_height()
        self.root.minsize(600, 300)  # 重置最小高度
        self.root.geometry(f"700x{target_height}")

    def toggle_advanced(self):
        """切换高级设置的显示/隐藏"""
        if self.advanced_visible:
            # 隐藏高级设置
            self.advanced_frame.grid_forget()
            self.advanced_button.config(text="高级设置 ▼")
            self.advanced_visible = False
        else:
            # 显示高级设置
            self.advanced_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            self.advanced_button.config(text="高级设置 ▲")
            self.advanced_visible = True

        # 调整窗口大小
        self.root.after(150, self._resize_window)

    def toggle_log(self):
        """切换日志的显示/隐藏"""
        if self.log_visible:
            # 隐藏日志
            self.log_frame.grid_forget()
            self.log_button.config(text="运行日志 ▼")
            self.log_visible = False
        else:
            # 显示日志
            self.log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            self.log_button.config(text="运行日志 ▲")
            self.log_visible = True

        # 调整窗口大小
        self.root.after(150, self._resize_window)

    def setup_ui(self):
        """设置UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置信息", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # URL输入
        ttk.Label(config_frame, text="视频链接:").grid(row=0, column=0, sticky=tk.W, pady=2)
        url_entry = tk.Entry(config_frame, textvariable=self.config['url'], width=80)
        url_entry.grid(row=0, column=1, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        url_entry.bind('<FocusOut>', self.on_url_focus_out)

        # Cookie输入
        ttk.Label(config_frame, text="Cookie:").grid(row=1, column=0, sticky=tk.W, pady=2)
        cookie_entry = tk.Entry(config_frame, textvariable=self.config['cookie'], width=80)
        cookie_entry.grid(row=1, column=1, columnspan=4, sticky=(tk.W, tk.E), pady=2)

        # 开始时间选择
        ttk.Label(config_frame, text="开始时间:").grid(row=2, column=0, sticky=tk.W, pady=2)
        start_time_frame = ttk.Frame(config_frame)
        start_time_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        start_years = [str(year) for year in range(2000, 2030)]
        start_year_combo = ttk.Combobox(start_time_frame, textvariable=self.config['start_year'],
                                       values=start_years, width=6, state="readonly")
        start_year_combo.grid(row=0, column=0, padx=(0, 5))

        start_months = [str(i) for i in range(1, 13)]
        start_month_combo = ttk.Combobox(start_time_frame, textvariable=self.config['start_month'],
                                        values=start_months, width=4, state="readonly")
        start_month_combo.grid(row=0, column=1, padx=(0, 5))

        start_days = [str(i) for i in range(1, 32)]
        start_day_combo = ttk.Combobox(start_time_frame, textvariable=self.config['start_day'],
                                      values=start_days, width=4, state="readonly")
        start_day_combo.grid(row=0, column=2)

        # 结束时间选择
        ttk.Label(config_frame, text="结束时间:").grid(row=3, column=0, sticky=tk.W, pady=2)
        end_time_frame = ttk.Frame(config_frame)
        end_time_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)

        end_years = [str(year) for year in range(2000, 2030)]
        end_year_combo = ttk.Combobox(end_time_frame, textvariable=self.config['end_year'],
                                    values=end_years, width=6, state="readonly")
        end_year_combo.grid(row=0, column=0, padx=(0, 5))

        end_months = [str(i) for i in range(1, 13)]
        end_month_combo = ttk.Combobox(end_time_frame, textvariable=self.config['end_month'],
                                     values=end_months, width=4, state="readonly")
        end_month_combo.grid(row=0, column=1, padx=(0, 5))

        end_days = [str(i) for i in range(1, 32)]
        end_day_combo = ttk.Combobox(end_time_frame, textvariable=self.config['end_day'],
                                   values=end_days, width=4, state="readonly")
        end_day_combo.grid(row=0, column=2)

        config_frame.columnconfigure(1, weight=1)

        # 进度和按钮区域（配置信息底部）
        bottom_frame = ttk.Frame(config_frame)
        bottom_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)

        # 左侧：进度条和统计（默认隐藏）
        self.progress_frame = ttk.Frame(bottom_frame)
        # 不grid，默认隐藏

        self.total_label = ttk.Label(self.progress_frame, text="视频总数: 0")
        self.total_label.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=150)
        self.progress_bar.pack(side=tk.LEFT, padx=5)

        self.stats_label = ttk.Label(self.progress_frame, text="成功: 0 / 失败: 0")
        self.stats_label.pack(side=tk.LEFT, padx=(10, 0))

        # 右侧：按钮
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(side=tk.RIGHT)

        self.advanced_button = ttk.Button(btn_frame, text="高级设置 ▼", command=self.toggle_advanced)
        self.advanced_button.pack(side=tk.LEFT, padx=2)

        self.log_button = ttk.Button(btn_frame, text="运行日志 ▼", command=self.toggle_log)
        self.log_button.pack(side=tk.LEFT, padx=2)

        bottom_frame.columnconfigure(0, weight=1)

        # 高级设置区域（默认隐藏）
        self.advanced_frame = ttk.LabelFrame(main_frame, text="高级设置", padding="10")
        # 初始不显示

        ttk.Label(self.advanced_frame, text="最大QPS:").grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Spinbox(self.advanced_frame, from_=1, to=10, textvariable=self.config['max_qps'], width=10).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.advanced_frame, text="并发限制:").grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Spinbox(self.advanced_frame, from_=1, to=20, textvariable=self.config['concurrent_limit'], width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(self.advanced_frame, text="输出目录:").grid(row=2, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(self.advanced_frame)
        output_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        tk.Entry(output_frame, textvariable=self.config['output_dir'], width=50).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_dir).grid(row=0, column=1, padx=(5, 0))

        ttk.Label(self.advanced_frame, text="图片格式:").grid(row=3, column=0, sticky=tk.W, pady=2)
        format_combo = ttk.Combobox(self.advanced_frame, textvariable=self.config['image_format'], values=["webp"], width=10, state="readonly")
        format_combo.grid(row=3, column=1, sticky=tk.W, pady=2)

        self.advanced_frame.columnconfigure(1, weight=1)

        # 日志显示区域（默认隐藏）
        self.log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        # 初始不显示

        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=15, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

        # 控制按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始提取", command=self.start_capture)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 主框架权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # 初始化
        self.advanced_visible = False
        self.log_visible = False
        self.total_videos = 0
        self.success_count = 0
        self.fail_count = 0

    def toggle_advanced(self):
        """切换高级设置的显示/隐藏"""
        if self.advanced_visible:
            # 隐藏高级设置
            self.advanced_frame.grid_forget()
            self.advanced_button.config(text="高级设置 ▼")
            self.advanced_visible = False
        else:
            # 显示高级设置
            self.advanced_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            self.advanced_button.config(text="高级设置 ▲")
            self.advanced_visible = True

        # 调整窗口大小
        self.root.after(150, self._resize_window)

    def toggle_log(self):
        """切换日志的显示/隐藏"""
        if self.log_visible:
            # 隐藏日志
            self.log_frame.grid_forget()
            self.log_button.config(text="运行日志 ▼")
            self.log_visible = False
        else:
            # 显示日志
            self.log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            self.log_button.config(text="运行日志 ▲")
            self.log_visible = True

        # 调整窗口大小
        self.root.after(150, self._resize_window)

    def show_progress(self):
        """显示进度条"""
        self.progress_frame.pack(side=tk.LEFT, padx=(0, 10))

    def hide_progress(self):
        """隐藏进度条"""
        self.progress_frame.pack_forget()

    def update_progress(self, total=None, success=None, fail=None, current=None):
        """更新进度显示"""
        if total is not None:
            self.total_videos = total
            self.total_label.config(text=f"视频总数: {total}")
            self.progress_bar['maximum'] = max(1, total)

        if success is not None:
            self.success_count = success

        if fail is not None:
            self.fail_count = fail

        self.stats_label.config(text=f"成功: {self.success_count} / 失败: {self.fail_count}")

        if current is not None:
            self.progress_bar['value'] = current

    def reset_progress(self):
        """重置进度"""
        self.total_videos = 0
        self.success_count = 0
        self.fail_count = 0
        self.total_label.config(text="视频总数: 0")
        self.stats_label.config(text="成功: 0 / 失败: 0")
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100

    def browse_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.config['output_dir'].set(directory)

    def parse_url(self):
        """解析URL提取up主id和合集id"""
        url = self.config['url'].get().strip()

        if not url:
            self.log_message("请输入视频链接")
            return None

        # 解析space.bilibili.com/后面的纯数字（up主id）
        up_id = None
        up_id_match = re.search(r'space\.bilibili\.com/?(\d+)', url)
        if up_id_match:
            up_id = up_id_match.group(1)
            self.log_message(f"已解析UP主ID: {up_id}")

        # 解析/lists/后面的纯数字（合集id）
        list_id = None
        list_id_match = re.search(r'/lists/?(\d+)', url)
        if list_id_match:
            list_id = list_id_match.group(1)
            self.log_message(f"已解析合集ID: {list_id}")

        if not up_id:
            self.log_message("无法从URL中解析UP主ID，请检查链接格式")
            return None

        return {'up_id': up_id, 'list_id': list_id}

    def on_url_focus_out(self, event):
        """URL输入框失去焦点时自动解析"""
        self.parse_url()

    def start_capture(self):
        """开始提取"""
        # 解析URL获取up主id和合集id
        url_info = self.parse_url()
        if not url_info:
            self.log_message("请输入有效的视频链接")
            return

        # 保存url_info供_run_capture_async使用
        self.url_info = url_info

        # 保存配置
        current_config = {
            'url': self.config['url'].get(),
            'cookie': self.config['cookie'].get(),
            'start_year': self.config['start_year'].get(),
            'start_month': self.config['start_month'].get(),
            'start_day': self.config['start_day'].get(),
            'end_year': self.config['end_year'].get(),
            'end_month': self.config['end_month'].get(),
            'end_day': self.config['end_day'].get(),
            'max_qps': self.config['max_qps'].get(),
            'concurrent_limit': self.config['concurrent_limit'].get(),
            'output_dir': self.config['output_dir'].get(),
            'image_format': self.config['image_format'].get()
        }
        save_user_config(current_config)

        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # 显示并重置进度条
        self.reset_progress()
        self.show_progress()

        # 清除停止标志
        self.stop_flag.clear()

        # 启动提取任务
        def run_async():
            asyncio.run(self._run_capture_async())

        self.capture_thread = threading.Thread(target=run_async)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def stop_capture(self):
        """停止提取"""
        # 设置停止标志
        self.stop_flag.set()
        self.log_message("停止请求已发送...")
        # 禁用停止按钮，启用开始按钮将在任务完成后进行
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)

    async def _run_capture_async(self):
        """异步执行提取任务"""
        try:
            # 创建输出目录
            os.makedirs(self.config['output_dir'].get(), exist_ok=True)

            # 构建时间字符串
            start_time_str = f"{self.config['start_year'].get()}-{self.config['start_month'].get().zfill(2)}-{self.config['start_day'].get().zfill(2)} 00:00:00"
            end_time_str = f"{self.config['end_year'].get()}-{self.config['end_month'].get().zfill(2)}-{self.config['end_day'].get().zfill(2)} 23:59:59"

            # 创建全局会话
            connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                force_close=False
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
                # 初始化组件
                self.log_message(f"初始化提取组件...")
                indexer = VideoIndexer(session=session, cookie=self.config['cookie'].get(), qps=self.config['max_qps'].get())
                sampler = SamplingEngine()
                extractor = ThumbnailExtractor(session=session, cookie=self.config['cookie'].get())

                # 执行提取流程
                up_id = self.url_info['up_id']
                list_id = self.url_info.get('list_id')

                if list_id:
                    self.log_message(f"开始获取UP主 {up_id} 的合集 {list_id} 的视频列表...")
                else:
                    self.log_message(f"开始获取UP主 {up_id} 的投稿视频列表...")

                # 构建时间对象
                start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

                # 检查停止标志
                if self.stop_flag.is_set():
                    self.log_message("任务已取消，停止获取视频列表")
                    return

                # 获取视频列表（带重试机制）
                video_list = None
                for attempt in range(2):
                    # 根据是否有合集ID使用不同的API
                    if list_id:
                        video_list = await indexer.get_videos_by_collection(
                            up_id=up_id,
                            collection_id=list_id,
                            start_time=start_dt,
                            end_time=end_dt
                        )
                    else:
                        video_list = await indexer.get_videos_by_up_id(
                            up_id=up_id,
                            start_time=start_dt,
                            end_time=end_dt
                        )

                    if video_list is not None:
                        break

                    if attempt == 0:
                        self.log_message("获取视频列表失败，正在重试...")
                        await asyncio.sleep(2)
                    else:
                        self.log_message("获取视频列表失败，请检查Cookie或提交反馈")
                        return

                self.log_message(f"获取到 {len(video_list)} 个视频")

                # 更新视频总数
                self.root.after(0, lambda: self.update_progress(total=len(video_list)))

                # 遍历视频列表
                for idx, video in enumerate(video_list):
                    if self.stop_flag.is_set():
                        self.log_message("任务已取消，停止处理视频")
                        return

                    self.log_message(f"处理视频: {video['bvid']} - {video['title']}")

                    # 计算采样点
                    sample_times = sampler.calculate_sample_points(video['duration'])
                    self.log_message(f"计算出 {len(sample_times)} 个采样点: {sample_times}")

                    # 提取缩略图
                    video_success = True
                    for sample_idx, sample_time in enumerate(sample_times):
                        if self.stop_flag.is_set():
                            self.log_message("任务已取消")
                            return

                        try:
                            # 生成文件名：格式为 "发布时间_BV(索引).格式"
                            # 例如: "2021-10-06_BV1xx4xx(1).webp"
                            publish_date = video['created_str'].split(' ')[0]  # 只取日期部分
                            bvid = video['bvid']  # 保留完整的BV编号，如 BV1vT2RBFENE
                            output_filename = f"{publish_date}_{bvid}({sample_idx + 1}).{self.config['image_format'].get()}"
                            output_path = os.path.join(self.config['output_dir'].get(), output_filename)

                            success = False
                            for attempt in range(2):
                                success = await extractor.extract_thumbnail_at_time(
                                    bvid=video['bvid'],
                                    time_in_seconds=sample_time,
                                    output_path=output_path
                                )

                                if success:
                                    break

                                if attempt == 0:
                                    self.log_message(f"提取缩略图失败，正在重试: {output_filename}")
                                    await asyncio.sleep(1)
                                else:
                                    self.log_message(f"提取缩略图失败，请检查Cookie或提交反馈: {output_filename}")

                            if success:
                                self.log_message(f"成功提取缩略图: {output_filename}")
                            else:
                                self.log_message(f"提取缩略图失败: {output_filename}")
                                video_success = False
                        except Exception as e:
                            self.log_message(f"处理采样点时出错: {str(e)}")
                            video_success = False

                    # 更新进度和统计
                    if video_success:
                        self.root.after(0, lambda s=self.success_count + 1: self.update_progress(success=s))
                    else:
                        self.root.after(0, lambda f=self.fail_count + 1: self.update_progress(fail=f))

                    # 更新当前进度
                    self.root.after(0, lambda c=idx + 1: self.update_progress(current=c))

                self.log_message("提取任务完成！")

        except Exception as e:
            self.log_message(f"提取过程中出错: {str(e)}")
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            # 隐藏进度条
            self.root.after(0, self.hide_progress)

    def log_message(self, message):
        """输出日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        # 在主线程中更新UI
        self.root.after(0, lambda: self._update_log_text(formatted_message))

    def _update_log_text(self, message):
        """更新日志文本"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
