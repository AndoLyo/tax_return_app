from typing import Dict, List
from models import TaxReturnData, TransactionType, IncomeCategory, ExpenseCategory
import math

class IncomeCalculator:
    def __init__(self):
        self.salary_deduction_rates = [
            (1625000, 0.55, 0),
        (1800000, 0.4, 427500),
        (3600000, 0.3, 636000),
        (6600000, 0.2, 1536000),
        (8500000, 0.1, 2196000),
        (float('inf'), 0.0, 2955000)
        ]
    
    def calculate_salary_deduction(self, salary_income: float) -> float:
        if salary_income <= 650000:
            return salary_income
        elif salary_income <= 1625000:
            return salary_income * 0.55
        else:
            for threshold, rate, fixed in self.salary_deduction_rates:
                if salary_income <= threshold:
                    return salary_income * rate + fixed
        return 2955000
    
    def calculate_business_income(self, business_revenue: float, business_expenses: float, 
                                blue_return_deduction: float = 0) -> float:
        net_income = business_revenue - business_expenses
        return max(0, net_income - blue_return_deduction)
    
    def calculate_rental_income(self, rental_revenue: float, rental_expenses: float) -> float:
        return max(0, rental_revenue - rental_expenses)
    
    def calculate_total_income(self, tax_data: TaxReturnData) -> Dict[str, float]:
        income_by_category = tax_data.get_income_by_category()
        expense_by_category = tax_data.get_expense_by_category()
        
        result = {
            'salary_income': 0,
            'business_income': 0,
            'rental_income': 0,
            'dividend_income': 0,
            'interest_income': 0,
            'capital_gain': 0,
            'pension_income': 0,
            'other_income': 0,
            'total_income': 0
        }
        
        for category, amount in income_by_category.items():
            if category == IncomeCategory.SALARY.value:
                salary_deduction = self.calculate_salary_deduction(amount)
                result['salary_income'] = max(0, amount - salary_deduction)
            elif category == IncomeCategory.BUSINESS.value:
                business_expenses = expense_by_category.get(ExpenseCategory.OUTSOURCING.value, 0)
                for exp_cat in ExpenseCategory:
                    if exp_cat != ExpenseCategory.MEDICAL and exp_cat != ExpenseCategory.DONATION:
                        business_expenses += expense_by_category.get(exp_cat.value, 0)
                
                blue_deduction = 650000 if tax_data.tax_settings.filing_type == "青色申告" else 0
                result['business_income'] = self.calculate_business_income(
                    amount, business_expenses, blue_deduction)
            elif category == IncomeCategory.RENTAL.value:
                rental_expenses = (expense_by_category.get(ExpenseCategory.OFFICE_RENT.value, 0) +
                                 expense_by_category.get(ExpenseCategory.UTILITIES.value, 0) +
                                 expense_by_category.get(ExpenseCategory.DEPRECIATION.value, 0))
                result['rental_income'] = self.calculate_rental_income(amount, rental_expenses)
            elif category == IncomeCategory.DIVIDEND.value:
                result['dividend_income'] = amount
            elif category == IncomeCategory.INTEREST.value:
                result['interest_income'] = amount
            elif category == IncomeCategory.CAPITAL_GAIN.value:
                result['capital_gain'] = amount
            elif category == IncomeCategory.PENSION.value:
                result['pension_income'] = amount
            elif category == IncomeCategory.OTHER.value:
                result['other_income'] = amount
        
        result['total_income'] = sum(result[key] for key in result if key != 'total_income')
        return result

