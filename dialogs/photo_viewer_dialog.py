from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QWidget, QPushButton, QFileDialog, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage

import os
import shutil


class PhotoViewerDialog(QDialog):
    """写真ビューアーダイアログ"""

    def __init__(self, db, project_id, parent=None):
        super().__init__(parent)

        self.db = db
        self.project_id = project_id
        self.photos = []
        self.current_index = 0

        self.setWindowTitle("案件写真ビューアー")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.setup_ui()
        self.load_photos()

    def setup_ui(self):
        """UIをセットアップする"""
        main_layout = QVBoxLayout(self)

        # 画像表示エリア
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(600, 400)

        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)

        main_layout.addWidget(scroll_area)

        # サムネイルエリア
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_widget)
        self.thumbnail_layout.setContentsMargins(10, 10, 10, 10)
        self.thumbnail_layout.setSpacing(10)

        thumbnail_scroll = QScrollArea()
        thumbnail_scroll.setWidget(self.thumbnail_widget)
        thumbnail_scroll.setWidgetResizable(True)
        thumbnail_scroll.setMaximumHeight(150)

        main_layout.addWidget(thumbnail_scroll)

        # 操作ボタン
        button_layout = QHBoxLayout()

        self.prev_button = QPushButton("前の写真")
        self.prev_button.clicked.connect(self.show_previous_photo)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("次の写真")
        self.next_button.clicked.connect(self.show_next_photo)
        button_layout.addWidget(self.next_button)

        button_layout.addStretch()

        self.export_button = QPushButton("エクスポート")
        self.export_button.clicked.connect(self.export_photos)
        button_layout.addWidget(self.export_button)

        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_current_photo)
        button_layout.addWidget(self.delete_button)

        self.close_button = QPushButton("閉じる")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

    def load_photos(self):
        """写真データを読み込む"""
        self.photos = self.db.get_project_photos(self.project_id)

        # サムネイル表示をクリア
        for i in reversed(range(self.thumbnail_layout.count())):
            self.thumbnail_layout.itemAt(i).widget().setParent(None)

        # サムネイルを表示
        for i, photo in enumerate(self.photos):
            thumbnail = self.create_thumbnail(photo['photo_path'], 100, 100)
            thumbnail.setObjectName(f"thumbnail_{i}")
            thumbnail.mousePressEvent = lambda event, idx=i: self.select_photo(idx)

            row = i // 6
            col = i % 6
            self.thumbnail_layout.addWidget(thumbnail, row, col)

        # 最初の写真を表示
        if self.photos:
            self.show_photo(0)
        else:
            self.image_label.setText("写真がありません")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.export_button.setEnabled(False)

    def create_thumbnail(self, image_path, width, height):
        """サムネイルを作成する"""
        label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.gray)

        label.setPixmap(pixmap)
        label.setFixedSize(width, height)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("border: 2px solid transparent; padding: 2px;")

        return label

    def select_photo(self, index):
        """写真を選択する"""
        if 0 <= index < len(self.photos):
            self.show_photo(index)

    def show_photo(self, index):
        """写真を表示する"""
        if not self.photos or index >= len(self.photos):
            return

        self.current_index = index

        # すべてのサムネイルの境界線をリセット
        for i in range(self.thumbnail_layout.count()):
            widget = self.thumbnail_layout.itemAt(i).widget()
            if widget:
                widget.setStyleSheet("border: 2px solid transparent; padding: 2px;")

        # 選択中のサムネイルを強調表示
        selected_widget = self.thumbnail_widget.findChild(QLabel, f"thumbnail_{index}")
        if selected_widget:
            selected_widget.setStyleSheet("border: 2px solid blue; padding: 2px;")

        # 大きな画像を表示
        photo_path = self.photos[index]['photo_path']
        pixmap = QPixmap(photo_path)

        if not pixmap.isNull():
            # ラベルのサイズに合わせて画像をリサイズ
            max_size = self.image_label.size()
            scaled_pixmap = pixmap.scaled(
                max_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("画像を読み込めませんでした")

        # ボタンの有効/無効を更新
        self.prev_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self.photos) - 1)

    def show_previous_photo(self):
        """前の写真を表示する"""
        if self.current_index > 0:
            self.show_photo(self.current_index - 1)

    def show_next_photo(self):
        """次の写真を表示する"""
        if self.current_index < len(self.photos) - 1:
            self.show_photo(self.current_index + 1)

    def delete_current_photo(self):
        """現在表示中の写真を削除する"""
        if not self.photos or self.current_index >= len(self.photos):
            return

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            "この写真を削除してもよろしいですか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 写真ID取得
        photo_id = self.photos[self.current_index]['id']
        photo_path = self.photos[self.current_index]['photo_path']

        # データベースから削除
        self.db.delete_project_photo(photo_id)

        # ファイルも削除
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            print(f"ファイル削除エラー: {e}")

        # 写真リストを更新
        self.photos.pop(self.current_index)

        # 表示を更新
        if self.photos:
            # 新しいインデックスの計算
            new_index = min(self.current_index, len(self.photos) - 1)
            self.load_photos()
            self.show_photo(new_index)
        else:
            self.load_photos()

    def export_photos(self):
        """写真をエクスポートする"""
        if not self.photos:
            QMessageBox.information(self, "情報", "エクスポートする写真がありません。")
            return

        # フォルダ選択ダイアログ
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "エクスポート先フォルダを選択",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )

        if not export_dir:
            return

        # 写真をエクスポート
        success_count = 0
        error_count = 0

        for photo in self.photos:
            src_path = photo['photo_path']
            file_name = os.path.basename(src_path)
            dest_path = os.path.join(export_dir, file_name)

            # 同名ファイルがある場合の名前を変更
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(file_name)
                i = 1
                while os.path.exists(os.path.join(export_dir, f"{base}_{i}{ext}")):
                    i += 1
                dest_path = os.path.join(export_dir, f"{base}_{i}{ext}")

            try:
                shutil.copy2(src_path, dest_path)
                success_count += 1
            except Exception as e:
                print(f"エクスポートエラー: {e}")
                error_count += 1

        # 結果表示
        message = f"{success_count}枚の写真をエクスポートしました。"
        if error_count > 0:
            message += f"\n{error_count}枚の写真でエラーが発生しました。"

        QMessageBox.information(self, "エクスポート完了", message)
