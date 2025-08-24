"""
確定申告アプリケーションのモデルテスト
"""
import pytest
from datetime import datetime
from models import (
    Transaction,
    TransactionType,
    IncomeCategory,
    ExpenseCategory,
    TaxReturnData,
    PersonalInfo,
    BankAccount,
    TaxSettings,
    Deductions
)


class TestTransaction:
    """Transactionクラスのテスト"""
    
    def test_transaction_creation(self):
        """取引の作成テスト"""
        transaction = Transaction(
            id="test-123",
            date=datetime(2024, 1, 1),
            amount=10000,
            description="テスト取引",
            category=IncomeCategory.SALARY,
            transaction_type=TransactionType.INCOME,
            notes="テスト用の取引"
        )
        
        assert transaction.id == "test-123"
        assert transaction.amount == 10000
        assert transaction.transaction_type == TransactionType.INCOME
        assert transaction.category == IncomeCategory.SALARY

    def test_transaction_validation(self):
        """取引のバリデーションテスト"""
        # 正の金額
        transaction = Transaction(
            id="test-123",
            date=datetime(2024, 1, 1),
            amount=10000,
            description="テスト取引",
            category=IncomeCategory.SALARY,
            transaction_type=TransactionType.INCOME
        )
        assert transaction.amount > 0


class TestTaxReturnData:
    """TaxReturnDataクラスのテスト"""
    
    def test_tax_return_data_creation(self):
        """確定申告データの作成テスト"""
        personal_info = PersonalInfo(
            name="テスト太郎",
            address="東京都渋谷区",
            phone="03-1234-5678",
            email="test@example.com"
        )
        
        tax_data = TaxReturnData(
            personal_info=personal_info,
            tax_year=2024
        )
        
        assert tax_data.personal_info.name == "テスト太郎"
        assert tax_data.tax_year == 2024

    def test_transactions_list_initialization(self):
        """取引リストの初期化テスト"""
        tax_data = TaxReturnData(tax_year=2024)
        assert isinstance(tax_data.transactions, list)
        assert len(tax_data.transactions) == 0


class TestPersonalInfo:
    """PersonalInfoクラスのテスト"""
    
    def test_personal_info_creation(self):
        """個人情報の作成テスト"""
        info = PersonalInfo(
            name="テスト太郎",
            address="東京都渋谷区",
            phone="03-1234-5678",
            email="test@example.com"
        )
        
        assert info.name == "テスト太郎"
        assert info.address == "東京都渋谷区"
        assert info.phone == "03-1234-5678"
        assert info.email == "test@example.com"


class TestEnums:
    """列挙型のテスト"""
    
    def test_transaction_type_values(self):
        """取引タイプの値テスト"""
        assert TransactionType.INCOME.value == "収入"
        assert TransactionType.EXPENSE.value == "支出"
    
    def test_income_category_values(self):
        """収入カテゴリの値テスト"""
        assert IncomeCategory.SALARY.value == "給与所得"
        assert IncomeCategory.BUSINESS.value == "事業所得"
    
    def test_expense_category_values(self):
        """支出カテゴリの値テスト"""
        assert ExpenseCategory.OFFICE_SUPPLIES.value == "事務用品費"
        assert ExpenseCategory.TRAVEL.value == "旅費交通費"


if __name__ == "__main__":
    pytest.main([__file__])
