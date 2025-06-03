from PyQt6.QtWidgets import QApplication, QPushButton, QListWidget, QLineEdit, QTextEdit, QLabel, QComboBox, QCheckBox, QRadioButton, QDateEdit, QTabWidget
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from PyQt6.QtCore import Qt, QSize

class StyleManager:
    """アプリケーションのスタイルを管理するクラス"""

    # メインカラー設定
    PRIMARY_COLOR = "#2a628f"  # 深い青
    SECONDARY_COLOR = "#3e92cc"  # 明るい青
    ACCENT_COLOR = "#e2924e"  # オレンジ/アクセント
    SURFACE_COLOR = "#ffffff"  # 白（背景）
    TEXT_COLOR = "#333333"  # 暗いグレー（メインテキスト）
    LIGHT_TEXT_COLOR = "#666666"  # 明るいグレー（サブテキスト）
    SUCCESS_COLOR = "#4e9e60"  # 成功色（緑）
    WARNING_COLOR = "#e2924e"  # 警告色（オレンジ）
    ERROR_COLOR = "#e05252"  # エラー色（赤）

    # フォント設定
    TITLE_FONT = QFont("メイリオ", 14, QFont.Weight.Bold)
    HEADER_FONT = QFont("メイリオ", 12, QFont.Weight.Bold)
    NORMAL_FONT = QFont("メイリオ", 10)
    SMALL_FONT = QFont("メイリオ", 9)

    # ボタンスタイル
    BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {SECONDARY_COLOR};
        }}
        QPushButton:pressed {{
            background-color: {PRIMARY_COLOR};
        }}
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #888888;
        }}
    """

    ACCENT_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {ACCENT_COLOR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #f6a054;
        }}
        QPushButton:pressed {{
            background-color: {ACCENT_COLOR};
        }}
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #888888;
        }}
    """

    DANGER_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {ERROR_COLOR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #f47272;
        }}
        QPushButton:pressed {{
            background-color: {ERROR_COLOR};
        }}
    """

    SUCCESS_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {SUCCESS_COLOR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #6abe7c;
        }}
        QPushButton:pressed {{
            background-color: {SUCCESS_COLOR};
        }}
    """

    FLAT_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: transparent;
            color: {PRIMARY_COLOR};
            border: 1px solid {PRIMARY_COLOR};
            border-radius: 5px;
            padding: 8px 15px;
        }}
        QPushButton:hover {{
            background-color: #f0f0f0;
        }}
        QPushButton:pressed {{
            background-color: #e0e0e0;
        }}
    """

    # 入力フィールドスタイル
    INPUT_STYLE = f"""
        QLineEdit, QTextEdit, QComboBox, QDateEdit {{
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
            background-color: {SURFACE_COLOR};
        }}
        QComboBox {{
            min-height: 25px;
            padding-right: 20px;
            font-weight: normal;
            color: {TEXT_COLOR};
            selection-background-color: {SECONDARY_COLOR};
            selection-color: white;
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
            border: 1px solid {SECONDARY_COLOR};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #cccccc;
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {PRIMARY_COLOR};
            margin-right: 5px;
        }}
        QComboBox::down-arrow:on {{
            top: 1px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid #cccccc;
            border-radius: 3px;
            background-color: {SURFACE_COLOR};
            selection-background-color: {SECONDARY_COLOR};
            selection-color: white;
            color: {TEXT_COLOR};
            padding: 3px;
            font: {NORMAL_FONT.family()};
            font-size: {NORMAL_FONT.pointSize()}pt;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 30px;
            padding: 5px;
            color: {TEXT_COLOR};
            border-bottom: 1px solid #f0f0f0;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: #c8e0f0;
            color: {TEXT_COLOR};
            font-weight: normal;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {SECONDARY_COLOR};
            color: white;
            font-weight: bold;
        }}
    """

    # テーブルスタイル
    TABLE_STYLE = f"""
        QTableView {{
            border: 1px solid #cccccc;
            gridline-color: #eeeeee;
            background-color: {SURFACE_COLOR};
        }}
        QTableView::item {{
            padding: 5px;
        }}
        QTableView::item:selected {{
            background-color: {SECONDARY_COLOR};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {PRIMARY_COLOR};
            color: white;
            padding: 5px;
            border: 1px solid #1a5580;
            font-weight: bold;
        }}
    """

    # リストスタイル
    LIST_STYLE = f"""
        QListWidget {{
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
            background-color: {SURFACE_COLOR};
        }}
        QListWidget::item {{
            padding: 5px;
            border-radius: 3px;
        }}
        QListWidget::item:selected {{
            background-color: {SECONDARY_COLOR};
            color: white;
        }}
        QListWidget::item:hover {{
            background-color: #f0f0f0;
        }}
    """

    # タブスタイル
    TAB_STYLE = f"""
        QTabWidget::pane {{
            border: 1px solid #cccccc;
            border-radius: 5px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 8px 15px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {SURFACE_COLOR};
            border-bottom: 1px solid {SURFACE_COLOR};
        }}
        QTabBar::tab:hover {{
            background-color: #e0e0e0;
        }}
    """

    # グループボックススタイル
    GROUP_BOX_STYLE = f"""
        QGroupBox {{
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
    """

    @classmethod
    def apply_styles(cls, app: QApplication) -> None:
        """アプリケーション全体にスタイルを適用する"""
        app.setStyle("Fusion")

        # フォント設定
        app.setFont(cls.NORMAL_FONT)

        # カラーパレット設定
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.SURFACE_COLOR))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.SURFACE_COLOR))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f5f5f5"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("white"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#333333"))
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.TEXT_COLOR))
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.PRIMARY_COLOR))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("white"))
        palette.setColor(QPalette.ColorRole.Link, QColor(cls.SECONDARY_COLOR))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.SECONDARY_COLOR))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))

        app.setPalette(palette)

    @classmethod
    def style_button(cls, button: QPushButton, button_type: str = "primary") -> None:
        """ボタンにスタイルを適用する"""
        if button_type == "primary":
            button.setStyleSheet(cls.BUTTON_STYLE)
        elif button_type == "accent":
            button.setStyleSheet(cls.ACCENT_BUTTON_STYLE)
        elif button_type == "danger":
            button.setStyleSheet(cls.DANGER_BUTTON_STYLE)
        elif button_type == "success":
            button.setStyleSheet(cls.SUCCESS_BUTTON_STYLE)
        elif button_type == "flat":
            button.setStyleSheet(cls.FLAT_BUTTON_STYLE)

    @classmethod
    def style_input(cls, widget) -> None:
        """入力ウィジェットにスタイルを適用する"""
        widget.setStyleSheet(cls.INPUT_STYLE)

    @classmethod
    def style_list(cls, list_widget: QListWidget) -> None:
        """リストウィジェットにスタイルを適用する"""
        list_widget.setStyleSheet(cls.LIST_STYLE)

    @classmethod
    def style_table(cls, table_widget) -> None:
        """テーブルウィジェットにスタイルを適用する"""
        table_widget.setStyleSheet(cls.TABLE_STYLE)

    @classmethod
    def style_tabs(cls, tab_widget: QTabWidget) -> None:
        """タブウィジェットにスタイルを適用する"""
        tab_widget.setStyleSheet(cls.TAB_STYLE)

    @classmethod
    def style_group_box(cls, group_box) -> None:
        """グループボックスにスタイルを適用する"""
        group_box.setStyleSheet(cls.GROUP_BOX_STYLE)

    @classmethod
    def set_title_font(cls, label: QLabel) -> None:
        """タイトルフォントを設定する"""
        label.setFont(cls.TITLE_FONT)

    @classmethod
    def set_header_font(cls, label: QLabel) -> None:
        """ヘッダーフォントを設定する"""
        label.setFont(cls.HEADER_FONT)

    @classmethod
    def create_icon(cls, icon_name: str) -> QIcon:
        """アイコンを作成する"""
        return QIcon(f"resources/icons/{icon_name}.png")

    @classmethod
    def get_chart_colors(cls, count: int = 1) -> list:
        """チャート用の色パレットを取得する"""
        # 高級感のあるハーモニーのとれた色パレット
        palette = [
            "#1f77b4",  # ダークブルー
            "#ff7f0e",  # オレンジ
            "#2ca02c",  # グリーン
            "#d62728",  # レッド
            "#9467bd",  # パープル
            "#8c564b",  # ブラウン
            "#e377c2",  # ピンク
            "#7f7f7f",  # グレー
            "#bcbd22",  # オリーブ
            "#17becf",  # ターコイズ
            "#aec7e8",  # ライトブルー
            "#ffbb78",  # ライトオレンジ
            "#98df8a",  # ライトグリーン
            "#ff9896",  # ライトレッド
            "#c5b0d5",  # ライトパープル
            "#c49c94",  # ライトブラウン
            "#f7b6d2",  # ライトピンク
            "#c7c7c7",  # ライトグレー
            "#dbdb8d",  # ライトオリーブ
            "#9edae5"   # ライトターコイズ
        ]

        if count <= len(palette):
            return palette[:count]
        else:
            # パレットの色を繰り返し使用
            return [palette[i % len(palette)] for i in range(count)]

    @classmethod
    def set_value_font(cls, label: QLabel) -> None:
        """値フォントを設定する（数値等の表示用）"""
        font = QFont(cls.NORMAL_FONT)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(f"color: {cls.PRIMARY_COLOR};")

    @classmethod
    def style_combo_box(cls, combo_box: QComboBox) -> None:
        """コンボボックスにスタイルを適用する"""
        combo_box.setStyleSheet(cls.INPUT_STYLE)