class DeductionCalculator:
    def __init__(self):
        self.basic_deduction_amount = 480000
        self.spouse_deduction_amount = 380000
        self.dependent_deduction_amount = 380000
        
    def calculate_basic_deduction(self, total_income: float) -> float:
        if total_income <= 24000000:
            return self.basic_deduction_amount
        elif total_income <= 24500000:
            return 320000
        elif total_income <= 25000000:
            return 160000
        else:
            return 0
    
    def calculate_spouse_deduction(self, spouse_income: float, total_income: float) -> float:
        if spouse_income > 480000 or total_income > 10000000:
            return 0
        
        if total_income <= 9000000:
            base_amount = self.spouse_deduction_amount
        elif total_income <= 9500000:
            base_amount = 260000
        elif total_income <= 10000000:
            base_amount = 130000
        else:
            return 0
            
        if spouse_income <= 480000:
            return base_amount
        else:
            return max(0, base_amount - (spouse_income - 480000))
    
    def calculate_dependent_deduction(self, dependents: List[Dict]) -> float:
        total = 0
        for dependent in dependents:
            age = int(dependent.get('age', 0))
            if age >= 70:
                total += 580000
            elif age >= 19 and age <= 22:
                total += 630000
            else:
                total += self.dependent_deduction_amount
        return total
    
    def calculate_social_insurance_deduction(self, premium: float) -> float:
        return premium
    
    def calculate_life_insurance_deduction(self, premium: float) -> float:
        if premium <= 20000:
            return premium
        elif premium <= 40000:
            return premium * 0.5 + 10000
        elif premium <= 80000:
            return premium * 0.25 + 20000
        else:
            return 40000
    
    def calculate_earthquake_insurance_deduction(self, premium: float) -> float:
        return min(premium, 50000)
    
    def calculate_donation_deduction(self, donation: float, total_income: float) -> float:
        return max(0, donation - 2000)
    
    def calculate_medical_deduction(self, medical_expense: float, total_income: float) -> float:
        threshold = min(total_income * 0.05, 100000)
        return max(0, medical_expense - threshold)
    
    def calculate_home_loan_deduction(self, loan_balance: float, tax_amount: float) -> float:
        deduction = min(loan_balance * 0.007, 350000)
        return min(deduction, tax_amount)
    
    def calculate_total_deductions(self, tax_data: TaxReturnData, total_income: float) -> Dict[str, float]:
        deductions = tax_data.deductions
        
        result = {
            'basic_deduction': 0,
            'spouse_deduction': 0,
            'dependent_deduction': 0,
            'social_insurance_deduction': 0,
            'life_insurance_deduction': 0,
            'earthquake_insurance_deduction': 0,
            'donation_deduction': 0,
            'medical_deduction': 0,
            'home_loan_deduction': 0,
            'total_deductions': 0
        }
        
        if deductions.basic_deduction:
            result['basic_deduction'] = self.calculate_basic_deduction(total_income)
        
        if deductions.spouse_deduction:
            result['spouse_deduction'] = self.calculate_spouse_deduction(
                tax_data.personal_info.spouse_income, total_income)
        
        result['dependent_deduction'] = self.calculate_dependent_deduction(
            tax_data.personal_info.dependents)
        
        result['social_insurance_deduction'] = self.calculate_social_insurance_deduction(
            deductions.social_insurance_premium)
        
        result['life_insurance_deduction'] = self.calculate_life_insurance_deduction(
            deductions.life_insurance_premium)
        
        result['earthquake_insurance_deduction'] = self.calculate_earthquake_insurance_deduction(
            deductions.earthquake_insurance_premium)
        
        result['donation_deduction'] = self.calculate_donation_deduction(
            deductions.donation, total_income)
        
        result['medical_deduction'] = self.calculate_medical_deduction(
            deductions.medical_expense, total_income)
        
        result['home_loan_deduction'] = deductions.home_loan_deduction
        
        result['total_deductions'] = sum(result[key] for key in result if key not in ['home_loan_deduction', 'total_deductions'])
        
        return result

