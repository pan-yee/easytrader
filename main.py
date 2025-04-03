from http.cookiejar import debug

import easytrader


def xq():
    # 创建雪球用户并登陆
    user = easytrader.use('xq')
    user.prepare('xq.json')
    # print("获取资金状况:" + user.balance)
    # print("获取持仓:" + user.position)
    print(user.account_config)
    print(user.account_config.get("cookies"))
    xq_follower = easytrader.follower('xq')
    xq_follower.login(cookies=user.account_config.get("cookies"))
    # 创建银河用户并登陆
    userYh = yh()
    xq_follower.follow(userYh,
                       user.account_config.get("portfolio_code"),
                       total_assets=100000,
                       initial_assets=None,
                       adjust_sell=True,
                       track_interval=1,
                       trade_cmd_expire_seconds=120000000,
                       cmd_cache=True,
                       slippage=0.01, )


def yh():
    userYh = easytrader.use('yh_client',debug)
    userYh.prepare('yh_client.json')
    userYh.login()
    return userYh


def main():
    xq()


if __name__ == '__main__':
    main()
