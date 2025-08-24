"""
基本的なテストファイル
CIパイプラインでの基本的な動作を確認
"""
import pytest
import sys
import os


def test_python_version():
    """Pythonバージョンが適切であることを確認"""
    assert sys.version_info >= (3, 8), f"Python version {sys.version_info} is too old"


def test_pytest_working():
    """pytestが正常に動作することを確認"""
    assert 1 + 1 == 2
    assert "hello" + " world" == "hello world"


def test_basic_math():
    """基本的な数学演算をテスト"""
    assert 2 * 3 == 6
    assert 10 / 2 == 5
    assert 2 ** 3 == 8


def test_string_operations():
    """文字列操作をテスト"""
    text = "Hello, World!"
    assert len(text) == 13
    assert text.upper() == "HELLO, WORLD!"
    assert text.lower() == "hello, world!"


def test_list_operations():
    """リスト操作をテスト"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1


def test_dict_operations():
    """辞書操作をテスト"""
    data = {"name": "Test", "age": 25, "city": "Tokyo"}
    assert len(data) == 3
    assert data["name"] == "Test"
    assert "age" in data
    assert data.get("country", "Japan") == "Japan"


def test_file_system():
    """ファイルシステムの基本操作をテスト"""
    # 現在のディレクトリが存在することを確認
    assert os.path.exists(".")
    assert os.path.isdir(".")
    
    # testsディレクトリが存在することを確認
    assert os.path.exists("tests")
    assert os.path.isdir("tests")


def test_import_system():
    """インポートシステムが正常に動作することを確認"""
    # 標準ライブラリのインポート
    import datetime
    import json
    import math
    
    # 基本的な使用
    assert datetime.datetime.now().year >= 2024
    assert json.dumps({"test": "value"}) == '{"test": "value"}'
    assert math.sqrt(16) == 4


class TestBasicClass:
    """基本的なクラスのテスト"""
    
    def test_class_creation(self):
        """クラスの作成とインスタンス化をテスト"""
        class SimpleClass:
            def __init__(self, value):
                self.value = value
            
            def get_value(self):
                return self.value
        
        obj = SimpleClass(42)
        assert obj.value == 42
        assert obj.get_value() == 42
    
    def test_inheritance(self):
        """継承をテスト"""
        class Parent:
            def __init__(self):
                self.parent_value = "parent"
        
        class Child(Parent):
            def __init__(self):
                super().__init__()
                self.child_value = "child"
        
        child = Child()
        assert child.parent_value == "parent"
        assert child.child_value == "child"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
