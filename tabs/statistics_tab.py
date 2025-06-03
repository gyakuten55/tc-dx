from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTabWidget, QGridLayout, QFormLayout, QSpinBox, QLineEdit,
    QDoubleSpinBox, QGroupBox, QFrame, QSplitter, QScrollArea,
    QPushButton, QSizePolicy, QRadioButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import datetime
import mplcursors  # ホバー表示用モジュール

from styles import StyleManager
from components import EnhancedTable

# 年度リスト（2025年から2035年まで）
YEARS = list(range(2025, 2036))

class MatplotlibCanvas(FigureCanvasQTAgg):
    """MatplotlibをQtに統合するためのキャンバスクラス"""
    def __init__(self, figure=None, parent=None, dpi=100):
        if figure is None:
            self.figure = Figure(figsize=(5, 4), dpi=dpi)
            self.figure.patch.set_facecolor('#F5F5F7')  # 背景色
        else:
            self.figure = figure

        super().__init__(self.figure)
        self.setParent(parent)

        # グラフスタイルを設定
        plt.style.use('ggplot')

        # フォントの設定
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Meiryo', 'Yu Gothic', 'Noto Sans CJK JP']


class BarChartWidget(QWidget):
    """サービス別統計の棒グラフを表示するウィジェット"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 年度選択コンボボックス
        self.year_combo = QComboBox()
        StyleManager.style_combo_box(self.year_combo)
        for year in YEARS:
            self.year_combo.addItem(f"{year}年度", year)

        # 現在の年を選択
        current_year = datetime.datetime.now().year
        for i in range(self.year_combo.count()):
            if self.year_combo.itemData(i) == current_year:
                self.year_combo.setCurrentIndex(i)
                break

        # コントロールレイアウト
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("表示年度:"))
        controls_layout.addWidget(self.year_combo)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # グラフキャンバス
        self.canvas = MatplotlibCanvas()
        layout.addWidget(self.canvas)

        # シグナル接続
        self.year_combo.currentIndexChanged.connect(self.update_chart)

        # 初期データでグラフを更新
        self.update_chart()

    def update_chart(self):
        """年度を選択してグラフを更新する"""
        year = self.year_combo.currentData()
        service_stats = self.db.get_service_stats_for_chart(year)

        # グラフをクリア
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        # データの準備
        services = [stat['service_name'] for stat in service_stats]
        amounts = [stat['total_amount'] for stat in service_stats]

        # サービスが0件の場合、空のグラフを表示
        if not services:
            ax.text(0.5, 0.5, 'データがありません', ha='center', va='center', fontsize=12)
            ax.set_axis_off()
            self.canvas.draw()
            return

        # 棒グラフを描画
        bars = ax.bar(services, amounts, color=StyleManager.get_chart_colors(len(services)))

        # グラフのスタイル設定
        ax.set_title(f'{year}年度 サービス別売上', fontsize=14, fontweight='bold')
        ax.set_xlabel('サービス名', fontsize=12)
        ax.set_ylabel('売上金額(円)', fontsize=12)

        # Y軸のフォーマット（通貨表示）
        ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}円'))

        # X軸ラベルを回転して表示
        plt.xticks(rotation=45, ha='right')

        # データラベルを表示
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2, height + 5,
                f'{int(height):,}円', ha='center', va='bottom',
                fontsize=10, rotation=0
            )

        # レイアウトの調整
        self.canvas.figure.tight_layout()

        # グラフを描画
        self.canvas.draw()


class PriceStatsWidget(QWidget):
    """価格統計情報を表示するウィジェット"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 年度選択コンボボックス
        self.year_combo = QComboBox()
        StyleManager.style_combo_box(self.year_combo)
        for year in YEARS:
            self.year_combo.addItem(f"{year}年度", year)

        # 現在の年を選択
        current_year = datetime.datetime.now().year
        for i in range(self.year_combo.count()):
            if self.year_combo.itemData(i) == current_year:
                self.year_combo.setCurrentIndex(i)
                break

        # コントロールレイアウト
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("表示年度:"))
        controls_layout.addWidget(self.year_combo)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # 統計情報表示用のグループボックス
        stats_group = QGroupBox("価格統計")
        stats_layout = QFormLayout(stats_group)

        # 統計値表示用のラベル
        self.average_label = QLabel()
        self.min_label = QLabel()
        self.max_label = QLabel()
        self.total_label = QLabel()
        self.count_label = QLabel()

        # スタイル適用
        for label in [self.average_label, self.min_label, self.max_label,
                      self.total_label, self.count_label]:
            StyleManager.set_value_font(label)

        # フォームに追加
        stats_layout.addRow(QLabel("平均単価:"), self.average_label)
        stats_layout.addRow(QLabel("最小単価:"), self.min_label)
        stats_layout.addRow(QLabel("最大単価:"), self.max_label)
        stats_layout.addRow(QLabel("合計金額:"), self.total_label)
        stats_layout.addRow(QLabel("案件数:"), self.count_label)

        layout.addWidget(stats_group)

        # シグナル接続
        self.year_combo.currentIndexChanged.connect(self.update_stats)

        # スペーサを追加してウィジェットを上部に配置
        layout.addStretch()

        # 初期データで統計情報を更新
        self.update_stats()

    def update_stats(self):
        """年度を選択して統計情報を更新する"""
        year = self.year_combo.currentData()
        stats = self.db.get_price_statistics(year)

        # 金額フォーマット関数
        def format_price(price):
            return f"{int(price):,}円" if price else "0円"

        # 統計情報を表示
        self.average_label.setText(format_price(stats['average_price']))
        self.min_label.setText(format_price(stats['min_price']))
        self.max_label.setText(format_price(stats['max_price']))
        self.total_label.setText(format_price(stats['total_price']))
        self.count_label.setText(f"{stats['total_count']}件")


