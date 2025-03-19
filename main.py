import easytrader


def main():
    user = easytrader.use('xq')
    user.prepare('xq.json')
    # print("获取资金状况:" + user.balance)
    # print("获取持仓:" + user.position)
    print(user.account_config)
    print(user.account_config.get("cookies"))
    xq_follower = easytrader.follower('xq')
    xq_follower.login(cookies=user.account_config.get("cookies"))
    xq_follower.follow(user, user.account_config.get("portfolio_code"))

if __name__ == '__main__':
    main()
