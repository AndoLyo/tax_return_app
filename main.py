"""
確定申告支援アプリケーション

このモジュールは確定申告の計算を支援するGUIアプリケーションのメインエントリポイントです。
収支管理、税額計算、PDF出力、レポート生成、減価償却計算などの機能を提供します。

Authors: AI Assistant with Claude Code
Version: 2.0.0
License: Educational/Personal use only
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, Menu
import threading
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from models import TaxReturnData, PersonalInfo, BankAccount, TaxSettings, Deductions
from transaction_manager import TransactionManager
from calculators import TaxCalculator
from pdf_generator import PDFGenerator
from data_manager import DataManager
from reports import ReportGenerator
from depreciation_calculator import DepreciationCalculator

# tkcalendarのインポート試行
try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("警告: tkcalendarがインストールされていません。")
    print("カレンダー機能を使用するには: pip install tkcalendar")

# --- アプリの基本設定 ---
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class TaxReturnApp:
    """
    確定申告支援アプリケーションのメインクラス
    
    このクラスはGUIインターフェースを管理し、ユーザーの操作を処理します。
    税額計算、データ保存、PDF出力、減価償却計算などの機能を統合して提供します。
    
    Attributes:
        root (ctk.CTk): メインウィンドウ
        tax_data (TaxReturnData): 申告データ
        data_manager (DataManager): データ管理機能
        tax_calculator (TaxCalculator): 税額計算機能
        pdf_generator (PDFGenerator): PDF出力機能
        depreciation_calculator (DepreciationCalculator): 減価償却計算機能
        current_filename (Optional[str]): 現在のファイル名
        is_modified (bool): データ変更フラグ
    """
    def __init__(self, root: ctk.CTk) -> None:
        """
        アプリケーションを初期化します
        
        Args:
            root (ctk.CTk): CustomTkinterのルートウィンドウ
            
        Note:
            このメソッドはGUIの初期化、データマネージャーの設定、
            イベントハンドラーの登録を行います。
        """
        self.root = root
        self.root.title("確定申告支援アプリケーション - Tax Return Helper")
        self.root.geometry("1400x900")
        
        # データ管理オブジェクトの初期化
        self.tax_data = TaxReturnData()
        self.data_manager = DataManager()
        self.tax_calculator = TaxCalculator()
        self.pdf_generator = PDFGenerator()
        self.depreciation_calculator = DepreciationCalculator()
        
        # ファイル管理状態の初期化
        self.current_filename: Optional[str] = None
        self.is_modified: bool = False
        
        # UI初期化処理
        self.create_menu()
        self.setup_ui()
        self.setup_auto_save()
        
        # ウィンドウクローズイベントの設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="新規作成", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="開く", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="名前を付けて保存", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        
        recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近使ったファイル", menu=recent_menu)
        self.update_recent_files_menu(recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)
        
        calc_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="計算", menu=calc_menu)
        calc_menu.add_command(label="税額計算", command=self.calculate_taxes)
        calc_menu.add_command(label="シミュレーション", command=self.show_tax_simulation)
        calc_menu.add_command(label="減価償却計算", command=self.show_depreciation_calculator)
        
        output_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="出力", menu=output_menu)
        output_menu.add_command(label="確定申告書PDF", command=self.export_tax_return_pdf)
        output_menu.add_command(label="月次レポートPDF", command=self.export_monthly_report_pdf)
        output_menu.add_command(label="CSV出力", command=self.export_csv)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="バックアップ管理", command=self.show_backup_manager)
        tools_menu.add_command(label="設定", command=self.show_settings)
        tools_menu.add_command(label="データ検証", command=self.validate_data)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self.show_help)
        help_menu.add_command(label="バージョン情報", command=self.show_about)
        
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as_file())
        
    def setup_ui(self):
        # メインフレーム
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ヘッダー
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="確定申告支援アプリケーション", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        self.status_label = ctk.CTkLabel(
            header_frame, 
            text="新規ファイル", 
            font=ctk.CTkFont(size=16)
        )
        self.status_label.pack(pady=(0, 20))
        
        # ダッシュボードカード
        self.setup_dashboard(main_frame)
        
        # タブビュー
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=10)
        
        # タブを先に追加
        self.tabview.add("基本情報")
        self.tabview.add("収支入力")
        self.tabview.add("所得控除")
        self.tabview.add("税額計算")
        self.tabview.add("減価償却")
        self.tabview.add("レポート")
        
        # タブの設定
        self.setup_personal_info_tab()
        self.setup_transaction_tab()
        self.setup_deduction_tab()
        self.setup_calculation_tab()
        self.setup_depreciation_tab()
        self.setup_report_tab()
        
        # ステータスバー
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=(10, 0))
        
        self.modification_status = ctk.CTkLabel(status_frame, text="")
        self.modification_status.pack(side="left", padx=10, pady=5)
        
        self.calculation_status = ctk.CTkLabel(status_frame, text="税額未計算")
        self.calculation_status.pack(side="right", padx=10, pady=5)
    
    def setup_dashboard(self, parent):
        """ダッシュボードの設定"""
        dashboard_frame = ctk.CTkFrame(parent)
        dashboard_frame.pack(fill="x", pady=(0, 20))
        
        dashboard_title = ctk.CTkLabel(
            dashboard_frame, 
            text="📊 申告状況ダッシュボード", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        dashboard_title.pack(pady=10)
        
        # カード表示
        cards_frame = ctk.CTkFrame(dashboard_frame)
        cards_frame.pack(pady=10, padx=20, fill="x")
        
        # グリッドの列を均等に配置
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # カード表示（初期値）
        cards = [
            ("申告年度", f"{datetime.now().year}年", "#2196F3"),
            ("所得金額", "未入力", "#4CAF50"),
            ("税額", "未計算", "#FF9800"),
            ("還付額", "未計算", "#9C27B0"),
        ]
        
        for i, (label, value, color) in enumerate(cards):
            card = ctk.CTkFrame(cards_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            
            label_widget = ctk.CTkLabel(card, text=label, text_color="white", font=ctk.CTkFont(size=12))
            label_widget.pack(pady=(10, 5), padx=20)
            
            value_widget = ctk.CTkLabel(card, text=value, text_color="white", font=ctk.CTkFont(size=20, weight="bold"))
            value_widget.pack(pady=(5, 10), padx=20)
            
            # 後で更新できるように保存
            if label == "所得金額":
                self.income_card = value_widget
            elif label == "税額":
                self.tax_card = value_widget
            elif label == "還付額":
                self.refund_card = value_widget
        
    def setup_personal_info_tab(self):
        frame = ctk.CTkFrame(self.tabview.tab("基本情報"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(frame)
        scrollbar = tk.ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 個人情報セクション
        personal_title = ctk.CTkLabel(scrollable_frame, text="個人情報", font=ctk.CTkFont(size=16, weight="bold"))
        personal_title.pack(pady=(10, 5))
        
        personal_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        personal_frame.pack(padx=20, pady=10, fill="x")
        
        row = 0
        ctk.CTkLabel(personal_frame, text="氏名*:").pack(pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ctk.CTkEntry(personal_frame, width=400)
        self.name_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(personal_frame, text="フリガナ:").pack(pady=5)
        self.name_kana_var = tk.StringVar()
        self.name_kana_entry = ctk.CTkEntry(personal_frame, width=400)
        self.name_kana_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(personal_frame, text="住所*:").pack(pady=5)
        self.address_var = tk.StringVar()
        self.address_entry = ctk.CTkEntry(personal_frame, width=400)
        self.address_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(personal_frame, text="郵便番号:").pack(pady=5)
        self.postal_code_var = tk.StringVar()
        self.postal_code_entry = ctk.CTkEntry(personal_frame, width=200)
        self.postal_code_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(personal_frame, text="電話番号:").pack(pady=5)
        self.phone_var = tk.StringVar()
        self.phone_entry = ctk.CTkEntry(personal_frame, width=300)
        self.phone_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(personal_frame, text="生年月日:").pack(pady=5)
        self.birthdate_var = tk.StringVar()
        self.birthdate_entry = ctk.CTkEntry(personal_frame, width=300)
        self.birthdate_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(personal_frame, text="職業:").pack(pady=5)
        self.occupation_var = tk.StringVar()
        self.occupation_entry = ctk.CTkEntry(personal_frame, width=400)
        self.occupation_entry.pack(pady=5)
        
        # 申告設定セクション
        tax_settings_title = ctk.CTkLabel(scrollable_frame, text="申告設定", font=ctk.CTkFont(size=16, weight="bold"))
        tax_settings_title.pack(pady=(20, 5))
        
        tax_settings_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        tax_settings_frame.pack(padx=20, pady=10, fill="x")
        
        row = 0
        ctk.CTkLabel(tax_settings_frame, text="申告年度:").pack(pady=5)
        self.tax_year_var = tk.StringVar(value=str(datetime.now().year))
        self.tax_year_entry = ctk.CTkEntry(tax_settings_frame, width=200, placeholder_text="2024")
        self.tax_year_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(tax_settings_frame, text="申告区分:").pack(pady=5)
        self.filing_type_var = tk.StringVar(value="青色申告")
        self.filing_combo = ctk.CTkComboBox(tax_settings_frame, values=["青色申告", "白色申告"], width=200)
        self.filing_combo.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(tax_settings_frame, text="事業種別:").pack(pady=5)
        self.business_type_var = tk.StringVar()
        self.business_type_entry = ctk.CTkEntry(tax_settings_frame, width=400)
        self.business_type_entry.pack(pady=5)
        
        # 還付先口座情報セクション
        bank_title = ctk.CTkLabel(scrollable_frame, text="還付先口座情報", font=ctk.CTkFont(size=16, weight="bold"))
        bank_title.pack(pady=(20, 5))
        
        bank_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        bank_frame.pack(padx=20, pady=10, fill="x")
        
        row = 0
        ctk.CTkLabel(bank_frame, text="金融機関名:").pack(pady=5)
        self.bank_name_var = tk.StringVar()
        self.bank_name_entry = ctk.CTkEntry(bank_frame, width=300)
        self.bank_name_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(bank_frame, text="支店名:").pack(pady=5)
        self.branch_name_var = tk.StringVar()
        self.branch_name_entry = ctk.CTkEntry(bank_frame, width=300)
        self.branch_name_entry.pack(pady=5)
        
        row += 1
        ctk.CTkLabel(bank_frame, text="口座番号:").pack(pady=5)
        self.account_number_var = tk.StringVar()
        self.account_number_entry = ctk.CTkEntry(bank_frame, width=200)
        self.account_number_entry.pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_transaction_tab(self):
        frame = ctk.CTkFrame(self.tabview.tab("収支入力"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.transaction_manager = TransactionManager(frame, self.tax_data)
        
    def setup_deduction_tab(self):
        frame = ctk.CTkFrame(self.tabview.tab("所得控除"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(frame)
        scrollbar = tk.ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 基本的な控除セクション
        basic_title = ctk.CTkLabel(scrollable_frame, text="基本的な控除", font=ctk.CTkFont(size=16, weight="bold"))
        basic_title.pack(pady=(10, 5))
        
        basic_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        basic_frame.pack(padx=20, pady=10, fill="x")
        
        self.basic_deduction_var = tk.BooleanVar(value=True)
        ctk.CTkCheckbutton(basic_frame, text="基礎控除 (480,000円)", 
                       variable=self.basic_deduction_var).pack(pady=5)
        
        self.spouse_deduction_var = tk.BooleanVar()
        ctk.CTkCheckbutton(basic_frame, text="配偶者控除", 
                       variable=self.spouse_deduction_var).pack(pady=5)
        
        ctk.CTkLabel(basic_frame, text="配偶者所得:").pack(pady=5)
        self.spouse_income_var = tk.StringVar()
        self.spouse_income_entry = ctk.CTkEntry(basic_frame, width=200)
        self.spouse_income_entry.pack(pady=5)
        ctk.CTkLabel(basic_frame, text="円").pack(pady=5)
        
        # 保険料控除セクション
        insurance_title = ctk.CTkLabel(scrollable_frame, text="保険料控除", font=ctk.CTkFont(size=16, weight="bold"))
        insurance_title.pack(pady=(20, 5))
        
        insurance_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        insurance_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(insurance_frame, text="社会保険料:").pack(pady=5)
        self.social_insurance_var = tk.StringVar()
        self.social_insurance_entry = ctk.CTkEntry(insurance_frame, width=200)
        self.social_insurance_entry.pack(pady=5)
        ctk.CTkLabel(insurance_frame, text="円").pack(pady=5)
        
        ctk.CTkLabel(insurance_frame, text="生命保険料:").pack(pady=5)
        self.life_insurance_var = tk.StringVar()
        self.life_insurance_entry = ctk.CTkEntry(insurance_frame, width=200)
        self.life_insurance_entry.pack(pady=5)
        ctk.CTkLabel(insurance_frame, text="円").pack(pady=5)
        
        ctk.CTkLabel(insurance_frame, text="地震保険料:").pack(pady=5)
        self.earthquake_insurance_var = tk.StringVar()
        self.earthquake_insurance_entry = ctk.CTkEntry(insurance_frame, width=200)
        self.earthquake_insurance_entry.pack(pady=5)
        ctk.CTkLabel(insurance_frame, text="円").pack(pady=5)
        
        # その他の控除セクション
        other_title = ctk.CTkLabel(scrollable_frame, text="その他の控除", font=ctk.CTkFont(size=16, weight="bold"))
        other_title.pack(pady=(20, 5))
        
        other_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        other_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(other_frame, text="医療費:").pack(pady=5)
        self.medical_expense_var = tk.StringVar()
        self.medical_expense_entry = ctk.CTkEntry(other_frame, width=200)
        self.medical_expense_entry.pack(pady=5)
        ctk.CTkLabel(other_frame, text="円").pack(pady=5)
        
        ctk.CTkLabel(other_frame, text="寄付金:").pack(pady=5)
        self.donation_var = tk.StringVar()
        self.donation_entry = ctk.CTkEntry(other_frame, width=200)
        self.donation_entry.pack(pady=5)
        ctk.CTkLabel(other_frame, text="円").pack(pady=5)
        
        ctk.CTkLabel(other_frame, text="住宅ローン控除:").pack(pady=5)
        self.home_loan_var = tk.StringVar()
        self.home_loan_entry = ctk.CTkEntry(other_frame, width=200)
        self.home_loan_entry.pack(pady=5)
        ctk.CTkLabel(other_frame, text="円").pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_calculation_tab(self):
        frame = ctk.CTkFrame(self.tabview.tab("税額計算"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        calc_title = ctk.CTkLabel(frame, text="計算結果", font=ctk.CTkFont(size=18, weight="bold"))
        calc_title.pack(pady=(10, 5))
        
        calc_frame = ctk.CTkFrame(frame, corner_radius=10)
        calc_frame.pack(padx=20, pady=10, fill="x")
        
        button_frame = ctk.CTkFrame(calc_frame)
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text="税額計算実行", command=self.calculate_taxes).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="詳細表示", command=self.show_detailed_calculation).pack(side=tk.LEFT, padx=5)
        
        result_frame = ctk.CTkFrame(calc_frame)
        result_frame.pack(pady=10)
        
        self.total_income_label = ctk.CTkLabel(result_frame, text="総所得金額: -", font=('Arial', 12))
        self.total_income_label.pack(pady=5)
        
        self.total_deduction_label = ctk.CTkLabel(result_frame, text="所得控除合計: -", font=('Arial', 12))
        self.total_deduction_label.pack(pady=5)
        
        self.taxable_income_label = ctk.CTkLabel(result_frame, text="課税所得金額: -", font=('Arial', 12))
        self.taxable_income_label.pack(pady=5)
        
        self.income_tax_label = ctk.CTkLabel(result_frame, text="所得税額: -", font=('Arial', 12))
        self.income_tax_label.pack(pady=5)
        
        self.resident_tax_label = ctk.CTkLabel(result_frame, text="住民税額: -", font=('Arial', 12))
        self.resident_tax_label.pack(pady=5)
        
        self.total_tax_label = ctk.CTkLabel(result_frame, text="税額合計: -", font=('Arial', 12, 'bold'))
        self.total_tax_label.pack(pady=10)
        
        self.payment_label = ctk.CTkLabel(result_frame, text="納税/還付: -", font=('Arial', 12, 'bold'))
        self.payment_label.pack(pady=5)
        
    def setup_depreciation_tab(self):
        """減価償却タブの設定"""
        frame = ctk.CTkFrame(self.tabview.tab("減価償却"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 資産入力フォーム
        input_title = ctk.CTkLabel(frame, text="資産情報入力", font=ctk.CTkFont(size=18, weight="bold"))
        input_title.pack(pady=(10, 5))
        
        input_frame = ctk.CTkFrame(frame, corner_radius=10)
        input_frame.pack(padx=20, pady=10, fill="x")

        # 資産名
        asset_name_frame = ctk.CTkFrame(input_frame)
        asset_name_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(asset_name_frame, text="資産名:", width=100).pack(side="left", padx=10)
        self.asset_name_var = tk.StringVar()
        self.asset_name_entry = ctk.CTkEntry(asset_name_frame, width=200)
        self.asset_name_entry.pack(side="left", padx=10)

        # 資産カテゴリ
        category_frame = ctk.CTkFrame(input_frame)
        category_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(category_frame, text="カテゴリ:", width=100).pack(side="left", padx=10)
        self.asset_category_var = tk.StringVar()
        categories = self.depreciation_calculator.get_asset_categories()
        self.category_combo = ctk.CTkComboBox(category_frame, values=categories, width=200)
        self.category_combo.pack(side="left", padx=10)

        # 購入日
        date_frame = ctk.CTkFrame(input_frame)
        date_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(date_frame, text="購入日:", width=100).pack(side="left", padx=10)
        
        if CALENDAR_AVAILABLE:
            self.purchase_date_entry = DateEntry(
                date_frame,
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day,
                date_pattern='yyyy-mm-dd',
                locale='ja_JP'
            )
            self.purchase_date_entry.pack(side="left", padx=10)
        else:
            self.purchase_date_var = tk.StringVar()
            self.purchase_date_entry = ctk.CTkEntry(date_frame, width=200, placeholder_text="YYYY-MM-DD")
            self.purchase_date_entry.pack(side="left", padx=10)
            self.purchase_date_var.set(datetime.now().strftime("%Y-%m-%d"))

        # 購入価格
        price_frame = ctk.CTkFrame(input_frame)
        price_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(price_frame, text="購入価格:", width=100).pack(side="left", padx=10)
        self.asset_price_var = tk.StringVar()
        self.asset_price_entry = ctk.CTkEntry(price_frame, width=200, placeholder_text="円")
        self.asset_price_entry.pack(side="left", padx=10)

        # 耐用年数
        years_frame = ctk.CTkFrame(input_frame)
        years_frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(years_frame, text="耐用年数:", width=100).pack(side="left", padx=10)
        self.useful_life_var = tk.StringVar()
        self.useful_life_entry = ctk.CTkEntry(years_frame, width=200, placeholder_text="年")
        self.useful_life_entry.pack(side="left", padx=10)

        # ボタンフレーム
        button_frame = ctk.CTkFrame(input_frame)
        button_frame.pack(pady=20, padx=20)
        
        ctk.CTkButton(button_frame, text="資産を追加", command=self.add_asset, fg_color="#4CAF50").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="減価償却計算", command=self.calculate_depreciation, fg_color="#2196F3").pack(side="left", padx=5)

        # 資産一覧
        assets_title = ctk.CTkLabel(frame, text="資産一覧", font=ctk.CTkFont(size=18, weight="bold"))
        assets_title.pack(pady=(20, 5))
        
        assets_frame = ctk.CTkFrame(frame, corner_radius=10)
        assets_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # 資産一覧表示
        self.assets_text = ctk.CTkTextbox(assets_frame, height=200)
        self.assets_text.pack(pady=10, padx=20, fill="both", expand=True)

        # 計算結果表示
        result_title = ctk.CTkLabel(frame, text="減価償却計算結果", font=ctk.CTkFont(size=18, weight="bold"))
        result_title.pack(pady=(20, 5))
        
        result_frame = ctk.CTkFrame(frame, corner_radius=10)
        result_frame.pack(padx=20, pady=10, fill="x")

        self.depreciation_result_label = ctk.CTkLabel(result_frame, text="減価償却額: -", font=ctk.CTkFont(size=16, weight="bold"))
        self.depreciation_result_label.pack(pady=10)

        # 初期データ読み込み
        self.refresh_assets_list()
        
        # 初期値設定
        categories = self.depreciation_calculator.get_asset_categories()
        if categories:
            self.asset_category_var.set(categories[0])

    def setup_report_tab(self):
        frame = ctk.CTkFrame(self.tabview.tab("レポート"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.report_generator = ReportGenerator(frame, self.tax_data)
        
    def collect_data(self):
        try:
            personal_info = PersonalInfo(
                name=self.name_entry.get(),
                name_kana=self.name_kana_entry.get(),
                address=self.address_entry.get(),
                postal_code=self.postal_code_entry.get(),
                phone=self.phone_entry.get(),
                birthdate=self.birthdate_entry.get(),
                occupation=self.occupation_entry.get(),
                spouse_income=float(self.spouse_income_entry.get() or 0)
            )
            
            bank_account = BankAccount(
                bank_name=self.bank_name_entry.get(),
                branch_name=self.branch_name_entry.get(),
                account_type="普通",
                account_number=self.account_number_entry.get(),
                account_holder=self.name_entry.get()
            )
            
            tax_settings = TaxSettings(
                tax_year=int(self.tax_year_entry.get()),
                filing_type=self.filing_combo.get(),
                business_type=self.business_type_entry.get()
            )
            
            deductions = Deductions(
                basic_deduction=self.basic_deduction_var.get(),
                spouse_deduction=self.spouse_deduction_var.get(),
                social_insurance_premium=float(self.social_insurance_entry.get() or 0),
                life_insurance_premium=float(self.life_insurance_entry.get() or 0),
                earthquake_insurance_premium=float(self.earthquake_insurance_entry.get() or 0),
                medical_expense=float(self.medical_expense_entry.get() or 0),
                donation=float(self.donation_entry.get() or 0),
                home_loan_deduction=float(self.home_loan_entry.get() or 0)
            )
            
            self.tax_data.personal_info = personal_info
            self.tax_data.bank_account = bank_account
            self.tax_data.tax_settings = tax_settings
            self.tax_data.deductions = deductions
            self.tax_data.updated_at = datetime.now()
            
            self.is_modified = True
            self.update_status()
            
        except ValueError as e:
            messagebox.showerror("入力エラー", "数値の入力に誤りがあります。")
            
    def load_data_to_ui(self):
        info = self.tax_data.personal_info
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, info.name)
        self.name_kana_entry.delete(0, tk.END)
        self.name_kana_entry.insert(0, info.name_kana)
        self.address_entry.delete(0, tk.END)
        self.address_entry.insert(0, info.address)
        self.postal_code_entry.delete(0, tk.END)
        self.postal_code_entry.insert(0, info.postal_code)
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, info.phone)
        self.birthdate_entry.delete(0, tk.END)
        self.birthdate_entry.insert(0, info.birthdate)
        self.occupation_entry.delete(0, tk.END)
        self.occupation_entry.insert(0, info.occupation)
        self.spouse_income_entry.delete(0, tk.END)
        self.spouse_income_entry.insert(0, str(info.spouse_income))
        
        bank = self.tax_data.bank_account
        self.bank_name_entry.delete(0, tk.END)
        self.bank_name_entry.insert(0, bank.bank_name)
        self.branch_name_entry.delete(0, tk.END)
        self.branch_name_entry.insert(0, bank.branch_name)
        self.account_number_entry.delete(0, tk.END)
        self.account_number_entry.insert(0, bank.account_number)
        
        settings = self.tax_data.tax_settings
        self.tax_year_entry.delete(0, tk.END)
        self.tax_year_entry.insert(0, str(settings.tax_year))
        self.filing_combo.set(settings.filing_type)
        self.business_type_entry.delete(0, tk.END)
        self.business_type_entry.insert(0, settings.business_type)
        
        deductions = self.tax_data.deductions
        self.basic_deduction_var.set(deductions.basic_deduction)
        self.spouse_deduction_var.set(deductions.spouse_deduction)
        self.social_insurance_entry.delete(0, tk.END)
        self.social_insurance_entry.insert(0, str(deductions.social_insurance_premium))
        self.life_insurance_entry.delete(0, tk.END)
        self.life_insurance_entry.insert(0, str(deductions.life_insurance_premium))
        self.earthquake_insurance_entry.delete(0, tk.END)
        self.earthquake_insurance_entry.insert(0, str(deductions.earthquake_insurance_premium))
        self.medical_expense_entry.delete(0, tk.END)
        self.medical_expense_entry.insert(0, str(deductions.medical_expense))
        self.donation_entry.delete(0, tk.END)
        self.donation_entry.insert(0, str(deductions.donation))
        self.home_loan_entry.delete(0, tk.END)
        self.home_loan_entry.insert(0, str(deductions.home_loan_deduction))
        
        self.transaction_manager.refresh_transaction_list()
        
        if hasattr(self.tax_data, 'calculation_result') and self.tax_data.calculation_result:
            self.update_calculation_display()
            
    def calculate_taxes(self):
        try:
            self.collect_data()
            
            calc_result = self.tax_calculator.calculate_all_taxes(self.tax_data)
            
            from models import TaxCalculationResult
            self.tax_data.calculation_result = TaxCalculationResult(**calc_result)
            
            self.update_calculation_display()
            
            self.calculation_status.config(text="税額計算済み", text_color="green")
            
            messagebox.showinfo("計算完了", "税額計算が完了しました。")
            
        except Exception as e:
            messagebox.showerror("計算エラー", f"税額計算中にエラーが発生しました: {str(e)}")
            
    def update_calculation_display(self):
        result = self.tax_data.calculation_result
        
        self.total_income_label.config(text=f"総所得金額: {result.total_income:,.0f}円")
        self.total_deduction_label.config(text=f"所得控除合計: {result.total_deductions:,.0f}円")
        self.taxable_income_label.config(text=f"課税所得金額: {result.taxable_income:,.0f}円")
        self.income_tax_label.config(text=f"所得税額: {result.income_tax:,.0f}円")
        self.resident_tax_label.config(text=f"住民税額: {result.resident_tax:,.0f}円")
        self.total_tax_label.config(text=f"税額合計: {result.total_tax:,.0f}円")
        
        if result.tax_due > 0:
            self.payment_label.config(text=f"納税額: {result.tax_due:,.0f}円", text_color="red")
        else:
            self.payment_label.config(text=f"還付額: {result.refund_amount:,.0f}円", text_color="green")
            
    def new_file(self):
        if self.check_unsaved_changes():
            self.tax_data = TaxReturnData()
            self.current_filename = None
            self.is_modified = False
            self.load_data_to_ui()
            self.update_status()
            
    def open_file(self):
        if self.check_unsaved_changes():
            filename = filedialog.askopenfilename(
                title="確定申告データを開く",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                tax_data = self.data_manager.load_data(filename)
                if tax_data:
                    self.tax_data = tax_data
                    self.current_filename = filename
                    self.is_modified = False
                    self.load_data_to_ui()
                    self.update_status()
                    self.data_manager.add_recent_file(filename)
                    
    def save_file(self):
        if self.current_filename:
            self.collect_data()
            if self.data_manager.save_data(self.tax_data, self.current_filename):
                self.is_modified = False
                self.update_status()
                messagebox.showinfo("保存完了", "ファイルが保存されました。")
        else:
            self.save_as_file()
            
    def save_as_file(self):
        filename = filedialog.asksaveasfilename(
            title="名前を付けて保存",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.collect_data()
            if self.data_manager.save_data(self.tax_data, filename):
                self.current_filename = filename
                self.is_modified = False
                self.update_status()
                self.data_manager.add_recent_file(filename)
                messagebox.showinfo("保存完了", "ファイルが保存されました。")
                
    def export_tax_return_pdf(self):
        if not self.tax_data.calculation_result or not self.tax_data.calculation_result.total_tax:
            messagebox.showwarning("警告", "まず税額計算を実行してください。")
            return
            
        filename = filedialog.asksaveasfilename(
            title="確定申告書PDFを保存",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.collect_data()
            if self.pdf_generator.generate_tax_return_pdf(self.tax_data, filename):
                messagebox.showinfo("出力完了", "確定申告書PDFが出力されました。")
                
    def export_monthly_report_pdf(self):
        filename = filedialog.asksaveasfilename(
            title="月次レポートPDFを保存",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            if self.pdf_generator.generate_monthly_report(self.tax_data, filename):
                messagebox.showinfo("出力完了", "月次レポートPDFが出力されました。")
                
    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="CSVファイルを保存",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            if self.data_manager.export_to_csv(self.tax_data, filename):
                messagebox.showinfo("出力完了", "CSVファイルが出力されました。")
                
    def check_unsaved_changes(self):
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "未保存の変更",
                "未保存の変更があります。保存しますか？"
            )
            if result is True:
                self.save_file()
                return not self.is_modified
            elif result is False:
                return True
            else:
                return False
        return True
        
    def update_status(self):
        if self.current_filename:
            filename = os.path.basename(self.current_filename)
            status_text = f"{filename}"
        else:
            status_text = "新規ファイル"
            
        if self.is_modified:
            status_text += " *"
            
        self.status_label.config(text=status_text)
        
    def update_recent_files_menu(self, menu):
        menu.delete(0, tk.END)
        recent_files = self.data_manager.get_recent_files()
        
        if recent_files:
            for filepath in recent_files:
                filename = os.path.basename(filepath)
                menu.add_command(
                    label=filename,
                    command=lambda path=filepath: self.open_recent_file(path)
                )
        else:
            menu.add_command(label="(なし)", state=tk.DISABLED)
            
    def open_recent_file(self, filepath):
        if self.check_unsaved_changes():
            tax_data = self.data_manager.load_data(filepath)
            if tax_data:
                self.tax_data = tax_data
                self.current_filename = filepath
                self.is_modified = False
                self.load_data_to_ui()
                self.update_status()
                
    def show_detailed_calculation(self):
        if not self.tax_data.calculation_result:
            messagebox.showwarning("警告", "まず税額計算を実行してください。")
            return
            
        detail_window = tk.Toplevel(self.root)
        detail_window.title("詳細計算結果")
        detail_window.geometry("600x500")
        
    def show_tax_simulation(self):
        messagebox.showinfo("シミュレーション", "税額シミュレーション機能は開発中です。")
        
    def show_backup_manager(self):
        messagebox.showinfo("バックアップ管理", "バックアップ管理機能は開発中です。")
        
    def show_settings(self):
        messagebox.showinfo("設定", "設定画面は開発中です。")
        
    def validate_data(self):
        errors = []
        
        if not self.name_var.get().strip():
            errors.append("氏名が入力されていません。")
            
        if not self.address_var.get().strip():
            errors.append("住所が入力されていません。")
            
        if len(self.tax_data.transactions) == 0:
            errors.append("取引データが入力されていません。")
            
        if errors:
            messagebox.showerror("データ検証エラー", "\n".join(errors))
        else:
            messagebox.showinfo("データ検証", "データに問題はありません。")
            
    def show_help(self):
        help_text = """
