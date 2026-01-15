"""
样式管理模块
负责加载和管理UI样式
"""
import os
import tkinter as tk
from tkinter import ttk


class StyleManager:
    """样式管理器"""

    def __init__(self, root=None):
        """
        初始化样式管理器

        Args:
            root: Tkinter根窗口对象
        """
        self.root = root
        self.style = ttk.Style()
        self._load_theme()

    def _load_theme(self):
        """加载主题样式"""
        try:
            # 使用 clam 主题作为基础
            self.style.theme_use('clam')
        except:
            pass

        # 定义颜色
        colors = {
            'bg': '#f5f5f5',
            'fg': '#333333',
            'primary': '#4a90d9',
            'primary_active': '#3a7bc8'
        }

        # 配置 LabelFrame 样式
        self.style.configure('TLabelframe',
                           background=colors['bg'],
                           borderwidth=1,
                           relief='solid')
        self.style.configure('TLabelframe.Label',
                           background=colors['bg'],
                           foreground=colors['fg'],
                           font=('Arial', 10, 'bold'))

        # 配置 Label 样式
        self.style.configure('TLabel',
                           background=colors['bg'],
                           foreground=colors['fg'],
                           font=('Arial', 9))

        # 配置 Entry 样式
        self.style.configure('TEntry',
                           fieldbackground='white',
                           borderwidth=1,
                           relief='solid')

        # 配置 Button 样式
        self.style.configure('TButton',
                           background=colors['primary'],
                           foreground='white',
                           borderwidth=0,
                           font=('Arial', 9),
                           padding=5)
        self.style.map('TButton',
                      background=[('active', colors['primary_active'])])

        # 配置 Frame 样式
        self.style.configure('TFrame',
                           background=colors['bg'])

        # 配置 Checkbutton 样式
        self.style.configure('TCheckbutton',
                           background=colors['bg'],
                           foreground=colors['fg'])

        # 配置 Combobox 样式
        self.style.configure('TCombobox',
                           fieldbackground='white',
                           background='white')

    def apply_root_style(self):
        """应用根窗口样式"""
        if self.root:
            self.root.configure(bg='#f5f5f5')
