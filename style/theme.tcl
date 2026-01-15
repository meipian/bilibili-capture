# Bilibili Capture 主题样式文件
# 使用 ttk.Style 配置界面外观

# 设置主题
ttk::style theme use clam

# 配置颜色变量
set colors(bg) "#f5f5f5"
set colors(fg) "#333333"
set colors(primary) "#4a90d9"
set colors(primary_active) "#3a7bc8"
set colors(border) "#e0e0e0"

# 配置 LabelFrame 样式
ttk::style configure TLabelframe \
    -background $colors(bg) \
    -borderwidth 1 \
    -relief solid

ttk::style configure TLabelframe.Label \
    -background $colors(bg) \
    -foreground $colors(fg) \
    -font {Arial 10 bold}

# 配置 Label 样式
ttk::style configure TLabel \
    -background $colors(bg) \
    -foreground $colors(fg) \
    -font {Arial 9}

# 配置 Entry 样式
ttk::style configure TEntry \
    -fieldbackground white \
    -borderwidth 1 \
    -relief solid

# 配置 Button 样式
ttk::style configure TButton \
    -background $colors(primary) \
    -foreground white \
    -borderwidth 0 \
    -font {Arial 9} \
    -padding {5 5}

ttk::style map TButton \
    -background [list active $colors(primary_active)]

# 配置 Frame 样式
ttk::style configure TFrame \
    -background $colors(bg)

# 配置 Checkbutton 样式
ttk::style configure TCheckbutton \
    -background $colors(bg) \
    -foreground $colors(fg)

# 配置 Combobox 样式
ttk::style configure TCombobox \
    -fieldbackground white \
    -background white
