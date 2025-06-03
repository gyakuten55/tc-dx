from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QDateEdit, QTextEdit, QGroupBox,
    QComboBox, QSpinBox, QFileDialog, QCheckBox, QTabWidget,
    QMessageBox, QDialogButtonBox, QWidget, QGridLayout, QRadioButton, QButtonGroup,
    QTimeEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
import os
import sys
import datetime
import tempfile
import webbrowser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.platypus.tables import TableStyle
from reportlab.platypus import Table
from reportlab.lib import colors

# 循環インポートを避けるため、型チェック用の文字列を定義
WORK_ORDERS_TAB_CLASS = 'WorkOrdersTab'

class WorkOrderDialog(QDialog):
    """業務指示書ダイアログ"""

    def __init__(self, db, project_data=None, parent=None, order_data=None):
        super().__init__(parent)
        self.db = db
        self.project_data = project_data
        self.order_data = order_data
        self.setWindowTitle("業務指示書")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)

        # 保存完了フラグ
        self.saved = False

        # 従業員リストを取得
        self.workers = self.db.get_workers()

        self.setup_ui()

        # プロジェクトデータが提供された場合はそのデータを設定
        if project_data:
            self.populate_data()

        # 業務指示書データが提供された場合はそのデータを設定
        if order_data:
            self.populate_order_data()

    def setup_ui(self):
        """UIをセットアップする"""
        main_layout = QVBoxLayout(self)

        # タブウィジェットを作成
        tab_widget = QTabWidget()

        # 基本情報タブ
        basic_info_tab = QWidget()
        basic_layout = QVBoxLayout(basic_info_tab)

        # フォームレイアウト（基本情報）
        basic_form_layout = QFormLayout()
        basic_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        basic_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # 作成日
        self.creation_date_edit = QDateEdit()
        self.creation_date_edit.setDate(QDate.currentDate())
        self.creation_date_edit.setCalendarPopup(True)
        basic_form_layout.addRow("作成日:", self.creation_date_edit)

        # 作業性
        self.work_type_edit = QLineEdit()
        self.work_type_edit.setText("通常")
        basic_form_layout.addRow("作業性:", self.work_type_edit)

        # 担当者（従業員選択式）
        self.manager_combo = QComboBox()
        for worker in self.workers:
            self.manager_combo.addItem(worker['name'], worker['id'])
        basic_form_layout.addRow("担当:", self.manager_combo)

        # 作成者（従業員選択式）- 新規追加
        self.creator_combo = QComboBox()
        for worker in self.workers:
            self.creator_combo.addItem(worker['name'], worker['id'])
        basic_form_layout.addRow("作成者:", self.creator_combo)

        # 現場名
        self.site_name_edit = QLineEdit()
        self.site_name_edit.setMaxLength(50)  # 文字数制限を追加
        basic_form_layout.addRow("現場名:", self.site_name_edit)

        # 現場住所
        self.site_address_edit = QLineEdit()
        self.site_address_edit.setMaxLength(50)  # 文字数制限を追加
        basic_form_layout.addRow("現場住所:", self.site_address_edit)

        # 管理室と勤務（グループ化）
        management_group = QGroupBox("管理室・勤務")
        management_layout = QFormLayout(management_group)

        self.management_tel_edit = QLineEdit()
        self.management_tel_edit.setMaxLength(20)  # 文字数制限を追加
        self.management_tel_edit.setPlaceholderText("TEL")
        management_layout.addRow("管理室:", self.management_tel_edit)

        # 勤務（フリー入力）
        self.duty_edit = QTextEdit()
        self.duty_edit.setPlaceholderText("勤務内容を入力")
        # TextEditには直接maxLengthがないので、textChanged信号で文字数を監視します
        self.duty_edit.textChanged.connect(lambda: self.limit_text_length(self.duty_edit, 150))
        management_layout.addRow("勤務:", self.duty_edit)

        # 作業日
        date_group = QGroupBox("作業期間")
        date_layout = QGridLayout(date_group)

        date_layout.addWidget(QLabel("開始日:"), 0, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.start_date_edit, 0, 1)

        date_layout.addWidget(QLabel("終了日:"), 0, 2)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.end_date_edit, 0, 3)

        # 作業日数表示
        self.work_days_label = QLabel("作業日数: 0日間")
        date_layout.addWidget(self.work_days_label, 1, 0, 1, 4)

        # 日付が変更されたときに作業日数を計算
        self.start_date_edit.dateChanged.connect(self.calculate_work_days)
        self.end_date_edit.dateChanged.connect(self.calculate_work_days)

        # 作業時間
        time_group = QGroupBox("作業時間")
        time_layout = QGridLayout(time_group)
        time_layout.setVerticalSpacing(10)  # 垂直方向の間隔を追加
        time_layout.setHorizontalSpacing(10)  # 水平方向の間隔を追加

        # ラベルを太字にして目立たせる
        current_label = QLabel("現着:")
        current_label.setStyleSheet("font-weight: bold;")
        time_layout.addWidget(current_label, 0, 0)

        self.arrival_time_edit = QTimeEdit()
        self.arrival_time_edit.setDisplayFormat("HH:mm")
        self.arrival_time_edit.setTime(QTime(9, 0))
        self.arrival_time_edit.setMaximumWidth(100)
        time_layout.addWidget(self.arrival_time_edit, 0, 1)

        # 予定の開始・終了時間を１行に配置
        plan_label = QLabel("予定:")
        plan_label.setStyleSheet("font-weight: bold;")
        time_layout.addWidget(plan_label, 0, 2)

        self.scheduled_start_edit = QTimeEdit()
        self.scheduled_start_edit.setDisplayFormat("HH:mm")
        self.scheduled_start_edit.setTime(QTime(9, 0))
        self.scheduled_start_edit.setMaximumWidth(100)
        time_layout.addWidget(self.scheduled_start_edit, 0, 3)

        time_layout.addWidget(QLabel("〜"), 0, 4, Qt.AlignmentFlag.AlignCenter)

        self.scheduled_end_edit = QTimeEdit()
        self.scheduled_end_edit.setDisplayFormat("HH:mm")
        self.scheduled_end_edit.setTime(QTime(17, 0))
        self.scheduled_end_edit.setMaximumWidth(100)
        time_layout.addWidget(self.scheduled_end_edit, 0, 5)

        # 実働の開始・終了時間を１行に配置
        actual_label = QLabel("実働:")
        actual_label.setStyleSheet("font-weight: bold;")
        time_layout.addWidget(actual_label, 1, 0)

        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(9, 0))
        self.start_time_edit.setMaximumWidth(100)
        time_layout.addWidget(self.start_time_edit, 1, 1)

        time_layout.addWidget(QLabel("〜"), 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(17, 0))
        self.end_time_edit.setMaximumWidth(100)
        time_layout.addWidget(self.end_time_edit, 1, 3)

        # グリッドレイアウトの残りの列を調整
        time_layout.setColumnStretch(6, 1)  # 最後の列を伸縮させる

        # 基本情報タブのレイアウトに追加
        basic_layout.addLayout(basic_form_layout)
        basic_layout.addWidget(management_group)
        basic_layout.addWidget(date_group)
        basic_layout.addWidget(time_group)
        basic_layout.addStretch()

        # 作業内容タブ
        work_info_tab = QWidget()
        work_layout = QVBoxLayout(work_info_tab)

        # 作業内容グループ
        work_content_group = QGroupBox("作業内容")
        work_content_layout = QHBoxLayout(work_content_group)

        self.drainage_checkbox = QCheckBox("排水")
        work_content_layout.addWidget(self.drainage_checkbox)

        self.water_storage_checkbox = QCheckBox("貯水")
        work_content_layout.addWidget(self.water_storage_checkbox)

        self.construction_checkbox = QCheckBox("工事/その他")
        work_content_layout.addWidget(self.construction_checkbox)
        work_content_layout.addStretch()

        # 元請情報グループ
        contractor_group = QGroupBox("元請情報")
        contractor_layout = QFormLayout(contractor_group)

        self.contractor_company_edit = QLineEdit()
        contractor_layout.addRow("元請会社:", self.contractor_company_edit)

        self.contractor_manager_edit = QLineEdit()
        contractor_layout.addRow("元請担当者:", self.contractor_manager_edit)

        contact_layout = QHBoxLayout()
        self.contact_number_edit = QLineEdit()
        self.contact_number_edit.setMaximumWidth(100)
        contact_layout.addWidget(self.contact_number_edit)
        contact_layout.addStretch()
        contractor_layout.addRow("連絡先:", contact_layout)

        # 看板社名
        self.signboard_name_edit = QLineEdit()
        contractor_layout.addRow("看板社名:", self.signboard_name_edit)

        # 連絡先グループ
        contact_group = QGroupBox("連絡先情報")
        contact_form = QFormLayout(contact_group)

        # 現着連絡
        arrival_layout = QHBoxLayout()

        self.arrival_number_edit = QLineEdit()
        self.arrival_number_edit.setMaximumWidth(80)
        arrival_layout.addWidget(self.arrival_number_edit)

        arrival_layout.addWidget(QLabel("担当:"))
        self.arrival_manager_edit = QLineEdit()
        self.arrival_manager_edit.setMaximumWidth(80)
        arrival_layout.addWidget(self.arrival_manager_edit)

        arrival_layout.addWidget(QLabel("連絡先:"))
        self.arrival_contact_edit = QLineEdit()
        self.arrival_contact_edit.setMaximumWidth(80)
        arrival_layout.addWidget(self.arrival_contact_edit)
        arrival_layout.addStretch()

        contact_form.addRow("現着連絡:", arrival_layout)

        # 終了連絡
        completion_layout = QHBoxLayout()

        self.completion_number_edit = QLineEdit()
        self.completion_number_edit.setMaximumWidth(80)
        completion_layout.addWidget(self.completion_number_edit)

        completion_layout.addWidget(QLabel("担当:"))
        self.completion_manager_edit = QLineEdit()
        self.completion_manager_edit.setMaximumWidth(80)
        completion_layout.addWidget(self.completion_manager_edit)

        completion_layout.addWidget(QLabel("連絡先:"))
        self.completion_contact_edit = QLineEdit()
        self.completion_contact_edit.setMaximumWidth(80)
        completion_layout.addWidget(self.completion_contact_edit)
        completion_layout.addStretch()

        contact_form.addRow("終了連絡:", completion_layout)

        # 作業詳細
        details_group = QGroupBox("作業詳細")
        details_layout = QVBoxLayout(details_group)

        self.work_details_edit = QTextEdit()
        self.work_details_edit.setPlaceholderText("作業の詳細な内容を入力してください")
        # 作業詳細にも文字数制限を設定
        self.work_details_edit.textChanged.connect(lambda: self.limit_text_length(self.work_details_edit, 300))
        details_layout.addWidget(self.work_details_edit)

        # 作業内容タブのレイアウトに追加
        work_layout.addWidget(work_content_group)
        work_layout.addWidget(contractor_group)
        work_layout.addWidget(contact_group)
        work_layout.addWidget(details_group)

        # 備考タブ
        remarks_tab = QWidget()
        remarks_layout = QVBoxLayout(remarks_tab)

        # その他の注意事項
        other_group = QGroupBox("その他注意事項")
        other_layout = QHBoxLayout(other_group)

        self.business_card_check = QCheckBox("業者証")
        other_layout.addWidget(self.business_card_check)

        self.vest_check = QCheckBox("ベスト")
        other_layout.addWidget(self.vest_check)

        other_layout.addStretch()

        # 写真撮影・報告書
        photo_group = QGroupBox("写真撮影・報告書")
        photo_layout = QGridLayout(photo_group)

        photo_layout.addWidget(QLabel("写真撮影:"), 0, 0)
        self.digicam_edit = QLineEdit()
        self.digicam_edit.setText("デジカメ")
        self.digicam_edit.setMaximumWidth(150)
        photo_layout.addWidget(self.digicam_edit, 0, 1)

        photo_layout.addWidget(QLabel("報告書:"), 0, 2)
        self.report_radio_yes = QRadioButton("有")
        self.report_radio_no = QRadioButton("無")
        self.report_radio_no.setChecked(True)
        report_radio_group = QButtonGroup()
        report_radio_group.addButton(self.report_radio_yes)
        report_radio_group.addButton(self.report_radio_no)

        report_radio_layout = QHBoxLayout()
        report_radio_layout.addWidget(self.report_radio_yes)
        report_radio_layout.addWidget(self.report_radio_no)
        photo_layout.addLayout(report_radio_layout, 0, 3)

        photo_layout.addWidget(QLabel("部数:"), 0, 4)
        self.reports_count_edit = QLineEdit()
        self.reports_count_edit.setText("0")
        self.reports_count_edit.setMaximumWidth(50)
        self.reports_count_edit.setEnabled(False)
        photo_layout.addWidget(self.reports_count_edit, 0, 5)

        # 部数入力フィールドの有効/無効を切り替える
        self.report_radio_yes.toggled.connect(lambda checked: self.reports_count_edit.setEnabled(checked))

        photo_layout.setColumnStretch(6, 1)

        # 水質検査
        water_group = QGroupBox("水質検査")
        water_grid = QGridLayout(water_group)

        water_grid.addWidget(QLabel("検査業者名:"), 0, 1)
        self.inspector_edit = QLineEdit()
        self.inspector_edit.setText("ヒロエンジニアリング")
        water_grid.addWidget(self.inspector_edit, 0, 2, 1, 3)

        water_grid.addWidget(QLabel("採水場所:"), 1, 0)
        self.sampling_place_edit = QLineEdit()
        water_grid.addWidget(self.sampling_place_edit, 1, 1, 1, 2)

        water_grid.addWidget(QLabel("採水者:"), 1, 3)
        self.sampler_edit = QLineEdit()
        water_grid.addWidget(self.sampler_edit, 1, 4)

        # 水質：あり・なしの選択
        water_quality_layout = QHBoxLayout()
        water_grid.addWidget(QLabel("水質:"), 2, 0)
        self.water_quality_yes = QRadioButton("あり")
        self.water_quality_no = QRadioButton("なし")
        self.water_quality_yes.setChecked(True)
        self.has_water_quality = True
        water_quality_group = QButtonGroup()
        water_quality_group.addButton(self.water_quality_yes)
        water_quality_group.addButton(self.water_quality_no)

        self.water_quality_yes.toggled.connect(self.toggle_water_quality)

        water_quality_layout.addWidget(self.water_quality_yes)
        water_quality_layout.addWidget(self.water_quality_no)
        water_grid.addLayout(water_quality_layout, 2, 1)

        # 水質項目数の入力フィールド
        water_grid.addWidget(QLabel("水質項目:"), 2, 2)
        self.water_quality_items_edit = QLineEdit()
        self.water_quality_items_edit.setPlaceholderText("項目数を入力")
        water_grid.addWidget(self.water_quality_items_edit, 2, 3)

        # 水質検査チェックボックス
        water_checks_layout = QHBoxLayout()

        self.chlorine_check = QCheckBox("塩素")
        water_checks_layout.addWidget(self.chlorine_check)

        self.seal_check = QCheckBox("シール記入")
        water_checks_layout.addWidget(self.seal_check)

        self.report_form_check = QCheckBox("依頼書記入")
        water_checks_layout.addWidget(self.report_form_check)
        water_checks_layout.addStretch()

        water_grid.addLayout(water_checks_layout, 3, 0, 1, 5)

        # 作業者名（最大4人）
        worker_group = QGroupBox("作業者情報")
        worker_layout = QGridLayout(worker_group)

        self.worker_name_edits = []

        for i in range(4):
            worker_layout.addWidget(QLabel(f"作業者{i+1}:"), i, 0)
            worker_edit = QLineEdit()
            self.worker_name_edits.append(worker_edit)
            worker_layout.addWidget(worker_edit, i, 1)

        # 照合事項
        collation_group = QGroupBox("照合事項")
        collation_layout = QHBoxLayout(collation_group)

        self.slip_check = QCheckBox("台帳")
        collation_layout.addWidget(self.slip_check)

        self.bill_check = QCheckBox("請求")
        collation_layout.addWidget(self.bill_check)

        self.report_check2 = QCheckBox("報告書")
        collation_layout.addWidget(self.report_check2)

        collation_layout.addStretch()

        # MEMOセクションを追加
        memo_group = QGroupBox("MEMO")
        memo_layout = QVBoxLayout(memo_group)

        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText("メモを入力してください")
        self.memo_edit.setMinimumHeight(80)  # 十分な高さを確保
        # MEMO欄にも文字数制限を設定
        self.memo_edit.textChanged.connect(lambda: self.limit_text_length(self.memo_edit, 400))
        memo_layout.addWidget(self.memo_edit)

        # 備考タブのレイアウトに追加
        remarks_layout.addWidget(other_group)
        remarks_layout.addWidget(photo_group)
        remarks_layout.addWidget(water_group)
        remarks_layout.addWidget(worker_group)
        remarks_layout.addWidget(collation_group)
        remarks_layout.addWidget(memo_group)  # MEMOグループを追加
        remarks_layout.addStretch()

        # タブウィジェットにタブを追加
        tab_widget.addTab(basic_info_tab, "基本情報")
        tab_widget.addTab(work_info_tab, "作業内容")
        tab_widget.addTab(remarks_tab, "備考")

        # メインレイアウトにタブウィジェットを追加
        main_layout.addWidget(tab_widget)

        # ボタン
        button_layout = QHBoxLayout()

        self.preview_button = QPushButton("プレビュー")
        self.preview_button.clicked.connect(self.preview_order)
        button_layout.addWidget(self.preview_button)

        self.save_pdf_button = QPushButton("PDF保存")
        self.save_pdf_button.clicked.connect(self.save_as_pdf)
        button_layout.addWidget(self.save_pdf_button)

        self.save_db_button = QPushButton("DB保存")
        self.save_db_button.clicked.connect(self.save_to_database)
        button_layout.addWidget(self.save_db_button)

        self.print_button = QPushButton("印刷")
        self.print_button.clicked.connect(self.print_order)
        button_layout.addWidget(self.print_button)

        self.close_button = QPushButton("閉じる")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

    def calculate_work_days(self):
        """作業日数を計算する"""
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()

        # 日付の差を計算
        delta = end_date - start_date
        days = delta.days + 1  # 初日も含める

        self.work_days_label.setText(f"作業日数: {days}日間")

    def populate_data(self):
        """プロジェクトデータからフォームにデータを設定する"""
        if not self.project_data:
            return

        # 案件名を現場名として設定
        self.site_name_edit.setText(self.project_data.get('title', ''))

        # 住所
        self.site_address_edit.setText(self.project_data.get('site_address', ''))

        # 担当者を設定（workers_listから最初の作業員を選択）
        project_workers = self.db.get_project_workers(self.project_data.get('id', 0))
        if project_workers and len(project_workers) > 0:
            worker_id = project_workers[0]['id']
            # コンボボックスで該当するIDを持つ項目を選択
            for i in range(self.manager_combo.count()):
                if self.manager_combo.itemData(i) == worker_id:
                    self.manager_combo.setCurrentIndex(i)
                    break

            # 作成者も同じ作業員を初期選択
            for i in range(self.creator_combo.count()):
                if self.creator_combo.itemData(i) == worker_id:
                    self.creator_combo.setCurrentIndex(i)
                    break

        # 取引先名を看板社名として設定
        self.signboard_name_edit.setText(self.project_data.get('client_name', ''))

        # 作業日
        if self.project_data.get('start_date'):
            start_date = QDate.fromString(self.project_data['start_date'], 'yyyy-MM-dd')
            if start_date.isValid():
                self.start_date_edit.setDate(start_date)

        if self.project_data.get('end_date'):
            end_date = QDate.fromString(self.project_data['end_date'], 'yyyy-MM-dd')
            if end_date.isValid():
                self.end_date_edit.setDate(end_date)

        # 作業内容
        service_name = self.project_data.get('service_name', '').lower()
        if '排水' in service_name:
            self.drainage_checkbox.setChecked(True)
        elif '貯水' in service_name:
            self.water_storage_checkbox.setChecked(True)
        else:
            self.construction_checkbox.setChecked(True)

        # 作業日数を計算
        self.calculate_work_days()

    def populate_order_data(self):
        """業務指示書データからフォームにデータを設定する"""
        if not self.order_data:
            return

        # 基本情報の設定
        creation_date = QDate.fromString(self.order_data.get('creation_date', ''), "yyyy-MM-dd")
        if creation_date.isValid():
            self.creation_date_edit.setDate(creation_date)

        self.work_type_edit.setText(self.order_data.get('work_type', ''))

        # 担当者と作成者
        manager_id = self.order_data.get('manager_id')
        creator_id = self.order_data.get('creator_id')

        if manager_id:
            for i in range(self.manager_combo.count()):
                if self.manager_combo.itemData(i) == manager_id:
                    self.manager_combo.setCurrentIndex(i)
                    break

        if creator_id:
            for i in range(self.creator_combo.count()):
                if self.creator_combo.itemData(i) == creator_id:
                    self.creator_combo.setCurrentIndex(i)
                    break

        self.site_name_edit.setText(self.order_data.get('site_name', ''))
        self.site_address_edit.setText(self.order_data.get('site_address', ''))
        self.management_tel_edit.setText(self.order_data.get('management_tel', ''))
        self.duty_edit.setPlainText(self.order_data.get('duty', ''))

        # 日付
        start_date = QDate.fromString(self.order_data.get('start_date', ''), "yyyy-MM-dd")
        if start_date.isValid():
            self.start_date_edit.setDate(start_date)

        end_date = QDate.fromString(self.order_data.get('end_date', ''), "yyyy-MM-dd")
        if end_date.isValid():
            self.end_date_edit.setDate(end_date)

        # 時間
        if self.order_data.get('arrival_time'):
            try:
                time_parts = self.order_data.get('arrival_time', '').split(':')
                if len(time_parts) == 2:
                    hour, minute = int(time_parts[0]), int(time_parts[1])
                    self.arrival_time_edit.setTime(QTime(hour, minute))
            except:
                pass

        if self.order_data.get('scheduled_start'):
            try:
                time_parts = self.order_data.get('scheduled_start', '').split(':')
                if len(time_parts) == 2:
                    hour, minute = int(time_parts[0]), int(time_parts[1])
                    self.scheduled_start_edit.setTime(QTime(hour, minute))
            except:
                pass

        if self.order_data.get('scheduled_end'):
            try:
                time_parts = self.order_data.get('scheduled_end', '').split(':')
                if len(time_parts) == 2:
                    hour, minute = int(time_parts[0]), int(time_parts[1])
                    self.scheduled_end_edit.setTime(QTime(hour, minute))
            except:
                pass

        if self.order_data.get('actual_start'):
            try:
                time_parts = self.order_data.get('actual_start', '').split(':')
                if len(time_parts) == 2:
                    hour, minute = int(time_parts[0]), int(time_parts[1])
                    self.start_time_edit.setTime(QTime(hour, minute))
            except:
                pass

        if self.order_data.get('actual_end'):
            try:
                time_parts = self.order_data.get('actual_end', '').split(':')
                if len(time_parts) == 2:
                    hour, minute = int(time_parts[0]), int(time_parts[1])
                    self.end_time_edit.setTime(QTime(hour, minute))
            except:
                pass

        # 作業内容チェックボックス
        work_content = self.order_data.get('work_content', '')
        self.drainage_checkbox.setChecked('排水' in work_content)
        self.water_storage_checkbox.setChecked('貯水' in work_content)
        self.construction_checkbox.setChecked('工事' in work_content or 'その他' in work_content)

        # 元請情報
        self.contractor_company_edit.setText(self.order_data.get('contractor_company', ''))
        self.contractor_manager_edit.setText(self.order_data.get('contractor_manager', ''))
        self.contact_number_edit.setText(self.order_data.get('contact_number', ''))
        self.signboard_name_edit.setText(self.order_data.get('signboard_name', ''))

        # 連絡先情報
        self.arrival_number_edit.setText(self.order_data.get('arrival_number', ''))
        self.arrival_manager_edit.setText(self.order_data.get('arrival_manager', ''))
        self.arrival_contact_edit.setText(self.order_data.get('arrival_contact', ''))
        self.completion_number_edit.setText(self.order_data.get('completion_number', ''))
        self.completion_manager_edit.setText(self.order_data.get('completion_manager', ''))
        self.completion_contact_edit.setText(self.order_data.get('completion_contact', ''))

        # 作業詳細
        self.work_details_edit.setPlainText(self.order_data.get('work_details', ''))

        # チェック項目
        self.business_card_check.setChecked(self.order_data.get('business_card', 0) == 1)
        self.vest_check.setChecked(self.order_data.get('vest', 0) == 1)

        # 写真・報告書
        self.digicam_edit.setText(self.order_data.get('digicam', ''))
        self.report_radio_yes.setChecked(self.order_data.get('has_report', 0) == 1)
        self.report_radio_no.setChecked(self.order_data.get('has_report', 0) == 0)
        self.reports_count_edit.setText(str(self.order_data.get('reports_count', 0)))

        # 水質検査
        self.inspector_edit.setText(self.order_data.get('inspector', ''))
        self.sampling_place_edit.setText(self.order_data.get('sampling_place', ''))
        self.sampler_edit.setText(self.order_data.get('sampler', ''))
        self.water_quality_yes.setChecked(self.order_data.get('has_water_quality', 1) == 1)
        self.water_quality_no.setChecked(self.order_data.get('has_water_quality', 1) == 0)
        self.water_quality_items_edit.setText(str(self.order_data.get('water_quality_items', 0)))
        self.chlorine_check.setChecked(self.order_data.get('chlorine', 0) == 1)
        self.seal_check.setChecked(self.order_data.get('seal', 0) == 1)
        self.report_form_check.setChecked(self.order_data.get('report_form', 0) == 1)

        # 作業者
        for i in range(min(4, len(self.worker_name_edits))):
            worker_edit = self.worker_name_edits[i]
            worker_edit.setText(self.order_data.get(f'worker{i+1}', ''))
        self.slip_check.setChecked(self.order_data['slip'] == 1)
        self.bill_check.setChecked(self.order_data['bill'] == 1)
        self.report_check2.setChecked(self.order_data['report'] == 1)

        # MEMOの設定
        if 'memo' in self.order_data:
            self.memo_edit.setPlainText(self.order_data.get('memo', ''))

    def generate_pdf(self, filename=None):
        """PDFを生成する"""
        # フォントの登録
        font_path = os.path.join("fonts", "ipaexg.ttf")

        # フォントファイルが存在する場合のみ登録を試みる
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("IPAexGothic", font_path))
            default_font = "IPAexGothic"
        else:
            # 代替としてHelveticaを使用
            default_font = "Helvetica"

        try:
            # 一時ファイルを作成（ファイル名が指定されていない場合）
            if not filename:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                filename = temp_file.name
                temp_file.close()

            # キャンバスを作成
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # デフォルトフォントを設定
            c.setFont(default_font, 10)

            # ヘッダー部分の作成 (表形式)
            # 会社名とタイトルのテーブル - No.のセルサイズをさらに拡大
            order_id = self.project_data.get("id", "") if self.project_data else ""
            header_data = [
                ['ティーシー', '業 務 指 示 書', f'No. {order_id}']
            ]
            header_style = TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 12),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (2, 0), 1, colors.black),
                ('BOX', (0, 0), (0, 0), 1, colors.black),  # 会社名を枠で囲む
            ])
            # Noのセル幅を調整して右寄せを確実にする
            header_table = Table(header_data, colWidths=[80, 355, 100])
            header_table.setStyle(header_style)
            header_table.wrapOn(c, width, height)
            # ヘッダーの位置を上げる
            header_table.drawOn(c, 30, height - 40)

            # 基本情報セクション
            # 作成欄に選択された従業員名を表示
            selected_manager = self.manager_combo.currentText()
            selected_creator = self.creator_combo.currentText()

            # 勤務内容を制限（PDFのセルに収まるようにする）
            duty_text = self.duty_edit.toPlainText()
            if len(duty_text) > 150:
                duty_text = duty_text[:147] + "..."  # 省略記号を追加

            base_info_data = [
                ['作成日', f'{self.creation_date_edit.date().toString("yyyy年M月d日")}', '', '', ''],
                ['作業性', f'{self.work_type_edit.text()}', '担当', f'{selected_manager}', f'作成  {selected_creator}'],
                ['現場名', f'{self.site_name_edit.text()[:50]}', '', '', ''],
                ['現場住所', f'{self.site_address_edit.text()[:50]}', '', '', ''],
                ['管理室:', f'{self.management_tel_edit.text()[:20]}', '', '', ''],
                ['勤務:', f'{duty_text}', '', '', '']
            ]

            base_info_style = TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.white),
                ('BACKGROUND', (2, 1), (2, 1), colors.white),
                ('BACKGROUND', (2, 4), (2, 4), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('SPAN', (1, 0), (4, 0)),  # 作成日
                ('SPAN', (1, 2), (4, 2)),  # 現場名
                ('SPAN', (1, 3), (4, 3)),  # 現場住所
                ('SPAN', (1, 4), (4, 4)),  # 管理室
                ('SPAN', (1, 5), (4, 5)),  # 勤務セルを結合して大きく
            ])

            base_info_table = Table(base_info_data, colWidths=[80, 120, 80, 120, 135])
            base_info_table.setStyle(base_info_style)
            base_info_table.wrapOn(c, width, height)
            # 基本情報テーブルの位置を下げる
            base_info_table.drawOn(c, 30, height - 160)

            # 作業日程セクション - セルサイズをさらに拡大
            # 作業日の計算
            work_days = int(self.work_days_label.text().split(':')[1].strip().replace('日間', ''))

            schedule_data = [
                ['作 業 日', f'{self.start_date_edit.date().toString("yyyy年M月d日")} 〜 {self.end_date_edit.date().toString("yyyy年M月d日")}', '作業日数', f'{work_days}日間'],
                ['作業時間', f'現着: {self.arrival_time_edit.time().toString("HH:mm")}', f'予定: {self.scheduled_start_edit.time().toString("HH:mm")} 〜 {self.scheduled_end_edit.time().toString("HH:mm")}', f'実働: {self.start_time_edit.time().toString("HH:mm")} 〜 {self.end_time_edit.time().toString("HH:mm")}'],
                ['作業内容', f'{"排水" if self.drainage_checkbox.isChecked() else ""}', f'{"貯水" if self.water_storage_checkbox.isChecked() else ""}', f'{"工事/その他" if self.construction_checkbox.isChecked() else ""}']
            ]

            schedule_style = TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.white),
                ('BACKGROUND', (2, 0), (2, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('SPAN', (0, 0), (0, 0)),  # 作業日
                ('SPAN', (1, 0), (1, 0)),  # 作業日の値
            ])

            # セルサイズをさらに調整 - 予定時刻が十分入るよう幅を拡大
            schedule_table = Table(schedule_data, colWidths=[80, 170, 120, 165])
            schedule_table.setStyle(schedule_style)
            schedule_table.wrapOn(c, width, height)
            schedule_table.drawOn(c, 30, height - 230)

            # 元請会社セクション
            # 連絡担当者情報を追加
            company_data = [
                ['元請会社', '連絡先', f'{self.contact_number_edit.text()}'],
                ['', '元請担当', f'{self.contractor_manager_edit.text()}'],
                ['看板社名', f'{self.signboard_name_edit.text()}', ''],
                ['現着連絡', f'{self.arrival_number_edit.text()}', f'担当: {self.arrival_manager_edit.text()}  連絡先: {self.arrival_contact_edit.text()}'],
                ['終了連絡', f'{self.completion_number_edit.text()}', f'担当: {self.completion_manager_edit.text()}  連絡先: {self.completion_contact_edit.text()}']
            ]

            company_style = TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('SPAN', (0, 0), (0, 1)),  # 元請会社
                ('SPAN', (1, 2), (2, 2)),  # 看板社名の値
            ])

            # より見やすいセル幅に調整
            company_table = Table(company_data, colWidths=[80, 120, 335])
            company_table.setStyle(company_style)
            company_table.wrapOn(c, width, height)
            company_table.drawOn(c, 30, height - 330)

            # 水平線
            c.line(30, height - 340, width - 30, height - 340)

            # 作業詳細と注意事項（左右分割）- レイアウト改善
            c.drawString(40, height - 355, "作業詳細")
            c.drawString(width - 170, height - 355, "<その他注意事項等>")

            # 作業詳細テキストの文字数を制限
            work_details = self.work_details_edit.toPlainText()
            if len(work_details) > 300:
                work_details = work_details[:297] + "..."

            # 作業詳細テキストエリアの内容を描画（左側に配置、自動改行あり）
            text_lines = work_details.split('\n')
            max_width = width/2 - 60  # 左側領域の最大幅
            y_position = height - 375

            # 最大表示行数を制限
            max_details_lines = 6
            details_line_count = 0

            # テキストを描画（自動改行あり）
            for line in text_lines:
                # 一行の文字が長すぎる場合は折り返し
                if c.stringWidth(line, default_font, 10) > max_width:
                    words = []
                    current_line = ""
                    for char in line:
                        test_line = current_line + char
                        if c.stringWidth(test_line, default_font, 10) <= max_width:
                            current_line = test_line
                        else:
                            words.append(current_line)
                            current_line = char
                    if current_line:
                        words.append(current_line)

                    for word in words:
                        c.drawString(40, y_position, word)
                        y_position -= 15
                        details_line_count += 1
                        if details_line_count >= max_details_lines:  # 最大行数に達したら終了
                            break
                else:
                    c.drawString(40, y_position, line)
                    y_position -= 15
                    details_line_count += 1

                if details_line_count >= max_details_lines:  # 最大行数に達したら終了
                    break

            # その他注意事項（右側に配置）
            y_position = height - 375

            # チェックボックスの表示を修正
            if self.business_card_check.isChecked():
                c.drawString(width/2 + 30, y_position, "☑ 業者証")
            else:
                c.drawString(width/2 + 30, y_position, "□ 業者証")
            y_position -= 20

            if self.vest_check.isChecked():
                c.drawString(width/2 + 30, y_position, "☑ ベスト")
            else:
                c.drawString(width/2 + 30, y_position, "□ ベスト")

            # 水平線
            c.line(30, height - 480, width - 30, height - 480)

            # MEMOセクション（中央に表示、より大きいスペース）
            c.setFont(default_font, 12)
            c.drawCentredString(width/2, height - 500, "★ ★   MEMO   ★ ★")
            c.setFont(default_font, 10)

            # MEMOテキストを描画（文字数制限を適用）
            memo_text = self.memo_edit.toPlainText()
            if len(memo_text) > 400:  # MEMO欄の文字数制限
                memo_text = memo_text[:397] + "..."

            if memo_text:
                # テキストを複数行に分割して描画
                memo_lines = memo_text.split('\n')
                memo_y = height - 520  # 開始Y位置

                # 最大表示行数を制限
                max_lines = 6
                line_count = 0

                for line in memo_lines:
                    # 一行の文字が長すぎる場合は折り返し
                    if c.stringWidth(line, default_font, 10) > width - 100:
                        words = []
                        current_line = ""
                        for char in line:
                            test_line = current_line + char
                            if c.stringWidth(test_line, default_font, 10) <= width - 100:
                                current_line = test_line
                            else:
                                words.append(current_line)
                                current_line = char
                        if current_line:
                            words.append(current_line)

                        for word in words:
                            c.drawString(40, memo_y, word)
                            memo_y -= 15
                            line_count += 1
                            if line_count >= max_lines:  # 最大行数に達したら終了
                                break
                    else:
                        c.drawString(40, memo_y, line)
                        memo_y -= 15
                        line_count += 1

                    if line_count >= max_lines:  # 最大行数に達したら終了
                        break

            # 備考情報（テーブル形式で洗練されたデザイン）
            # 水平線
            c.line(30, height - 590, width - 30, height - 590)

            remarks_label = [['備考']]
            remarks_table = Table(remarks_label, colWidths=[width - 60])
            remarks_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 11),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (0, 0), 1, colors.black),
            ]))
            remarks_table.wrapOn(c, width, height)
            remarks_table.drawOn(c, 30, height - 610)

            # 備考の詳細情報（テーブル形式）
            equipment_data = [
                ['写真撮影:', f'{self.digicam_edit.text()}', '報告書:',
                 f'{"有" if self.report_radio_yes.isChecked() else "無"}',
                 f'部数  {self.reports_count_edit.text()}部'],
                ['検査業者名:', f'{self.inspector_edit.text()}', '', '', ''],
                ['採水場所:', f'{self.sampling_place_edit.text()}', '採水者:', f'{self.sampler_edit.text()}', '水質: {"あり" if self.water_quality_yes.isChecked() else "なし"}']
            ]

            equipment_style = TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('SPAN', (1, 1), (4, 1)),  # 検査業者名
            ])

            equipment_table = Table(equipment_data, colWidths=[80, 120, 80, 100, 155])
            equipment_table.setStyle(equipment_style)
            equipment_table.wrapOn(c, width, height)
            equipment_table.drawOn(c, 30, height - 680)

            # チェックボックス部分（テーブル形式）
            items_text = self.water_quality_items_edit.text()
            items_display = f"{items_text}項目" if items_text else ""
            checks_data = [['水質検査チェック項目  ' + items_display]]
            checks_table = Table(checks_data, colWidths=[width - 60])
            checks_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), default_font, 11),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (0, 0), 1, colors.black),
            ]))
            checks_table.wrapOn(c, width, height)
            checks_table.drawOn(c, 30, height - 700)

            # チェックボックスを描画（より洗練されたデザイン）
            check_y = height - 720
            check_spacing = 20

            # チェックボックスは印刷時には常に空（□）で表示する
            # 塩素チェック
            c.drawString(50, check_y, "□ 塩素")

            # シール記入チェック
            c.drawString(200, check_y, "□ シール記入")

            # 依頼書記入チェック
            c.drawString(350, check_y, "□ 依頼書記入")

            # 作業者情報（テーブル形式）
            c.drawString(30, check_y - 30, "作業者:")

            # 作業者を横並びに表示（変更）
            worker_names = []
            for i, worker_edit in enumerate(self.worker_name_edits):
                if worker_edit.text():
                    worker_names.append(f"{i+1}. {worker_edit.text()}")

            # 作業者名を横に並べて表示
            if worker_names:
                worker_text = "   ".join(worker_names)  # 複数の空白で区切る
                c.drawString(50, check_y - 50, worker_text)

            # 照合事項セクションはPDFには表示しない

            # 文書を保存
            c.save()

            return filename
        except Exception as e:
            error_message = f"PDF生成中にエラーが発生しました: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "エラー", error_message)
            return None

    def preview_order(self):
        """業務指示書をプレビューする"""
        try:
            # PDFを一時ファイルに生成
            temp_pdf = self.generate_pdf()
            if temp_pdf:
                # デフォルトのPDFビューアで開く
                webbrowser.open(temp_pdf)
        except Exception as e:
            error_message = f"プレビュー中にエラーが発生しました: {str(e)}"
            QMessageBox.critical(self, "エラー", error_message)
            print(f"プレビューエラーの詳細: {str(e)}")
            import traceback
            traceback.print_exc()

    def save_to_database(self):
        """業務指示書をデータベースに保存する"""
        try:
            # 業務指示書データを収集
            order_data = {
                'project_id': self.project_data.get('id') if self.project_data else None,
                'order_number': self.order_data.get('order_number') if self.order_data else self.db.get_next_order_number(),
                'creation_date': self.creation_date_edit.date().toString("yyyy-MM-dd"),
                'work_type': self.work_type_edit.text(),
                'manager_id': self.manager_combo.currentData(),
                'creator_id': self.creator_combo.currentData(),
                'site_name': self.site_name_edit.text(),
                'site_address': self.site_address_edit.text(),
                'management_tel': self.management_tel_edit.text(),
                'duty': self.duty_edit.toPlainText(),
                'start_date': self.start_date_edit.date().toString("yyyy-MM-dd"),
                'end_date': self.end_date_edit.date().toString("yyyy-MM-dd"),
                'arrival_time': self.arrival_time_edit.time().toString("HH:mm"),
                'scheduled_start': self.scheduled_start_edit.time().toString("HH:mm"),
                'scheduled_end': self.scheduled_end_edit.time().toString("HH:mm"),
                'actual_start': self.start_time_edit.time().toString("HH:mm"),
                'actual_end': self.end_time_edit.time().toString("HH:mm"),
                'work_content': '排水' if self.drainage_checkbox.isChecked() else ('貯水' if self.water_storage_checkbox.isChecked() else '工事/その他'),
                'contractor_company': self.contractor_company_edit.text(),
                'contractor_manager': self.contractor_manager_edit.text(),
                'contact_number': self.contact_number_edit.text(),
                'signboard_name': self.signboard_name_edit.text(),
                'arrival_number': self.arrival_number_edit.text(),
                'arrival_manager': self.arrival_manager_edit.text(),
                'arrival_contact': self.arrival_contact_edit.text(),
                'completion_number': self.completion_number_edit.text(),
                'completion_manager': self.completion_manager_edit.text(),
                'completion_contact': self.completion_contact_edit.text(),
                'work_details': self.work_details_edit.toPlainText(),
                'business_card': 1 if self.business_card_check.isChecked() else 0,
                'vest': 1 if self.vest_check.isChecked() else 0,
                'digicam': self.digicam_edit.text(),
                'has_report': 1 if self.report_radio_yes.isChecked() else 0,
                'reports_count': int(self.reports_count_edit.text() or 0),
                'inspector': self.inspector_edit.text(),
                'sampling_place': self.sampling_place_edit.text(),
                'sampler': self.sampler_edit.text(),
                'has_water_quality': 1 if self.water_quality_yes.isChecked() else 0,
                'water_quality_items': int(self.water_quality_items_edit.text() or 0),
                'chlorine': 1 if self.chlorine_check.isChecked() else 0,
                'seal': 1 if self.seal_check.isChecked() else 0,
                'report_form': 1 if self.report_form_check.isChecked() else 0,
                'worker1': self.worker_name_edits[0].text() if len(self.worker_name_edits) > 0 else '',
                'worker2': self.worker_name_edits[1].text() if len(self.worker_name_edits) > 1 else '',
                'worker3': self.worker_name_edits[2].text() if len(self.worker_name_edits) > 2 else '',
                'worker4': self.worker_name_edits[3].text() if len(self.worker_name_edits) > 3 else '',
                'slip': 1 if self.slip_check.isChecked() else 0,
                'bill': 1 if self.bill_check.isChecked() else 0,
                'report': 1 if self.report_check2.isChecked() else 0,
                'memo': self.memo_edit.toPlainText()
            }

            # 既存の指示書を編集している場合はIDを設定
            if self.order_data and 'id' in self.order_data:
                order_data['id'] = self.order_data['id']

            # データベースに保存
            order_id = self.db.save_work_order(order_data)

            if order_id:
                QMessageBox.information(self, "保存完了", "業務指示書がデータベースに保存されました。")

                # 保存完了フラグを設定
                self.saved = True

                # 親ウィジェットがload_work_ordersメソッドを持っている場合は呼び出す
                parent = self.parent()
                if parent:
                    print(f"親ウィジェットのクラス: {parent.__class__.__name__}")

                    # メソッドの存在を確認
                    if hasattr(parent, 'load_work_orders') and callable(getattr(parent, 'load_work_orders')):
                        print("load_work_orders メソッドを呼び出します")
                        parent.load_work_orders()

                        # ordersChangedシグナルが存在する場合は発行
                        if hasattr(parent, 'ordersChanged') and isinstance(getattr(parent, 'ordersChanged'), pyqtSignal):
                            print("ordersChanged シグナルを発行します")
                            parent.ordersChanged.emit()

                # ダイアログを閉じる（必要な場合）
                # self.close()

                return True
            else:
                QMessageBox.warning(self, "保存失敗", "業務指示書の保存に失敗しました。")
                return False

        except Exception as e:
            error_message = f"データベース保存中にエラーが発生しました: {str(e)}"
            QMessageBox.critical(self, "エラー", error_message)
            print(f"データベース保存エラーの詳細: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def save_as_pdf(self):
        """業務指示書をPDFとして保存する"""
        try:
            # プロジェクト名をファイル名のベースにする
            default_filename = f"業務指示書_{self.site_name_edit.text()}_{self.creation_date_edit.date().toString('yyyyMMdd')}.pdf"

            # ファイル保存ダイアログを表示
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "PDFとして保存",
                default_filename,
                "PDF文書 (*.pdf)"
            )

            if filename:
                # PDFを生成して保存
                generated_file = self.generate_pdf(filename)
                if generated_file:
                    QMessageBox.information(self, "保存完了", f"PDFが保存されました: {filename}")
        except Exception as e:
            error_message = f"PDF保存中にエラーが発生しました: {str(e)}"
            QMessageBox.critical(self, "エラー", error_message)
            print(f"PDF保存エラーの詳細: {str(e)}")
            import traceback
            traceback.print_exc()

    def print_order(self):
        """業務指示書を印刷する"""
        try:
            # PDFを一時ファイルに生成
            temp_pdf = self.generate_pdf()
            if not temp_pdf:
                return

            printer = QPrinter()
            print_dialog = QPrintDialog(printer, self)

            if print_dialog.exec() == QDialog.DialogCode.Accepted:
                self.print_pdf(printer, temp_pdf)

        except Exception as e:
            error_message = f"印刷中にエラーが発生しました: {str(e)}"
            QMessageBox.critical(self, "エラー", error_message)
            print(f"印刷エラーの詳細: {str(e)}")
            import traceback
            traceback.print_exc()

    def print_pdf(self, printer, pdf_file):
        """PDFを印刷する"""
        # ここにPDFを印刷する実装を追加
        # 実際の印刷処理は環境によって異なる場合があります
        # 外部コマンドを使用する方法も考えられます
        pass

    def closeEvent(self, event):
        """ダイアログが閉じられるときの処理"""
        # 保存が完了していて、親ウィジェットがload_work_ordersメソッドを持つ場合は呼び出す
        if self.saved:
            parent = self.parent()
            if parent and hasattr(parent, 'load_work_orders') and callable(getattr(parent, 'load_work_orders')):
                parent.load_work_orders()
                if hasattr(parent, 'ordersChanged') and isinstance(getattr(parent, 'ordersChanged'), pyqtSignal):
                    parent.ordersChanged.emit()

        # 親クラスのcloseEventを呼び出す
        super().closeEvent(event)

    def limit_text_length(self, text_edit, max_length):
        """テキストエディタの文字数を制限する"""
        text = text_edit.toPlainText()
        if len(text) > max_length:
            text_edit.setPlainText(text[:max_length])
            # カーソル位置を末尾に設定
            cursor = text_edit.textCursor()
            cursor.setPosition(max_length)
            text_edit.setTextCursor(cursor)

    def toggle_water_quality(self, checked):
        """水質ありなしの切り替え処理"""
        self.has_water_quality = checked
        self.water_quality_items_edit.setEnabled(checked)
        self.chlorine_check.setEnabled(checked)
        self.seal_check.setEnabled(checked)
        self.report_form_check.setEnabled(checked)

    def toggle_water_quality_items(self):
        """水質項目数を切り替える"""
        self.water_quality_items_edit.setText(str(int(self.water_quality_items_edit.text()) + 1))

    def toggle_water_quality_items_decrement(self):
        """水質項目数を減らす"""
        current_value = int(self.water_quality_items_edit.text())
        if current_value > 0:
            self.water_quality_items_edit.setText(str(current_value - 1))

    def toggle_water_quality_items_reset(self):
        """水質項目数をリセットする"""
        self.water_quality_items_edit.setText("0")

    def toggle_water_quality_items_set(self, value):
        """水質項目数を設定する"""
        self.water_quality_items_edit.setText(str(value))
