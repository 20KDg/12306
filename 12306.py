# -*- coding: utf-8 -*-
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import itchat
import qqMsg
import config

'''
实现功能：
   1）根据车次和座位选票  
   2）查询超时重刷
   3）自动提交订单
   
12306相关参数
座位简写----SW:商务  YD:一等座  ED:二等座 GR:高软 PR:软 DW:动卧 YW:硬卧  YZ:硬座 RZ 软座
选座位下拉值------ 3:硬卧 1：硬座 4：软卧 O：二等座 M:一等座  9商务座
'''

login_url = "https://kyfw.12306.cn/otn/login/init"
initmy_url = "https://kyfw.12306.cn/otn/index/initMy12306"
ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
mp_url="https://kyfw.12306.cn/otn/confirmPassenger/initDc"#购票页面
pay_url="https://kyfw.12306.cn/otn//payOrder/init"

#维护一个座位和下拉值的对应关系
zuowei_select = {"SW":"9","YD":"M","ED":"O","PR":"4","YW":"3","YZ":"1"}

#判断购票是否成功
buyFlag = False


# 发送信息类型 0:发送QQ信息  1：发送微信信息
sendType = 0







def login(browser):

    time.sleep(1)
    #输入用户名
    elem = browser.find_element_by_id("username")
    elem.clear()
    elem.send_keys(config.username)
    #输入密码
    elem = browser.find_element_by_id("password")
    elem.clear()
    elem.send_keys(config.password)
    print(u"等待验证码，自行输入...")
    while True:
        if browser.current_url != initmy_url:
            time.sleep(2)

        else:

            break
    print("验证成功")
    return browser

def main():

    #itchat.auto_login()

    browser = webdriver.Chrome()
    browser.get(login_url)
    browser = login(browser)
    browser.get(ticket_url)
    count = 0
    global  buyFlag
    while (buyFlag == False and browser.current_url == ticket_url  ):
        browser.add_cookie({'name': '_jc_save_fromStation', 'value': config.fromStation})
        browser.add_cookie({'name': '_jc_save_toStation', 'value': config.toStation})
        login_user = browser.find_element_by_id('login_user').text
        if login_user == "登录":
            sendMsg(sendType,config.to_user,"请登录")
            currentWin = browser.current_window_handle
            browser.find_element_by_id('login_user').click()
            browser = fowardPage(browser, currentWin)
            browser =login(browser)
            browser.get(ticket_url)
            continue
        for fromDate in config.fromDates:
            count += 1
            browser.add_cookie({'name': '_jc_save_fromDate', 'value': fromDate})
            browser.refresh()
            print(u'开始第 %s 次查询...' % count)
            sendMsg(sendType, config.to_user, u'开始第 %s 次查询...' % count)
            try:
                btnElm =  WebDriverWait(browser, 1).until(
                    EC.presence_of_element_located((By.ID, "query_ticket")))
                btnElm.click()
            except:
                continue
            # 等待加载完成 判断是否有可预订的车次
            try:
                WebDriverWait(browser, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btn72"))
                )
            except:
                continue
            try:
                for i in browser.find_elements_by_class_name('btn72'):
                    train = i.find_element_by_xpath('../..')
                    cells = train.find_elements_by_tag_name('td')
                    # 车次
                    tnumber = train.find_element_by_class_name('train').text
                    # 始发站-结束站
                    fromToStation = re.sub('\n', '-', train.find_element_by_class_name('cdz').text)
                    # 始发时间-结束时间
                    fromToDate = re.sub('\n', '-', train.find_element_by_class_name('cds').text)

                    ls = re.sub('\n', '-', train.find_element_by_class_name('ls').text)

                    # 按钮元素
                    btnElm = cells[12]

                    # 车次信息
                    checiInfo = {}
                    checiInfo["SW"] = cells[1].text
                    checiInfo["YD"] = cells[2].text
                    checiInfo["ED"] = cells[3].text
                    checiInfo["GR"] = cells[4].text
                    checiInfo["PR"] = cells[5].text
                    checiInfo["DW"] = cells[6].text
                    checiInfo["YW"] = cells[7].text
                    checiInfo["RZ"] = cells[8].text
                    checiInfo["YZ"] = cells[9].text

                    '''
                   优先级  车次>座位号
                  '''
                    if type == 0:
                        for checi in config.checis:
                            # 判断车子是否是想要的车次
                            if tnumber == checi:
                                # 判断座位是否是想要的座位
                                for zc in config.zuocis:
                                    # 条件满足 有票
                                    if checiInfo[zc] != '--':
                                        # 座位下拉值
                                        zuoweiSelect = zuowei_select[zc]
                                        # 打印车次信息
                                        showCheciInfo(fromDate,tnumber, fromToStation, fromToDate, cells)
                                        # 以上条件都满足 开始购票啦
                                        currentWin = browser.current_window_handle
                                        btnElm.click()
                                        buyTicket(browser, currentWin, zuoweiSelect)

                    '''
                    优先级  座位号>车次
                  '''
                    if type == 1:
                        for zc in config.zuocis:
                            if checiInfo[zc] != '--':
                                # 判断车子是否是想要的车次
                                # 判断座位是否是想要的座位
                                for checi in config.checis:
                                    # 条件满足 有票
                                    if tnumber == checi:
                                        # 座位下拉值
                                        zuoweiSelect = zuowei_select[zc]
                                        # 打印车次信息
                                        showCheciInfo(fromDate,tnumber, fromToStation, fromToDate, cells)
                                        # 以上条件都满足 开始购票啦
                                        currentWin = browser.current_window_handle
                                        btnElm.click()
                                        buyFlag =  buyTicket(browser, currentWin, zuoweiSelect)

            except BusinessException as e:
                # 如果购票失败则跳到购票页面
                # selectYuding = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "selectYuding")))
                # currentWin = browser.current_window_handle
                # selectYuding.click()
                # browser = fowardPage(browser, currentWin)
                browser.get(ticket_url)
                #itchat.send(e.value, toUserName='filehelper')
                sendMsg(sendType, config.to_user, e.value)

                print("\033[0;31;40m\t"+e.value+"\033[0m")
                continue




