"""
文件加密器 - 图形界面
支持打包成 exe

功能：
- AES-256-GCM 加密/解密
- 显示/隐藏密码
- 进度条显示
- 拖拽文件支持
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from crypto_core import FileEncryptor

# 尝试导入拖拽支持
try:
    import tkinterdnd2 as tkdnd
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


def get_desktop_path():
    """获取桌面路径"""
    return os.path.join(os.path.expanduser("~"), "Desktop")


class App:
    # 统一的尺寸配置
    ENTRY_WIDTH = 52          # 输入框宽度
    BUTTON_WIDTH = 6          # 小按钮宽度
    ACTION_BTN_WIDTH = 15     # 操作按钮宽度
    
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 文件加密器")
        self.root.geometry("540x400")
        self.root.resizable(False, False)
        
        self.desktop_path = get_desktop_path()
        self.password_visible = False
        self.is_processing = False
        
        self._setup_styles()
        self._center_window()
        self._set_icon()
        self._create_widgets()
        self._setup_drag_drop()
    
    def _setup_styles(self):
        """设置自定义样式"""
        style = ttk.Style()
        
        # 进度条样式 - 现代扁平风格
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#e0e0e0',
            background='#4CAF50',
            lightcolor='#4CAF50',
            darkcolor='#388E3C',
            bordercolor='#e0e0e0',
            thickness=20
        )
    
    def _center_window(self):
        """窗口居中显示"""
        width = 540
        height = 400
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _set_icon(self):
        """设置窗口图标"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(__file__)
            
            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
    
    def _create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置列权重，使布局居中
        main_frame.columnconfigure(0, weight=1)
        
        # === 标题区域 ===
        title_label = ttk.Label(
            main_frame, 
            text="文件加密器", 
            font=("Microsoft YaHei UI", 20, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 3))
        
        # 拖拽提示
        hint_text = "支持拖拽文件到此窗口" if DND_AVAILABLE else "选择文件进行加密或解密"
        hint_label = ttk.Label(
            main_frame, 
            text=hint_text, 
            font=("Microsoft YaHei UI", 9),
            foreground="gray"
        )
        hint_label.grid(row=1, column=0, pady=(0, 18))
        
        # === 选择文件 ===
        file_label = ttk.Label(main_frame, text="选择文件:", font=("Microsoft YaHei UI", 10))
        file_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 3))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=3, column=0, sticky=tk.EW, pady=(0, 12))
        
        self.file_entry = ttk.Entry(input_frame, width=self.ENTRY_WIDTH, font=("Consolas", 9))
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.file_entry.bind('<KeyRelease>', self._on_input_change)
        
        self.browse_btn = ttk.Button(
            input_frame, text="浏览", command=self._browse_input, width=self.BUTTON_WIDTH
        )
        self.browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # === 输出位置 ===
        output_label = ttk.Label(main_frame, text="输出位置:", font=("Microsoft YaHei UI", 10))
        output_label.grid(row=4, column=0, sticky=tk.W, pady=(0, 3))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=5, column=0, sticky=tk.EW, pady=(0, 12))
        
        self.output_entry = ttk.Entry(output_frame, width=self.ENTRY_WIDTH, font=("Consolas", 9))
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.change_btn = ttk.Button(
            output_frame, text="更改", command=self._browse_output, width=self.BUTTON_WIDTH
        )
        self.change_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # === 密码输入 ===
        password_label = ttk.Label(main_frame, text="密码:", font=("Microsoft YaHei UI", 10))
        password_label.grid(row=6, column=0, sticky=tk.W, pady=(0, 3))
        
        password_frame = ttk.Frame(main_frame)
        password_frame.grid(row=7, column=0, sticky=tk.EW, pady=(0, 15))
        
        self.password_entry = ttk.Entry(
            password_frame, show="●", width=self.ENTRY_WIDTH, font=("Consolas", 10)
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.toggle_btn = ttk.Button(
            password_frame, text="👁", command=self._toggle_password, width=self.BUTTON_WIDTH
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # === 进度条 ===
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=8, column=0, sticky=tk.EW, pady=(0, 18))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        
        self.progress_label = ttk.Label(
            progress_frame, text="0%", font=("Consolas", 10, "bold"), width=5
        )
        self.progress_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # === 操作按钮 ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=9, column=0, pady=(5, 0))
        
        self.encrypt_btn = ttk.Button(
            btn_frame, text="🔒 加密文件", command=self._encrypt, width=self.ACTION_BTN_WIDTH
        )
        self.encrypt_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        self.decrypt_btn = ttk.Button(
            btn_frame, text="🔓 解密文件", command=self._decrypt, width=self.ACTION_BTN_WIDTH
        )
        self.decrypt_btn.pack(side=tk.LEFT, padx=(20, 0))
        
        # === 绑定事件 ===
        self.root.bind('<Return>', lambda e: self._encrypt())
        self.file_entry.bind('<Button-3>', lambda e: self._paste_to_entry(self.file_entry))
        self.output_entry.bind('<Button-3>', lambda e: self._paste_to_entry(self.output_entry))
    
    def _setup_drag_drop(self):
        """设置拖拽支持"""
        if not DND_AVAILABLE:
            return
        
        try:
            # 注册拖拽目标
            self.root.drop_target_register(tkdnd.DND_FILES)
            self.root.dnd_bind('<<Drop>>', self._on_drop)
        except Exception as e:
            print(f"拖拽功能初始化失败: {e}")
    
    def _on_drop(self, event):
        """处理拖拽放下事件"""
        if self.is_processing:
            return
        
        # 获取拖拽的文件路径
        files = event.data
        
        # 处理路径（可能包含花括号或空格）
        if files.startswith('{') and files.endswith('}'):
            files = files[1:-1]
        
        # 取第一个文件
        file_path = files.split()[0] if ' ' in files and not files.startswith('"') else files
        file_path = file_path.strip('"').strip("'")
        
        if os.path.isfile(file_path):
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self._update_output_path()
    
    def _toggle_password(self):
        """切换密码显示/隐藏"""
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_entry.config(show="")
            self.toggle_btn.config(text="🙈")
        else:
            self.password_entry.config(show="●")
            self.toggle_btn.config(text="👁")
    
    def _paste_to_entry(self, entry):
        """右键粘贴到输入框"""
        try:
            path = self.root.clipboard_get().strip().strip('"')
            if path:
                entry.delete(0, tk.END)
                entry.insert(0, path)
                if entry == self.file_entry:
                    self._update_output_path()
        except:
            pass
    
    def _browse_input(self):
        """浏览选择输入文件"""
        filepath = filedialog.askopenfilename(title="选择要处理的文件")
        if filepath:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filepath)
            self._update_output_path()
    
    def _browse_output(self):
        """浏览选择输出位置"""
        input_path = self.file_entry.get().strip()
        
        if input_path.endswith('.enc'):
            default_name = os.path.basename(input_path)[:-4]
            filetypes = [("所有文件", "*.*")]
        else:
            default_name = os.path.basename(input_path) + '.enc' if input_path else "encrypted.enc"
            filetypes = [("加密文件", "*.enc"), ("所有文件", "*.*")]
        
        filepath = filedialog.asksaveasfilename(
            title="选择输出位置",
            initialdir=self.desktop_path,
            initialfile=default_name,
            filetypes=filetypes
        )
        if filepath:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filepath)
    
    def _on_input_change(self, event=None):
        """输入文件变化时更新输出路径"""
        self._update_output_path()
    
    def _update_output_path(self):
        """根据输入文件自动生成输出路径（默认桌面）"""
        input_path = self.file_entry.get().strip().strip('"')
        
        if not input_path:
            self.output_entry.delete(0, tk.END)
            return
        
        filename = os.path.basename(input_path)
        
        if input_path.endswith('.enc'):
            output_name = filename[:-4] if filename.endswith('.enc') else filename + '.decrypted'
        else:
            output_name = filename + '.enc'
        
        output_path = os.path.join(self.desktop_path, output_name)
        
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, output_path)
    
    def _validate_input(self):
        """验证输入"""
        input_path = self.file_entry.get().strip().strip('"')
        output_path = self.output_entry.get().strip().strip('"')
        password = self.password_entry.get()
        
        if not input_path:
            messagebox.showerror("错误", "请选择要处理的文件")
            return None, None, None
        
        if not os.path.exists(input_path):
            messagebox.showerror("错误", "输入文件不存在，请检查路径")
            return None, None, None
        
        if not output_path:
            messagebox.showerror("错误", "请指定输出位置")
            return None, None, None
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            messagebox.showerror("错误", "输出目录不存在")
            return None, None, None
        
        if not password:
            messagebox.showerror("错误", "请输入密码")
            return None, None, None
        
        if os.path.exists(output_path):
            if not messagebox.askyesno("确认", f"输出文件已存在，是否覆盖？\n{output_path}"):
                return None, None, None
        
        return input_path, output_path, password
    
    def _set_busy(self, busy: bool):
        """设置忙碌状态"""
        self.is_processing = busy
        state = 'disabled' if busy else 'normal'
        cursor = "wait" if busy else ""
        
        self.root.config(cursor=cursor)
        # 禁用所有按钮，防止处理过程中误操作
        self.encrypt_btn.config(state=state)
        self.decrypt_btn.config(state=state)
        self.toggle_btn.config(state=state)
        self.browse_btn.config(state=state)
        self.change_btn.config(state=state)
        # 禁用输入框
        entry_state = 'disabled' if busy else 'normal'
        self.file_entry.config(state=entry_state)
        self.output_entry.config(state=entry_state)
        self.password_entry.config(state=entry_state)
        
        self.root.update()
    
    def _update_progress(self, current: int, total: int):
        """更新进度条（线程安全）"""
        if total > 0:
            percent = min(100, (current / total) * 100)
            self.progress_var.set(percent)
            self.progress_label.config(text=f"{int(percent)}%")
            self.root.update_idletasks()
    
    def _reset_progress(self):
        """重置进度条"""
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
    
    def _encrypt(self):
        """加密文件"""
        input_path, output_path, password = self._validate_input()
        if not input_path:
            return
        
        self._set_busy(True)
        self._reset_progress()
        
        def do_encrypt():
            try:
                encryptor = FileEncryptor(password)
                encryptor.encrypt_file(
                    input_path, 
                    output_path,
                    progress_callback=self._update_progress
                )
                # 使用默认参数捕获当前值，避免闭包延迟执行问题
                self.root.after(0, lambda p=output_path: self._on_encrypt_success(p))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: self._on_encrypt_error(msg))
        
        threading.Thread(target=do_encrypt, daemon=True).start()
    
    def _on_encrypt_success(self, output_path):
        """加密成功回调"""
        self._set_busy(False)
        messagebox.showinfo("加密成功", f"文件已加密！\n\n输出文件：\n{output_path}")
        self._clear_inputs()
    
    def _on_encrypt_error(self, error):
        """加密失败回调"""
        self._set_busy(False)
        self._reset_progress()
        messagebox.showerror("加密失败", f"发生错误：{error}")
    
    def _decrypt(self):
        """解密文件"""
        input_path, output_path, password = self._validate_input()
        if not input_path:
            return
        
        self._set_busy(True)
        self._reset_progress()
        
        def do_decrypt():
            try:
                encryptor = FileEncryptor(password)
                encryptor.decrypt_file(
                    input_path, 
                    output_path,
                    progress_callback=self._update_progress
                )
                # 使用默认参数捕获当前值
                self.root.after(0, lambda p=output_path: self._on_decrypt_success(p))
                
            except Exception:
                self.root.after(0, self._on_decrypt_error)
        
        threading.Thread(target=do_decrypt, daemon=True).start()
    
    def _on_decrypt_success(self, output_path):
        """解密成功回调"""
        self._set_busy(False)
        messagebox.showinfo("解密成功", f"文件已解密！\n\n输出文件：\n{output_path}")
        self._clear_inputs()
    
    def _on_decrypt_error(self):
        """解密失败回调"""
        self._set_busy(False)
        self._reset_progress()
        messagebox.showerror("解密失败", "密码错误或文件已损坏\n\n请确保使用加密时相同的密码")
    
    def _clear_inputs(self):
        """清空所有输入框"""
        self.file_entry.delete(0, tk.END)
        self.output_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self._reset_progress()


def main():
    # 根据是否有拖拽支持选择窗口类型
    if DND_AVAILABLE:
        root = tkdnd.Tk()
    else:
        root = tk.Tk()
    
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

