import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
import threading
import os
import sys
from datetime import datetime

from models import TaxReturnData, PersonalInfo, BankAccount, TaxSettings, Deductions
from transaction_manager import TransactionManager
from calculators import TaxCalculator
from pdf_generator import PDFGenerator
from data_manager import DataManager
from reports import ReportGenerator

class TaxReturnApp:
    def __init__(self, root):
        self.root = root
        self.root.title("確定申告支援アプリケーション - Tax Return Helper")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        self.tax_data = TaxReturnData()
        self.data_manager = DataManager()
        self.tax_calculator = TaxCalculator()
        self.pdf_generator = PDFGenerator()
        
        self.current_filename = None
        self.is_modified = False
        
        self.setup_styles()
        self.create_menu()
        self.setup_ui()
        self.setup_auto_save()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), foreground='#34495e')
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Error.TLabel', foreground='#e74c3c')
        
    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="新規作成", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="開く", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="名前を付けて保存", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        
        recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近使ったファイル", menu=recent_menu)
        self.update_recent_files_menu(recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)
        
        calc_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="計算", menu=calc_menu)
        calc_menu.add_command(label="税額計算", command=self.calculate_taxes)
        calc_menu.add_command(label="シミュレーション", command=self.show_tax_simulation)
        
        output_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="出力", menu=output_menu)
        output_menu.add_command(label="確定申告書PDF", command=self.export_tax_return_pdf)
        output_menu.add_command(label="月次レポートPDF", command=self.export_monthly_report_pdf)
        output_menu.add_command(label="CSV出力", command=self.export_csv)
        
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="バックアップ管理", command=self.show_backup_manager)
        tools_menu.add_command(label="設定", command=self.show_settings)
        tools_menu.add_command(label="データ検証", command=self.validate_data)
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self.show_help)
        help_menu.add_command(label="バージョン情報", command=self.show_about)
        
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as_file())
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(header_frame, text="確定申告支援アプリケーション", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        self.status_label = ttk.Label(header_frame, text="新規ファイル", style='Heading.TLabel')
        self.status_label.grid(row=0, column=1, sticky=tk.E)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.setup_personal_info_tab()
        self.setup_transaction_tab()
        self.setup_deduction_tab()
        self.setup_calculation_tab()
        self.setup_report_tab()
        
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)
        
        self.modification_status = ttk.Label(status_frame, text="")
        self.modification_status.grid(row=0, column=0, sticky=tk.W)
        
        self.calculation_status = ttk.Label(status_frame, text="税額未計算")
        self.calculation_status.grid(row=0, column=1, sticky=tk.E)
        
    def setup_personal_info_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="基本情報")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        personal_frame = ttk.LabelFrame(scrollable_frame, text="個人情報", padding="10")
        personal_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        row = 0
        ttk.Label(personal_frame, text="氏名*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.name_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(personal_frame, text="フリガナ:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_kana_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.name_kana_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(personal_frame, text="住所*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.address_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.address_var, width=60).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(personal_frame, text="郵便番号:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.postal_code_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.postal_code_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(personal_frame, text="電話番号:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.phone_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(personal_frame, text="生年月日:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.birthdate_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.birthdate_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(personal_frame, text="職業:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.occupation_var = tk.StringVar()
        ttk.Entry(personal_frame, textvariable=self.occupation_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        tax_settings_frame = ttk.LabelFrame(scrollable_frame, text="申告設定", padding="10")
        tax_settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        row = 0
        ttk.Label(tax_settings_frame, text="申告年度:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tax_year_var = tk.IntVar(value=datetime.now().year)
        ttk.Spinbox(tax_settings_frame, from_=2020, to=2030, textvariable=self.tax_year_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(tax_settings_frame, text="申告区分:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.filing_type_var = tk.StringVar(value="青色申告")
        filing_combo = ttk.Combobox(tax_settings_frame, textvariable=self.filing_type_var, width=20)
        filing_combo['values'] = ["青色申告", "白色申告"]
        filing_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(tax_settings_frame, text="事業種別:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.business_type_var = tk.StringVar()
        ttk.Entry(tax_settings_frame, textvariable=self.business_type_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        bank_frame = ttk.LabelFrame(scrollable_frame, text="還付先口座情報", padding="10")
        bank_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        row = 0
        ttk.Label(bank_frame, text="金融機関名:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.bank_name_var = tk.StringVar()
        ttk.Entry(bank_frame, textvariable=self.bank_name_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(bank_frame, text="支店名:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.branch_name_var = tk.StringVar()
        ttk.Entry(bank_frame, textvariable=self.branch_name_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        row += 1
        ttk.Label(bank_frame, text="口座番号:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.account_number_var = tk.StringVar()
        ttk.Entry(bank_frame, textvariable=self.account_number_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_transaction_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="収支入力")
        self.transaction_manager = TransactionManager(frame, self.tax_data)
        
    def setup_deduction_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="所得控除")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        basic_frame = ttk.LabelFrame(scrollable_frame, text="基本的な控除", padding="10")
        basic_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        self.basic_deduction_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(basic_frame, text="基礎控除 (480,000円)", 
                       variable=self.basic_deduction_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.spouse_deduction_var = tk.BooleanVar()
        ttk.Checkbutton(basic_frame, text="配偶者控除", 
                       variable=self.spouse_deduction_var).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(basic_frame, text="配偶者所得:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.spouse_income_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.spouse_income_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(basic_frame, text="円").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        insurance_frame = ttk.LabelFrame(scrollable_frame, text="保険料控除", padding="10")
        insurance_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(insurance_frame, text="社会保険料:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.social_insurance_var = tk.StringVar()
        ttk.Entry(insurance_frame, textvariable=self.social_insurance_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(insurance_frame, text="円").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(insurance_frame, text="生命保険料:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.life_insurance_var = tk.StringVar()
        ttk.Entry(insurance_frame, textvariable=self.life_insurance_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(insurance_frame, text="円").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(insurance_frame, text="地震保険料:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.earthquake_insurance_var = tk.StringVar()
        ttk.Entry(insurance_frame, textvariable=self.earthquake_insurance_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(insurance_frame, text="円").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        other_frame = ttk.LabelFrame(scrollable_frame, text="その他の控除", padding="10")
        other_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(other_frame, text="医療費:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.medical_expense_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.medical_expense_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(other_frame, text="円").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(other_frame, text="寄付金:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.donation_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.donation_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(other_frame, text="円").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(other_frame, text="住宅ローン控除:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.home_loan_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.home_loan_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(other_frame, text="円").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_calculation_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="税額計算")
        
        calc_frame = ttk.LabelFrame(frame, text="計算結果", padding="10")
        calc_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        button_frame = ttk.Frame(calc_frame)
        button_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="税額計算実行", command=self.calculate_taxes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="詳細表示", command=self.show_detailed_calculation).pack(side=tk.LEFT, padx=5)
        
        result_frame = ttk.Frame(calc_frame)
        result_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.total_income_label = ttk.Label(result_frame, text="総所得金額: -", font=('Arial', 12))
        self.total_income_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.total_deduction_label = ttk.Label(result_frame, text="所得控除合計: -", font=('Arial', 12))
        self.total_deduction_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.taxable_income_label = ttk.Label(result_frame, text="課税所得金額: -", font=('Arial', 12))
        self.taxable_income_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.income_tax_label = ttk.Label(result_frame, text="所得税額: -", font=('Arial', 12))
        self.income_tax_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.resident_tax_label = ttk.Label(result_frame, text="住民税額: -", font=('Arial', 12))
        self.resident_tax_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.total_tax_label = ttk.Label(result_frame, text="税額合計: -", font=('Arial', 12, 'bold'))
        self.total_tax_label.grid(row=5, column=0, sticky=tk.W, pady=10)
        
        self.payment_label = ttk.Label(result_frame, text="納税/還付: -", font=('Arial', 12, 'bold'))
        self.payment_label.grid(row=6, column=0, sticky=tk.W, pady=5)
        
    def setup_report_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="レポート")
        self.report_generator = ReportGenerator(frame, self.tax_data)
        
    def collect_data(self):
        try:
            personal_info = PersonalInfo(
                name=self.name_var.get(),
                name_kana=self.name_kana_var.get(),
                address=self.address_var.get(),
                postal_code=self.postal_code_var.get(),
                phone=self.phone_var.get(),
                birthdate=self.birthdate_var.get(),
                occupation=self.occupation_var.get(),
                spouse_income=float(self.spouse_income_var.get() or 0)
            )
            
            bank_account = BankAccount(
                bank_name=self.bank_name_var.get(),
                branch_name=self.branch_name_var.get(),
                account_type="普通",
                account_number=self.account_number_var.get(),
                account_holder=self.name_var.get()
            )
            
            tax_settings = TaxSettings(
                tax_year=self.tax_year_var.get(),
                filing_type=self.filing_type_var.get(),
                business_type=self.business_type_var.get()
            )
            
            deductions = Deductions(
                basic_deduction=self.basic_deduction_var.get(),
                spouse_deduction=self.spouse_deduction_var.get(),
                social_insurance_premium=float(self.social_insurance_var.get() or 0),
                life_insurance_premium=float(self.life_insurance_var.get() or 0),
                earthquake_insurance_premium=float(self.earthquake_insurance_var.get() or 0),
                medical_expense=float(self.medical_expense_var.get() or 0),
                donation=float(self.donation_var.get() or 0),
                home_loan_deduction=float(self.home_loan_var.get() or 0)
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
        self.name_var.set(info.name)
        self.name_kana_var.set(info.name_kana)
        self.address_var.set(info.address)
        self.postal_code_var.set(info.postal_code)
        self.phone_var.set(info.phone)
        self.birthdate_var.set(info.birthdate)
        self.occupation_var.set(info.occupation)
        self.spouse_income_var.set(str(info.spouse_income))
        
        bank = self.tax_data.bank_account
        self.bank_name_var.set(bank.bank_name)
        self.branch_name_var.set(bank.branch_name)
        self.account_number_var.set(bank.account_number)
        
        settings = self.tax_data.tax_settings
        self.tax_year_var.set(settings.tax_year)
        self.filing_type_var.set(settings.filing_type)
        self.business_type_var.set(settings.business_type)
        
        deductions = self.tax_data.deductions
        self.basic_deduction_var.set(deductions.basic_deduction)
        self.spouse_deduction_var.set(deductions.spouse_deduction)
        self.social_insurance_var.set(str(deductions.social_insurance_premium))
        self.life_insurance_var.set(str(deductions.life_insurance_premium))
        self.earthquake_insurance_var.set(str(deductions.earthquake_insurance_premium))
        self.medical_expense_var.set(str(deductions.medical_expense))
        self.donation_var.set(str(deductions.donation))
        self.home_loan_var.set(str(deductions.home_loan_deduction))
        
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
            
            self.calculation_status.config(text="税額計算済み", style='Success.TLabel')
            
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
            self.payment_label.config(text=f"納税額: {result.tax_due:,.0f}円", foreground='red')
        else:
            self.payment_label.config(text=f"還付額: {result.refund_amount:,.0f}円", foreground='green')
            
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
Version 1.0

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

def main():
    try:
        root = tk.Tk()
        app = TaxReturnApp(root)
        
        settings = app.data_manager.get_settings()
        if settings.get('window_geometry'):
            root.geometry(settings['window_geometry'])
            
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("起動エラー", f"アプリケーションの起動中にエラーが発生しました: {str(e)}")
        
if __name__ == "__main__":
    main()