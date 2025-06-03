from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QFormLayout, QDialog, QDialogButtonBox, QMessageBox,
    QDoubleSpinBox, QDateEdit, QComboBox, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QRadioButton, QButtonGroup, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components import (
    SearchBar, ActionBar, EnhancedTable, ConfirmDialog,
    EnhancedComboBox, DateRangeSelector
)
from styles import StyleManager


class ProjectDialog(QDialog):
    """案件データ編集ダイアログ"""

    def __init__(self, parent=None, db=None, project_data=None):
        super().__init__(parent)

        self.db = db
        self.project_data = project_data or {}
        self.is_edit_mode = bool(project_data)

        self.setWindowTitle("案件" + ("編集" if self.is_edit_mode else "登録"))
        self.setMinimumWidth(500)

        self.setup_ui()
        self.load_master_data()

        if self.is_edit_mode:
            self.load_project_workers()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # フォームレイアウト
        form_layout = QFormLayout()

        # 案件タイトル
        self.title_input = QLineEdit()
        StyleManager.style_input(self.title_input)
        if self.is_edit_mode:
            self.title_input.setText(self.project_data.get('title', ''))
        form_layout.addRow("案件タイトル:", self.title_input)

        # 取引先選択
        self.client_combo = EnhancedComboBox()
        form_layout.addRow("取引先:", self.client_combo)

        # サービス選択
        self.service_combo = EnhancedComboBox()
        self.service_combo.currentIndexChanged.connect(self.update_price_from_service)
        form_layout.addRow("サービス:", self.service_combo)

        # 現場住所
        self.site_address_input = QLineEdit()
        StyleManager.style_input(self.site_address_input)
        if self.is_edit_mode:
            self.site_address_input.setText(self.project_data.get('site_address', ''))
        form_layout.addRow("現場住所:", self.site_address_input)

        # 価格
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 100000000)
        self.price_input.setSingleStep(1000)
        self.price_input.setPrefix("¥ ")
        self.price_input.setGroupSeparatorShown(True)
        self.price_input.setDecimals(0)  # 小数点以下の桁数を0に設定
        StyleManager.style_input(self.price_input)
        if self.is_edit_mode and self.project_data.get('price') is not None:
            self.price_input.setValue(float(self.project_data.get('price', 0)))
        form_layout.addRow("価格:", self.price_input)

        # 作業期間
        date_layout = QHBoxLayout()

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        StyleManager.style_input(self.start_date)

        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("〜"))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        StyleManager.style_input(self.end_date)

        date_layout.addWidget(self.end_date)

        if self.is_edit_mode:
            if self.project_data.get('start_date'):
                try:
                    date_parts = self.project_data.get('start_date').split('-')
                    if len(date_parts) == 3:
                        self.start_date.setDate(QDate(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])))
                except:
                    pass

            if self.project_data.get('end_date'):
                try:
                    date_parts = self.project_data.get('end_date').split('-')
                    if len(date_parts) == 3:
                        self.end_date.setDate(QDate(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])))
                except:
                    pass

        form_layout.addRow("作業期間:", date_layout)

        # 状態
        self.status_combo = QComboBox()
        self.status_combo.addItems(["作業前", "作業中", "完了", "キャンセル"])
        StyleManager.style_input(self.status_combo)
        if self.is_edit_mode:
            index = self.status_combo.findText(self.project_data.get('status', '作業前'))
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        form_layout.addRow("状態:", self.status_combo)

        # 完了日
        self.completion_date = QDateEdit()
        self.completion_date.setCalendarPopup(True)
        self.completion_date.setDate(QDate.currentDate())
        StyleManager.style_input(self.completion_date)
        if self.is_edit_mode and self.project_data.get('completion_date'):
            try:
                date_parts = self.project_data.get('completion_date').split('-')
                if len(date_parts) == 3:
                    self.completion_date.setDate(QDate(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])))
            except:
                pass
        form_layout.addRow("完了日:", self.completion_date)

        # トラブル情報
        trouble_layout = QHBoxLayout()

        self.has_trouble_check = QCheckBox("トラブルあり")
        if self.is_edit_mode and self.project_data.get('has_trouble') == 1:
            self.has_trouble_check.setChecked(True)

        trouble_layout.addWidget(self.has_trouble_check)

        self.trouble_worker_combo = EnhancedComboBox()
        self.trouble_worker_combo.setEnabled(self.has_trouble_check.isChecked())

        self.has_trouble_check.stateChanged.connect(self._on_trouble_check_changed)

        trouble_layout.addWidget(QLabel("担当者:"))
        trouble_layout.addWidget(self.trouble_worker_combo)

        form_layout.addRow("トラブル:", trouble_layout)

        # 説明
        self.description_input = QTextEdit()
        StyleManager.style_input(self.description_input)
        if self.is_edit_mode:
            self.description_input.setText(self.project_data.get('description', ''))
        form_layout.addRow("説明:", self.description_input)

        layout.addLayout(form_layout)

        # 作業員選択部分
        workers_group = QGroupBox("担当作業員")
        workers_layout = QVBoxLayout()

        self.workers_list = QListWidget()
        StyleManager.style_list(self.workers_list)

        workers_layout.addWidget(self.workers_list)

        workers_group.setLayout(workers_layout)
        layout.addWidget(workers_group)

        # 写真部分
        if self.is_edit_mode:
            photo_group = QGroupBox("写真")
            photo_layout = QVBoxLayout()

            photo_info_layout = QHBoxLayout()

            photo_count = self.project_data.get('photo_count', 0)
            self.photo_count_label = QLabel(f"登録済み写真: {photo_count} 枚")
            photo_info_layout.addWidget(self.photo_count_label)

            add_photo_button = QPushButton("写真追加")
            add_photo_button.clicked.connect(self.add_photo)
            photo_info_layout.addWidget(add_photo_button)

            view_photos_button = QPushButton("写真表示")
            view_photos_button.clicked.connect(self.view_photos)
            photo_info_layout.addWidget(view_photos_button)

            photo_layout.addLayout(photo_info_layout)
            photo_group.setLayout(photo_layout)
            layout.addWidget(photo_group)

        # ボタン
        button_layout = QHBoxLayout()

        if self.is_edit_mode:
            work_order_button = QPushButton("業務指示書")
            work_order_button.clicked.connect(self.open_work_order)
            button_layout.addWidget(work_order_button)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        button_layout.addWidget(button_box)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_master_data(self):
        """マスターデータをロードする"""
        # 取引先データロード
        clients = self.db.get_clients()
        self.client_combo.set_items(clients)

        if self.is_edit_mode and self.project_data.get('client_id'):
            self.client_combo.set_selected_value(self.project_data.get('client_id'))

        # サービスデータロード
        services = self.db.get_services()
        self.service_combo.set_items(services)

        if self.is_edit_mode and self.project_data.get('service_id'):
            self.service_combo.set_selected_value(self.project_data.get('service_id'))

        # 作業員データロード
        workers = self.db.get_workers()
        self.workers_list.clear()

        for worker in workers:
            item = QListWidgetItem(worker['name'])
            item.setData(Qt.ItemDataRole.UserRole, worker['id'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.workers_list.addItem(item)

        # トラブル担当者選択用のデータをロード
        # まず空のオプションを追加
        self.trouble_worker_combo.clear()
        self.trouble_worker_combo.addItem("選択してください", None)
        
        # 作業員データを追加
        for worker in workers:
            self.trouble_worker_combo.addItem(worker['name'], worker['id'])
        
        if self.is_edit_mode and self.project_data.get('trouble_worker_id'):
            self.trouble_worker_combo.set_selected_value(self.project_data.get('trouble_worker_id'))

    def load_project_workers(self):
        """案件に関連する作業員データをロード"""
        if not self.project_data.get('id'):
            return

        project_workers = self.db.get_project_workers(self.project_data.get('id'))
        project_worker_ids = [w['id'] for w in project_workers]

        # チェック状態を設定
        for i in range(self.workers_list.count()):
            item = self.workers_list.item(i)
            worker_id = item.data(Qt.ItemDataRole.UserRole)

            if worker_id in project_worker_ids:
                item.setCheckState(Qt.CheckState.Checked)

    def _on_trouble_check_changed(self, state):
        """トラブルチェックボックス状態変更時の処理"""
        is_checked = state == Qt.CheckState.Checked
        self.trouble_worker_combo.setEnabled(is_checked)
        
        # チェックが外れた場合、選択をリセット
        if not is_checked:
            self.trouble_worker_combo.setCurrentIndex(0)  # "選択してください"を選択

    def update_price_from_service(self):
        """選択されたサービスに基づいて価格を設定"""
        service_id = self.service_combo.get_selected_value()
        if not service_id:
            return

        # サービス標準価格の設定機能が削除されたため、このメソッドでは何も行わない
        # 将来的に価格設定のロジックが必要であれば、ここに追加する

    def get_project_data(self):
        """入力された案件データを取得する"""
        return {
            'title': self.title_input.text(),
            'client_id': self.client_combo.get_selected_value(),
            'service_id': self.service_combo.get_selected_value(),
            'site_address': self.site_address_input.text(),
            'price': self.price_input.value(),
            'status': self.status_combo.currentText(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'completion_date': self.completion_date.date().toString("yyyy-MM-dd"),
            'has_trouble': 1 if self.has_trouble_check.isChecked() else 0,
            'trouble_worker_id': self.trouble_worker_combo.get_selected_value() if self.has_trouble_check.isChecked() else None,
            'description': self.description_input.toPlainText()
        }

    def get_selected_worker_ids(self):
        """選択された作業員IDのリストを取得"""
        worker_ids = []

        for i in range(self.workers_list.count()):
            item = self.workers_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                worker_id = item.data(Qt.ItemDataRole.UserRole)
                worker_ids.append(worker_id)

        return worker_ids

    def validate(self):
        """入力データを検証する"""
        if not self.title_input.text():
            QMessageBox.warning(self, "入力エラー", "案件タイトルを入力してください。")
            return False

        if not self.client_combo.get_selected_value():
            QMessageBox.warning(self, "入力エラー", "取引先を選択してください。")
            return False

        if not self.service_combo.get_selected_value():
            QMessageBox.warning(self, "入力エラー", "サービスを選択してください。")
            return False

        if not self.site_address_input.text():
            QMessageBox.warning(self, "入力エラー", "現場住所を入力してください。")
            return False

        if self.price_input.value() <= 0:
            QMessageBox.warning(self, "入力エラー", "価格は0より大きい値で入力してください。")
            return False

        if self.has_trouble_check.isChecked():
            trouble_worker_id = self.trouble_worker_combo.get_selected_value()
            if not trouble_worker_id:
                QMessageBox.warning(self, "入力エラー", "トラブルありをチェックした場合は、担当者を選択してください。")
                return False

        return True

    def accept(self):
        """OKボタンが押された時の処理"""
        if self.validate():
            super().accept()

    def add_photo(self):
        """写真を追加する"""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QDir
        import shutil
        import os

        # 写真選択ダイアログを表示
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "写真の選択",
            QDir.homePath(),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if not files:
            return

        if len(files) > 100:
            QMessageBox.warning(self, "エラー", "一度に追加できる写真は100枚までです。")
            return

        # 保存先ディレクトリを確認、なければ作成
        save_dir = os.path.join("resources", "project_photos", str(self.project_data.get('id')))
        os.makedirs(save_dir, exist_ok=True)

        # 写真をリソースディレクトリにコピー
        for file_path in files:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(save_dir, file_name)

            # 同名ファイルがある場合、名前を変更
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(file_name)
                i = 1
                while os.path.exists(os.path.join(save_dir, f"{base}_{i}{ext}")):
                    i += 1
                dest_path = os.path.join(save_dir, f"{base}_{i}{ext}")

            # ファイルコピー
            shutil.copy2(file_path, dest_path)

            # データベースに写真情報を登録
            self.db.add_project_photo(self.project_data.get('id'), dest_path)

        # 写真カウントラベルを更新
        photo_count = self.db.select('project_photos', 'COUNT(*) as count', 'project_id = ?', (self.project_data.get('id'),))[0]['count']
        self.photo_count_label.setText(f"登録済み写真: {photo_count} 枚")
        self.project_data['photo_count'] = photo_count

        QMessageBox.information(self, "完了", f"{len(files)}枚の写真を追加しました。")

    def view_photos(self):
        """写真一覧を表示する"""
        from dialogs.photo_viewer_dialog import PhotoViewerDialog

        project_id = self.project_data.get('id')
        if not project_id:
            return

        photos = self.db.get_project_photos(project_id)
        if not photos:
            QMessageBox.information(self, "情報", "この案件にはまだ写真が登録されていません。")
            return

        dialog = PhotoViewerDialog(self.db, project_id, parent=self)
        dialog.exec()

    def open_work_order(self):
        """業務指示書ダイアログを開く"""
        from dialogs.work_order_dialog import WorkOrderDialog

        # DialogのインスタンスとProjectDataをセットして作成
        dialog = WorkOrderDialog(self.db, self.project_data, parent=self)
        dialog.exec()

        # ダイアログが閉じられた後、業務指示書が保存されている場合
        if hasattr(dialog, 'saved') and dialog.saved:
            # 親ウィンドウ（メインウィンドウ）を取得して業務指示書タブを更新
            main_window = self.window()
            if hasattr(main_window, 'work_orders_tab'):
                main_window.work_orders_tab.load_work_orders()
                # 必要に応じてデータ変更シグナルを発行
                if hasattr(main_window.work_orders_tab, 'ordersChanged'):
                    main_window.work_orders_tab.ordersChanged.emit()


class ProjectsTab(QWidget):
    """案件管理タブ"""

    # シグナル定義
    projectsChanged = pyqtSignal()  # 案件データが変更された時に発行するシグナル

    def __init__(self, db):
        super().__init__()

        self.db = db
        # ソート設定の初期化
        self.current_sort_column = "created_at"
        self.current_sort_order = "DESC"
        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # ヘッダー部分
        header_label = QLabel("案件管理")
        StyleManager.set_header_font(header_label)
        layout.addWidget(header_label)

        # フィルター部分
        filter_layout = QHBoxLayout()

        # 検索バー
        self.search_bar = SearchBar("案件タイトルで検索...")
        filter_layout.addWidget(self.search_bar)

        # 状態フィルター
        status_group = QGroupBox("状態フィルター")
        status_layout = QHBoxLayout()

        self.status_all = QRadioButton("すべて")
        self.status_all.setChecked(True)
        self.status_before = QRadioButton("作業前")
        self.status_ongoing = QRadioButton("作業中")
        self.status_completed = QRadioButton("完了")
        self.status_cancelled = QRadioButton("キャンセル")

        self.status_filter_group = QButtonGroup()
        self.status_filter_group.addButton(self.status_all, 0)
        self.status_filter_group.addButton(self.status_before, 1)
        self.status_filter_group.addButton(self.status_ongoing, 2)
        self.status_filter_group.addButton(self.status_completed, 3)
        self.status_filter_group.addButton(self.status_cancelled, 4)

        status_layout.addWidget(self.status_all)
        status_layout.addWidget(self.status_before)
        status_layout.addWidget(self.status_ongoing)
        status_layout.addWidget(self.status_completed)
        status_layout.addWidget(self.status_cancelled)

        status_group.setLayout(status_layout)
        filter_layout.addWidget(status_group)

        layout.addLayout(filter_layout)

        # 追加フィルター部分
        additional_filter_layout = QHBoxLayout()

        # 取引先フィルター
        client_filter_group = QGroupBox("取引先")
        client_filter_layout = QHBoxLayout()

        self.client_combo = EnhancedComboBox()
        # 取引先データをロード
        clients = self.db.get_clients()
        # 空のオプションを先頭に追加
        self.client_combo.clear()
        self.client_combo.addItem("すべての取引先", None)
        # 残りのアイテムを追加
        for client in clients:
            self.client_combo.addItem(client["name"], client["id"])

        client_filter_layout.addWidget(self.client_combo)
        client_filter_group.setLayout(client_filter_layout)
        additional_filter_layout.addWidget(client_filter_group)

        # サービスフィルター
        service_filter_group = QGroupBox("サービス")
        service_filter_layout = QHBoxLayout()

        self.service_combo = EnhancedComboBox()
        # サービスデータをロード
        services = self.db.get_services()
        # 空のオプションを先頭に追加
        self.service_combo.clear()
        self.service_combo.addItem("すべてのサービス", None)
        # 残りのアイテムを追加
        for service in services:
            self.service_combo.addItem(service["name"], service["id"])

        service_filter_layout.addWidget(self.service_combo)
        service_filter_group.setLayout(service_filter_layout)
        additional_filter_layout.addWidget(service_filter_group)

        # 並び替えフィルター
        sort_filter_group = QGroupBox("並び替え")
        sort_filter_layout = QHBoxLayout()

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("登録日（新しい順）", ("created_at", "DESC"))
        self.sort_combo.addItem("登録日（古い順）", ("created_at", "ASC"))
        self.sort_combo.addItem("価格（高い順）", ("price", "DESC"))
        self.sort_combo.addItem("価格（安い順）", ("price", "ASC"))
        self.sort_combo.addItem("案件名（昇順）", ("title", "ASC"))
        self.sort_combo.addItem("案件名（降順）", ("title", "DESC"))

        StyleManager.style_input(self.sort_combo)

        sort_filter_layout.addWidget(self.sort_combo)
        sort_filter_group.setLayout(sort_filter_layout)
        additional_filter_layout.addWidget(sort_filter_group)

        layout.addLayout(additional_filter_layout)

        # 日付範囲選択
        date_filter_group = QGroupBox("期間")
        date_filter_layout = QHBoxLayout()

        # 年と月の選択コンボボックスに変更
        date_filter_layout.addWidget(QLabel("年:"))

        # 年選択コンボボックス
        self.year_combo = QComboBox()
        self.year_combo.addItem("すべて", None)
        for year in range(2025, 2031):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentIndex(0)  # 初期選択を「すべて」に設定
        StyleManager.style_input(self.year_combo)

        self.year_combo.currentIndexChanged.connect(self.apply_filters)
        date_filter_layout.addWidget(self.year_combo)

        # 月選択コンボボックス
        date_filter_layout.addWidget(QLabel("月:"))

        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(80)
        StyleManager.style_input(self.month_combo)

        # 「すべて」と月の選択肢を追加
        self.month_combo.addItem("すべて", None)

        for month in range(1, 13):
            self.month_combo.addItem(f"{month}月", month)

        # 初期選択を「すべて」にする
        self.month_combo.setCurrentIndex(0)  # インデックス0は「すべて」
        self.month_combo.currentIndexChanged.connect(self.apply_filters)
        date_filter_layout.addWidget(self.month_combo)

        date_filter_group.setLayout(date_filter_layout)

        layout.addWidget(date_filter_group)

        # アクションバー
        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        # テーブル
        self.table = EnhancedTable([
            "ID", "案件タイトル", "取引先", "サービス", "価格", "状態", "作業日", "担当作業員", "説明"
        ])
        self.table.setColumnHidden(0, True)  # ID列を非表示
        self.table.horizontalHeader().setStretchLastSection(True)  # 最後の列を引き伸ばし
        self.table.setMinimumWidth(1000)  # 最小幅設定
        # サイズポリシーをExpandingに設定して、テーブルが画面幅いっぱいに広がるようにする
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.table)

        self.setLayout(layout)

        # シグナル接続
        self.search_bar.searchClicked.connect(self.apply_filters)
        self.search_bar.resetClicked.connect(self.reset_filters)
        self.status_filter_group.buttonClicked.connect(self.apply_filters)
        self.year_combo.currentIndexChanged.connect(self.apply_filters)
        self.month_combo.currentIndexChanged.connect(self.apply_filters)
        self.action_bar.addClicked.connect(self.add_project)
        self.action_bar.editClicked.connect(self.edit_project)
        self.action_bar.deleteClicked.connect(self.delete_project)
        self.table.doubleClicked.connect(lambda row: self.edit_project())
        # 新しいフィルターと並び替えに関するシグナル接続
        self.client_combo.currentIndexChanged.connect(self.apply_filters)
        self.service_combo.currentIndexChanged.connect(self.apply_filters)
        self.sort_combo.currentIndexChanged.connect(self.apply_filters)

    def load_projects(self, condition="", values=()):
        """案件データをロードする"""
        # 並び替え設定を取得
        sort_column, sort_order = self.current_sort_column, self.current_sort_order

        # 条件構築、ORDER BY句は含めない
        # 並び替えは別パラメータとして渡す
        projects = self.db.get_projects(
            condition=condition,
            values=values,
            sort_column=sort_column,
            sort_order=sort_order
        )
        self.set_table_data(projects)

        # データ変更を通知する（統計情報の更新のため）
        self.projectsChanged.emit()

    def apply_filters(self):
        """フィルターを適用する"""
        # 検索テキスト
        search_text = self.search_bar.search_input.text()

        # 状態フィルター
        status_id = self.status_filter_group.checkedId()
        status_map = {
            0: None,  # すべて
            1: "作業前",
            2: "作業中",
            3: "完了",
            4: "キャンセル"
        }
        status = status_map.get(status_id)

        # 取引先フィルター
        selected_client_id = self.client_combo.currentData()

        # サービスフィルター
        selected_service_id = self.service_combo.currentData()

        # 日付フィルター
        selected_year = self.year_combo.currentData()
        selected_month = self.month_combo.currentData()

        # ソート設定
        sort_data = self.sort_combo.currentData()

        # 条件とパラメータの構築
        conditions = []
        values = []

        if search_text:
            conditions.append("p.title LIKE ?")
            values.append(f"%{search_text}%")

        if status:
            conditions.append("p.status = ?")
            values.append(status)

        if selected_client_id:
            conditions.append("p.client_id = ?")
            values.append(selected_client_id)

        if selected_service_id:
            conditions.append("p.service_id = ?")
            values.append(selected_service_id)

        # 日付フィルターの条件構築
        if selected_year and selected_month:
            # 年と月の両方が選択されている場合
            conditions.append("p.completion_date >= ? AND p.completion_date <= ?")
            values.append(f"{selected_year}-{selected_month:02d}-01")
            last_day = QDate(selected_year, selected_month, 1).daysInMonth()
            values.append(f"{selected_year}-{selected_month:02d}-{last_day:02d}")
        elif selected_year:
            # 年のみが選択されている場合
            conditions.append("strftime('%Y', p.completion_date) = ?")
            values.append(str(selected_year))
        elif selected_month:
            # 月のみが選択されている場合
            conditions.append("strftime('%m', p.completion_date) = ?")
            values.append(f"{selected_month:02d}")

        # ソート設定の更新
        if sort_data:
            self.current_sort_column, self.current_sort_order = sort_data

        # 条件文字列の構築
        condition = " AND ".join(conditions) if conditions else ""

        # フィルターを適用
        self.load_projects(condition, tuple(values))

    def reset_filters(self):
        """フィルターをリセットする"""
        self.search_bar.search_input.clear()
        self.status_all.setChecked(True)
        self.client_combo.setCurrentIndex(0)  # すべての取引先
        self.service_combo.setCurrentIndex(0)  # すべてのサービス
        self.sort_combo.setCurrentIndex(0)    # デフォルトソート
        self.year_combo.setCurrentIndex(0)    # すべて
        self.month_combo.setCurrentIndex(0)   # すべて

        # ソート設定をリセット
        self.current_sort_column = "created_at"
        self.current_sort_order = "DESC"

        self.load_projects()

        # データ変更を通知する（統計情報の更新のため）
        self.projectsChanged.emit()

    def set_table_data(self, projects):
        """テーブルにデータをセットする"""
        # データをテーブル表示用に整形
        display_data = []
        for project in projects:
            # 価格表示のフォーマット
            price_str = f"¥ {project['price']:,.0f}" if project['price'] else ""

            # 担当作業員情報を取得
            project_workers = self.db.get_project_workers(project["id"])
            worker_names = [w["name"] for w in project_workers]
            worker_str = ", ".join(worker_names) if worker_names else ""

            display_data.append({
                "ID": project["id"],
                "案件タイトル": project["title"],
                "取引先": project["client_name"],
                "サービス": project["service_name"],
                "価格": price_str,
                "状態": project["status"],
                "作業日": project["completion_date"] or "",
                "担当作業員": worker_str,
                "説明": project["description"] or ""
            })

        self.table.set_data(display_data)

        # 列幅調整
        self.table.resizeColumnsToContents()

        # 列幅最適化して、テーブル全体が表示領域に合うようにする
        table_width = self.table.width()
        total_column_width = 0
        for i in range(self.table.columnCount()):
            if not self.table.isColumnHidden(i):
                total_column_width += self.table.columnWidth(i)

        # 最小幅設定して、テーブルが画面幅に合うようにする
        for i in range(self.table.columnCount()):
            if not self.table.isColumnHidden(i):
                # 説明列は少し幅固定
                if i == 8:  # 説明列
                    self.table.setColumnWidth(i, 250)
                elif i == 1:  # 案件タイトル列も少し広く
                    self.table.setColumnWidth(i, max(180, self.table.columnWidth(i)))
                elif i == 7:  # 担当作業員列も少し広く
                    self.table.setColumnWidth(i, max(150, self.table.columnWidth(i)))
                elif i == 2:  # 取引先列も少し広く
                    self.table.setColumnWidth(i, max(150, self.table.columnWidth(i)))

    def add_project(self):
        """案件を追加する"""
        dialog = ProjectDialog(self, self.db)
        if dialog.exec():
            project_data = dialog.get_project_data()
            try:
                # 案件を追加
                project_id = self.db.insert('projects', project_data)

                # 作業員との関連を追加
                worker_ids = dialog.get_selected_worker_ids()
                for worker_id in worker_ids:
                    self.db.add_project_worker(project_id, worker_id)

                self.load_projects()
                QMessageBox.information(self, "成功", "案件を登録しました。")

                # データ変更シグナルを発行
                self.projectsChanged.emit()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"案件の登録に失敗しました: {str(e)}")

    def edit_project(self):
        """案件を編集する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "編集する案件を選択してください。")
            return

        # IDをintに変換
        project_id = int(selected_data["ID"])

        # 案件データを取得
        project_data = self.db.get_projects("p.id = ?", (project_id,))
        if not project_data:
            QMessageBox.warning(self, "警告", "案件データが見つかりません。")
            return

        dialog = ProjectDialog(self, self.db, project_data[0])
        if dialog.exec():
            updated_data = dialog.get_project_data()
            try:
                # 案件を更新
                self.db.update('projects', updated_data, "id = ?", (project_id,))

                # 作業員との関連を更新（いったん全部削除して再登録）
                self.db.delete('project_workers', "project_id = ?", (project_id,))

                worker_ids = dialog.get_selected_worker_ids()
                for worker_id in worker_ids:
                    self.db.add_project_worker(project_id, worker_id)

                self.load_projects()
                QMessageBox.information(self, "成功", "案件情報を更新しました。")

                # データ変更シグナルを発行
                self.projectsChanged.emit()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"案件の更新に失敗しました: {str(e)}")

    def delete_project(self):
        """案件を削除する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "削除する案件を選択してください。")
            return

        # 確認ダイアログ
        confirm_dialog = ConfirmDialog(
            "案件削除の確認",
            f"案件「{selected_data['案件タイトル']}」を削除してもよろしいですか？",
            self
        )

        if confirm_dialog.exec():
            project_id = int(selected_data["ID"])
            try:
                # 作業員との関連を先に削除
                self.db.delete('project_workers', "project_id = ?", (project_id,))

                # 案件を削除
                self.db.delete('projects', "id = ?", (project_id,))

                self.load_projects()
                QMessageBox.information(self, "成功", "案件を削除しました。")

                # データ変更シグナルを発行
                self.projectsChanged.emit()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"案件の削除に失敗しました: {str(e)}")
