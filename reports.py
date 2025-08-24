import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from models import TaxReturnData, TransactionType
import seaborn as sns
import numpy as np

plt.rcParams['font.family'] = ['MS Gothic', 'DejaVu Sans']

class ReportGenerator:
    def __init__(self, parent_frame, tax_return_data):
        self.parent_frame = parent_frame
        self.tax_return_data = tax_return_data
        self.setup_ui()
        
    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # レポート設定
        control_title = ctk.CTkLabel(self.main_frame, text="レポート設定", font=ctk.CTkFont(size=16, weight="bold"))
        control_title.pack(pady=(10, 5))
        control_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        control_frame.pack(fill="x", pady=(0, 20))
        
        # レポート種類
        report_type_frame = ctk.CTkFrame(control_frame)
        report_type_frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(report_type_frame, text="レポート種類:", width=100).pack(side="left", padx=10)
        self.report_type_var = tk.StringVar()
        report_combo = ctk.CTkComboBox(report_type_frame, textvariable=self.report_type_var, width=200)
        report_combo['values'] = [
            "月別収支推移",
            "カテゴリ別収入",
            "カテゴリ別支出", 
            "四半期比較",
            "年間サマリー",
            "税額シミュレーション"
        ]
        report_combo.set("月別収支推移")
        report_combo.pack(side="left", padx=10)
        
        # 期間設定
        period_frame = ctk.CTkFrame(control_frame)
        period_frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(period_frame, text="期間:", width=100).pack(side="left", padx=10)
        self.start_date_var = tk.StringVar(value=f"{datetime.now().year}-01-01")
        ctk.CTkEntry(period_frame, textvariable=self.start_date_var, width=120).pack(side="left", padx=5)
        ctk.CTkLabel(period_frame, text="〜").pack(side="left", padx=5)
        self.end_date_var = tk.StringVar(value=f"{datetime.now().year}-12-31")
        ctk.CTkEntry(period_frame, textvariable=self.end_date_var, width=120).pack(side="left", padx=5)
        
        # ボタン
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.pack(pady=20, padx=20)
        
        ctk.CTkButton(button_frame, text="レポート生成", command=self.generate_report, fg_color="#2196F3").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Excel出力", command=self.export_excel, fg_color="#4CAF50").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="PDF出力", command=self.export_pdf, fg_color="#FF9800").pack(side="left", padx=5)
        
        # メインコンテンツエリア
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, pady=10)
        
        # 左側：集計情報と詳細データ
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 集計情報
        summary_title = ctk.CTkLabel(left_frame, text="集計情報", font=ctk.CTkFont(size=14, weight="bold"))
        summary_title.pack(pady=(10, 5))
        summary_frame = ctk.CTkFrame(left_frame, corner_radius=10)
        summary_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.summary_text = ctk.CTkTextbox(summary_frame, height=200)
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 詳細データ
        detail_title = ctk.CTkLabel(left_frame, text="詳細データ", font=ctk.CTkFont(size=14, weight="bold"))
        detail_title.pack(pady=(10, 5))
        detail_frame = ctk.CTkFrame(left_frame, corner_radius=10)
        detail_frame.pack(fill="both", expand=True)
        
        columns = ("項目", "値")
        self.detail_tree = ctk.CTkTreeview(detail_frame, columns=columns, show="headings", height=200)
        
        self.detail_tree.heading("項目", text="項目")
        self.detail_tree.heading("値", text="値")
        self.detail_tree.column("項目", width=200)
        self.detail_tree.column("値", width=150)
        
        self.detail_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 右側：グラフ
        chart_title = ctk.CTkLabel(content_frame, text="グラフ", font=ctk.CTkFont(size=14, weight="bold"))
        chart_title.pack(pady=(10, 5))
        chart_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        chart_frame.pack(side="right", fill="both", expand=True)
        
        self.chart_canvas = None
        self.chart_frame = chart_frame
        
    def generate_report(self):
        try:
            report_type = self.report_type_var.get()
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            
            filtered_transactions = self.tax_return_data.get_transactions_by_date_range(start_date, end_date)
            
            if report_type == "月別収支推移":
                self.generate_monthly_trend_report(filtered_transactions)
            elif report_type == "カテゴリ別収入":
                self.generate_income_category_report(filtered_transactions)
            elif report_type == "カテゴリ別支出":
                self.generate_expense_category_report(filtered_transactions)
            elif report_type == "四半期比較":
                self.generate_quarterly_report(filtered_transactions)
            elif report_type == "年間サマリー":
                self.generate_annual_summary(filtered_transactions)
            elif report_type == "税額シミュレーション":
                self.generate_tax_simulation()
                
        except Exception as e:
            messagebox.showerror("エラー", f"レポート生成中にエラーが発生しました: {str(e)}")
            
    def generate_monthly_trend_report(self, transactions):
        monthly_data = {}
        
        for transaction in transactions:
            month_key = transaction.date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"income": 0, "expense": 0, "net": 0}
                
            if transaction.transaction_type == TransactionType.INCOME and transaction.tax_related:
                monthly_data[month_key]["income"] += transaction.amount
            elif transaction.transaction_type == TransactionType.EXPENSE and transaction.tax_related:
                monthly_data[month_key]["expense"] += transaction.amount
                
        for month in monthly_data:
            monthly_data[month]["net"] = monthly_data[month]["income"] - monthly_data[month]["expense"]
            
        self.update_summary_text("月別収支推移", monthly_data)
        self.create_monthly_chart(monthly_data)
        self.update_detail_tree(monthly_data)
        
    def generate_income_category_report(self, transactions):
        income_data = {}
        
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.INCOME and transaction.tax_related:
                category = transaction.category
                if category not in income_data:
                    income_data[category] = 0
                income_data[category] += transaction.amount
                
        self.update_summary_text("カテゴリ別収入", income_data)
        self.create_pie_chart(income_data, "収入カテゴリ別割合")
        self.update_detail_tree(income_data)
        
    def generate_expense_category_report(self, transactions):
        expense_data = {}
        
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.EXPENSE and transaction.tax_related:
                category = transaction.category
                if category not in expense_data:
                    expense_data[category] = 0
                expense_data[category] += transaction.amount
                
        self.update_summary_text("カテゴリ別支出", expense_data)
        self.create_pie_chart(expense_data, "支出カテゴリ別割合")
        self.update_detail_tree(expense_data)
        
    def generate_quarterly_report(self, transactions):
        quarterly_data = {}
        
        for transaction in transactions:
            quarter = f"{transaction.date.year}-Q{(transaction.date.month - 1) // 3 + 1}"
            if quarter not in quarterly_data:
                quarterly_data[quarter] = {"income": 0, "expense": 0, "net": 0}
                
            if transaction.transaction_type == TransactionType.INCOME and transaction.tax_related:
                quarterly_data[quarter]["income"] += transaction.amount
            elif transaction.transaction_type == TransactionType.EXPENSE and transaction.tax_related:
                quarterly_data[quarter]["expense"] += transaction.amount
                
        for quarter in quarterly_data:
            quarterly_data[quarter]["net"] = quarterly_data[quarter]["income"] - quarterly_data[quarter]["expense"]
            
        self.update_summary_text("四半期比較", quarterly_data)
        self.create_quarterly_chart(quarterly_data)
        self.update_detail_tree(quarterly_data)
        
    def generate_annual_summary(self, transactions):
        total_income = 0
        total_expense = 0
        transaction_count = 0
        
        income_by_month = {}
        expense_by_month = {}
        
        for transaction in transactions:
            if transaction.tax_related:
                transaction_count += 1
                month = transaction.date.strftime("%Y-%m")
                
                if transaction.transaction_type == TransactionType.INCOME:
                    total_income += transaction.amount
                    income_by_month[month] = income_by_month.get(month, 0) + transaction.amount
                elif transaction.transaction_type == TransactionType.EXPENSE:
                    total_expense += transaction.amount
                    expense_by_month[month] = expense_by_month.get(month, 0) + transaction.amount
                    
        net_income = total_income - total_expense
        avg_monthly_income = total_income / 12 if len(income_by_month) > 0 else 0
        avg_monthly_expense = total_expense / 12 if len(expense_by_month) > 0 else 0
        
        summary_data = {
            "総収入": total_income,
            "総支出": total_expense,
            "純利益": net_income,
            "取引件数": transaction_count,
            "月平均収入": avg_monthly_income,
            "月平均支出": avg_monthly_expense
        }
        
        self.update_summary_text("年間サマリー", summary_data)
        self.create_summary_chart(summary_data)
        self.update_detail_tree(summary_data)
        
    def generate_tax_simulation(self):
        from calculators import TaxCalculator
        
        tax_calc = TaxCalculator()
        calc_result = tax_calc.calculate_all_taxes(self.tax_return_data)
        
        simulation_data = {
            "総所得": calc_result['total_income'],
            "課税所得": calc_result['taxable_income'],
            "所得税": calc_result['income_tax'],
            "住民税": calc_result['resident_tax'],
            "事業税": calc_result['business_tax'],
            "消費税": calc_result['consumption_tax'],
            "合計税額": calc_result['total_tax'],
            "実効税率": (calc_result['total_tax'] / calc_result['total_income'] * 100) if calc_result['total_income'] > 0 else 0
        }
        
        self.update_summary_text("税額シミュレーション", simulation_data)
        self.create_tax_chart(simulation_data)
        self.update_detail_tree(simulation_data)
        
    def update_summary_text(self, report_type, data):
        self.summary_text.delete(1.0, tk.END)
        
        summary = f"{report_type}\n" + "="*50 + "\n\n"
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    summary += f"{key}:\n"
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, float):
                            summary += f"  {sub_key}: {sub_value:,.0f}円\n"
                        else:
                            summary += f"  {sub_key}: {sub_value}\n"
                    summary += "\n"
                else:
                    if isinstance(value, float):
                        summary += f"{key}: {value:,.0f}円\n"
                    else:
                        summary += f"{key}: {value}\n"
                        
        self.summary_text.insert(1.0, summary)
        
    def create_monthly_chart(self, monthly_data):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        months = sorted(monthly_data.keys())
        income_values = [monthly_data[month]["income"] for month in months]
        expense_values = [monthly_data[month]["expense"] for month in months]
        net_values = [monthly_data[month]["net"] for month in months]
        
        x = range(len(months))
        
        ax.plot(x, income_values, label='収入', marker='o', color='blue')
        ax.plot(x, expense_values, label='支出', marker='s', color='red')
        ax.plot(x, net_values, label='差引', marker='^', color='green')
        
        ax.set_xlabel('月')
        ax.set_ylabel('金額(円)')
        ax.set_title('月別収支推移')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        self.chart_canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_pie_chart(self, data, title):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        labels = list(data.keys())
        values = list(data.values())
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                         colors=colors, startangle=90)
        
        ax.set_title(title)
        
        plt.tight_layout()
        
        self.chart_canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_quarterly_chart(self, quarterly_data):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        quarters = sorted(quarterly_data.keys())
        income_values = [quarterly_data[quarter]["income"] for quarter in quarters]
        expense_values = [quarterly_data[quarter]["expense"] for quarter in quarters]
        net_values = [quarterly_data[quarter]["net"] for quarter in quarters]
        
        x = np.arange(len(quarters))
        width = 0.25
        
        ax.bar(x - width, income_values, width, label='収入', color='skyblue')
        ax.bar(x, expense_values, width, label='支出', color='lightcoral')
        ax.bar(x + width, net_values, width, label='差引', color='lightgreen')
        
        ax.set_xlabel('四半期')
        ax.set_ylabel('金額(円)')
        ax.set_title('四半期別収支比較')
        ax.set_xticks(x)
        ax.set_xticklabels(quarters)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        self.chart_canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_summary_chart(self, summary_data):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        main_items = ['総収入', '総支出', '純利益']
        main_values = [summary_data[item] for item in main_items]
        colors = ['blue', 'red', 'green']
        
        bars = ax1.bar(main_items, main_values, color=colors, alpha=0.7)
        ax1.set_title('年間収支サマリー')
        ax1.set_ylabel('金額(円)')
        
        for bar, value in zip(bars, main_values):
            height = bar.get_height()
            ax1.annotate(f'{value:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        avg_items = ['月平均収入', '月平均支出']
        avg_values = [summary_data[item] for item in avg_items]
        
        ax2.bar(avg_items, avg_values, color=['lightblue', 'lightcoral'], alpha=0.7)
        ax2.set_title('月平均')
        ax2.set_ylabel('金額(円)')
        
        plt.tight_layout()
        
        self.chart_canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_tax_chart(self, tax_data):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        tax_items = ['所得税', '住民税', '事業税', '消費税']
        tax_values = [tax_data[item] for item in tax_items if tax_data[item] > 0]
        tax_labels = [item for item in tax_items if tax_data[item] > 0]
        
        if tax_values:
            ax1.pie(tax_values, labels=tax_labels, autopct='%1.1f%%', startangle=90)
            ax1.set_title('税額内訳')
        
        income_after_tax = tax_data['総所得'] - tax_data['合計税額']
        
        ax2.bar(['税引前所得', '税額', '税引後所得'], 
               [tax_data['総所得'], tax_data['合計税額'], income_after_tax],
               color=['blue', 'red', 'green'], alpha=0.7)
        ax2.set_title('税引前後比較')
        ax2.set_ylabel('金額(円)')
        
        plt.tight_layout()
        
        self.chart_canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def update_detail_tree(self, data):
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
            
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    parent = self.detail_tree.insert("", tk.END, values=(key, ""))
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, float):
                            self.detail_tree.insert(parent, tk.END, values=(sub_key, f"{sub_value:,.0f}円"))
                        else:
                            self.detail_tree.insert(parent, tk.END, values=(sub_key, str(sub_value)))
                else:
                    if isinstance(value, float):
                        self.detail_tree.insert("", tk.END, values=(key, f"{value:,.0f}円"))
                    else:
                        self.detail_tree.insert("", tk.END, values=(key, str(value)))
                        
    def export_excel(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not filename:
                return
                
            from data_manager import DataManager
            data_manager = DataManager()
            
            if data_manager.export_to_excel(self.tax_return_data, filename):
                messagebox.showinfo("出力完了", "Excelファイルに出力しました。")
            else:
                messagebox.showerror("エラー", "Excel出力に失敗しました。")
                
        except Exception as e:
            messagebox.showerror("エラー", f"Excel出力中にエラーが発生しました: {str(e)}")
            
    def export_pdf(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            
            if not filename:
                return
                
            from pdf_generator import PDFGenerator
            pdf_gen = PDFGenerator()
            
            if pdf_gen.generate_monthly_report(self.tax_return_data, filename):
                messagebox.showinfo("出力完了", "PDFファイルに出力しました。")
            else:
                messagebox.showerror("エラー", "PDF出力に失敗しました。")
                
        except Exception as e:
            messagebox.showerror("エラー", f"PDF出力中にエラーが発生しました: {str(e)}")