class TroubleStatsWidget(QWidget):
    """トラブル統計情報を表示するウィジェット"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 年度選択コンボボックス
        self.year_combo = QComboBox()
        StyleManager.style_combo_box(self.year_combo)
        for year in YEARS:
            self.year_combo.addItem(f"{year}年度", year)

        # 現在の年を選択
        current_year = datetime.datetime.now().year
        for i in range(self.year_combo.count()):
            if self.year_combo.itemData(i) == current_year:
                self.year_combo.setCurrentIndex(i)
                break

        # コントロールレイアウト
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("表示年度:"))
        controls_layout.addWidget(self.year_combo)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # タブウィジェット
        self.tabs = QTabWidget()
        StyleManager.style_tabs(self.tabs)

        # 作業員別トラブル率タブ
        self.worker_tab = QWidget()
        worker_layout = QVBoxLayout(self.worker_tab)
        self.worker_table = EnhancedTable(["作業員ID", "作業員名", "トラブル件数", "担当案件数", "トラブル率(%)"])
        self.worker_table.setColumnHidden(0, True)  # ID列を非表示
        self.worker_table.setSortingEnabled(True)  # 並び替え機能を有効化
        worker_layout.addWidget(self.worker_table)

        # 取引先別トラブル率タブ
        self.client_tab = QWidget()
        client_layout = QVBoxLayout(self.client_tab)
        self.client_table = EnhancedTable(["取引先ID", "取引先名", "トラブル件数", "案件数", "トラブル率(%)"])
        self.client_table.setColumnHidden(0, True)  # ID列を非表示
        self.client_table.setSortingEnabled(True)  # 並び替え機能を有効化
        client_layout.addWidget(self.client_table)

        # タブに追加
        self.tabs.addTab(self.worker_tab, "作業員別トラブル率")
        self.tabs.addTab(self.client_tab, "取引先別トラブル率")

        layout.addWidget(self.tabs)

        # シグナル接続
        self.year_combo.currentIndexChanged.connect(self.update_stats)

        # 初期データで統計情報を更新
        self.update_stats()

    def update_stats(self):
        """年度を選択して統計情報を更新する"""
        year = self.year_combo.currentData()

        # 作業員別トラブル統計
        worker_stats = self.db.get_trouble_statistics_by_worker(year)
        worker_data = []
        for stat in worker_stats:
            worker_data.append({
                "作業員ID": stat['worker_id'],
                "作業員名": stat['worker_name'],
                "トラブル件数": stat['trouble_count'],
                "担当案件数": stat['project_count'],
                "トラブル率(%)": f"{stat['trouble_rate']:.2f}"
            })
        self.worker_table.set_data(worker_data)

        # 取引先別トラブル統計
        client_stats = self.db.get_trouble_statistics_by_client(year)
        client_data = []
        for stat in client_stats:
            client_data.append({
                "取引先ID": stat['client_id'],
                "取引先名": stat['client_name'],
                "トラブル件数": stat['trouble_count'],
                "案件数": stat['project_count'],
                "トラブル率(%)": f"{stat['trouble_rate']:.2f}"
            })
        self.client_table.set_data(client_data)


class YearlyComparisonWidget(QWidget):
    """年度間比較グラフを表示するウィジェット"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # コントロールグループ
        controls_layout = QHBoxLayout()

        # 対象年度選択
        current_year_label = QLabel("対象年度:")
        self.current_year_combo = QComboBox()
        StyleManager.style_combo_box(self.current_year_combo)
        for year in YEARS:
            self.current_year_combo.addItem(f"{year}年度", year)

        # 比較年度選択
        compare_year_label = QLabel("比較年度:")
        self.compare_year_combo = QComboBox()
        StyleManager.style_combo_box(self.compare_year_combo)
        for year in YEARS:
            self.compare_year_combo.addItem(f"{year}年度", year)

        # 現在の年と前年を選択
        current_year = datetime.datetime.now().year
        for i in range(self.current_year_combo.count()):
            if self.current_year_combo.itemData(i) == current_year:
                self.current_year_combo.setCurrentIndex(i)
                if i > 0:  # 前年度がある場合に選択
                    self.compare_year_combo.setCurrentIndex(i-1)
                break

        # コントロールをレイアウトに追加
        controls_layout.addWidget(current_year_label)
        controls_layout.addWidget(self.current_year_combo)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(compare_year_label)
        controls_layout.addWidget(self.compare_year_combo)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # グラフキャンバス
        self.canvas = MatplotlibCanvas()
        layout.addWidget(self.canvas)

        # シグナル接続
        self.current_year_combo.currentIndexChanged.connect(self.update_chart)
        self.compare_year_combo.currentIndexChanged.connect(self.update_chart)

        # 初期データでグラフを更新
        self.update_chart()

    def update_chart(self):
        """選択した年度で比較グラフを更新する"""
        current_year = self.current_year_combo.currentData()
        compare_year = self.compare_year_combo.currentData()

        # 年間目標を取得（売上目標設定タブで設定された値のみを使用）
        yearly_target = self.db.get_sales_target(current_year, 0)

        # データ取得
        comparison_data = self.db.get_yearly_comparison_data(current_year, compare_year)

        # グラフをクリア
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        # X軸の月ラベル
        months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        x = np.arange(len(months))

        # 現在年度と比較年度のデータ
        monthly_data_current = comparison_data['current_data']
        monthly_data_compare = comparison_data['compare_data']

        # 累計データの計算
        cumulative_data_current = np.cumsum(monthly_data_current)
        cumulative_data_compare = np.cumsum(monthly_data_compare)

        # 月別目標を取得
        monthly_targets = []
        for month in range(1, 13):
            target = self.db.get_sales_target(current_year, month)
            monthly_targets.append(target)

        # 月別目標が設定されていない場合、年間目標を按分
        if sum(monthly_targets) <= 0:
            monthly_targets = [yearly_target / 12] * 12

        # 月別目標の累積値を計算
        monthly_cumulative_targets = np.cumsum(monthly_targets)

        # データの最大値を取得してY軸の範囲を決定
        max_value = max(
            max(cumulative_data_current) if len(cumulative_data_current) > 0 else 0,
            max(cumulative_data_compare) if len(cumulative_data_compare) > 0 else 0,
            max(monthly_cumulative_targets) if len(monthly_cumulative_targets) > 0 else yearly_target  # 最大の目標値
        )

        # 棒グラフ（月別売上）より薄い色で表示
        bar_width = 0.25  # 棒グラフの幅を小さくして目標バーも表示できるようにする
        bars_current = ax.bar(x - bar_width, monthly_data_current, bar_width,
                    label=f'{current_year}年度 月別', color='#1F77B4', alpha=0.3)
        bars_compare = ax.bar(x, monthly_data_compare, bar_width,
                    label=f'{compare_year}年度 月別', color='#FF7F0E', alpha=0.3)
        # 月別目標を棒グラフで表示
        bars_target = ax.bar(x + bar_width, monthly_targets, bar_width,
                    label=f'月別目標', color='#FF0000', alpha=0.3)

        # 折れ線グラフ（累計売上）より強調して表示
        line_current = ax.plot(x, cumulative_data_current, 'o-', linewidth=2.5,
                     label=f'{current_year}年度 累計', color='#1F77B4')
        line_compare = ax.plot(x, cumulative_data_compare, 'o--', linewidth=2,
                     label=f'{compare_year}年度 累計', color='#FF7F0E')

        # 年間目標ラインを描画（赤色の太い破線）
        target_line = ax.plot(x, monthly_cumulative_targets, '--', linewidth=2.5,
                         label=f'目標累計({int(yearly_target):,}円)', color='red', alpha=0.8)

        # Y軸の範囲を設定（最大値の20%増しで設定）
        ax.set_ylim(0, max_value * 1.2)

        # グラフのスタイル設定
        ax.set_title(f'{current_year}年度 vs {compare_year}年度 売上比較(月別・累計)', fontsize=14, fontweight='bold')
        ax.set_xlabel('月', fontsize=12)
        ax.set_ylabel('売上金額(円)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.grid(True, linestyle='--', alpha=0.7)

        # X軸の範囲を少し広げてラベル用のスペースを確保
        ax.set_xlim(-0.5, 11.5)

        # Y軸のフォーマット（通貨表示）
        ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}円'))

        # 凡例を表示（適切な位置に）
        ax.legend(loc='upper left')

        # 目標達成率の表示
        for i, (target, current) in enumerate(zip(monthly_cumulative_targets, cumulative_data_current)):
            if i == 11:  # 12月（最終月）の場合
                achievement_rate = (current / target * 100) if target > 0 else 0
                ax.annotate(f'達成率 {achievement_rate:.1f}%',
                           xy=(i, current),
                           xytext=(0, 10),
                           textcoords='offset points',
                           ha='center',
                           fontsize=10,
                           color='#1F77B4',
                           fontweight='bold')

        # ホバー時の詳細表示を追加
        # 折れ線グラフ（累計）とバー（月別）の両方にカーソルを追加
        cursor = mplcursors.cursor([line_current[0], line_compare[0], bars_current, bars_compare, bars_target], hover=True)

        @cursor.connect("add")
        def on_hover(sel):
            # インデックスの取得方法を修正
            try:
                # グラフの種類によって異なる方法でインデックスを取得
                index = 0  # デフォルト値

                # まず、sel.targetのオブジェクトタイプに基づいて処理
                if hasattr(sel, 'index'):
                    # 直接インデックスプロパティがある場合
                    index = sel.index
                elif hasattr(sel.target, 'get_offsets'):
                    # OffsetCollectionの場合
                    offsets = sel.target.get_offsets()
                    if len(offsets) > 0 and sel.index < len(offsets):
                        index = int(offsets[sel.index][0])
                elif hasattr(sel, 'target') and hasattr(sel.target, 'get_xdata'):
                    # Lineの場合
                    xdata = sel.target.get_xdata()
                    if len(xdata) > 0 and hasattr(sel, 'index') and sel.index < len(xdata):
                        index = int(xdata[sel.index])
                elif hasattr(sel, 'point_index'):
                    # point_indexプロパティがある場合
                    index = sel.point_index
                elif hasattr(sel, 'dataIdx'):
                    # dataIdxプロパティがある場合
                    index = sel.dataIdx
                else:
                    # どの方法でもインデックスが取得できない場合、
                    # インデックス0（最初の要素）をデフォルトとして使用
                    index = 0

                # インデックスの範囲を確認し、有効な範囲に収める
                index = min(max(int(index), 0), len(months) - 1)

                month = months[index]

                if sel.artist == line_current[0]:
                    # 現在年度の累計売上
                    month_value = monthly_data_current[index]
                    cumulative_value = cumulative_data_current[index]
                    target_value = monthly_cumulative_targets[index]
                    achievement_rate = (cumulative_value / target_value * 100) if target_value > 0 else 0

                    sel.annotation.set_text(
                        f"{month} ({current_year}年度)\n"
                        f"月別売上: {int(month_value):,}円\n"
                        f"累計売上: {int(cumulative_value):,}円\n"
                        f"目標累計: {int(target_value):,}円\n"
                        f"達成率: {achievement_rate:.1f}%"
                    )
                elif sel.artist == line_compare[0]:
                    # 比較年度の累計売上
                    month_value = monthly_data_compare[index]
                    cumulative_value = cumulative_data_compare[index]

                    sel.annotation.set_text(
                        f"{month} ({compare_year}年度)\n"
                        f"月別売上: {int(month_value):,}円\n"
                        f"累計売上: {int(cumulative_value):,}円"
                    )
                elif sel.artist in bars_current:
                    # 現在年度の月別売上（バーグラフ）
                    month_value = monthly_data_current[index]
                    cumulative_value = cumulative_data_current[index]

                    sel.annotation.set_text(
                        f"{month} ({current_year}年度)\n"
                        f"月別売上: {int(month_value):,}円\n"
                        f"累計売上: {int(cumulative_value):,}円"
                    )
                elif sel.artist in bars_compare:
                    # 比較年度の月別売上（バーグラフ）
                    month_value = monthly_data_compare[index]
                    cumulative_value = cumulative_data_compare[index]

                    sel.annotation.set_text(
                        f"{month} ({compare_year}年度)\n"
                        f"月別売上: {int(month_value):,}円\n"
                        f"累計売上: {int(cumulative_value):,}円"
                    )
                elif sel.artist in bars_target:
                    # 月別目標（バーグラフ）
                    target = monthly_targets[index]
                    cumulative_target = monthly_cumulative_targets[index]

                    sel.annotation.set_text(
                        f"{month} (目標)\n"
                        f"月別目標: {int(target):,}円\n"
                        f"累計目標: {int(cumulative_target):,}円"
                    )
            except Exception as e:
                # エラーが発生した場合、簡単なメッセージを表示
                print(f"ホバー表示エラー: {e}")
                sel.annotation.set_text(f"データ表示エラー")

        # レイアウトの調整
        self.canvas.figure.tight_layout()

        # グラフを描画
        self.canvas.draw()


