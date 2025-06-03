from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from styles import StyleManager

class LoginDialog(QDialog):
    """ログインダイアログ"""

    def __init__(self, db, parent=None):
        super().__init__(parent)

        self.db = db
        self.user_id = None
        self.user_level = None

        self.setWindowTitle("ログイン")
        self.setWindowIcon(QIcon("resources/icon.png"))
        self.setFixedSize(450, 500)  # 高さを増加
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # ロゴ部分
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel()
        logo_pixmap = QPixmap("resources/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(100, 60, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            placeholder = QLabel("TC")
            placeholder.setStyleSheet("font-size: 36px; color: red; font-weight: bold;")
            logo_layout.addWidget(placeholder)

        logo_layout.addWidget(logo_label)
        layout.addLayout(logo_layout)

        # タイトル
        title_label = QLabel("株式会社ティーシー 業務管理システム")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title_label)

        # 説明
        desc_label = QLabel("ユーザーIDとパスワードを入力してください")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        # スペースを取るためのストレッチを追加
        layout.addStretch(1)

        # 入力フォームエリア - FormLayoutを使用する
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 5, 0, 5)
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # ユーザーID入力
        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("例: 0001")
        self.user_id_input.setMinimumHeight(30)
        self.user_id_input.setMinimumWidth(250)
        StyleManager.style_input(self.user_id_input)
        form_layout.addRow("ユーザーID:", self.user_id_input)

        # パスワード入力
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(30)
        self.password_input.setMinimumWidth(250)
        StyleManager.style_input(self.password_input)
        form_layout.addRow("パスワード:", self.password_input)

        form_container = QWidget()
        form_container.setLayout(form_layout)
        layout.addWidget(form_container)

        # スペースを取るためのストレッチを追加
        layout.addStretch(2)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.login_button = QPushButton("ログイン")
        self.login_button.setMinimumWidth(120)
        self.login_button.setMinimumHeight(35)
        StyleManager.style_button(self.login_button, "primary")
        # 明示的にログインボタンのシグナルをクリアして再接続
        self.login_button.clicked.disconnect() if hasattr(self.login_button, "clicked") and self.login_button.receivers(self.login_button.clicked) > 0 else None
        self.login_button.clicked.connect(self.login)

        self.exit_button = QPushButton("終了")
        self.exit_button.setMinimumWidth(120)
        self.exit_button.setMinimumHeight(35)
        StyleManager.style_button(self.exit_button, "flat")
        self.exit_button.clicked.disconnect() if hasattr(self.exit_button, "clicked") and self.exit_button.receivers(self.exit_button.clicked) > 0 else None
        self.exit_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.exit_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # バージョン表示
        version_label = QLabel("Ver 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setFont(StyleManager.SMALL_FONT)
        layout.addWidget(version_label)

        self.setLayout(layout)

        # Enterキーでログイン
        self.password_input.returnPressed.connect(self.login)

    def login(self):
        """ログイン処理"""
        try:
            # ユーザー入力を取得
            user_id = self.user_id_input.text().strip()
            password = self.password_input.text().strip()

            print(f"ログイン試行: ID='{user_id}', PWD='{password}'")

            # バックアップログイン - メンテナンス用
            if user_id == "admin" and password == "tcadmin":
                print("バックアップ管理者アカウントでログイン")
                self.user_id = "0001"  # 管理者IDに置き換え
                self.user_level = "admin"
                self.accept()
                return

            # 入力チェック
            if not user_id:
                QMessageBox.warning(self, "エラー", "ユーザーIDを入力してください。")
                self.user_id_input.setFocus()
                return

            if not password:
                QMessageBox.warning(self, "エラー", "パスワードを入力してください。")
                self.password_input.setFocus()
                return

            # データベース接続確認
            if not self.db or not hasattr(self.db, 'verify_password'):
                QMessageBox.critical(self, "エラー", "データベース接続が確立されていません。")
                return

            # 認証処理
            try:
                is_valid = self.db.verify_password(user_id, password)
                print(f"認証結果: {is_valid}")
            except Exception as e:
                print(f"認証処理中にエラー発生: {str(e)}")
                QMessageBox.critical(self, "エラー", f"認証処理中にエラーが発生しました: {str(e)}")
                return

            # 認証結果に応じた処理
            if is_valid:
                self.user_id = user_id

                # データベースから権限レベルを取得
                try:
                    self.user_level = self.db.get_user_level(user_id)
                    print(f"ユーザーレベル: {self.user_level}")
                except Exception as e:
                    print(f"権限レベル取得エラー: {str(e)}")
                    self.user_level = "user"  # エラー時のデフォルト値

                print(f"ログイン成功: ID={self.user_id}, Level={self.user_level}")
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "認証エラー",
                    "ユーザーIDまたはパスワードが正しくありません。"
                )
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            print(f"ログイン処理の例外: {str(e)}")
            QMessageBox.critical(self, "エラー", f"ログイン処理中にエラーが発生しました: {str(e)}")

    def get_user_info(self):
        """ユーザー情報を取得する"""
        return {
            "user_id": self.user_id,
            "user_level": self.user_level
        }
