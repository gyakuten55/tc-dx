from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QFormLayout, QDialog, QDialogButtonBox, QMessageBox,
    QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from components import SearchBar, ActionBar, EnhancedTable, ConfirmDialog
from styles import StyleManager


class ServiceDialog(QDialog):
    """サービスデータ編集ダイアログ"""

    def __init__(self, parent=None, service_data=None):
        super().__init__(parent)

        self.service_data = service_data or {}
        self.is_edit_mode = bool(service_data)

        self.setWindowTitle("サービス" + ("編集" if self.is_edit_mode else "追加"))
        self.setMinimumWidth(400)

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # フォームレイアウト
        form_layout = QFormLayout()

        # サービス名
        self.name_input = QLineEdit()
        StyleManager.style_input(self.name_input)
        if self.is_edit_mode:
            self.name_input.setText(self.service_data.get('name', ''))
        form_layout.addRow("サービス名:", self.name_input)

        # 説明
        self.description_input = QTextEdit()
        StyleManager.style_input(self.description_input)
        self.description_input.setMaximumHeight(100)
        if self.is_edit_mode:
            self.description_input.setText(self.service_data.get('description', ''))
        form_layout.addRow("説明:", self.description_input)

        layout.addLayout(form_layout)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_service_data(self):
        """入力されたサービスデータを取得する"""
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText()
        }

    def validate(self):
        """入力データを検証する"""
        if not self.name_input.text():
            QMessageBox.warning(self, "入力エラー", "サービス名は必須です。")
            return False
        return True

    def accept(self):
        """OKボタンが押された時の処理"""
        if self.validate():
            super().accept()


class ServicesTab(QWidget):
    """サービスマスター管理タブ"""

    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setup_ui()
        self.load_services()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # ヘッダー部分
        header_label = QLabel("サービスマスター管理")
        StyleManager.set_header_font(header_label)
        layout.addWidget(header_label)

        # 検索バー
        self.search_bar = SearchBar("サービス名で検索...")
        layout.addWidget(self.search_bar)

        # アクションバー
        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        # テーブル
        self.table = EnhancedTable(["ID", "サービス名", "説明"])
        self.table.setColumnHidden(0, True)  # ID列を非表示
        layout.addWidget(self.table)

        self.setLayout(layout)

        # シグナル接続
        self.search_bar.searchClicked.connect(self.search_services)
        self.search_bar.resetClicked.connect(self.load_services)
        self.action_bar.addClicked.connect(self.add_service)
        self.action_bar.editClicked.connect(self.edit_service)
        self.action_bar.deleteClicked.connect(self.delete_service)
        self.table.doubleClicked.connect(lambda row: self.edit_service())

    def load_services(self):
        """サービスデータをロードする"""
        services = self.db.get_services()
        self.set_table_data(services)

    def search_services(self, search_text):
        """サービスを検索する"""
        if not search_text:
            self.load_services()
            return

        services = self.db.select('services', condition="name LIKE ?", values=(f"%{search_text}%",))
        self.set_table_data(services)

    def set_table_data(self, services):
        """テーブルにデータをセットする"""
        # データをテーブル表示用に整形
        display_data = []
        for service in services:
            display_data.append({
                "ID": service["id"],
                "サービス名": service["name"],
                "説明": service.get("description", "") or ""
            })

        self.table.set_data(display_data)

    def add_service(self):
        """サービスを追加する"""
        dialog = ServiceDialog(self)
        if dialog.exec():
            service_data = dialog.get_service_data()
            try:
                self.db.insert('services', service_data)
                self.load_services()
                QMessageBox.information(self, "成功", "サービスを追加しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"サービスの追加に失敗しました: {str(e)}")

    def edit_service(self):
        """サービスを編集する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "編集するサービスを選択してください。")
            return

        # IDをintに変換
        service_id = int(selected_data["ID"])

        # サービスデータを取得
        service_data = self.db.select('services', condition="id = ?", values=(service_id,))
        if not service_data:
            QMessageBox.warning(self, "警告", "サービスデータが見つかりません。")
            return

        dialog = ServiceDialog(self, service_data[0])
        if dialog.exec():
            updated_data = dialog.get_service_data()
            try:
                self.db.update('services', updated_data, "id = ?", (service_id,))
                self.load_services()
                QMessageBox.information(self, "成功", "サービス情報を更新しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"サービスの更新に失敗しました: {str(e)}")

    def delete_service(self):
        """サービスを削除する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "削除するサービスを選択してください。")
            return

        # 確認ダイアログ
        confirm_dialog = ConfirmDialog(
            "サービス削除の確認",
            f"サービス「{selected_data['サービス名']}」を削除してもよろしいですか？\n"
            "このサービスに関連する案件データも削除される可能性があります。",
            self
        )

        if confirm_dialog.exec():
            service_id = int(selected_data["ID"])
            try:
                # 関連する案件データを確認
                related_projects = self.db.select('projects', condition="service_id = ?", values=(service_id,))
                if related_projects:
                    # 関連する案件がある場合、再確認
                    confirm_cascade = ConfirmDialog(
                        "関連データの削除確認",
                        f"このサービスには{len(related_projects)}件の案件データが関連付けられています。\n"
                        "削除を続行すると、これらの案件データも失われます。\n\n"
                        "本当に削除してもよろしいですか？",
                        self
                    )
                    if not confirm_cascade.exec():
                        return

                # 削除実行
                self.db.delete('services', "id = ?", (service_id,))
                self.load_services()
                QMessageBox.information(self, "成功", "サービスを削除しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"サービスの削除に失敗しました: {str(e)}")
