from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QFormLayout, QDialog, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from components import SearchBar, ActionBar, EnhancedTable, ConfirmDialog
from styles import StyleManager


class WorkerDialog(QDialog):
    """作業員データ編集ダイアログ"""

    def __init__(self, parent=None, worker_data=None):
        super().__init__(parent)

        self.worker_data = worker_data or {}
        self.is_edit_mode = bool(worker_data)

        self.setWindowTitle("作業員" + ("編集" if self.is_edit_mode else "追加"))
        self.setMinimumWidth(400)

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # フォームレイアウト
        form_layout = QFormLayout()

        # 作業員名
        self.name_input = QLineEdit()
        StyleManager.style_input(self.name_input)
        if self.is_edit_mode:
            self.name_input.setText(self.worker_data.get('name', ''))
        form_layout.addRow("作業員名:", self.name_input)

        # 住所
        self.address_input = QLineEdit()
        StyleManager.style_input(self.address_input)
        if self.is_edit_mode:
            self.address_input.setText(self.worker_data.get('address', ''))
        form_layout.addRow("住所:", self.address_input)

        # 電話番号
        self.phone_input = QLineEdit()
        StyleManager.style_input(self.phone_input)
        if self.is_edit_mode:
            self.phone_input.setText(self.worker_data.get('phone', ''))
        form_layout.addRow("電話番号:", self.phone_input)

        # メールアドレス
        self.email_input = QLineEdit()
        StyleManager.style_input(self.email_input)
        if self.is_edit_mode:
            self.email_input.setText(self.worker_data.get('email', ''))
        form_layout.addRow("メールアドレス:", self.email_input)

        # マイナンバー
        self.my_number_input = QLineEdit()
        StyleManager.style_input(self.my_number_input)
        if self.is_edit_mode:
            self.my_number_input.setText(self.worker_data.get('my_number', ''))
        form_layout.addRow("マイナンバー:", self.my_number_input)

        # 血液型
        self.blood_type_input = QLineEdit()
        StyleManager.style_input(self.blood_type_input)
        if self.is_edit_mode:
            self.blood_type_input.setText(self.worker_data.get('blood_type', ''))
        form_layout.addRow("血液型:", self.blood_type_input)

        # 緊急連絡先（氏名）
        self.emergency_contact_input = QLineEdit()
        StyleManager.style_input(self.emergency_contact_input)
        if self.is_edit_mode:
            self.emergency_contact_input.setText(self.worker_data.get('emergency_contact', ''))
        form_layout.addRow("緊急連絡先（氏名）:", self.emergency_contact_input)

        # 緊急連絡先（電話番号）
        self.emergency_phone_input = QLineEdit()
        StyleManager.style_input(self.emergency_phone_input)
        if self.is_edit_mode:
            self.emergency_phone_input.setText(self.worker_data.get('emergency_phone', ''))
        form_layout.addRow("緊急連絡先（電話）:", self.emergency_phone_input)

        # 緊急連絡先（住所）
        self.emergency_address_input = QLineEdit()
        StyleManager.style_input(self.emergency_address_input)
        if self.is_edit_mode:
            self.emergency_address_input.setText(self.worker_data.get('emergency_address', ''))
        form_layout.addRow("緊急連絡先（住所）:", self.emergency_address_input)

        # 備考
        self.note_input = QTextEdit()
        StyleManager.style_input(self.note_input)
        self.note_input.setMaximumHeight(100)
        if self.is_edit_mode:
            self.note_input.setText(self.worker_data.get('note', ''))
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

    def get_worker_data(self):
        """入力された作業員データを取得する"""
        return {
            'name': self.name_input.text(),
            'address': self.address_input.text(),
            'phone': self.phone_input.text(),
            'email': self.email_input.text(),
            'my_number': self.my_number_input.text(),
            'blood_type': self.blood_type_input.text(),
            'emergency_contact': self.emergency_contact_input.text(),
            'emergency_phone': self.emergency_phone_input.text(),
            'emergency_address': self.emergency_address_input.text(),
            'note': self.note_input.toPlainText()
        }

    def validate(self):
        """入力データを検証する"""
        if not self.name_input.text():
            QMessageBox.warning(self, "入力エラー", "作業員名は必須です。")
            return False
        return True

    def accept(self):
        """OKボタンが押された時の処理"""
        if self.validate():
            super().accept()


