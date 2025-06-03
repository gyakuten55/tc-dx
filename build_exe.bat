@echo off
echo ===================================
echo = 株式会社ティーシー業務管理システム =
echo = EXEファイルビルドスクリプト       =
echo ===================================

echo.
echo リソースディレクトリの確認...
if not exist resources mkdir resources

echo.
echo 必要なパッケージのインストール確認...
pip install -r requirements.txt

echo.
echo PyInstallerを使用してEXEファイルをビルド...
pyinstaller --name "TC業務管理システム" --onefile --windowed --icon=resources/icon.ico main.py

echo.
echo ビルドが完了しました。
echo EXEファイルは dist フォルダ内に作成されています。
echo.

pause 