# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import time
from datetime import datetime
from numbers import Number
from threading import Thread

from easytrader.follower import BaseFollower
from easytrader.log import logger
from easytrader.utils.misc import parse_cookies_str


class PingAnFollower(BaseFollower):
    LOGIN_PAGE = "https://m.stock.pingan.com/invest/zuhe/detail.html"
    LOGIN_API = "https://m.stock.pingan.com/invest/chaogu/shipintougu/v2/checkToken"
    TRANSACTION_API = "https://m.stock.pingan.com/portfoliofront/zuhedetail/getProductTransferHistory"
    PORTFOLIO_URL = "https://m.stock.pingan.com/invest/zuhe/detail.html"
    WEB_REFERER = "https://m.stock.pingan.com/invest/zuhe/detail.html?WT.mc_id=WX-xxts-tctx&productNo=22608"

    def __init__(self):
        super().__init__()
        self._adjust_sell = None
        self._users = None

    def login(self, user=None, password=None, **kwargs):
        """
        PA登陆， 需要设置 cookies
        :param cookies: PA登陆需要设置 cookies， 具体见
            https://smalltool.github.io/2016/08/02/cookie/
        :return:
        """
        cookies = kwargs.get("cookies")
        if cookies is None:
            raise TypeError(
                "PA登陆需要设置 cookies， 具体见" "https://smalltool.github.io/2016/08/02/cookie/"
            )
        headers = self._generate_headers()
        self.s.headers.update(headers)
        cookie_dict = parse_cookies_str(cookies)
        self.s.cookies.update(cookie_dict)

        self.s.get(self.LOGIN_PAGE, params={"WT.mc_id": "WX-xxts-tctx", "productNo": "22608"})

        logger.info("登录成功")

    def follow(  # type: ignore
            self,
            users,
            strategies,
            total_assets=10000,
            initial_assets=None,
            adjust_sell=False,
            track_interval=10,
            trade_cmd_expire_seconds=120,
            cmd_cache=True,
            slippage: float = 0.0,
    ):
        """跟踪 PA 对应的模拟交易，支持多用户多策略
        :param users: 支持 easytrader 的用户对象，支持使用 [] 指定多个用户
        :param strategies: PA组合名, 类似 ZH123450
        :param total_assets: PA组合对应的总资产， 格式 [组合1对应资金, 组合2对应资金]
            若 strategies=['ZH000001', 'ZH000002'],
                设置 total_assets=[10000, 10000], 则表明每个组合对应的资产为 1w 元
            假设组合 ZH000001 加仓 价格为 p 股票 A 10%,
                则对应的交易指令为 买入 股票 A 价格 P 股数 1w * 10% / p 并按 100 取整
        :param adjust_sell: 是否根据用户的实际持仓数调整卖出股票数量，
            当卖出股票数大于实际持仓数时，调整为实际持仓数。目前仅在银河客户端测试通过。
            当 users 为多个时，根据第一个 user 的持仓数决定
        :type adjust_sell: bool
        :param initial_assets: PA组合对应的初始资产,
            格式 [ 组合1对应资金, 组合2对应资金 ]
            总资产由 初始资产 × 组合净值 算得， total_assets 会覆盖此参数
        :param track_interval: 轮训模拟交易时间，单位为秒
        :param trade_cmd_expire_seconds: 交易指令过期时间, 单位为秒
        :param cmd_cache: 是否读取存储历史执行过的指令，防止重启时重复执行已经交易过的指令
        :param slippage: 滑点，0.0 表示无滑点, 0.05 表示滑点为 5%
        """
        super().follow(
            users=users,
            strategies=strategies,
            track_interval=track_interval,
            trade_cmd_expire_seconds=trade_cmd_expire_seconds,
            cmd_cache=cmd_cache,
            slippage=slippage,
        )

        self._adjust_sell = adjust_sell

        self._users = self.warp_list(users)

        strategies = self.warp_list(strategies)
        total_assets = self.warp_list(total_assets)
        initial_assets = self.warp_list(initial_assets)

        if cmd_cache:
            self.load_expired_cmd_cache()

        self.start_trader_thread(self._users, trade_cmd_expire_seconds)

        for strategy_url, strategy_total_assets, strategy_initial_assets in zip(
                strategies, total_assets, initial_assets
        ):
            assets = self.calculate_assets(
                strategy_total_assets, strategy_initial_assets
            )
            try:
                strategy_id = self.extract_strategy_id(strategy_url)
                strategy_name = self.extract_strategy_name(strategy_url)
            except:
                logger.error("抽取交易id和策略名失败, 无效模拟交易url: %s", strategy_url)
                raise
            strategy_worker = Thread(
                target=self.track_strategy_worker,
                args=[strategy_id, strategy_name],
                kwargs={"interval": track_interval, "assets": assets},
            )
            strategy_worker.start()
            logger.info("开始跟踪策略: %s", strategy_name)

    def calculate_assets(self, total_assets=None, initial_assets=None):
        # 都设置时优先选择 total_assets
        if total_assets is None and initial_assets is not None:
            net_value = 1
            total_assets = initial_assets * net_value
        if not isinstance(total_assets, Number):
            raise TypeError("input assets type must be number(int, float)")
        if total_assets < 1e3:
            raise ValueError("pa总资产不能小于1000元，当前预设值 {}".format(total_assets))
        return total_assets

    @staticmethod
    def extract_strategy_id(strategy_url):
        return strategy_url

    def extract_strategy_name(self, strategy_url):
        base_url = "https://m.stock.pingan.com/portfoliofront/zuhe/queryProductInfo?_={}"
        params = {"_": self.get_timestamp_ms}
        jsonBody = {
            "appName": "PA18",
            "tokenId": "",
            "cltplt": "h5",
            "cltver": "1.0",
            "body": {
                "productNo": strategy_url,
                "grayEnv": "B"
            }
        }
        rep = self.s.post(base_url, params=params, json=jsonBody)
        return rep.json()["data"]["product"]["productName"]

    def extract_transactions(self, history):
        if int(history["data"]["totalrows"]) <= 0:
            return []
        raw_transactions = history["data"]["datas"]
        transactions = []
        for transaction in raw_transactions:
            if transaction["exec_price"] is None:
                logger.info("该笔交易无法获取价格，疑似未成交，跳过。交易详情: %s", transaction)
                continue
            transaction["price"]= transaction["exec_price"]
            transactions.append(transaction)

        return transactions

    def query_strategy_transaction(self, strategy, **kwargs):
        params = self.create_query_transaction_params(strategy)
        jsonBody = {"appName": "PA18",
                    "body": {"curPage": 1, "rowOfPage": 3, "productNo": strategy},
                    "cltplt": "h5",
                    "cltver": "1.0",
                    "tokenId": ""}
        rep = self.s.post(self.TRANSACTION_API, params=params, json=jsonBody)
        history = rep.json()

        transactions = self.extract_transactions(history)
        self.project_transactions(transactions, **kwargs)
        return self.order_transactions_sell_first(transactions)

    def create_query_transaction_params(self, strategy):
        params = {"_": self.get_timestamp_ms}
        return params

    # noinspection PyMethodOverriding
    def none_to_zero(self, data):
        if data is None:
            return 0
        return data

    # noinspection PyMethodOverriding
    def project_transactions(self, transactions, assets):
        for transaction in transactions:
            weight_diff = float(self.none_to_zero(transaction["singleAfterPosition"])) - float(
                self.none_to_zero(transaction["singleBeforePosition"]))

            initial_amount = abs(weight_diff)  * assets / float(transaction["exec_price"])

            transaction["datetime"] = datetime.strptime(
                (transaction["exec_date"] + " " + transaction["exec_time"])
                , '%Y%m%d %H:%M:%S'
            )

            transaction["stock_code"] = transaction["stock_code"].lower()

            transaction["action"] = "buy" if weight_diff > 0 else "sell"

            transaction["amount"] = int(round(initial_amount, -2))
            if transaction["action"] == "sell" and self._adjust_sell:
                transaction["amount"] = self._adjust_sell_amount(
                    transaction["stock_code"], transaction["amount"]
                )

    def _adjust_sell_amount(self, stock_code, amount):
        """
        根据实际持仓值计算雪球卖出股数
          因为pa的交易指令是基于持仓百分比，在取近似值的情况下可能出现不精确的问题。
        导致如下情况的产生，计算出的指令为买入 1049 股，取近似值买入 1000 股。
        而卖出的指令计算出为卖出 1051 股，取近似值卖出 1100 股，超过 1000 股的买入量，
        导致卖出失败
        :param stock_code: 证券代码
        :type stock_code: str
        :param amount: 卖出股份数
        :type amount: int
        :return: 考虑实际持仓之后的卖出股份数
        :rtype: int
        """
        stock_code = stock_code[-6:]
        user = self._users[0]
        position = user.position
        try:
            stock = next(s for s in position if s["证券代码"] == stock_code)
        except StopIteration:
            logger.info("根据持仓调整 %s 卖出额，发现未持有股票 %s, 不做任何调整", stock_code, stock_code)
            return amount

        available_amount = stock["可用余额"]
        if available_amount >= amount:
            return amount

        adjust_amount = available_amount // 100 * 100
        logger.info(
            "股票 %s 实际可用余额 %s, 指令卖出股数为 %s, 调整为 %s",
            stock_code,
            available_amount,
            amount,
            adjust_amount,
        )
        return adjust_amount

    @staticmethod
    def get_timestamp_ms():
        """获取当前时间的毫秒级时间戳"""
        return int(time.time() * 1000)