class WorkersTab(QWidget):
    """作業員マスター管理タブ"""

    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setup_ui()
        self.load_workers()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # ヘッダー部分
        header_label = QLabel("作業員マスター管理")
        StyleManager.set_header_font(header_label)
        layout.addWidget(header_label)

        # 検索バー
        self.search_bar = SearchBar("作業員名で検索...")
        layout.addWidget(self.search_bar)

        # アクションバー
        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        # テーブル
        self.table = EnhancedTable(["ID", "作業員名", "住所", "電話番号", "血液型", "緊急連絡先", "緊急連絡先住所", "備考"])
        self.table.setColumnHidden(0, True)  # ID列を非表示
        layout.addWidget(self.table)

        self.setLayout(layout)

        # シグナル接続
        self.search_bar.searchClicked.connect(self.search_workers)
        self.search_bar.resetClicked.connect(self.load_workers)
        self.action_bar.addClicked.connect(self.add_worker)
        self.action_bar.editClicked.connect(self.edit_worker)
        self.action_bar.deleteClicked.connect(self.delete_worker)
        self.table.doubleClicked.connect(lambda row: self.edit_worker())

    def load_workers(self):
        """作業員データをロードする"""
        workers = self.db.get_workers()
        self.set_table_data(workers)

    def search_workers(self, search_text):
        """作業員を検索する"""
        if not search_text:
            self.load_workers()
            return

        workers = self.db.select('workers', condition="name LIKE ?", values=(f"%{search_text}%",))
        self.set_table_data(workers)

    def set_table_data(self, workers):
        """テーブルにデータをセットする"""
        # データをテーブル表示用に整形
        display_data = []
        for worker in workers:
            display_data.append({
                "ID": worker["id"],
                "作業員名": worker["name"],
                "住所": worker.get("address", "") or "",
                "電話番号": worker.get("phone", "") or "",
                "血液型": worker.get("blood_type", "") or "",
                "緊急連絡先": worker.get("emergency_contact", "") or "",
                "緊急連絡先住所": worker.get("emergency_address", "") or "",
                "備考": worker.get("note", "") or ""
            })

        self.table.set_data(display_data)

    def add_worker(self):
        """作業員を追加する"""
        dialog = WorkerDialog(self)
        if dialog.exec():
            worker_data = dialog.get_worker_data()
            try:
                self.db.insert('workers', worker_data)
                self.load_workers()
                QMessageBox.information(self, "成功", "作業員を追加しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"作業員の追加に失敗しました: {str(e)}")

    def edit_worker(self):
        """作業員を編集する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "編集する作業員を選択してください。")
            return

        # IDをintに変換
        worker_id = int(selected_data["ID"])

        # 作業員データを取得
        worker_data = self.db.select('workers', condition="id = ?", values=(worker_id,))
        if not worker_data:
            QMessageBox.warning(self, "警告", "作業員データが見つかりません。")
            return

        dialog = WorkerDialog(self, worker_data[0])
        if dialog.exec():
            updated_data = dialog.get_worker_data()
            try:
                self.db.update('workers', updated_data, "id = ?", (worker_id,))
                self.load_workers()
                QMessageBox.information(self, "成功", "作業員情報を更新しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"作業員の更新に失敗しました: {str(e)}")

    def delete_worker(self):
        """作業員を削除する"""
        selected_data = self.table.get_selected_row_data()
        if not selected_data:
            QMessageBox.warning(self, "警告", "削除する作業員を選択してください。")
            return

        # 確認ダイアログ
        confirm_dialog = ConfirmDialog(
            "作業員削除の確認",
            f"作業員「{selected_data['作業員名']}」を削除してもよろしいですか？\n"
            "この作業員に関連する案件データも影響を受ける可能性があります。",
            self
        )

        if confirm_dialog.exec():
            worker_id = int(selected_data["ID"])
            try:
                # 関連する案件-作業員の関連データを確認
                related_projects = self.db.execute_query(
                    """
                    SELECT p.* FROM projects p
                    JOIN project_workers pw ON p.id = pw.project_id
                    WHERE pw.worker_id = ?
                    """,
                    (worker_id,)
                )

                if related_projects:
                    # 関連する案件がある場合、再確認
                    confirm_cascade = ConfirmDialog(
                        "関連データの削除確認",
                        f"この作業員は{len(related_projects)}件の案件に関連付けられています。\n"
                        "削除を続行すると、これらの関連データが失われます。\n\n"
                        "本当に削除してもよろしいですか？",
                        self
                    )
                    if not confirm_cascade.exec():
                        return

                # 作業員-案件の関連を先に削除
                self.db.delete('project_workers', "worker_id = ?", (worker_id,))

                # 作業員を削除
                self.db.delete('workers', "id = ?", (worker_id,))
                self.load_workers()
                QMessageBox.information(self, "成功", "作業員を削除しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"作業員の削除に失敗しました: {str(e)}")
