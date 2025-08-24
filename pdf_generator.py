from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from typing import Dict, Any
from models import TaxReturnData, TransactionType
import os
import tempfile

class PDFGenerator:
    def __init__(self):
        self.setup_fonts()
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_fonts(self):
        try:
            font_paths = [
                r"C:\Windows\Fonts\msgothic.ttc",
                r"C:\Windows\Fonts\msmincho.ttc", 
                r"C:\Windows\Fonts\meiryo.ttc"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))
                        break
                    except:
                        continue
            else:
                print("日本語フォントが見つかりませんでした。")
                
        except Exception as e:
            print(f"フォント設定エラー: {str(e)}")
            
    def setup_custom_styles(self):
        try:
            self.title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontName='JapaneseFont',
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.black
            )
            
            self.heading_style = ParagraphStyle(
                'CustomHeading',
                parent=self.styles['Heading2'],
                fontName='JapaneseFont',
                fontSize=14,
                spaceAfter=15,
                spaceBefore=20,
                textColor=colors.darkblue
            )
            
            self.normal_style = ParagraphStyle(
                'CustomNormal',
                parent=self.styles['Normal'],
                fontName='JapaneseFont',
                fontSize=10,
                spaceAfter=6,
                leading=14
            )
            
            self.small_style = ParagraphStyle(
                'CustomSmall',
                parent=self.styles['Normal'],
                fontName='JapaneseFont',
                fontSize=9,
                spaceAfter=4,
                leading=12
            )
            
        except:
            self.title_style = self.styles['Heading1']
            self.heading_style = self.styles['Heading2']
            self.normal_style = self.styles['Normal']
            self.small_style = self.styles['Normal']
            
    def generate_tax_return_pdf(self, tax_data: TaxReturnData, output_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            story = []
            
            story.extend(self.create_title_page(tax_data))
            story.append(PageBreak())
            
            story.extend(self.create_personal_info_section(tax_data))
            story.append(Spacer(1, 20))
            
            story.extend(self.create_income_section(tax_data))
            story.append(PageBreak())
            
            story.extend(self.create_expense_section(tax_data))
            story.append(PageBreak())
            
            story.extend(self.create_deduction_section(tax_data))
            story.append(Spacer(1, 20))
            
            story.extend(self.create_tax_calculation_section(tax_data))
            story.append(PageBreak())
            
            story.extend(self.create_summary_section(tax_data))
            story.append(PageBreak())
            
            story.extend(self.create_transaction_detail_section(tax_data))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"PDF生成エラー: {str(e)}")
            return False
            
    def create_title_page(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Spacer(1, 50))
        elements.append(Paragraph("確定申告書", self.title_style))
        elements.append(Spacer(1, 30))
        
        elements.append(Paragraph(f"令和{tax_data.tax_settings.tax_year - 2018}年分", self.heading_style))
        elements.append(Spacer(1, 20))
        
        info_data = [
            ['氏名', tax_data.personal_info.name],
            ['住所', tax_data.personal_info.address],
            ['職業', tax_data.personal_info.occupation],
            ['申告区分', tax_data.tax_settings.filing_type]
        ]
        
        info_table = Table(info_data, colWidths=[60*mm, 100*mm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 50))
        
        elements.append(Paragraph(
            f"作成日: {datetime.now().strftime('%Y年%m月%d日')}",
            self.normal_style
        ))
        
        return elements
        
    def create_personal_info_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("1. 基本情報", self.heading_style))
        
        personal_data = [
            ['項目', '内容'],
            ['氏名', tax_data.personal_info.name],
            ['フリガナ', tax_data.personal_info.name_kana],
            ['住所', tax_data.personal_info.address],
            ['郵便番号', tax_data.personal_info.postal_code],
            ['電話番号', tax_data.personal_info.phone],
            ['生年月日', tax_data.personal_info.birthdate],
            ['職業', tax_data.personal_info.occupation]
        ]
        
        personal_table = Table(personal_data, colWidths=[50*mm, 120*mm])
        personal_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(personal_table)
        
        return elements
        
    def create_income_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("2. 所得の部", self.heading_style))
        
        income_by_category = tax_data.get_income_by_category()
        
        income_data = [['所得区分', '金額(円)']]
        
        total_income = 0
        for category, amount in income_by_category.items():
            income_data.append([category, f"{amount:,.0f}"])
            total_income += amount
            
        income_data.append(['合計', f"{total_income:,.0f}"])
        
        income_table = Table(income_data, colWidths=[100*mm, 70*mm])
        income_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
        ]))
        
        elements.append(income_table)
        
        return elements
        
    def create_expense_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("3. 必要経費の部", self.heading_style))
        
        expense_by_category = tax_data.get_expense_by_category()
        
        expense_data = [['経費区分', '金額(円)']]
        
        total_expense = 0
        for category, amount in expense_by_category.items():
            if category != '医療費' and category != '寄付金':
                expense_data.append([category, f"{amount:,.0f}"])
                total_expense += amount
                
        expense_data.append(['合計', f"{total_expense:,.0f}"])
        
        expense_table = Table(expense_data, colWidths=[100*mm, 70*mm])
        expense_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
        ]))
        
        elements.append(expense_table)
        
        return elements
        
    def create_deduction_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("4. 所得控除の部", self.heading_style))
        
        deductions = tax_data.deductions
        calc_result = tax_data.calculation_result
        
        deduction_data = [['控除項目', '金額(円)']]
        
        if deductions.basic_deduction:
            deduction_data.append(['基礎控除', f"{deductions.basic_deduction_amount:,.0f}"])
            
        if deductions.spouse_deduction:
            deduction_data.append(['配偶者控除', f"{deductions.spouse_deduction_amount:,.0f}"])
            
        if deductions.dependent_deduction > 0:
            deduction_data.append(['扶養控除', f"{deductions.dependent_deduction:,.0f}"])
            
        if deductions.social_insurance_premium > 0:
            deduction_data.append(['社会保険料控除', f"{deductions.social_insurance_premium:,.0f}"])
            
        if deductions.life_insurance_premium > 0:
            deduction_data.append(['生命保険料控除', f"{deductions.life_insurance_premium:,.0f}"])
            
        if deductions.earthquake_insurance_premium > 0:
            deduction_data.append(['地震保険料控除', f"{deductions.earthquake_insurance_premium:,.0f}"])
            
        if deductions.medical_expense > 0:
            deduction_data.append(['医療費控除', f"{deductions.medical_expense:,.0f}"])
            
        if deductions.donation > 0:
            deduction_data.append(['寄付金控除', f"{deductions.donation:,.0f}"])
            
        total_deductions = (deductions.basic_deduction_amount + 
                          deductions.spouse_deduction_amount +
                          deductions.dependent_deduction +
                          deductions.social_insurance_premium +
                          deductions.life_insurance_premium +
                          deductions.earthquake_insurance_premium +
                          deductions.medical_expense +
                          deductions.donation)
        
        deduction_data.append(['所得控除合計', f"{total_deductions:,.0f}"])
        
        deduction_table = Table(deduction_data, colWidths=[100*mm, 70*mm])
        deduction_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
        ]))
        
        elements.append(deduction_table)
        
        return elements
        
    def create_tax_calculation_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("5. 税額計算の部", self.heading_style))
        
        calc = tax_data.calculation_result
        
        calc_data = [
            ['項目', '金額(円)'],
            ['総所得金額', f"{calc.total_income:,.0f}"],
            ['所得控除合計', f"{calc.total_deductions:,.0f}"],
            ['課税所得金額', f"{calc.taxable_income:,.0f}"],
            ['所得税額', f"{calc.income_tax:,.0f}"],
            ['復興特別所得税額', f"{calc.reconstruction_tax:,.0f}"],
            ['住民税額', f"{calc.resident_tax:,.0f}"],
            ['事業税額', f"{calc.business_tax:,.0f}"],
            ['消費税額', f"{calc.consumption_tax:,.0f}"],
            ['税額合計', f"{calc.total_tax:,.0f}"]
        ]
        
        calc_table = Table(calc_data, colWidths=[100*mm, 70*mm])
        calc_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
            ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
        ]))
        
        elements.append(calc_table)
        
        return elements
        
    def create_summary_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("6. 申告納税額", self.heading_style))
        
        calc = tax_data.calculation_result
        
        summary_data = [
            ['項目', '金額(円)'],
            ['計算税額', f"{calc.total_tax:,.0f}"],
            ['源泉徴収税額', f"{calc.withholding_tax:,.0f}"],
            ['予定納税額', f"{calc.prepaid_tax:,.0f}"]
        ]
        
        if calc.tax_due > 0:
            summary_data.append(['申告納税額', f"{calc.tax_due:,.0f}"])
        else:
            summary_data.append(['還付金額', f"{calc.refund_amount:,.0f}"])
            
        summary_table = Table(summary_data, colWidths=[100*mm, 70*mm])
        summary_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
            ('BACKGROUND', (0, -1), (-1, -1), colors.gold),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('FONTNAME', (0, -1), (-1, -1), 'JapaneseFont'),
        ]))
        
        elements.append(summary_table)
        
        return elements
        
    def create_transaction_detail_section(self, tax_data: TaxReturnData) -> list:
        elements = []
        
        elements.append(Paragraph("7. 取引明細", self.heading_style))
        
        transactions = sorted(tax_data.transactions, key=lambda t: t.date)
        
        income_transactions = [t for t in transactions if t.transaction_type == TransactionType.INCOME and t.tax_related]
        expense_transactions = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE and t.tax_related]
        
        if income_transactions:
            elements.append(Paragraph("収入取引", self.normal_style))
            
            income_detail_data = [['日付', 'カテゴリ', '摘要', '金額(円)']]
            
            for transaction in income_transactions:
                income_detail_data.append([
                    transaction.date.strftime("%Y/%m/%d"),
                    transaction.category,
                    transaction.description[:30] + "..." if len(transaction.description) > 30 else transaction.description,
                    f"{transaction.amount:,.0f}"
                ])
                
            income_detail_table = Table(income_detail_data, colWidths=[25*mm, 40*mm, 80*mm, 25*mm])
            income_detail_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(income_detail_table)
            elements.append(Spacer(1, 20))
            
        if expense_transactions:
            elements.append(Paragraph("支出取引", self.normal_style))
            
            expense_detail_data = [['日付', 'カテゴリ', '摘要', '金額(円)']]
            
            for transaction in expense_transactions:
                expense_detail_data.append([
                    transaction.date.strftime("%Y/%m/%d"),
                    transaction.category,
                    transaction.description[:30] + "..." if len(transaction.description) > 30 else transaction.description,
                    f"{transaction.amount:,.0f}"
                ])
                
            expense_detail_table = Table(expense_detail_data, colWidths=[25*mm, 40*mm, 80*mm, 25*mm])
            expense_detail_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(expense_detail_table)
            
        return elements
        
    def generate_monthly_report(self, tax_data: TaxReturnData, output_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            story.append(Paragraph("月別収支レポート", self.title_style))
            story.append(Spacer(1, 20))
            
            monthly_summary = tax_data.get_monthly_summary()
            
            monthly_data = [['年月', '収入(円)', '支出(円)', '差引(円)']]
            
            total_income = 0
            total_expense = 0
            
            for month, summary in monthly_summary.items():
                monthly_data.append([
                    month,
                    f"{summary['income']:,.0f}",
                    f"{summary['expense']:,.0f}",
                    f"{summary['net']:,.0f}"
                ])
                total_income += summary['income']
                total_expense += summary['expense']
                
            monthly_data.append([
                '合計',
                f"{total_income:,.0f}",
                f"{total_expense:,.0f}",
                f"{total_income - total_expense:,.0f}"
            ])
            
            monthly_table = Table(monthly_data, colWidths=[40*mm, 40*mm, 40*mm, 40*mm])
            monthly_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'JapaneseFont', 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(monthly_table)
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"月別レポートPDF生成エラー: {str(e)}")
            return False