import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional

class DepreciationCalculator:
    """減価償却計算クラス"""
    
    def __init__(self):
        self.assets_file = "assets.json"
        self.load_assets()
        
        # 減価償却の耐用年数（簡易版）
        self.useful_life = {
            "PC・ノートPC": 4,
            "デスクトップPC": 4,
            "タブレット": 3,
            "スマートフォン": 3,
            "プリンター": 5,
            "スキャナー": 5,
            "サーバー": 5,
            "ネットワーク機器": 5,
            "ソフトウェア": 3,
            "家具・什器": 8,
            "建物": 22,
            "車両": 6,
            "その他": 5
        }
    
    def load_assets(self):
        """資産データを読み込み"""
        try:
            if os.path.exists(self.assets_file):
                with open(self.assets_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        self.assets = json.loads(content)
                    else:
                        self.assets = []
            else:
                self.assets = []
        except (json.JSONDecodeError, ValueError):
            self.assets = []
    
    def save_assets(self):
        """資産データを保存"""
        with open(self.assets_file, 'w', encoding='utf-8') as f:
            json.dump(self.assets, f, ensure_ascii=False, indent=2)
    
    def add_asset(self, name: str, category: str, purchase_date: str, 
                  purchase_price: float, useful_life: Optional[int] = None):
        """新しい資産を追加"""
        if useful_life is None:
            useful_life = self.useful_life.get(category, 5)
        
        asset = {
            "id": f"asset_{len(self.assets) + 1}",
            "name": name,
            "category": category,
            "purchase_date": purchase_date,
            "purchase_price": purchase_price,
            "useful_life": useful_life,
            "current_value": purchase_price,
            "depreciation_method": "定額法",  # 定額法のみ対応
            "notes": ""
        }
        
        self.assets.append(asset)
        self.save_assets()
        return asset
    
    def calculate_depreciation(self, asset: Dict, target_year: int = None) -> Dict:
        """減価償却費を計算"""
        if target_year is None:
            target_year = datetime.now().year
        
        purchase_date = datetime.strptime(asset["purchase_date"], "%Y-%m-%d")
        purchase_year = purchase_date.year
        
        # 購入年の月数を計算
        if purchase_year == target_year:
            months_used = 13 - purchase_date.month
        else:
            months_used = 12
        
        # 定額法による減価償却費
        annual_depreciation = asset["purchase_price"] / asset["useful_life"]
        monthly_depreciation = annual_depreciation / 12
        depreciation_amount = monthly_depreciation * months_used
        
        # 現在価値を計算
        years_passed = target_year - purchase_year
        if years_passed > 0:
            years_passed = max(0, years_passed - 1)  # 購入年は部分計算
        
        total_depreciation = (annual_depreciation * years_passed) + depreciation_amount
        current_value = max(0, asset["purchase_price"] - total_depreciation)
        
        return {
            "depreciation_amount": depreciation_amount,
            "total_depreciation": total_depreciation,
            "current_value": current_value,
            "months_used": months_used
        }
    
    def get_assets_for_year(self, year: int) -> List[Dict]:
        """指定年の資産一覧を取得"""
        year_assets = []
        
        for asset in self.assets:
            purchase_date = datetime.strptime(asset["purchase_date"], "%Y-%m-%d")
            purchase_year = purchase_date.year
            
            # 購入年以降で、耐用年数内の資産
            if purchase_year <= year <= purchase_year + asset["useful_life"]:
                depreciation_info = self.calculate_depreciation(asset, year)
                asset_copy = asset.copy()
                asset_copy.update(depreciation_info)
                year_assets.append(asset_copy)
        
        return year_assets
    
    def get_total_depreciation_for_year(self, year: int) -> float:
        """指定年の総減価償却費を計算"""
        year_assets = self.get_assets_for_year(year)
        total = sum(asset["depreciation_amount"] for asset in year_assets)
        return total
    
    def update_asset(self, asset_id: str, **kwargs):
        """資産情報を更新"""
        for asset in self.assets:
            if asset["id"] == asset_id:
                asset.update(kwargs)
                break
        self.save_assets()
    
    def delete_asset(self, asset_id: str):
        """資産を削除"""
        self.assets = [asset for asset in self.assets if asset["id"] != asset_id]
        self.save_assets()
    
    def get_asset_categories(self) -> List[str]:
        """利用可能な資産カテゴリを取得"""
        return list(self.useful_life.keys())
    
    def add_custom_category(self, category: str, useful_life: int):
        """カスタムカテゴリを追加"""
        self.useful_life[category] = useful_life
