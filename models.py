from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class TransactionType(Enum):
    INCOME = "収入"
    EXPENSE = "支出"

class IncomeCategory(Enum):
    SALARY = "給与所得"
    BUSINESS = "事業所得"
    RENTAL = "不動産所得"
    DIVIDEND = "配当所得"
    INTEREST = "利子所得"
    CAPITAL_GAIN = "譲渡所得"
    PENSION = "雑所得(年金)"
    OTHER = "その他雑所得"

class ExpenseCategory(Enum):
    OFFICE_RENT = "事務所家賃"
    UTILITIES = "水道光熱費"
    COMMUNICATION = "通信費"
    TRAVEL = "旅費交通費"
    ENTERTAINMENT = "接待交際費"
    SUPPLIES = "消耗品費"
    ADVERTISING = "広告宣伝費"
    INSURANCE = "保険料"
    DEPRECIATION = "減価償却費"
    OUTSOURCING = "外注費"
    TRAINING = "研修費"
    MEDICAL = "医療費"
    DONATION = "寄付金"
    OTHER = "その他経費"

@dataclass
class Transaction:
    id: str
    date: datetime
    transaction_type: TransactionType
    category: str
    subcategory: str
    amount: float
    description: str
    tax_related: bool = True
    receipt_attached: bool = False
    receipt_path: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'transaction_type': self.transaction_type.value,
            'category': self.category,
            'subcategory': self.subcategory,
            'amount': self.amount,
            'description': self.description,
            'tax_related': self.tax_related,
            'receipt_attached': self.receipt_attached,
            'receipt_path': self.receipt_path,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        return cls(
            id=data['id'],
            date=datetime.fromisoformat(data['date']),
            transaction_type=TransactionType(data['transaction_type']),
            category=data['category'],
            subcategory=data['subcategory'],
            amount=data['amount'],
            description=data['description'],
            tax_related=data.get('tax_related', True),
            receipt_attached=data.get('receipt_attached', False),
            receipt_path=data.get('receipt_path'),
            notes=data.get('notes', '')
        )

@dataclass
class PersonalInfo:
    name: str = ""
    name_kana: str = ""
    address: str = ""
    postal_code: str = ""
    phone: str = ""
    birthdate: str = ""
    occupation: str = ""
    mynumber: str = ""
    spouse_name: str = ""
    spouse_income: float = 0
    dependents: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class BankAccount:
    bank_name: str
    branch_name: str
    account_type: str
    account_number: str
    account_holder: str

@dataclass
class TaxSettings:
    tax_year: int = datetime.now().year
    filing_type: str = "青色申告"  # 青色申告, 白色申告
    business_type: str = ""
    start_date: Optional[datetime] = None
    accounting_method: str = "現金主義"  # 現金主義, 発生主義
    
@dataclass
class Deductions:
    basic_deduction: bool = True
    basic_deduction_amount: float = 480000
    spouse_deduction: bool = False
    spouse_deduction_amount: float = 0
    dependent_deduction: float = 0
    social_insurance_premium: float = 0
    life_insurance_premium: float = 0
    earthquake_insurance_premium: float = 0
    donation: float = 0
    medical_expense: float = 0
    home_loan_deduction: float = 0
    special_deductions: Dict[str, float] = field(default_factory=dict)

@dataclass
class TaxCalculationResult:
    total_income: float = 0
    total_expense: float = 0
    net_income: float = 0
    total_deductions: float = 0
    taxable_income: float = 0
    income_tax: float = 0
    reconstruction_tax: float = 0
    resident_tax: float = 0
    business_tax: float = 0
    consumption_tax: float = 0
    total_tax: float = 0
    withholding_tax: float = 0
    prepaid_tax: float = 0
    tax_due: float = 0
    refund_amount: float = 0
    estimated_quarterly_tax: List[float] = field(default_factory=list)

