from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QCheckBox,
    QDialog, QMessageBox, QGroupBox, QFormLayout, QSpinBox,
    QDialogButtonBox, QListWidget, QListWidgetItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap

from styles import StyleManager

class SearchBar(QWidget):
    """検索バー付きウィジェット"""

    searchClicked = pyqtSignal(str)
    resetClicked = pyqtSignal()

    def __init__(self, placeholder_text="検索..."):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 検索入力フィールド
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder_text)
        StyleManager.style_input(self.search_input)

        # 検索ボタン
        self.search_button = QPushButton("検索")
        StyleManager.style_button(self.search_button)
        self.search_button.setFixedWidth(80)

        # リセットボタン
        self.reset_button = QPushButton("リセット")
        StyleManager.style_button(self.reset_button, "flat")
        self.reset_button.setFixedWidth(80)

        # レイアウトに追加
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)

        # シグナル接続
        self.search_button.clicked.connect(self._on_search)
        self.reset_button.clicked.connect(self._on_reset)
        self.search_input.returnPressed.connect(self._on_search)

    def _on_search(self):
        """検索ボタンクリック時の処理"""
        text = self.search_input.text()
        self.searchClicked.emit(text)

    def _on_reset(self):
        """リセットボタンクリック時の処理"""
        self.search_input.clear()
        self.resetClicked.emit()


class ActionBar(QWidget):
    """アクションボタン付きウィジェット"""

    addClicked = pyqtSignal()
    editClicked = pyqtSignal()
    deleteClicked = pyqtSignal()

    def __init__(self, show_edit=True, show_delete=True):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 追加ボタン
        self.add_button = QPushButton("追加")
        StyleManager.style_button(self.add_button, "success")

        # 編集ボタン
        self.edit_button = QPushButton("編集")
        StyleManager.style_button(self.edit_button)

        # 削除ボタン
        self.delete_button = QPushButton("削除")
        StyleManager.style_button(self.delete_button, "danger")

        # レイアウトに追加
        layout.addWidget(self.add_button)
        if show_edit:
            layout.addWidget(self.edit_button)
        if show_delete:
            layout.addWidget(self.delete_button)

        layout.addStretch()

        self.setLayout(layout)

        # シグナル接続
        self.add_button.clicked.connect(self.addClicked)
        self.edit_button.clicked.connect(self.editClicked)
        self.delete_button.clicked.connect(self.deleteClicked)


class ConfirmDialog(QDialog):
    """確認ダイアログ"""

    def __init__(self, title, message, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # メッセージラベル
        label = QLabel(message)
        label.setWordWrap(True)

        # ボタン
        buttons = QDialogButtonBox()
        buttons.setStandardButtons(
            QDialogButtonBox.StandardButton.Yes |
            QDialogButtonBox.StandardButton.No
        )

        # レイアウトに追加
        layout.addWidget(label)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # シグナル接続
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)


class EnhancedTable(QTableWidget):
    """拡張機能付きテーブルウィジェット"""

    doubleClicked = pyqtSignal(int)  # 行のインデックスを送信

    def __init__(self, headers):
        super().__init__()

        # テーブル設定
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # テーブルの幅を最大限に拡張する
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # スタイル適用
        StyleManager.style_table(self)

        # シグナル接続
        self.itemDoubleClicked.connect(self._on_double_click)

    def _on_double_click(self, item):
        """項目のダブルクリック時の処理"""
        row = item.row()
        self.doubleClicked.emit(row)

    def set_data(self, data, id_column=None):
        """テーブルにデータをセットする"""
        self.setRowCount(0)  # テーブルをクリア

        for row_idx, row_data in enumerate(data):
            self.insertRow(row_idx)

            for col_idx, header in enumerate(self.horizontalHeaderLabels()):
                if header in row_data:
                    item = QTableWidgetItem(str(row_data[header]))

                    # ID列の場合は非表示データとして格納
                    if id_column and header == id_column:
                        item.setData(Qt.ItemDataRole.UserRole, row_data[header])

                    self.setItem(row_idx, col_idx, item)

        # 列幅調整
        self.resizeColumnsToContents()

    def get_selected_row_data(self):
        """選択された行のデータを取得する"""
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        data = {}

        for col in range(self.columnCount()):
            header = self.horizontalHeaderItem(col).text()
            item = self.item(row, col)

            if item:
                # UserRoleにデータがあればそれを使用
                user_data = item.data(Qt.ItemDataRole.UserRole)
                if user_data:
                    data[header] = user_data
                else:
                    data[header] = item.text()

        return data

    def clear_selection(self):
        """選択をクリアする"""
        self.clearSelection()

    def horizontalHeaderLabels(self):
        """ヘッダーラベルのリストを取得する"""
        return [self.horizontalHeaderItem(i).text() for i in range(self.columnCount())]


