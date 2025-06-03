import os
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QEventLoop
from main_window import process_login, show_splash_screen, MainWindow
from styles import StyleManager

def main():
    """アプリケーションのメインエントリーポイント"""
    # リソースディレクトリを確認し、存在しなければ作成
    if not os.path.exists("resources"):
        os.makedirs("resources")

    # fontsディレクトリも確認する
    if not os.path.exists("fonts"):
        os.makedirs("fonts")

    # アプリケーション初期化
    app = QApplication(sys.argv)

    # スタイル適用
    StyleManager.apply_styles(app)

    # スプラッシュスクリーン表示
    splash = show_splash_screen()

    # 少し待機してからログインダイアログを表示 - シグナル/スロットをダイレクト接続に変更
    print("ログインダイアログを表示します...")

    # メインウィンドウ参照を保持するグローバル変数
    global main_window
    main_window = None

    # リトライカウンターを設定
    retry_count = 0
    max_retries = 3

    # ログイン処理を直接呼び出す
    time.sleep(1)  # スプラッシュ画面表示のため少し待機

    while retry_count < max_retries:
        try:
            # ログイン処理を直接呼び出す
            process_login(app, splash)

            # アプリケーションのイベントループを開始
            print("アプリケーションのイベントループを開始します...")

            # メインイベントループ開始
            return_code = app.exec()
            print(f"アプリケーションのイベントループが終了しました: {return_code}")
            sys.exit(return_code)

        except Exception as e:
            retry_count += 1
            print(f"エラーが発生しました（試行 {retry_count}/{max_retries}）: {str(e)}")
            import traceback
            traceback.print_exc()

            if retry_count >= max_retries:
                print("最大リトライ回数に達しました。アプリケーションを終了します。")
                sys.exit(1)

            print(f"{2**retry_count}秒後に再試行します...")
            time.sleep(2**retry_count)  # 指数バックオフで待機時間を増やす

if __name__ == "__main__":
    try:
        # メイン関数実行
        main()
    except Exception as e:
        print(f"アプリケーション実行中に例外が発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
