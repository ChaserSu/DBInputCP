from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget


class CopyHistoryApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(** kwargs)
        self.orientation = "vertical"
        self.padding = "20dp"
        self.spacing = "15dp"
        Window.clearcolor = (1, 1, 1, 1)
        Window.size = (800, 650)  # 加宽加高窗口适配顶部栏

        # 初始化历史记录栈和指针
        self.history_stack = []
        self.history_index = -1

        # ========== 新增：顶部剪贴板显示栏（横向布局） ==========
        self.top_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height="40dp",
            spacing="10dp"
        )
        # 左侧剪贴板内容显示标签
        self.clipboard_label = Label(
            text=f"剪贴板内容：{self.get_clipboard_content()}",
            size_hint=(0.8, 1),
            color=(0.2, 0.2, 0.2, 1),
            font_size=14,
            halign="left",
            valign="middle"
        )
        self.clipboard_label.bind(size=self.clipboard_label.setter('text_size'))
        self.top_bar.add_widget(self.clipboard_label)

        # 右侧清空剪贴板按钮（方形小按钮）
        self.clear_clipboard_btn = Button(
            text="清空剪切板",
            size_hint=(0.2, 1),
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=12,
            halign="center",
            valign="middle"
        )
        self.clear_clipboard_btn.bind(on_press=self.clear_clipboard)
        self.top_bar.add_widget(self.clear_clipboard_btn)
        # 将顶部栏添加到主布局最上方
        self.add_widget(self.top_bar)

        # 背景绘制
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # 多行输入框（调整高度，预留顶部栏空间）
        self.text_input = TextInput(
            hint_text="请输入要处理的内容（支持多行）",
            size_hint=(1, None),
            height=Window.height - 280,  # 增加60dp预留顶部栏高度
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            border=(16, 16, 16, 16),
            padding=(10, 10),
            multiline=True,
            font_size=16
        )
        self.add_widget(self.text_input)

        # 提示标签
        self.tip_label = Label(
            text="",
            color=(0, 0.7, 0, 1),
            size_hint=(1, None),
            height="30dp",
            font_size=14
        )
        self.add_widget(self.tip_label)

        # 按钮网格布局（3列）
        self.button_layout = GridLayout(
            cols=3,
            size_hint=(1, None),
            height="120dp",
            spacing="10dp"
        )

        # 按钮1：仅写入剪贴板
        self.btn_write = Button(
            text="写入",
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.btn_write.bind(on_press=self.write_to_clipboard)
        self.button_layout.add_widget(self.btn_write)

        # 按钮2：写入并清空输入框
        self.btn_write_clear = Button(
            text="写入并清空",
            background_color=(0.38, 0, 0.93, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.btn_write_clear.bind(on_press=self.write_and_clear)
        self.button_layout.add_widget(self.btn_write_clear)

        # 按钮3：清空输入框（不写入剪贴板）
        self.btn_clear_only = Button(
            text="清空",
            background_color=(0.9, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.btn_clear_only.bind(on_press=self.clear_only)
        self.button_layout.add_widget(self.btn_clear_only)

        # 按钮4：恢复上一条记录
        self.btn_prev = Button(
            text="恢复上一条",
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.btn_prev.bind(on_press=self.restore_previous)
        self.button_layout.add_widget(self.btn_prev)

        # 按钮5：恢复下一条记录
        self.btn_next = Button(
            text="恢复下一条",
            background_color=(1, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.btn_next.bind(on_press=self.restore_next)
        self.button_layout.add_widget(self.btn_next)

        # 按钮6：清空历史记录
        self.btn_clear_history = Button(
            text="清空历史",
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.btn_clear_history.bind(on_press=self.clear_history)
        self.button_layout.add_widget(self.btn_clear_history)

        self.add_widget(self.button_layout)

        # 窗口大小监听
        Window.bind(on_size=self._update_input_height)
        Window.bind(on_keyboard=self._on_keyboard)

    def update_rect(self, *args):
        """更新布局背景大小"""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _update_input_height(self, window, width, height):
        """窗口大小变化时调整输入框高度"""
        self.text_input.height = height - 280

    def _on_keyboard(self, window, key, *args):
        """软键盘弹出/收起时调整布局"""
        if key == 1001:
            self.y = Window.height - window.keyboard_height - self.height
        elif key == 1002:
            self.y = 0
        return True

    def show_tip(self, text, is_success=True):
        """显示提示信息，3秒后自动消失"""
        self.tip_label.color = (0, 0.7, 0, 1) if is_success else (0.9, 0.2, 0.2, 1)
        self.tip_label.text = text
        Clock.schedule_once(lambda dt: setattr(self.tip_label, "text", ""), 3)

    def get_clipboard_content(self):
        """获取剪贴板内容，过长时截断显示"""
        content = Clipboard.paste()
        # 过滤空字节，确保显示"空"
        if len(content) == 0 or content == "\x00":
            return "空"
        elif len(content) > 20:
            return content[:20] + "..."
        return content

    def update_clipboard_display(self):
        """更新顶部剪贴板显示标签内容"""
        self.clipboard_label.text = f"剪贴板内容：{self.get_clipboard_content()}"

    def clear_clipboard(self, instance):
        """修复清空剪贴板功能：写入空字节，兼容所有系统"""
        Clipboard.copy("\x00")  # 用空字节替代空字符串
        self.update_clipboard_display()
        self.show_tip("✓ 剪切板已清空", True)

    def write_to_clipboard(self, instance):
        """仅写入剪贴板，不清空输入框"""
        content = self.text_input.text.strip()
        if not content:
            self.show_tip("输入框为空，请输入内容", False)
            return
        Clipboard.copy(content)
        self.history_stack.append(content)
        self.history_index = len(self.history_stack) - 1
        self.update_clipboard_display()  # 点击后更新剪贴板显示
        self.show_tip(f"✓ 已写入剪贴板（历史记录共 {len(self.history_stack)} 条）")

    def write_and_clear(self, instance):
        """写入剪贴板并清空输入框"""
        content = self.text_input.text.strip()
        if not content:
            self.show_tip("输入框为空，请输入内容", False)
            return
        Clipboard.copy(content)
        self.history_stack.append(content)
        self.history_index = len(self.history_stack) - 1
        self.text_input.text = ""
        self.update_clipboard_display()  # 点击后更新剪贴板显示
        self.show_tip(f"✓ 已写入并清空（历史记录共 {len(self.history_stack)} 条）")

    def clear_only(self, instance):
        """仅清空输入框，不写入剪贴板"""
        content = self.text_input.text.strip()
        if not content:
            self.show_tip("输入框已为空", False)
            return
        self.history_stack.append(content)
        self.history_index = len(self.history_stack) - 1
        self.text_input.text = ""
        self.update_clipboard_display()  # 点击后更新剪贴板显示
        self.show_tip(f"✓ 已清空输入框（历史记录共 {len(self.history_stack)} 条）")

    def restore_previous(self, instance):
        """恢复上一条：单条记录可恢复，多条记录按指针前移"""
        if len(self.history_stack) == 0:
            self.show_tip("暂无历史记录", False)
            return
        if len(self.history_stack) == 1:
            self.text_input.text = self.history_stack[0]
            self.show_tip(f"已恢复记录（当前唯一记录）")
        elif self.history_index > 0:
            self.history_index -= 1
            self.text_input.text = self.history_stack[self.history_index]
            self.show_tip(f"已恢复上一条（当前第 {self.history_index + 1}/{len(self.history_stack)} 条）")
        else:
            self.show_tip("已是第一条记录", False)
        self.update_clipboard_display()  # 点击后更新剪贴板显示

    def restore_next(self, instance):
        """恢复下一条：单条记录提示最后一条，多条记录按指针后移"""
        if len(self.history_stack) == 0:
            self.show_tip("暂无历史记录", False)
            return
        if len(self.history_stack) == 1:
            self.show_tip("已是最后一条记录", False)
        elif self.history_index < len(self.history_stack) - 1:
            self.history_index += 1
            self.text_input.text = self.history_stack[self.history_index]
            self.show_tip(f"已恢复下一条（当前第 {self.history_index + 1}/{len(self.history_stack)} 条）")
        else:
            self.show_tip("已是最后一条记录", False)
        self.update_clipboard_display()  # 点击后更新剪贴板显示

    def clear_history(self, instance):
        """清空历史记录队列，不影响剪贴板"""
        if not self.history_stack:
            self.show_tip("暂无历史记录可清空", False)
            return
        self.history_stack.clear()
        self.history_index = -1
        self.update_clipboard_display()  # 点击后更新剪贴板显示
        self.show_tip("✓ 历史记录已清空", True)


class MyApp(App):
    def build(self):
        return CopyHistoryApp()


if __name__ == "__main__":
    MyApp().run()