# 打印车次信息
def showCheciInfo(fromDate,tnumber,fromToStation,fromToDate,cells):
    try:
        tickMsg = "时间："+fromDate+" 车次：" + tnumber + " " + fromToStation + " " + fromToDate + "商务:" + cells[1].text+" 一等：" + cells[2].text + " 二等：" + cells[3].text + " 高软：" + cells[4].text + " 软："\
                   + cells[5].text+ " 动卧：" + cells[6].text + " 硬卧：" + cells[7].text + " 软座：" + cells[8].text + " 硬座：" + cells[9].text
        print(tickMsg)
        itchat.send(tickMsg, toUserName='filehelper')
    except:
        raise BusinessException("打印失败")

def test():
    global buyFlag
    buyFlag = True

## 进入购票页面开始购票
'''
currentWin:当前窗口
zuoweiSelect：购票页面下拉值
'''
def buyTicket(browser,currentWin,zuoweiSelect):
    global buyFlag
    #重定向到购票页面
    browser = fowardPage(browser, currentWin)
    try:
        # 选人
        selectPerson(browser)
    except:
        raise BusinessException("选人失败--跳转到购票页面重新查询")

    # 选座位'
    try:
        seatType_1 =  WebDriverWait(browser, 2).until(EC.presence_of_element_located((By.ID, "seatType_1")))
        seatType_1.send_keys(zuoweiSelect)
    except:
        raise BusinessException("选座位失败--跳转到购票页面重新查询")

    # 一切准备就绪 提交订单
    try:
        submitOrder_id =  WebDriverWait(browser, 2).until(EC.element_to_be_clickable((By.ID, "submitOrder_id")))
        submitOrder_id.click()
    except:
        raise BusinessException("提交订单--跳转到购票页面重新查询")

    #确认订单

    try:
        qr_submit_id =  WebDriverWait(browser, 2).until(EC.element_to_be_clickable((By.ID, "qr_submit_id")))
        qr_submit_id.click()
    except:
        try:
            qr_submit_id = WebDriverWait(browser, 2).until(EC.element_to_be_clickable((By.ID, "qr_submit_id")))
            qr_submit_id.click()
        except:
            raise BusinessException("购票失败-没有余票--跳转到购票页面重新查询")
    url = browser.current_url

    if url.index(pay_url)>-1:
        print("购票成功：订单页面-->" + url)
        #itchat.send("购票成功：订单页面-->" + url)
        sendMsg(sendType, config.to_user,  "购票成功：订单页面-->" + url)

        buyFlag = True


# 根据人的名字自动选中人
def selectPerson(browser):
    lis = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@id='normal_passenger_id']/li")))
    for person in lis:

        personName = person.text
        if personName in config.persons:
            person.find_element_by_tag_name("input").click()


#自定义异常
class BusinessException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)



#跳转重定向页面
def fowardPage(browser,currentWin):
    # 跳转到购票页面
    handles = browser.window_handles
    for i in handles:
        if currentWin == i:
            continue
        else:
            # 将driver与新的页面绑定起来
            browser = browser.switch_to_window(i)
    return browser

'''
type 0:发送QQ信息  1：发送微信信息
to  接受人用户名
msg 发送内容
'''

def sendMsg(type,to,msg):
    if type==0:#发送QQ信息
        qqMsg.send_qq(to,msg)
    else:#发送微信信息
        itchat.send(msg, toUserName=to)




if __name__ == '__main__':
    main()


