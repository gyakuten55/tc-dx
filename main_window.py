import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QMessageBox, QSplashScreen, QProgressBar
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, QEventLoop

from models import Database
from styles import StyleManager
from tabs.clients_tab import ClientsTab
from tabs.workers_tab import WorkersTab
from tabs.services_tab import ServicesTab
from tabs.projects_tab import ProjectsTab
from tabs.work_orders_tab import WorkOrdersTab
from tabs.statistics_tab import StatisticsTab

# グローバル変数でウィンドウ参照を保持
main_window = None

class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウクラス"""

    def __init__(self, user_info=None):
        super().__init__()

        # ユーザー情報を保存
        self.user_info = user_info or {"user_id": "unknown", "user_level": "user"}

        # データベース初期化
        self.db = Database()

        # UIセットアップ
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        self.setWindowTitle("株式会社ティーシー 業務管理システム")
        self.setWindowIcon(QIcon("resources/icon.png"))
        self.setMinimumSize(1200, 800)

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # ヘッダー部分
        header_layout = QHBoxLayout()

        # ロゴとタイトル
        logo_label = QLabel()
        logo_pixmap = QPixmap("resources/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))

        title_label = QLabel("業務管理システム")
        StyleManager.set_title_font(title_label)

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # ログインユーザー情報
        user_layout = QVBoxLayout()
        user_label = QLabel(f"ユーザー: {self.user_info['user_id']}")
        user_label.setFont(StyleManager.SMALL_FONT)
        user_layout.addWidget(user_label)

        # 管理者表示（管理者の場合のみ）
        if self.user_info['user_level'] == 'admin':
            level_label = QLabel("権限: 管理者")
            level_label.setFont(StyleManager.SMALL_FONT)
            level_label.setStyleSheet("color: #FF5722;")  # オレンジ色で管理者表示
            user_layout.addWidget(level_label)

        header_layout.addLayout(user_layout)

        # バージョン情報
        version_label = QLabel("Ver 1.0.0")
        version_label.setFont(StyleManager.SMALL_FONT)
        version_label.setStyleSheet(f"color: {StyleManager.LIGHT_TEXT_COLOR};")
        header_layout.addWidget(version_label)

        main_layout.addLayout(header_layout)

        # タブウィジェット
        self.tab_widget = QTabWidget()
        StyleManager.style_tabs(self.tab_widget)

        # 各タブの作成
        self.clients_tab = ClientsTab(self.db)
        self.workers_tab = WorkersTab(self.db)
        self.services_tab = ServicesTab(self.db)
        self.projects_tab = ProjectsTab(self.db)
        self.work_orders_tab = WorkOrdersTab(self.db)

        # タブの追加
        self.tab_widget.addTab(self.projects_tab, "案件管理")

        # 管理者のみがアクセスできるタブを設定
        if self.user_info['user_level'] == 'admin':
            self.tab_widget.addTab(self.clients_tab, "取引先マスター")
            self.tab_widget.addTab(self.workers_tab, "作業員マスター")
            self.tab_widget.addTab(self.services_tab, "サービスマスター")
            self.tab_widget.addTab(self.work_orders_tab, "業務指示書")

            # 統計情報タブ
            self.statistics_tab = StatisticsTab(self.db)
            self.tab_widget.addTab(self.statistics_tab, "統計情報")

            # プロジェクトデータ変更時に統計情報タブを更新するシグナル接続
            self.projects_tab.projectsChanged.connect(self.update_statistics)
        else:
            # 一般ユーザーの場合は業務指示書タブのみ追加
            self.tab_widget.addTab(self.work_orders_tab, "業務指示書")

        main_layout.addWidget(self.tab_widget)

        # フッター部分
        footer_layout = QHBoxLayout()

        # ステータスラベル
        self.status_label = QLabel("準備完了")
        self.status_label.setFont(StyleManager.SMALL_FONT)

        # 著作権表示
        copyright_label = QLabel("© 2025 株式会社ティーシー")
        copyright_label.setFont(StyleManager.SMALL_FONT)
        copyright_label.setStyleSheet(f"color: {StyleManager.LIGHT_TEXT_COLOR};")

        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(copyright_label)

        main_layout.addLayout(footer_layout)

        # メインウィジェットを設定
        self.setCentralWidget(main_widget)

    def closeEvent(self, event):
        """アプリケーション終了時の処理"""
        reply = QMessageBox.question(
            self,
            '確認',
            "アプリケーションを終了してもよろしいですか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # データベース接続を閉じる
            self.db.close()
            event.accept()
        else:
            event.ignore()

    def update_statistics(self):
        """統計情報タブのデータを更新する"""
        if hasattr(self, 'statistics_tab'):
            # 現在表示されているタブのデータを更新
            if hasattr(self.statistics_tab, 'update_all_stats'):
                self.statistics_tab.update_all_stats()

            # 現在の選択タブが統計タブの場合は画面を更新
            if self.tab_widget.currentWidget() == self.statistics_tab:
                self.status_label.setText("統計情報を更新しました")


def show_splash_screen():
    """スプラッシュスクリーンを表示する"""
    splash_pix = QPixmap("resources/splash.png")
    if splash_pix.isNull():
        # スプラッシュ画像がない場合は、テキストのみのスプラッシュスクリーンを作成
        splash_pix = QPixmap(600, 400)
        splash_pix.fill(Qt.GlobalColor.white)

    splash = QSplashScreen(splash_pix)

    # より見やすいフォントと色の設定
    font = QFont("Yu Gothic UI", 10)
    font.setBold(True)
    splash.setFont(font)

    # スプラッシュ画面に初期テキストを追加
    splash.showMessage(
        "株式会社ティーシー 業務管理システム 起動中...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white
    )

    splash.show()

    # 進行状況を更新する関数
    def update_splash_message(message):
        splash.showMessage(
            message,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.white
        )
        # メッセージ更新後にイベントを処理して表示を確実に更新
        QApplication.processEvents()

    # 少し待機して初期化ステップを表示
    timer = QTimer()
    timer.singleShot(300, lambda: update_splash_message("データベース初期化中..."))
    timer.singleShot(600, lambda: update_splash_message("モジュール読み込み中..."))
    timer.singleShot(900, lambda: update_splash_message("インターフェース準備中..."))

    return splash


def main():
    """アプリケーションのメインエントリーポイント"""
    # リソースディレクトリを確認し、存在しなければ作成
    if not os.path.exists("resources"):
        os.makedirs("resources")

    # アプリケーション初期化
    app = QApplication(sys.argv)

    # スタイル適用
    StyleManager.apply_styles(app)

    # スプラッシュスクリーン表示
    splash = show_splash_screen()

    # 少し待機してからログインダイアログを表示
    QTimer.singleShot(1000, lambda: process_login(app, splash))

    sys.exit(app.exec())


def process_login(app, splash):
    """ログイン処理を行う"""
    from dialogs.login_dialog import LoginDialog
    from PyQt6.QtWidgets import QDialog

    print("===== ログイン処理を開始します =====")

    # Database初期化
    db = Database()

    # グローバル変数でウィンドウ参照を保持（ガベージコレクションされないように）
    global main_window

    # ログインループ（ログイン成功または明示的にキャンセルされるまで繰り返す）
    while True:
        # ログインダイアログ表示
        login_dialog = LoginDialog(db)
        splash.finish(login_dialog)

        # ダイアログの結果に応じて処理
        result = login_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # ログイン成功時、ユーザー情報を取得
            user_info = login_dialog.get_user_info()
            print(f"ログイン成功: ユーザー情報取得 - {user_info}")

            # メインウィンドウ初期化（ユーザー情報を渡す）
            print("メインウィンドウを初期化します...")
            try:
                main_window = MainWindow(user_info)
                print("メインウィンドウの表示を試みます...")
                main_window.setWindowTitle(f"株式会社ティーシー 業務管理システム - ユーザー: {user_info['user_id']}")
                main_window.show()
                print("メインウィンドウの表示に成功しました")

                # ウィンドウがアクティブになることを確認
                main_window.activateWindow()
                main_window.raise_()

                # イベントループを一時的に処理して表示を確実にする
                app.processEvents()

                return  # ループを終了
            except Exception as e:
                print(f"メインウィンドウの初期化中にエラーが発生しました: {str(e)}")
                import traceback
                traceback.print_exc()
                # エラーメッセージを表示
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    None,
                    "エラー",
                    f"アプリケーションの起動中にエラーが発生しました: {str(e)}"
                )
                return  # エラー時もループを終了
        else:
            # ログインキャンセル時は確認メッセージを表示
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                None,
                "終了確認",
                "アプリケーションを終了しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 終了を選択した場合はアプリケーションを終了
                print("ユーザーによる終了が選択されました")
                app.quit()
                return  # ループを終了
            # Noの場合はループが継続し、ログインダイアログが再表示される


if __name__ == "__main__":
    main()
