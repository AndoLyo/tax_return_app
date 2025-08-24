import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import uuid
from typing import List, Optional
from models import Transaction, TransactionType, IncomeCategory, ExpenseCategory
import csv

class TransactionInputDialog:
    def __init__(self, parent, transaction: Optional[Transaction] = None):
        self.parent = parent
        self.transaction = transaction
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("取引入力" if transaction is None else "取引編集")
        self.dialog.geometry("600x700")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        if transaction:
            self.load_transaction_data()
            
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        row = 0
        
        ttk.Label(main_frame, text="日付*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(main_frame, textvariable=self.date_var, width=15).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="(YYYY-MM-DD)").grid(row=row, column=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="取引種別*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, width=20)
        type_combo['values'] = [t.value for t in TransactionType]
        type_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        row += 1
        
        ttk.Label(main_frame, text="カテゴリ*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, width=30)
        self.category_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="サブカテゴリ:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.subcategory_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.subcategory_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="金額*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        amount_frame = ttk.Frame(main_frame)
        amount_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(amount_frame, textvariable=self.amount_var, width=15).pack(side=tk.LEFT)
        ttk.Label(amount_frame, text="円").pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        ttk.Label(main_frame, text="摘要*:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.description_var, width=50).grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        self.tax_related_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="税務処理対象", 
                       variable=self.tax_related_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        self.receipt_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="レシート・領収書あり", 
                       variable=self.receipt_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="レシートファイル:").grid(row=row, column=0, sticky=tk.W, pady=5)
        receipt_frame = ttk.Frame(main_frame)
        receipt_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        self.receipt_path_var = tk.StringVar()
        ttk.Entry(receipt_frame, textvariable=self.receipt_path_var, width=40).pack(side=tk.LEFT)
        ttk.Button(receipt_frame, text="参照", command=self.browse_receipt).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        ttk.Label(main_frame, text="備考:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        notes_frame = ttk.Frame(main_frame)
        notes_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.notes_text = tk.Text(notes_frame, width=50, height=5)
        notes_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)
        self.notes_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        notes_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="保存", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
    def on_type_change(self, event=None):
        type_value = self.type_var.get()
        if type_value == TransactionType.INCOME.value:
            categories = [c.value for c in IncomeCategory]
        elif type_value == TransactionType.EXPENSE.value:
            categories = [c.value for c in ExpenseCategory]
        else:
            categories = []
            
        self.category_combo['values'] = categories
        self.category_var.set("")
        
    def browse_receipt(self):
        filename = filedialog.askopenfilename(
            title="レシート・領収書ファイルを選択",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("PDFファイル", "*.pdf"),
                ("すべてのファイル", "*.*")
            ]
        )
        if filename:
            self.receipt_path_var.set(filename)
            self.receipt_var.set(True)
            
    def load_transaction_data(self):
        t = self.transaction
        self.date_var.set(t.date.strftime("%Y-%m-%d"))
        self.type_var.set(t.transaction_type.value)
        self.on_type_change()
        self.category_var.set(t.category)
        self.subcategory_var.set(t.subcategory)
        self.amount_var.set(str(t.amount))
        self.description_var.set(t.description)
        self.tax_related_var.set(t.tax_related)
        self.receipt_var.set(t.receipt_attached)
        if t.receipt_path:
            self.receipt_path_var.set(t.receipt_path)
        self.notes_text.insert(1.0, t.notes)
        
    def validate_input(self):
        if not self.date_var.get().strip():
            messagebox.showerror("入力エラー", "日付を入力してください。")
            return False
            
        try:
            datetime.strptime(self.date_var.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("入力エラー", "日付の形式が正しくありません。(YYYY-MM-DD)")
            return False
            
        if not self.type_var.get():
            messagebox.showerror("入力エラー", "取引種別を選択してください。")
            return False
            
        if not self.category_var.get():
            messagebox.showerror("入力エラー", "カテゴリを選択してください。")
            return False
            
        if not self.amount_var.get().strip():
            messagebox.showerror("入力エラー", "金額を入力してください。")
            return False
            
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("入力エラー", "金額は正の値を入力してください。")
                return False
        except ValueError:
            messagebox.showerror("入力エラー", "金額は数値で入力してください。")
            return False
            
        if not self.description_var.get().strip():
            messagebox.showerror("入力エラー", "摘要を入力してください。")
            return False
            
        return True
        
    def on_save(self):
        if not self.validate_input():
            return
            
        transaction_id = self.transaction.id if self.transaction else str(uuid.uuid4())
        
        self.result = Transaction(
            id=transaction_id,
            date=datetime.strptime(self.date_var.get(), "%Y-%m-%d"),
            transaction_type=TransactionType(self.type_var.get()),
            category=self.category_var.get(),
            subcategory=self.subcategory_var.get(),
            amount=float(self.amount_var.get()),
            description=self.description_var.get(),
            tax_related=self.tax_related_var.get(),
            receipt_attached=self.receipt_var.get(),
            receipt_path=self.receipt_path_var.get() if self.receipt_path_var.get() else None,
            notes=self.notes_text.get(1.0, tk.END).strip()
        )
        
        self.dialog.destroy()
        
    def on_cancel(self):
        self.dialog.destroy()

class TransactionManager:
    def __init__(self, parent_frame, tax_return_data):
        self.parent_frame = parent_frame
        self.tax_return_data = tax_return_data
        self.setup_ui()
        self.refresh_transaction_list()
        
    def setup_ui(self):
        self.main_frame = ttk.Frame(self.parent_frame)
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="新規取引", command=self.add_transaction).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="編集", command=self.edit_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="削除", command=self.delete_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="CSV取込", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="CSV出力", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        
        filter_frame = ttk.LabelFrame(self.main_frame, text="フィルター", padding="10")
        filter_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(filter_frame, text="期間:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.start_date_var = tk.StringVar(value=f"{datetime.now().year}-01-01")
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=12).grid(row=0, column=1, padx=5)
        ttk.Label(filter_frame, text="〜").grid(row=0, column=2, padx=5)
        self.end_date_var = tk.StringVar(value=f"{datetime.now().year}-12-31")
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=12).grid(row=0, column=3, padx=5)
        
        ttk.Label(filter_frame, text="種別:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.filter_type_var = tk.StringVar()
        type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var, width=15)
        type_combo['values'] = ["すべて"] + [t.value for t in TransactionType]
        type_combo.set("すべて")
        type_combo.grid(row=0, column=5, padx=5)
        
        ttk.Button(filter_frame, text="絞込", command=self.apply_filter).grid(row=0, column=6, padx=(20, 0))
        ttk.Button(filter_frame, text="リセット", command=self.reset_filter).grid(row=0, column=7, padx=5)
        
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        columns = ("date", "type", "category", "description", "amount", "tax_related")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("date", text="日付")
        self.tree.heading("type", text="種別")
        self.tree.heading("category", text="カテゴリ")
        self.tree.heading("description", text="摘要")
        self.tree.heading("amount", text="金額")
        self.tree.heading("tax_related", text="税務対象")
        
        self.tree.column("date", width=100)
        self.tree.column("type", width=80)
        self.tree.column("category", width=120)
        self.tree.column("description", width=300)
        self.tree.column("amount", width=100, anchor=tk.E)
        self.tree.column("tax_related", width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        summary_frame = ttk.LabelFrame(self.main_frame, text="集計", padding="10")
        summary_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.income_sum_label = ttk.Label(summary_frame, text="収入合計: 0円")
        self.income_sum_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.expense_sum_label = ttk.Label(summary_frame, text="支出合計: 0円")
        self.expense_sum_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.net_sum_label = ttk.Label(summary_frame, text="差引: 0円")
        self.net_sum_label.grid(row=0, column=2, sticky=tk.W)
        
    def add_transaction(self):
        dialog = TransactionInputDialog(self.main_frame)
        self.main_frame.wait_window(dialog.dialog)
        
        if dialog.result:
            self.tax_return_data.add_transaction(dialog.result)
            self.refresh_transaction_list()
            
    def edit_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集する取引を選択してください。")
            return
            
        item = self.tree.item(selection[0])
        transaction_id = item['tags'][0]
        transaction = next((t for t in self.tax_return_data.transactions if t.id == transaction_id), None)
        
        if not transaction:
            messagebox.showerror("エラー", "取引データが見つかりません。")
            return
            
        dialog = TransactionInputDialog(self.main_frame, transaction)
        self.main_frame.wait_window(dialog.dialog)
        
        if dialog.result:
            self.tax_return_data.remove_transaction(transaction_id)
            self.tax_return_data.add_transaction(dialog.result)
            self.refresh_transaction_list()
            
    def delete_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除する取引を選択してください。")
            return
            
        if messagebox.askyesno("確認", "選択した取引を削除しますか？"):
            item = self.tree.item(selection[0])
            transaction_id = item['tags'][0]
            self.tax_return_data.remove_transaction(transaction_id)
            self.refresh_transaction_list()
            
    def on_double_click(self, event):
        self.edit_transaction()
        
    def apply_filter(self):
        self.refresh_transaction_list()
        
    def reset_filter(self):
        self.filter_type_var.set("すべて")
        self.start_date_var.set(f"{datetime.now().year}-01-01")
        self.end_date_var.set(f"{datetime.now().year}-12-31")
        self.refresh_transaction_list()
        
    def get_filtered_transactions(self):
        transactions = self.tax_return_data.transactions
        
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            transactions = [t for t in transactions if start_date <= t.date <= end_date]
        except ValueError:
            pass
            
        filter_type = self.filter_type_var.get()
        if filter_type != "すべて":
            transactions = [t for t in transactions if t.transaction_type.value == filter_type]
            
        return sorted(transactions, key=lambda t: t.date, reverse=True)
        
    def refresh_transaction_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        transactions = self.get_filtered_transactions()
        
        income_sum = 0
        expense_sum = 0
        
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.INCOME and transaction.tax_related:
                income_sum += transaction.amount
            elif transaction.transaction_type == TransactionType.EXPENSE and transaction.tax_related:
                expense_sum += transaction.amount
                
            self.tree.insert("", tk.END, values=(
                transaction.date.strftime("%Y-%m-%d"),
                transaction.transaction_type.value,
                transaction.category,
                transaction.description,
                f"{transaction.amount:,.0f}",
                "○" if transaction.tax_related else "×"
            ), tags=(transaction.id,))
            
        net_sum = income_sum - expense_sum
        
        self.income_sum_label.config(text=f"収入合計: {income_sum:,.0f}円")
        self.expense_sum_label.config(text=f"支出合計: {expense_sum:,.0f}円")
        self.net_sum_label.config(text=f"差引: {net_sum:,.0f}円")
        
    def import_csv(self):
        filename = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
        )
        
        if not filename:
            return
            
        try:
            imported_count = 0
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    transaction = Transaction(
                        id=str(uuid.uuid4()),
                        date=datetime.strptime(row['日付'], "%Y-%m-%d"),
                        transaction_type=TransactionType(row['種別']),
                        category=row['カテゴリ'],
                        subcategory=row.get('サブカテゴリ', ''),
                        amount=float(row['金額']),
                        description=row['摘要'],
                        tax_related=row.get('税務対象', 'True').lower() == 'true',
                        notes=row.get('備考', '')
                    )
                    self.tax_return_data.add_transaction(transaction)
                    imported_count += 1
                    
            self.refresh_transaction_list()
            messagebox.showinfo("取込完了", f"{imported_count}件の取引を取り込みました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"CSV取込中にエラーが発生しました: {str(e)}")
            
    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="CSVファイルを保存",
            defaultextension=".csv",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
        )
        
        if not filename:
            return
            
        try:
            transactions = self.get_filtered_transactions()
            
            with open(filename, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['日付', '種別', 'カテゴリ', 'サブカテゴリ', '金額', '摘要', '税務対象', '備考'])
                
                for transaction in transactions:
                    writer.writerow([
                        transaction.date.strftime("%Y-%m-%d"),
                        transaction.transaction_type.value,
                        transaction.category,
                        transaction.subcategory,
                        transaction.amount,
                        transaction.description,
                        transaction.tax_related,
                        transaction.notes
                    ])
                    
            messagebox.showinfo("出力完了", f"{len(transactions)}件の取引をCSVファイルに出力しました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"CSV出力中にエラーが発生しました: {str(e)}")