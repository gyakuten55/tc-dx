from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QFormLayout, QDialog, QDialogButtonBox, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from components import SearchBar, ActionBar, EnhancedTable, ConfirmDialog
from styles import StyleManager


class ClientDialog(QDialog):
    """取引先データ編集ダイアログ"""

    def __init__(self, parent=None, client_data=None):
        super().__init__(parent)

        self.client_data = client_data or {}
        self.is_edit_mode = bool(client_data)

        self.setWindowTitle("取引先" + ("編集" if self.is_edit_mode else "追加"))
        self.setMinimumWidth(400)

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # フォームレイアウト
        form_layout = QFormLayout()

        # 取引先名
        self.name_input = QLineEdit()
        StyleManager.style_input(self.name_input)
        if self.is_edit_mode:
            self.name_input.setText(self.client_data.get('name', ''))
        form_layout.addRow("取引先名:", self.name_input)

        # 住所
        self.address_input = QLineEdit()
        StyleManager.style_input(self.address_input)
        if self.is_edit_mode:
            self.address_input.setText(self.client_data.get('address', ''))
        form_layout.addRow("住所:", self.address_input)

        # 電話番号
        self.phone_input = QLineEdit()
        StyleManager.style_input(self.phone_input)
        if self.is_edit_mode:
            self.phone_input.setText(self.client_data.get('phone', ''))
        form_layout.addRow("電話番号:", self.phone_input)

        # メールアドレス
        self.email_input = QLineEdit()
        StyleManager.style_input(self.email_input)
        if self.is_edit_mode:
            self.email_input.setText(self.client_data.get('email', ''))
        form_layout.addRow("メールアドレス:", self.email_input)

        # 書類情報
        documents_layout = QHBoxLayout()

        # 図面の有無
        self.has_drawings_check = QCheckBox("図面あり")
        if self.is_edit_mode and self.client_data.get('has_drawings') == 1:
            self.has_drawings_check.setChecked(True)
        documents_layout.addWidget(self.has_drawings_check)

        # Excel書類の有無
        self.has_documents_check = QCheckBox("Excel書類あり")
        if self.is_edit_mode and self.client_data.get('has_documents') == 1:
            self.has_documents_check.setChecked(True)
        documents_layout.addWidget(self.has_documents_check)

        form_layout.addRow("書類情報:", documents_layout)

        # 備考
        self.note_input = QTextEdit()
        StyleManager.style_input(self.note_input)
        self.note_input.setMaximumHeight(100)
        if self.is_edit_mode:
            self.note_input.setText(self.client_data.get('note', ''))
        form_layout.addRow("備考:", self.note_input)

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

    def get_client_data(self):
        """入力された取引先データを取得する"""
        return {
            'name': self.name_input.text(),
            'address': self.address_input.text(),
            'phone': self.phone_input.text(),
            'email': self.email_input.text(),
            'has_drawings': 1 if self.has_drawings_check.isChecked() else 0,
            'has_documents': 1 if self.has_documents_check.isChecked() else 0,
            'note': self.note_input.toPlainText()
        }

    def validate(self):
        """入力データを検証する"""
        if not self.name_input.text():
            QMessageBox.warning(self, "入力エラー", "取引先名は必須です。")
            return False
        return True

    def accept(self):
        """OKボタンが押された時の処理"""
        if self.validate():
            super().accept()


class ClientsTab(QWidget):
    """取引先マスター管理タブ"""

    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setup_ui()
        self.load_clients()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # ヘッダー部分
        header_label = QLabel("取引先マスター管理")
        StyleManager.set_header_font(header_label)
        layout.addWidget(header_label)

        # 検索バー
        self.search_bar = SearchBar("取引先名で検索...")
        layout.addWidget(self.search_bar)

        # アクションバー
        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        # テーブル
        self.table = EnhancedTable(["ID", "取引先名", "住所", "電話番号", "図面", "書類", "備考"])
        self.table.setColumnHidden(0, True)  # ID列を非表示
        layout.addWidget(self.table)

        self.setLayout(layout)

        # シグナル接続
        self.search_bar.searchClicked.connect(self.search_clients)
        self.search_bar.resetClicked.connect(self.load_clients)
        self.action_bar.addClicked.connect(self.add_client)
        self.action_bar.editClicked.connect(self.edit_client)
        self.action_bar.deleteClicked.connect(self.delete_client)
        self.table.doubleClicked.connect(lambda row: self.edit_client())

    def load_clients(self):
        """取引先データをロードする"""
        clients = self.db.get_clients()
        self.set_table_data(clients)

    def search_clients(self, search_text):
        """取引先を検索する"""
        if not search_text:
            self.load_clients()
            return

        clients = self.db.select('clients', condition="name LIKE ?", values=(f"%{search_text}%",))
        self.set_table_data(clients)

    def set_table_data(self, clients):
        """テーブルにデータをセットする"""
        # データをテーブル表示用に整形
        display_data = []
        for client in clients:
            display_data.append({
                "ID": client["id"],
                "取引先名": client["name"],
                "住所": client.get("address", "") or "",
                "電話番号": client.get("phone", "") or "",
                "図面": "あり" if client.get("has_drawings", 0) == 1 else "なし",
                "書類": "あり" if client.get("has_documents", 0) == 1 else "なし",
                "備考": client.get("note", "") or ""
            })

        self.table.set_data(display_data)

    def add_client(self):
        """取引先を追加する"""
        dialog = ClientDialog(self)
        if dialog.exec():
            client_data = dialog.get_client_data()
            try:
                self.db.insert('clients', client_data)
                self.load_clients()
                QMessageBox.information(self, "成功", "取引先を追加しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"取引先の追加に失敗しました: {str(e)}")

    def edit_client(self):
        """取引先を編集する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "編集する取引先を選択してください。")
            return

        # IDをintに変換
        client_id = int(selected_data["ID"])

        # 取引先データを取得
        client_data = self.db.select('clients', condition="id = ?", values=(client_id,))
        if not client_data:
            QMessageBox.warning(self, "警告", "取引先データが見つかりません。")
            return

        dialog = ClientDialog(self, client_data[0])
        if dialog.exec():
            updated_data = dialog.get_client_data()
            try:
                self.db.update('clients', updated_data, "id = ?", (client_id,))
                self.load_clients()
                QMessageBox.information(self, "成功", "取引先情報を更新しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"取引先の更新に失敗しました: {str(e)}")

    def delete_client(self):
        """取引先を削除する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "削除する取引先を選択してください。")
            return

        # 確認ダイアログ
        confirm_dialog = ConfirmDialog(
            "取引先削除の確認",
            f"取引先「{selected_data['取引先名']}」を削除してもよろしいですか？\n"
            "この取引先に関連する案件データも削除される可能性があります。",
            self
        )

        if confirm_dialog.exec():
            client_id = int(selected_data["ID"])
            try:
                # 関連する案件データを確認
                related_projects = self.db.select('projects', condition="client_id = ?", values=(client_id,))
                if related_projects:
                    # 関連する案件がある場合、再確認
                    confirm_cascade = ConfirmDialog(
                        "関連データの削除確認",
                        f"この取引先には{len(related_projects)}件の案件データが関連付けられています。\n"
                        "削除を続行すると、これらの案件データも失われます。\n\n"
                        "本当に削除してもよろしいですか？",
                        self
                    )
                    if not confirm_cascade.exec():
                        return

                # 削除実行
                self.db.delete('clients', "id = ?", (client_id,))
                self.load_clients()
                QMessageBox.information(self, "成功", "取引先を削除しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"取引先の削除に失敗しました: {str(e)}")