確定申告支援アプリケーション ヘルプ

【基本的な使い方】
1. 基本情報タブで個人情報を入力
2. 収支入力タブで収入・支出データを入力
3. 所得控除タブで控除項目を入力
4. 税額計算タブで計算を実行
5. レポートタブで各種レポートを確認

【ファイル操作】
- Ctrl+N: 新規作成
- Ctrl+O: ファイルを開く
- Ctrl+S: ファイルを保存

【注意事項】
- このアプリケーションは計算支援ツールです
- 正式な申告前に税理士等の専門家にご相談ください
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("ヘルプ")
        help_window.geometry("600x400")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
    def show_about(self):
        about_text = f"""
確定申告支援アプリケーション
Version 2.0

開発: AI Assistant
作成日: {datetime.now().strftime('%Y年%m月%d日')}

このソフトウェアは確定申告の計算を支援するツールです。
実際の申告には税理士等の専門家にご相談することをお勧めします。
        """
        
        messagebox.showinfo("バージョン情報", about_text)
        
    def setup_auto_save(self):
        def auto_save():
            if self.is_modified and self.current_filename:
                self.collect_data()
                self.data_manager.auto_save(self.tax_data, self.current_filename)
            
            self.root.after(300000, auto_save)  # 5分ごと
            
        self.root.after(300000, auto_save)
        
    def on_closing(self):
        if self.check_unsaved_changes():
            settings = self.data_manager.get_settings()
            settings['window_geometry'] = self.root.geometry()
            self.data_manager.save_settings(settings)
            self.root.destroy()

    def add_asset(self):
        """資産を追加"""
        try:
            # 入力値を取得
            name = self.asset_name_entry.get().strip()
            category = self.category_combo.get()
            price_str = self.asset_price_entry.get().strip()
            useful_life_str = self.useful_life_entry.get().strip()
            
            # 入力チェック
            if not name:
                messagebox.showwarning("警告", "資産名を入力してください。")
                return
                
            if not category:
                messagebox.showwarning("警告", "カテゴリを選択してください。")
                return
                
            if not price_str:
                messagebox.showwarning("警告", "購入価格を入力してください。")
                return
                
            if not useful_life_str:
                messagebox.showwarning("警告", "耐用年数を入力してください。")
                return
            
            # 数値変換
            price = float(price_str)
            useful_life = int(useful_life_str)
            
            # 購入日を取得
            if CALENDAR_AVAILABLE:
                purchase_date = self.purchase_date_entry.get_date().strftime("%Y-%m-%d")
            else:
                purchase_date = self.purchase_date_var.get()
            
            # 資産を追加
            asset = self.depreciation_calculator.add_asset(
                name=name,
                category=category,
                purchase_date=purchase_date,
                purchase_price=price,
                useful_life=useful_life
            )
            
            # 入力フィールドをクリア
            self.asset_name_entry.delete(0, tk.END)
            self.asset_price_entry.delete(0, tk.END)
            self.useful_life_entry.delete(0, tk.END)
            
            # 資産一覧を更新
            self.refresh_assets_list()
            
            messagebox.showinfo("追加完了", f"資産 '{name}' が追加されました。")
            
        except ValueError as e:
            messagebox.showerror("入力エラー", "数値の入力に誤りがあります。")
        except Exception as e:
            messagebox.showerror("エラー", f"資産追加中にエラーが発生しました: {str(e)}")

    def calculate_depreciation(self):
        """減価償却計算を実行"""
        try:
            # 申告年度を取得
            tax_year = self.tax_year_entry.get()
            
            # 減価償却計算を実行
            total_depreciation = self.depreciation_calculator.get_total_depreciation_for_year(tax_year)
            
            # 結果を表示
            self.depreciation_result_label.configure(
                text=f"減価償却額: ¥{total_depreciation:,.0f}",
                text_color="#4CAF50"
            )
            
            # ダッシュボードを更新
            if hasattr(self, 'income_card'):
                # 減価償却費を所得控除として反映
                self.update_dashboard_with_depreciation(total_depreciation)
            
            messagebox.showinfo("計算完了", f"{tax_year}年の減価償却額: ¥{total_depreciation:,.0f}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"減価償却計算中にエラーが発生しました: {str(e)}")

    def refresh_assets_list(self):
        """資産一覧を更新"""
        try:
            self.assets_text.delete("1.0", tk.END)
            
            if not self.depreciation_calculator.assets:
                self.assets_text.insert(tk.END, "登録された資産はありません。")
                return
            
            # ヘッダー
            header = f"{'資産名':<20} {'カテゴリ':<15} {'購入日':<12} {'購入価格':<12} {'耐用年数':<8} {'現在価値':<12}\n"
            self.assets_text.insert(tk.END, header)
            self.assets_text.insert(tk.END, "-" * 80 + "\n")
            
            # 資産一覧
            for asset in self.depreciation_calculator.assets:
                current_year = datetime.now().year
                depreciation_info = self.depreciation_calculator.calculate_depreciation(asset, current_year)
                
                line = f"{asset['name']:<20} {asset['category']:<15} {asset['purchase_date']:<12} "
                line += f"¥{asset['purchase_price']:>10,} {asset['useful_life']:>6}年 "
                line += f"¥{depreciation_info['current_value']:>10,}\n"
                
                self.assets_text.insert(tk.END, line)
                
        except Exception as e:
            self.assets_text.delete("1.0", tk.END)
            self.assets_text.insert(tk.END, f"資産一覧の更新中にエラーが発生しました: {str(e)}")

    def update_dashboard_with_depreciation(self, depreciation_amount):
        """ダッシュボードを減価償却費で更新"""
        try:
            # 減価償却費を所得控除として反映
            if hasattr(self, 'income_card') and hasattr(self, 'tax_card'):
                # 所得控除の更新（簡易版）
                current_income = self.income_card.cget("text")
                if current_income != "未入力":
                    # 実際の実装では、所得控除の計算ロジックを更新する必要があります
                    pass
        except Exception as e:
            print(f"ダッシュボード更新エラー: {e}")

    def show_depreciation_calculator(self):
        """減価償却計算ウィンドウを表示"""
        # 既にタブで表示されているので、タブをアクティブにする
        self.tabview.set("減価償却")

def main():
    try:
        root = ctk.CTk()
        app = TaxReturnApp(root)
        
        settings = app.data_manager.get_settings()
        if settings.get('window_geometry'):
            root.geometry(settings['window_geometry'])
            
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("起動エラー", f"アプリケーションの起動中にエラーが発生しました: {str(e)}")
        
if __name__ == "__main__":
    main()