@dataclass
class TaxReturnData:
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    bank_account: BankAccount = field(default_factory=lambda: BankAccount("", "", "", "", ""))
    tax_settings: TaxSettings = field(default_factory=TaxSettings)
    transactions: List[Transaction] = field(default_factory=list)
    deductions: Deductions = field(default_factory=Deductions)
    calculation_result: TaxCalculationResult = field(default_factory=TaxCalculationResult)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)
        self.updated_at = datetime.now()
    
    def remove_transaction(self, transaction_id: str):
        self.transactions = [t for t in self.transactions if t.id != transaction_id]
        self.updated_at = datetime.now()
    
    def get_transactions_by_type(self, transaction_type: TransactionType) -> List[Transaction]:
        return [t for t in self.transactions if t.transaction_type == transaction_type]
    
    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        return [t for t in self.transactions if t.category == category]
    
    def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        return [t for t in self.transactions if start_date <= t.date <= end_date]
    
    def calculate_total_by_category(self, category: str) -> float:
        transactions = self.get_transactions_by_category(category)
        return sum(t.amount for t in transactions if t.tax_related)
    
    def calculate_total_income(self) -> float:
        income_transactions = self.get_transactions_by_type(TransactionType.INCOME)
        return sum(t.amount for t in income_transactions if t.tax_related)
    
    def calculate_total_expense(self) -> float:
        expense_transactions = self.get_transactions_by_type(TransactionType.EXPENSE)
        return sum(t.amount for t in expense_transactions if t.tax_related)
    
    def get_income_by_category(self) -> Dict[str, float]:
        income_transactions = self.get_transactions_by_type(TransactionType.INCOME)
        result = {}
        for transaction in income_transactions:
            if transaction.tax_related:
                if transaction.category not in result:
                    result[transaction.category] = 0
                result[transaction.category] += transaction.amount
        return result
    
    def get_expense_by_category(self) -> Dict[str, float]:
        expense_transactions = self.get_transactions_by_type(TransactionType.EXPENSE)
        result = {}
        for transaction in expense_transactions:
            if transaction.tax_related:
                if transaction.category not in result:
                    result[transaction.category] = 0
                result[transaction.category] += transaction.amount
        return result
    
    def get_monthly_summary(self) -> Dict[str, Dict[str, float]]:
        summary = {}
        for transaction in self.transactions:
            if not transaction.tax_related:
                continue
                
            month_key = transaction.date.strftime("%Y-%m")
            if month_key not in summary:
                summary[month_key] = {"income": 0, "expense": 0, "net": 0}
            
            if transaction.transaction_type == TransactionType.INCOME:
                summary[month_key]["income"] += transaction.amount
            else:
                summary[month_key]["expense"] += transaction.amount
            
            summary[month_key]["net"] = summary[month_key]["income"] - summary[month_key]["expense"]
        
        return dict(sorted(summary.items()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'personal_info': self.personal_info.__dict__,
            'bank_account': self.bank_account.__dict__,
            'tax_settings': {
                **self.tax_settings.__dict__,
                'start_date': self.tax_settings.start_date.isoformat() if self.tax_settings.start_date else None
            },
            'transactions': [t.to_dict() for t in self.transactions],
            'deductions': self.deductions.__dict__,
            'calculation_result': self.calculation_result.__dict__,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaxReturnData':
        personal_info = PersonalInfo(**data.get('personal_info', {}))
        bank_account = BankAccount(**data.get('bank_account', {}))
        
        tax_settings_data = data.get('tax_settings', {})
        if tax_settings_data.get('start_date'):
            tax_settings_data['start_date'] = datetime.fromisoformat(tax_settings_data['start_date'])
        tax_settings = TaxSettings(**tax_settings_data)
        
        transactions = [Transaction.from_dict(t) for t in data.get('transactions', [])]
        deductions = Deductions(**data.get('deductions', {}))
        calculation_result = TaxCalculationResult(**data.get('calculation_result', {}))
        
        instance = cls(
            personal_info=personal_info,
            bank_account=bank_account,
            tax_settings=tax_settings,
            transactions=transactions,
            deductions=deductions,
            calculation_result=calculation_result,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )
        
        return instance