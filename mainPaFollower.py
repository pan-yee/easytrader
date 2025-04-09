import easytrader
from easytrader.utils.misc import file2dict


def paToYh():
    account = file2dict("pa.json")
    xq_follower = easytrader.follower('pa')
    xq_follower.login(cookies=account["cookies"])
    # 创建银河用户并登陆
    userYh = yh()
    xq_follower.follow(userYh,
                       account["portfolio_code"],
                       total_assets=100000,
                       initial_assets=None,
                       adjust_sell=True,
                       track_interval=1,
                       trade_cmd_expire_seconds=120,
                       cmd_cache=True,
                       slippage=0.01, )


def yh():
    userYh = easytrader.use('yh_client', debug=True)
    userYh.prepare('yh_client.json')
    return userYh


def main():
    paToYh()


if __name__ == '__main__':
    main()