class SalesTargetWidget(QWidget):
    """売上目標設定ウィジェット"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 年度選択コンボボックス
        self.year_combo = QComboBox()
        StyleManager.style_combo_box(self.year_combo)
        for year in YEARS:
            self.year_combo.addItem(f"{year}年度", year)

        # 現在の年を選択
        current_year = datetime.datetime.now().year
        for i in range(self.year_combo.count()):
            if self.year_combo.itemData(i) == current_year:
                self.year_combo.setCurrentIndex(i)
                break

        # コントロールレイアウト
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("表示年度:"))
        controls_layout.addWidget(self.year_combo)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # 年間目標設定グループ
        annual_group = QGroupBox("年間売上目標")
        annual_layout = QFormLayout(annual_group)

        self.annual_target_input = QDoubleSpinBox()
        self.annual_target_input.setRange(0, 9999999999)
        self.annual_target_input.setSingleStep(1000000)
        self.annual_target_input.setSuffix("円")
        self.annual_target_input.setGroupSeparatorShown(True)
        self.annual_target_input.setValue(0)
        StyleManager.style_input(self.annual_target_input)

        annual_layout.addRow("年間目標金額:", self.annual_target_input)

        # 年間目標保存ボタン
        self.save_annual_button = QPushButton("年間目標を保存")
        StyleManager.style_button(self.save_annual_button)
        self.save_annual_button.clicked.connect(self.save_annual_target)
        annual_layout.addRow("", self.save_annual_button)

        layout.addWidget(annual_group)

        # 月別目標設定グループ
        monthly_group = QGroupBox("月別売上目標")
        monthly_layout = QVBoxLayout(monthly_group)

        # 月別目標テーブル
        self.monthly_table = QTableWidget(12, 2)
        self.monthly_table.setHorizontalHeaderLabels(["月", "目標金額(円)"])
        self.monthly_table.verticalHeader().setVisible(False)
        self.monthly_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.monthly_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.monthly_table.setColumnWidth(0, 80)

        # 各月の行を設定
        for row in range(12):
            month_item = QTableWidgetItem(f"{row+1}月")
            month_item.setFlags(month_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.monthly_table.setItem(row, 0, month_item)

            # 金額入力用のDoubleSpinBoxをセルに埋め込む
            target_spinbox = QDoubleSpinBox()
            target_spinbox.setRange(0, 9999999999)
            target_spinbox.setSingleStep(100000)
            target_spinbox.setSuffix("円")
            target_spinbox.setGroupSeparatorShown(True)
            target_spinbox.setValue(0)
            StyleManager.style_input(target_spinbox)
            self.monthly_table.setCellWidget(row, 1, target_spinbox)

        monthly_layout.addWidget(self.monthly_table)

        # 月別目標保存ボタン
        self.save_monthly_button = QPushButton("月別目標を保存")
        StyleManager.style_button(self.save_monthly_button)
        self.save_monthly_button.clicked.connect(self.save_monthly_targets)
        monthly_layout.addWidget(self.save_monthly_button)

        layout.addWidget(monthly_group)

        # シグナル接続
        self.year_combo.currentIndexChanged.connect(self.load_targets)

        # 初期データでターゲットを読み込む
        self.load_targets()

    def load_targets(self):
        """選択した年度の売上目標を読み込む"""
        year = self.year_combo.currentData()

        # 全ての目標を取得
        targets = self.db.get_all_sales_targets(year)

        # 年間目標を設定
        self.annual_target_input.setValue(targets.get(0, 0))

        # 月別目標を設定
        for row in range(12):
            month = row + 1
            target_spinbox = self.monthly_table.cellWidget(row, 1)
            if target_spinbox:
                target_spinbox.setValue(targets.get(month, 0))

    def save_annual_target(self):
        """年間売上目標を保存する"""
        year = self.year_combo.currentData()
        target_amount = self.annual_target_input.value()

        success = self.db.set_sales_target(year, 0, target_amount)
        if success:
            QMessageBox.information(self, "保存完了", f"{year}年度の年間売上目標を保存しました。")
        else:
            QMessageBox.warning(self, "保存エラー", "年間売上目標の保存に失敗しました。")

    def save_monthly_targets(self):
        """月別売上目標を保存する"""
        year = self.year_combo.currentData()
        error_months = []

        # 各月の目標を保存
        for row in range(12):
            month = row + 1
            target_spinbox = self.monthly_table.cellWidget(row, 1)
            if target_spinbox:
                target_amount = target_spinbox.value()
                success = self.db.set_sales_target(year, month, target_amount)
                if not success:
                    error_months.append(str(month))

        if error_months:
            QMessageBox.warning(
                self,
                "保存エラー",
                f"以下の月の売上目標保存に失敗しました: {', '.join(error_months)}"
            )
        else:
            QMessageBox.information(self, "保存完了", f"{year}年度の月別売上目標を保存しました。")


class StatisticsTab(QWidget):
    """統計情報タブ"""

    def __init__(self, db):
        super().__init__()

        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップする"""
        layout = QVBoxLayout()

        # ヘッダー部分
        header_label = QLabel("統計情報")
        StyleManager.set_header_font(header_label)
        layout.addWidget(header_label)

        # 統計情報タブ
        stats_tabs = QTabWidget()
        StyleManager.style_tabs(stats_tabs)

        # 売上目標設定タブ
        sales_target_widget = SalesTargetWidget(self.db)
        stats_tabs.addTab(sales_target_widget, "売上目標設定")

        # 前年度比較タブ
        yearly_comparison_widget = YearlyComparisonWidget(self.db)
        stats_tabs.addTab(yearly_comparison_widget, "前年度比較")

        # トラブル統計タブ
        trouble_stat_widget = TroubleStatsWidget(self.db)
        stats_tabs.addTab(trouble_stat_widget, "トラブル統計")

        # 価格統計タブ
        price_stat_widget = PriceStatsWidget(self.db)
        stats_tabs.addTab(price_stat_widget, "価格統計")

        # サービス別売上グラフタブ
        service_stat_widget = BarChartWidget(self.db)
        stats_tabs.addTab(service_stat_widget, "サービス別売上")

        layout.addWidget(stats_tabs)

        self.setLayout(layout)

        # インスタンス変数として統計ウィジェットを保存
        self.sales_target_widget = sales_target_widget
        self.yearly_comparison_widget = yearly_comparison_widget
        self.trouble_stat_widget = trouble_stat_widget
        self.price_stat_widget = price_stat_widget
        self.service_stat_widget = service_stat_widget
        self.stats_tabs = stats_tabs

    def update_all_stats(self):
        """全ての統計情報ウィジェットを更新する"""
        # 各統計ウィジェットの更新メソッドを呼び出し
        if hasattr(self, 'sales_target_widget'):
            self.sales_target_widget.load_targets()

        if hasattr(self, 'yearly_comparison_widget'):
            self.yearly_comparison_widget.update_chart()

        if hasattr(self, 'trouble_stat_widget'):
            self.trouble_stat_widget.update_stats()

        if hasattr(self, 'price_stat_widget'):
            self.price_stat_widget.update_stats()

        if hasattr(self, 'service_stat_widget'):
            self.service_stat_widget.update_chart()

        # 現在選択されているタブのインデックスを取得して同じタブに戻す
        current_index = self.stats_tabs.currentIndex()
        self.stats_tabs.setCurrentIndex(current_index)
