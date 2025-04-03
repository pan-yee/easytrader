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
                       100000,
                       None,
                       False,
                       1,
                       1200000000,
                       True,
                       0.01)


def yh():
    return easytrader.use('yh')


def main():
    xq()


if __name__ == '__main__':
    main()
