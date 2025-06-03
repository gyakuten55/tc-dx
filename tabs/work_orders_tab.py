from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QHeaderView, QSizePolicy,
    QDialog, QRadioButton, QGroupBox, QComboBox, QDialogButtonBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components import (
    SearchBar, ActionBar, EnhancedTable, ConfirmDialog,
    EnhancedComboBox, StyleManager
)
from dialogs.work_order_dialog import WorkOrderDialog

class ProjectSelectionDialog(QDialog):
    """案件選択ダイアログ"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_project = None
        self.projects = []

        self.setWindowTitle("業務指示書作成")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.setup_ui()
        self.load_all_projects()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # オプション選択グループ
        options_group = QGroupBox("作成方法")
        options_layout = QVBoxLayout()

        # 新規作成オプション
        self.new_radio = QRadioButton("空の状態から新規作成")
        self.new_radio.setChecked(True)
        self.new_radio.toggled.connect(self.toggle_project_selection)
        options_layout.addWidget(self.new_radio)

        # 既存案件からの作成オプション
        self.from_project_radio = QRadioButton("既存の案件を基に作成")
        self.from_project_radio.toggled.connect(self.toggle_project_selection)
        options_layout.addWidget(self.from_project_radio)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 案件選択セクション
        self.project_selection_group = QGroupBox("案件選択")
        project_selection_layout = QVBoxLayout()

        # 検索・フィルタ部分
        filter_layout = QHBoxLayout()

        # 検索バー
        self.search_bar = SearchBar("案件タイトルで検索...")
        self.search_bar.searchClicked.connect(self.filter_projects)
        self.search_bar.resetClicked.connect(self.reset_filters)
        filter_layout.addWidget(self.search_bar)

        project_selection_layout.addLayout(filter_layout)

        # 追加フィルタ部分（取引先・サービス）
        additional_filter_layout = QHBoxLayout()

        # 取引先フィルタ
        client_filter_group = QGroupBox("取引先")
        client_filter_layout = QHBoxLayout()

        self.client_combo = EnhancedComboBox()

        # 取引先データをロード
        clients = self.db.get_clients()
        self.client_combo.clear()
        self.client_combo.addItem("すべての取引先", None)
        for client in clients:
            self.client_combo.addItem(client["name"], client["id"])

        self.client_combo.currentIndexChanged.connect(self.filter_projects)
        client_filter_layout.addWidget(self.client_combo)
        client_filter_group.setLayout(client_filter_layout)
        additional_filter_layout.addWidget(client_filter_group)

        # サービスフィルタ
        service_filter_group = QGroupBox("サービス")
        service_filter_layout = QHBoxLayout()

        self.service_combo = EnhancedComboBox()

        # サービスデータをロード
        services = self.db.get_services()
        self.service_combo.clear()
        self.service_combo.addItem("すべてのサービス", None)
        for service in services:
            self.service_combo.addItem(service["name"], service["id"])

        self.service_combo.currentIndexChanged.connect(self.filter_projects)
        service_filter_layout.addWidget(self.service_combo)
        service_filter_group.setLayout(service_filter_layout)
        additional_filter_layout.addWidget(service_filter_group)

        project_selection_layout.addLayout(additional_filter_layout)

        # 案件一覧テーブル
        self.project_table = EnhancedTable([
            "ID", "案件タイトル", "取引先", "サービス", "現場住所", "状態", "作業期間"
        ])
        self.project_table.setColumnHidden(0, True)  # ID列を非表示
        self.project_table.horizontalHeader().setStretchLastSection(True)
        self.project_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.project_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.project_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.project_table.doubleClicked.connect(self.on_project_double_clicked)

        project_selection_layout.addWidget(self.project_table)

        # ステータス表示
        self.status_label = QLabel("案件数: 0")
        project_selection_layout.addWidget(self.status_label)

        self.project_selection_group.setLayout(project_selection_layout)
        self.project_selection_group.setEnabled(False)
        layout.addWidget(self.project_selection_group)

        # ボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_all_projects(self):
        """全案件データを読み込む"""
        self.projects = self.db.get_projects()
        self.update_project_table(self.projects)

    def update_project_table(self, projects):
        """プロジェクトテーブルを更新する"""
        # データをテーブル表示用に整形
        display_data = []
        for project in projects:
            # 作業期間の表示形式を整形
            start_date = project.get('start_date', '')
            end_date = project.get('end_date', '')
            work_period = f"{start_date} 〜 {end_date}" if start_date and end_date else ""

            display_data.append({
                "ID": project["id"],
                "案件タイトル": project["title"],
                "取引先": project["client_name"],
                "サービス": project["service_name"],
                "現場住所": project["site_address"] or "",
                "状態": project["status"],
                "作業期間": work_period
            })

        self.project_table.set_data(display_data)

        # 列幅を調整
        self.project_table.resizeColumnsToContents()

        # ステータス表示更新
        self.status_label.setText(f"案件数: {len(projects)}")

    def toggle_project_selection(self, checked):
        """案件選択グループの有効/無効を切り替える"""
        self.project_selection_group.setEnabled(self.from_project_radio.isChecked())

    def filter_projects(self):
        """案件一覧を絞り込む"""
        # 検索テキスト
        search_text = self.search_bar.search_input.text()

        # 取引先フィルタ
        selected_client_id = self.client_combo.currentData()

        # サービスフィルタ
        selected_service_id = self.service_combo.currentData()

        # 条件とパラメータの構築
        conditions = []
        values = []

        if search_text:
            conditions.append("p.title LIKE ? OR p.site_address LIKE ?")
            values.append(f"%{search_text}%")
            values.append(f"%{search_text}%")

        if selected_client_id:
            conditions.append("p.client_id = ?")
            values.append(selected_client_id)

        if selected_service_id:
            conditions.append("p.service_id = ?")
            values.append(selected_service_id)

        # 条件文の構築
        condition = " AND ".join(conditions) if conditions else ""

        # フィルタを適用
        self.projects = self.db.get_projects(condition, tuple(values))
        self.update_project_table(self.projects)

    def reset_filters(self):
        """フィルタをリセットする"""
        self.search_bar.search_input.clear()
        self.client_combo.setCurrentIndex(0)  # すべての取引先
        self.service_combo.setCurrentIndex(0)  # すべてのサービス

        # 全案件を再読み込み
        self.load_all_projects()

    def on_project_double_clicked(self, row):
        """案件がダブルクリックされたときの処理"""
        self.accept()

    def accept(self):
        """OKボタンが押されたときの処理"""
        if self.from_project_radio.isChecked():
            selected_data = self.project_table.get_selected_row_data()
            if not selected_data:
                QMessageBox.warning(self, "エラー", "案件を選択してください。")
                return

            # 選択された案件のIDを取得
            project_id = int(selected_data["ID"])

            # 選択された案件の詳細情報を取得
            projects = self.db.get_projects("p.id = ?", (project_id,))
            if projects:
                self.selected_project = projects[0]
            else:
                QMessageBox.warning(self, "エラー", "選択された案件の情報が取得できませんでした。")
                return

        super().accept()


class WorkOrdersTab(QWidget):
    """業務指示書管理タブ"""

    # シグナル定義
    ordersChanged = pyqtSignal()  # 業務指示書データが変更された時に発行するシグナル

    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setup_ui()
        self.load_work_orders()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # ヘッダー部分
        header_label = QLabel("業務指示書管理")
        StyleManager.set_header_font(header_label)
        layout.addWidget(header_label)

        # 検索バー
        self.search_bar = SearchBar("業務指示書を検索...")
        layout.addWidget(self.search_bar)

        # アクションバー
        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        # プレビューボタン
        preview_layout = QHBoxLayout()
        self.preview_button = QPushButton("プレビュー")
        self.preview_button.clicked.connect(self.preview_work_order)
        preview_layout.addWidget(self.preview_button)

        # PDFボタン
        self.pdf_button = QPushButton("PDF保存")
        self.pdf_button.clicked.connect(self.save_as_pdf)
        preview_layout.addWidget(self.pdf_button)

        # 印刷ボタン
        self.print_button = QPushButton("印刷")
        self.print_button.clicked.connect(self.print_work_order)
        preview_layout.addWidget(self.print_button)

        preview_layout.addStretch()
        layout.addLayout(preview_layout)

        # テーブル
        self.table = EnhancedTable([
            "ID", "番号", "作成日", "現場名", "作業期間", "作業内容", "担当者", "作成者", "案件"
        ])
        self.table.setColumnHidden(0, True)  # ID列を非表示
        self.table.horizontalHeader().setStretchLastSection(True)  # 最後の列を引き伸ばし
        # サイズポリシーをExpandingに設定して、テーブルが画面いっぱいに広がるようにする
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.table)

        self.setLayout(layout)

        # シグナル接続
        self.search_bar.searchClicked.connect(self.search_work_orders)
        self.search_bar.resetClicked.connect(self.load_work_orders)
        self.action_bar.addClicked.connect(self.add_work_order)
        self.action_bar.editClicked.connect(self.edit_work_order)
        self.action_bar.deleteClicked.connect(self.delete_work_order)
        self.table.doubleClicked.connect(lambda row: self.edit_work_order())

    def load_work_orders(self):
        """業務指示書データをロードする"""
        work_orders = self.db.get_work_orders()
        self.set_table_data(work_orders)

    def search_work_orders(self):
        """業務指示書を検索する"""
        search_text = self.search_bar.search_input.text()
        if not search_text:
            self.load_work_orders()
            return

        # 検索条件
        condition = "wo.site_name LIKE ? OR wo.order_number LIKE ? OR p.title LIKE ?"
        values = (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%")

        work_orders = self.db.get_work_orders(condition, values)
        self.set_table_data(work_orders)

    def set_table_data(self, work_orders):
        """テーブルにデータをセットする"""
        display_data = []
        for order in work_orders:
            display_data.append({
                "ID": order["id"],
                "番号": order["order_number"],
                "作成日": order["creation_date"],
                "現場名": order["site_name"],
                "作業期間": f"{order['start_date']} 〜 {order['end_date']}",
                "作業内容": order["work_content"],
                "担当者": order["manager_name"],
                "作成者": order["creator_name"],
                "案件": order["project_title"] if order["project_title"] else "なし"
            })

        self.table.set_data(display_data)

        # 列幅を調整
        self.table.resizeColumnsToContents()

    def add_work_order(self):
        """新規業務指示書を作成する"""
        # 案件選択ダイアログを表示
        selection_dialog = ProjectSelectionDialog(self.db, self)
        if selection_dialog.exec():
            # 案件が選択された場合
            project_data = selection_dialog.selected_project

            # 業務指示書ダイアログを表示
            dialog = WorkOrderDialog(self.db, project_data, self)
            result = dialog.exec()

            # ダイアログが完了したら、変更内容を更新
            # 保存が行われたかどうかにかかわらず、一覧を更新する
            self.load_work_orders()

            # データ変更シグナルを発行（保存された場合のみ）
            if hasattr(dialog, 'saved') and dialog.saved:
                self.ordersChanged.emit()

    def edit_work_order(self):
        """業務指示書を編集する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "編集する業務指示書を選択してください。")
            return

        # IDをintに変換
        order_id = int(selected_data["ID"])

        # 業務指示書データを取得
        order_data = self.db.get_work_order(order_id)
        if not order_data:
            QMessageBox.warning(self, "警告", "業務指示書データが見つかりません。")
            return

        # 関連するプロジェクトデータを取得
        project_data = None
        if order_data.get('project_id'):
            projects = self.db.get_projects("p.id = ?", (order_data['project_id'],))
            if projects:
                project_data = projects[0]

        # 業務指示書ダイアログを表示
        dialog = WorkOrderDialog(self.db, project_data, self, order_data)
        result = dialog.exec()

        # ダイアログが完了したら、変更内容を更新
        # 保存が行われたかどうかにかかわらず、一覧を更新する
        self.load_work_orders()

        # データ変更シグナルを発行
        if hasattr(dialog, 'saved') and dialog.saved:
            self.ordersChanged.emit()

    def load_work_order_dialog(self, order_data, project_data):
        """業務指示書ダイアログに既存データをロードする"""
        # 既存の業務指示書データを直接ダイアログに渡す
        dialog = WorkOrderDialog(self.db, project_data, self, order_data)
        return dialog

    def delete_work_order(self):
        """業務指示書を削除する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "削除する業務指示書を選択してください。")
            return

        # 確認ダイアログ
        confirm_dialog = ConfirmDialog(
            "業務指示書削除の確認",
            f"業務指示書「{selected_data['番号']}」を削除してもよろしいですか？",
            self
        )

        if confirm_dialog.exec():
            order_id = int(selected_data["ID"])
            try:
                # 業務指示書を削除
                self.db.delete_work_order(order_id)

                self.load_work_orders()
                QMessageBox.information(self, "成功", "業務指示書を削除しました。")

                # データ変更シグナルを発行
                self.ordersChanged.emit()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"業務指示書の削除に失敗しました: {str(e)}")

    def preview_work_order(self):
        """業務指示書をプレビューする"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "プレビューする業務指示書を選択してください。")
            return

        # IDをintに変換
        order_id = int(selected_data["ID"])

        # 業務指示書データを取得
        order_data = self.db.get_work_order(order_id)
        if not order_data:
            QMessageBox.warning(self, "警告", "業務指示書データが見つかりません。")
            return

        # 関連するプロジェクトデータを取得
        project_data = None
        if order_data.get('project_id'):
            projects = self.db.get_projects("p.id = ?", (order_data['project_id'],))
            if projects:
                project_data = projects[0]

        # 業務指示書ダイアログを表示
        dialog = WorkOrderDialog(self.db, project_data, self, order_data)
        dialog.preview_order()

    def save_as_pdf(self):
        """選択された業務指示書をPDFとして保存する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "PDF保存する業務指示書を選択してください。")
            return

        # IDをintに変換
        order_id = int(selected_data["ID"])

        # 業務指示書データを取得
        order_data = self.db.get_work_order(order_id)
        if not order_data:
            QMessageBox.warning(self, "警告", "業務指示書データが見つかりません。")
            return

        # 関連するプロジェクトデータを取得
        project_data = None
        if order_data.get('project_id'):
            projects = self.db.get_projects("p.id = ?", (order_data['project_id'],))
            if projects:
                project_data = projects[0]

        # 業務指示書ダイアログを表示
        dialog = WorkOrderDialog(self.db, project_data, self, order_data)
        dialog.save_as_pdf()

    def print_work_order(self):
        """選択された業務指示書を印刷する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "印刷する業務指示書を選択してください。")
            return

        # IDをintに変換
        order_id = int(selected_data["ID"])

        # 業務指示書データを取得
        order_data = self.db.get_work_order(order_id)
        if not order_data:
            QMessageBox.warning(self, "警告", "業務指示書データが見つかりません。")
            return

        # 関連するプロジェクトデータを取得
        project_data = None
        if order_data.get('project_id'):
            projects = self.db.get_projects("p.id = ?", (order_data['project_id'],))
            if projects:
                project_data = projects[0]

        # 業務指示書ダイアログを表示
        dialog = WorkOrderDialog(self.db, project_data, self, order_data)
        dialog.print_order()