class EnhancedComboBox(QComboBox):
    """拡張機能付きコンボボックス"""

    def __init__(self):
        super().__init__()
        StyleManager.style_input(self)

    def set_items(self, items, display_field="name", value_field="id"):
        """アイテムをセットする"""
        self.clear()

        for item in items:
            # 表示テキストと値を設定
            self.addItem(str(item[display_field]), item[value_field])

    def get_selected_value(self):
        """選択された値を取得する"""
        return self.currentData()

    def set_selected_value(self, value):
        """指定した値を選択する"""
        index = self.findData(value)
        if index >= 0:
            self.setCurrentIndex(index)


class DateRangeSelector(QWidget):
    """日付範囲選択ウィジェット"""

    rangeChanged = pyqtSignal(QDate, QDate)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ラベル
        from_label = QLabel("開始")
        from_label.setFixedWidth(40)
        to_label = QLabel("終了")
        to_label.setFixedWidth(40)

        # 日付選択
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setFixedWidth(120)
        StyleManager.style_input(self.from_date)

        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setFixedWidth(120)
        StyleManager.style_input(self.to_date)

        # 適用ボタン
        self.apply_button = QPushButton("適用")
        StyleManager.style_button(self.apply_button, "primary")
        self.apply_button.setFixedWidth(80)

        # レイアウトに追加
        layout.addWidget(from_label)
        layout.addWidget(self.from_date)
        layout.addWidget(to_label)
        layout.addWidget(self.to_date)
        layout.addWidget(self.apply_button)
        layout.addStretch()

        self.setLayout(layout)

        # シグナル接続
        self.apply_button.clicked.connect(self._on_apply)

    def _on_apply(self):
        """適用ボタンクリック時の処理"""
        from_date = self.from_date.date()
        to_date = self.to_date.date()

        if from_date <= to_date:
            self.rangeChanged.emit(from_date, to_date)
        else:
            QMessageBox.warning(self, "エラー", "開始日は終了日より前である必要があります。")


class YearSelector(QWidget):
    """年選択ウィジェット"""

    yearChanged = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # ラベル
        year_label = QLabel("年度:")

        # 年選択コンボボックス
        self.year_combo = QComboBox()
        self.year_combo.addItem("すべて", 0)
        for year in range(2025, 2031):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentIndex(0)  # 初期選択を「すべて」に設定
        StyleManager.style_input(self.year_combo)

        # 適用ボタン
        self.apply_button = QPushButton("表示")
        StyleManager.style_button(self.apply_button)

        # レイアウトに追加
        layout.addWidget(year_label)
        layout.addWidget(self.year_combo)
        layout.addWidget(self.apply_button)
        layout.addStretch()

        self.setLayout(layout)

        # シグナル接続
        self.apply_button.clicked.connect(self._on_apply)

    def _on_apply(self):
        """適用ボタンクリック時の処理"""
        year = self.year_combo.currentData()
        self.yearChanged.emit(year)

    def get_selected_year(self):
        """選択された年を取得する"""
        return self.year_combo.currentData()

    def set_year(self, year):
        """年度を設定する"""
        for i in range(self.year_combo.count()):
            if self.year_combo.itemData(i) == year:
                self.year_combo.setCurrentIndex(i)
                return
        # 見つからない場合は最初のアイテム（「すべて」）を選択
        self.year_combo.setCurrentIndex(0)
