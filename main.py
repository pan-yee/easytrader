import easytrader


def xqToYh():
    userXq = xq()
    # print("获取资金状况:" + user.balance)
    # print("获取持仓:" + user.position)
    xq_follower = easytrader.follower('xq')
    xq_follower.login(cookies=userXq.account_config.get("cookies"))
    # 创建银河用户并登陆
    userYh = yh()
    xq_follower.follow(userYh,
                       userXq.account_config.get("portfolio_code"),
                       total_assets=100000,
                       initial_assets=None,
                       adjust_sell=True,
                       track_interval=1,
                       trade_cmd_expire_seconds=120,
                       cmd_cache=True,
                       slippage=0.01, )

def xqToThs():
    userXq = xq()
    xq_follower = easytrader.follower('xq')
    # 创建同花顺通用用户并登陆
    userThs = ths()
    xq_follower.follow(userThs,
                       userXq.account_config.get("portfolio_code"),
                       total_assets=100000,
                       initial_assets=None,
                       adjust_sell=True,
                       track_interval=1,
                       trade_cmd_expire_seconds=120,
                       cmd_cache=True,
                       slippage=0.01, )

def xq():
    # 创建雪球用户并登陆
    userXq = easytrader.use('xq',debug=True)
    userXq.prepare('xq.json')
    # print("获取资金状况:" + user.balance)
    # print("获取持仓:" + user.position)
    #print(user.account_config)
    #print(user.account_config.get("cookies"))
    return userXq
def yh():
    userYh = easytrader.use('yh_client',debug=True)
    userYh.prepare('yh_client.json')
    return userYh
def ths():
    userThs = easytrader.use('universal_client',debug=True)
    userThs.prepare(user='用户名', password='雪球、银河客户端为明文密码', exe_path='E:\\同花顺软件\\同花顺\\xiadan.exe', comm_password='华泰通讯密码，其他券商不用')
    return userThs


def main():
    xqToYh()


if __name__ == '__main__':
    main()
