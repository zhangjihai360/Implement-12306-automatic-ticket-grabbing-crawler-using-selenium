import time
import json
import os
import selenium
from lxml.builder import unicode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys



class Spider:
    def __init__(self):

        # 保存用户的基本信息
        self.info = {}

        #爬虫循环次数
        self.cycle_num = 1

        #获取用户信息
        self.get_info()

        #打开浏览器并设置浏览器为全屏
        self.driver = webdriver.Edge()
        self.driver.maximize_window()
        self.driver.get('https://kyfw.12306.cn/index/')

        # 获取主窗口的句柄
        self.main_window = self.driver.current_window_handle

        #进行自动抢票操作
        self.initial_login()

        time.sleep(100)

        #关闭浏览器
        self.driver.close()

    def input_info(self, use_history_info = '否'):
        """获取用户的信息并将基本信息保存到文件中"""

        if use_history_info == '否':
            #用户个人的具体信息
            self.username = input('请输入用户名：')
            self.password = input('请输入密码：')
            self.id_card_last = input('请输入身份证后四位：')
            self.cookies = []

            #保存用户的基本信息
            self.info = {}
            self.info['username'] = self.username
            self.info['password'] = self.password
            self.info['id_card_last'] = self.id_card_last

        else:
            print(f'欢迎回来{self.username}')
            with open("info.json", "r") as file:
                self.info = json.load(file)

            # 接收以前保存的信息
            self.username = self.info['username']
            self.password = self.info['password']
            self.id_card_last = self.info['id_card_last']
            self.cookies = self.info['cookies']

        #用户车票的具体信息
        self.from_station_name = input('请输入行程的起始站（只需要写城市即可）：')
        self.to_station_name = input('请输入行程的终点站（只需要写城市即可）：')
        self.train_date_name = input('请输入出行的日期（格式为：2025-02-25）：')
        self.seat_num = input('请输入你想要购买的座位编号（A-F，当且仅当剩余座位较多时为您购买）')
        self.student_ticket = input('是否要购买学生票（使用是或否来回答）：')

    def get_info(self):
        """从以前保存的文件中获取获取用户的基本信息与需求"""

        #检测info.json文件是否存在，存在则读取
        if os.path.exists("info.json"):
            with open("info.json", "r") as file:
                info = json.load(file)

            #接收用户名
            self.username = info['username']

            #询问用户是否使用以前保存的信息
            print(f'你有已保存的个人信息，用户名为：{self.username}')
            use_history_info = input('请问是否需要使用（使用是或否来回答）；')
            self.input_info(use_history_info)

        else:
            self.input_info()

    def web_page_initialization(self):
        """输入想要的车辆信息，加载车次信息"""

        #返回首页
        home_page_box = self.driver.find_element(By.ID, "J-index")
        home_page_box.click()

        # 定位输入框元素
        input_from_station = self.driver.find_element(by = By.ID, value = 'fromStationText')
        input_to_station = self.driver.find_element(by = By.ID, value = 'toStationText')
        input_train_date = self.driver.find_element(by = By.ID, value = 'train_date')

        # 清除输入框中的内容，并输入文字选择站点
        #起始站
        input_from_station.clear()
        input_from_station.send_keys(self.from_station_name)
        select_from_station = self.driver.find_element(by = By.XPATH,
                                                       value = f'//*[@id="panel_cities"]//span[text()="{self.from_station_name}"]/..')
        select_from_station.click()

        #终点站
        input_to_station.clear()
        input_to_station.send_keys(self.to_station_name)
        select_to_station = self.driver.find_element(by = By.XPATH,
                                                     value = f'//*[@id="panel_cities"]//span[text()="{self.to_station_name}"]/..')
        select_to_station.click()

        #出行时间
        input_train_date.clear()
        input_train_date.send_keys(self.train_date_name)

        #模拟鼠标点击搜素
        select_box = self.driver.find_element(by = By.ID, value = 'search_one')
        select_box.click()

        #等待新页面加载完成，并将操作目标切换到新页面
        self.driver.implicitly_wait(5)
        self.driver.switch_to.window(self.driver.window_handles[-1])

        #勾选二等座选项
        second_class_seat_box = self.driver.find_element(By.ID, "cc_seat_type_O_check")
        second_class_seat_box.click()

        #获取车票信息
        self.get_ticket_info()

    def initial_login(self):
        """刚进入网站时的登录操作"""

        if self.cookies:
            # 添加登录 Cookie
            for cookie in self.cookies:
                #检查cookie的域名
                if '.kyfw.12306.cn' in cookie['domain'] or 'kyfw.12306.cn' in cookie['domain']:
                    self.driver.add_cookie(cookie)

            # 刷新页面，使 Cookie 生效
            self.driver.refresh()
        else:
            #等待页面刷新完毕
            self.driver.implicitly_wait(5)

            #进入登录页面
            log_in_box = self.driver.find_element(By.ID, "J-btn-login")
            log_in_box.click()

            #登录账号
            self.log_in()
            self.driver.implicitly_wait(10)

        #加载车次信息
        self.web_page_initialization()

    def log_in(self):
        """登录账号并保存账号和cookie"""

        #获取用户名输入框位置并输入用户名
        username_box = self.driver.find_element(By.ID, "J-userName")
        username_box.clear()
        username_box.send_keys(self.username)

        # 获取密码输入框位置并输入密码
        password_box = self.driver.find_element(By.ID, "J-password")
        password_box.clear()
        password_box.send_keys(self.password)

        #获取登录按钮位置并登录
        log_box = self.driver.find_element(By.ID, "J-login")
        log_box.click()

        # 等待弹窗出现后输入身份证后4位
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, "modal")))
        id_card_last_box = self.driver.find_element(By.ID, "id_card")
        id_card_last_box.clear()
        id_card_last_box.send_keys(self.id_card_last)

        #获取验证码
        get_verification_code_box = self.driver.find_element(By.ID, "verification_code")
        get_verification_code_box.click()

        #手动输入验证码到python中
        verification_code_box = self.driver.find_element(By.ID, "code")
        verification_code = input('请输入验证码：')
        time.sleep(8)

        #自动提交验证码
        verification_code_box.send_keys(verification_code)

        #提交验证码
        submit_verification_code = self.driver.find_element(By.ID, "sureClick")
        submit_verification_code.click()

        # 获取cookie并保存到文件
        self.cookies = self.driver.get_cookies()
        self.info['cookies'] = self.cookies
        with open("info.json", "w") as file:
            json.dump(self.info, file)

    def wait_ticket(self):
        """暂停十秒，重新爬取信息"""

        #暂停十秒
        time.sleep(10)

        #刷新页面
        self.driver.refresh()

        # 勾选二等座选项
        second_class_seat_box = self.driver.find_element(By.ID, "cc_seat_type_O_check")
        second_class_seat_box.click()

        #重新获取车票信息
        self.get_ticket_info()

    def get_ticket_info(self):
        """获取车票信息，如果有剩余车票则预订"""

        #输出当前已经循环的次数
        print(f'正在执行第{self.cycle_num}次抢票操作')
        self.cycle_num = self.cycle_num + 1

        #有余票执行预订操作，没有余票执行等待操作
        try:
            #定位有余票车次的预订按钮
            self.book_ticket_box = self.driver.find_element(By.XPATH,
                        "//*[contains(@aria-label, '二等座') and (contains(., '有') or translate(., '0123456789', '') != .)]/following-sibling::*[@class='no-br']/*")

        #如果没有余票会报错，这里我们使用异常处理执行等待操作
        except NoSuchElementException as e:
            self.wait_ticket()

        #对于预订后出现的一切问题我们都将其返回主窗口重新运行
        try:
            #点击预订按钮
            self.book_ticket()

        except:
            # 获取所有窗口句柄
            all_windows = self.driver.window_handles

            # 关闭所有非主窗口
            for window in all_windows:
                if window != self.main_window:
                    self.driver.switch_to.window(window)  # 切换到该窗口
                    self.driver.close()  # 关闭该窗口

            # 切换回主窗口
            self.driver.switch_to.window(self.main_window)

            #重新进行抢票操作
            self.web_page_initialization()

    def book_ticket(self):
        """发现余票后使用函数预订，需要传入预订按钮的位置"""

        #点击预订按钮
        self.book_ticket_box.click()

        #上一步操作可能会引起一个登录的弹窗，这里对其进行处理
        try:
            WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.ID, "login")))
            self.log_in()
            self.driver.implicitly_wait(10)

        except TimeoutException:
            pass

        #选择乘车人
        choose_rider = self.driver.find_element(By.ID, "normalPassenger_0")
        choose_rider.send_keys(Keys.SPACE)

        #上一步操作可能会引起一个是否购买学生票的弹窗，这里对其进行处理
        try:
            #等待弹窗的出现
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
                By.XPATH, "//*[@id='dialog_xsertcj']/div[2]")))

            if self.student_ticket == '是':
                student_ticket_box = self.driver.find_element(By.ID, "dialog_xsertcj_ok")
                student_ticket_box.click()
            else:
                student_ticket_box = self.driver.find_element(By.ID, "dialog_xsertcj_cancel")
                student_ticket_box.click()

        except TimeoutException:
            pass

        #提交订单
        submit_order_box = self.driver.find_element(By.ID, "submitOrder_id")
        submit_order_box.click()

        #处理弹窗并确认(注意：本程序中没有选座功能)
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
            By.ID, "content_checkticketinfo_id")))
        qr_submit_box = self.driver.find_element(By.ID, "qr_submit_id")

        time.sleep(2)

        qr_submit_box.click()

        time.sleep(2)

        self.driver.execute_script('arguments[0].click();', qr_submit_box)

        #进入支付阶段
        self.payment()

    def payment(self):
        """处理支付过程，使用微信支付"""

        # 等待新页面加载完成，并将操作目标切换到新页面
        time.sleep(10)
        self.driver.implicitly_wait(10)
        self.driver.switch_to.window(self.driver.window_handles[-1])

        #点击支付按钮
        pay_box = self.driver.find_element(By.ID, "payButton")
        pay_box.click()

        #处理购买保险弹窗，不购买保险
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='toolbar_Div']/div[3]")))
        not_buy_box = self.driver.find_element(By.ID, "continuePay")
        not_buy_box.click()

        try:
            #点击微信支付
            wechat_pay_box = self.driver.find_element(By.XPATH,
                                        '// *[ @ id = "toolbar_Div"] / div[2] / div[2] / div / form / div[10]')
            wechat_pay_box.click()
            print(1)
        except:
            try:
                # 点击微信支付
                wechat_pay_box = self.driver.find_element(By.XPATH,
                                                    '//*[@id="toolbar_Div"]/div[2]/div[2]/div/form/div[10]/div')
                wechat_pay_box.click()
                print(2)
            except:
                # 点击微信支付
                wechat_pay_box = self.driver.find_element(By.XPATH,
                                                          '//*[@id="toolbar_Div"]/div[2]/div[2]/div/form/div[10]/div/a')
                wechat_pay_box.click()
                print(3)


if __name__ == '__main__':

    Spider()




