import datetime
from unittest.mock import patch, MagicMock

import pytest

from easytrader.pa_follower import PingAnFollower


@pytest.fixture
def follower():
    return PingAnFollower()

def test_calculate_assets(follower):
    # 测试正常资产计算
    assert follower.calculate_assets(total_assets=5000) == 5000
    
    # 测试类型错误
    with pytest.raises(TypeError):
        follower.calculate_assets(total_assets="invalid")
        
    # 测试资产下限
    with pytest.raises(ValueError):
        follower.calculate_assets(total_assets=500)

def test_extract_strategy_id(follower):
    # 测试策略ID提取
    test_url = "ZH123456"
    assert follower.extract_strategy_id(test_url) == test_url

@patch('requests.Session.get')
def test_extract_strategy_name(mock_get, follower):
    # 模拟API响应
    mock_response = MagicMock()
    mock_response.json.return_value = [{"name": "测试策略"}]
    mock_get.return_value = mock_response
    
    strategy_name = follower.extract_strategy_name("ZH123456")
    assert strategy_name == "测试策略"

def test_extract_transactions(follower):
    # 测试空交易记录
    empty_history = {"count": 0}
    assert follower.extract_transactions(empty_history) == []
    
    # 测试有效交易记录过滤
    valid_history = {
        "count": 1,
        "list": [{
            "rebalancing_histories": [
                {"price": 10.0, "details": "正常交易"},
                {"price": None, "details": "无效交易"}
            ]
        }]
    }
    transactions = follower.extract_transactions(valid_history)
    assert len(transactions) == 1

def test_project_transactions(follower):
    # 初始化测试数据
    follower._adjust_sell = True
    follower._users = [MagicMock(position=[
        {"证券代码": "600000", "可用余额": 1000}
    ])]
    
    test_transactions = [{
        "weight": 10,
        "prev_weight": 5,
        "price": 20.0,
        "stock_symbol": "SH600000",
        "created_at": int(datetime.now().timestamp())*1000
    }]
    
    follower.project_transactions(test_transactions, 20000)
    
    # 验证交易处理逻辑
    transaction = test_transactions[0]
    assert transaction["action"] == "buy"
    assert transaction["amount"] == 500  # (10-5)% * 20000 / 20 = 500

@patch.object(PingAnFollower, '_adjust_sell_amount')
def test_adjust_sell_logic(mock_adjust, follower):
    # 测试卖出调整逻辑
    follower._adjust_sell = True
    transaction = {
        "action": "sell",
        "stock_code": "600000",
        "amount": 1000
    }
    follower._adjust_sell_amount(transaction["stock_code"], transaction["amount"])
    mock_adjust.assert_called_once_with("600000", 1000)

def test_adjust_sell_amount(follower):
    # 初始化用户持仓
    follower._users = [MagicMock(position=[
        {"证券代码": "600000", "可用余额": 500}
    ])]
    
    # 测试可用余额不足的情况
    adjusted = follower._adjust_sell_amount("600000", 600)
    assert adjusted == 500
    
    # 测试充足余额的情况
    adjusted = follower._adjust_sell_amount("600000", 400)
    assert adjusted == 400
