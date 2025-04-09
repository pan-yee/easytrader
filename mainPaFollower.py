import easytrader


def paToYh():
    # print("获取资金状况:" + user.balance)
    # print("获取持仓:" + user.position)
    xq_follower = easytrader.follower('pa')
    xq_follower.login(cookies="PA")
    # 创建银河用户并登陆
    userYh = yh()
    xq_follower.follow(userYh,
                       "22608",
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