class TaxCalculator:
    def __init__(self):
        self.income_tax_brackets = [
            (1950000, 0.05, 0),
            (3300000, 0.10, 97500),
            (6950000, 0.20, 427500),
            (9000000, 0.23, 636000),
            (18000000, 0.33, 1536000),
            (40000000, 0.40, 2796000),
            (float('inf'), 0.45, 4796000)
        ]
        
        self.resident_tax_rate = 0.10
        self.reconstruction_tax_rate = 0.021
        
    def calculate_income_tax(self, taxable_income: float) -> float:
        if taxable_income <= 0:
            return 0
            
        for threshold, rate, deduction in self.income_tax_brackets:
            if taxable_income <= threshold:
                return max(0, math.floor(taxable_income * rate - deduction))
        
        return math.floor(taxable_income * 0.45 - 4796000)
    
    def calculate_reconstruction_tax(self, income_tax: float) -> float:
        return math.floor(income_tax * self.reconstruction_tax_rate)
    
    def calculate_resident_tax(self, taxable_income: float) -> float:
        if taxable_income <= 0:
            return 0
        
        income_rate = taxable_income * self.resident_tax_rate
        per_capita_rate = 5000
        
        return math.floor(income_rate + per_capita_rate)
    
    def calculate_business_tax(self, business_income: float) -> float:
        if business_income <= 2900000:
            return 0
        
        taxable_business_income = business_income - 2900000
        
        if taxable_business_income <= 4000000:
            return math.floor(taxable_business_income * 0.05)
        else:
            return math.floor(4000000 * 0.05 + (taxable_business_income - 4000000) * 0.048)
    
    def calculate_consumption_tax(self, business_revenue: float) -> float:
        if business_revenue <= 10000000:
            return 0
        
        return math.floor(business_revenue * 0.10)
    
    def calculate_estimated_quarterly_tax(self, annual_tax: float) -> List[float]:
        quarterly_amount = annual_tax / 4
        return [quarterly_amount] * 4
    
    def calculate_all_taxes(self, tax_data: TaxReturnData) -> Dict[str, float]:
        income_calc = IncomeCalculator()
        deduction_calc = DeductionCalculator()
        
        income_breakdown = income_calc.calculate_total_income(tax_data)
        total_income = income_breakdown['total_income']
        
        deduction_breakdown = deduction_calc.calculate_total_deductions(tax_data, total_income)
        total_deductions = deduction_breakdown['total_deductions']
        
        taxable_income = max(0, total_income - total_deductions)
        
        income_tax = self.calculate_income_tax(taxable_income)
        reconstruction_tax = self.calculate_reconstruction_tax(income_tax)
        resident_tax = self.calculate_resident_tax(taxable_income)
        business_tax = self.calculate_business_tax(income_breakdown['business_income'])
        
        business_revenue = tax_data.get_income_by_category().get(IncomeCategory.BUSINESS.value, 0)
        consumption_tax = self.calculate_consumption_tax(business_revenue)
        
        total_tax = income_tax + reconstruction_tax + resident_tax + business_tax + consumption_tax
        
        home_loan_deduction = deduction_breakdown['home_loan_deduction']
        final_income_tax = max(0, income_tax - home_loan_deduction)
        final_total_tax = final_income_tax + reconstruction_tax + resident_tax + business_tax + consumption_tax
        
        withholding_tax = sum(t.amount for t in tax_data.transactions 
                            if t.description.find('源泉') >= 0 and t.transaction_type == TransactionType.EXPENSE)
        
        prepaid_tax = sum(t.amount for t in tax_data.transactions 
                         if t.description.find('予定納税') >= 0 and t.transaction_type == TransactionType.EXPENSE)
        
        paid_tax = withholding_tax + prepaid_tax
        
        if final_total_tax > paid_tax:
            tax_due = final_total_tax - paid_tax
            refund_amount = 0
        else:
            tax_due = 0
            refund_amount = paid_tax - final_total_tax
        
        estimated_quarterly = self.calculate_estimated_quarterly_tax(final_income_tax)
        
        return {
            'total_income': total_income,
            'total_expense': tax_data.calculate_total_expense(),
            'net_income': total_income - tax_data.calculate_total_expense(),
            'total_deductions': total_deductions,
            'taxable_income': taxable_income,
            'income_tax': final_income_tax,
            'reconstruction_tax': reconstruction_tax,
            'resident_tax': resident_tax,
            'business_tax': business_tax,
            'consumption_tax': consumption_tax,
            'total_tax': final_total_tax,
            'withholding_tax': withholding_tax,
            'prepaid_tax': prepaid_tax,
            'tax_due': tax_due,
            'refund_amount': refund_amount,
            'home_loan_deduction_applied': home_loan_deduction,
            'estimated_quarterly_tax': estimated_quarterly,
            'income_breakdown': income_breakdown,
            'deduction_breakdown': deduction_breakdown
        }