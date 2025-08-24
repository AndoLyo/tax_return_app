import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from models import TaxReturnData
import tkinter as tk
from tkinter import messagebox

class DataManager:
    def __init__(self):
        self.app_data_dir = os.path.expanduser("~/.tax_return_app")
        self.backup_dir = os.path.join(self.app_data_dir, "backups")
        self.ensure_directories()
        
    def ensure_directories(self):
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def save_data(self, tax_data: TaxReturnData, filename: str) -> bool:
        try:
            tax_data.updated_at = datetime.now()
            
            data_dict = tax_data.to_dict()
            
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data_dict, file, ensure_ascii=False, indent=2)
            
            self.create_backup(filename)
            return True
            
        except Exception as e:
            messagebox.showerror("保存エラー", f"データの保存中にエラーが発生しました: {str(e)}")
            return False
            
    def load_data(self, filename: str) -> Optional[TaxReturnData]:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data_dict = json.load(file)
            
            tax_data = TaxReturnData.from_dict(data_dict)
            return tax_data
            
        except FileNotFoundError:
            messagebox.showerror("読み込みエラー", "指定されたファイルが見つかりません。")
            return None
        except json.JSONDecodeError:
            messagebox.showerror("読み込みエラー", "ファイルの形式が正しくありません。")
            return None
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"データの読み込み中にエラーが発生しました: {str(e)}")
            return None
            
    def create_backup(self, filename: str):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(filename))[0]
            backup_filename = f"{base_name}_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(filename, backup_path)
            
            self.cleanup_old_backups()
            
        except Exception as e:
            print(f"バックアップ作成エラー: {str(e)}")
            
    def cleanup_old_backups(self, max_backups: int = 10):
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            for file_path, _ in backup_files[max_backups:]:
                os.remove(file_path)
                
        except Exception as e:
            print(f"バックアップファイル整理エラー: {str(e)}")
            
    def get_backup_list(self) -> list:
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, filename)
                    mtime = os.path.getmtime(file_path)
                    backup_files.append({
                        'filename': filename,
                        'path': file_path,
                        'date': datetime.fromtimestamp(mtime)
                    })
            
            return sorted(backup_files, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            print(f"バックアップリスト取得エラー: {str(e)}")
            return []
            
    def restore_backup(self, backup_path: str, restore_path: str) -> bool:
        try:
            shutil.copy2(backup_path, restore_path)
            return True
        except Exception as e:
            messagebox.showerror("復元エラー", f"バックアップの復元中にエラーが発生しました: {str(e)}")
            return False
            
    def auto_save(self, tax_data: TaxReturnData, auto_save_path: str):
        try:
            auto_save_file = os.path.join(self.app_data_dir, "autosave.json")
            self.save_data(tax_data, auto_save_file)
        except Exception as e:
            print(f"自動保存エラー: {str(e)}")
            
    def load_auto_save(self) -> Optional[TaxReturnData]:
        try:
            auto_save_file = os.path.join(self.app_data_dir, "autosave.json")
            if os.path.exists(auto_save_file):
                return self.load_data(auto_save_file)
            return None
        except Exception as e:
            print(f"自動保存ファイル読み込みエラー: {str(e)}")
            return None
            
    def export_to_csv(self, tax_data: TaxReturnData, csv_path: str) -> bool:
        try:
            import csv
            
            with open(csv_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                
                writer.writerow(['取引データ'])
                writer.writerow(['日付', '種別', 'カテゴリ', 'サブカテゴリ', '金額', '摘要', '税務対象', '備考'])
                
                for transaction in sorted(tax_data.transactions, key=lambda t: t.date):
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
                
                writer.writerow([])
                writer.writerow(['収入カテゴリ別集計'])
                income_by_category = tax_data.get_income_by_category()
                for category, amount in income_by_category.items():
                    writer.writerow([category, amount])
                
                writer.writerow([])
                writer.writerow(['支出カテゴリ別集計'])
                expense_by_category = tax_data.get_expense_by_category()
                for category, amount in expense_by_category.items():
                    writer.writerow([category, amount])
                
                writer.writerow([])
                writer.writerow(['月別集計'])
                monthly_summary = tax_data.get_monthly_summary()
                writer.writerow(['年月', '収入', '支出', '差引'])
                for month, summary in monthly_summary.items():
                    writer.writerow([month, summary['income'], summary['expense'], summary['net']])
                
            return True
            
        except Exception as e:
            messagebox.showerror("CSV出力エラー", f"CSV出力中にエラーが発生しました: {str(e)}")
            return False
            
    def import_from_csv(self, csv_path: str) -> Optional[list]:
        try:
            import csv
            from models import Transaction, TransactionType
            import uuid
            
            transactions = []
            
            with open(csv_path, 'r', encoding='utf-8') as file:
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
                    transactions.append(transaction)
                    
            return transactions
            
        except Exception as e:
            messagebox.showerror("CSV取込エラー", f"CSV取込中にエラーが発生しました: {str(e)}")
            return None
            
    def get_settings(self) -> Dict[str, Any]:
        try:
            settings_file = os.path.join(self.app_data_dir, "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                return self.get_default_settings()
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {str(e)}")
            return self.get_default_settings()
            
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        try:
            settings_file = os.path.join(self.app_data_dir, "settings.json")
            with open(settings_file, 'w', encoding='utf-8') as file:
                json.dump(settings, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {str(e)}")
            return False
            
    def get_default_settings(self) -> Dict[str, Any]:
        return {
            'auto_save_enabled': True,
            'auto_save_interval': 300,  # seconds
            'backup_enabled': True,
            'max_backups': 10,
            'default_tax_year': datetime.now().year,
            'default_filing_type': '青色申告',
            'window_geometry': '1200x800',
            'recent_files': []
        }
        
    def add_recent_file(self, filepath: str):
        settings = self.get_settings()
        recent_files = settings.get('recent_files', [])
        
        if filepath in recent_files:
            recent_files.remove(filepath)
            
        recent_files.insert(0, filepath)
        recent_files = recent_files[:10]  # Keep only last 10 files
        
        settings['recent_files'] = recent_files
        self.save_settings(settings)
        
    def get_recent_files(self) -> list:
        settings = self.get_settings()
        recent_files = settings.get('recent_files', [])
        
        valid_files = []
        for filepath in recent_files:
            if os.path.exists(filepath):
                valid_files.append(filepath)
                
        if len(valid_files) != len(recent_files):
            settings['recent_files'] = valid_files
            self.save_settings(settings)
            
        return valid_files