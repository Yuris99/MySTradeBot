from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from conf.errorCode import *
import json

with open('.mydata/key.json') as json_file:
    json_data = json.load(json_file)


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        

        print("Kiwoom 클래스 호출")

        ########## 변수모음
        self.account_stock_dict = {}

        ########## 이벤트루프 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()




        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()



    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

    def login_slot(self, errCode):
        print(errors(errCode))

        self.login_event_loop.exit()

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_info(self):
        self.user_name = self.dynamicCall("GetLoginInfo(String)", "USER_NAME")
        self.user_id = self.dynamicCall("GetLoginInfo(String)", "USER_ID")
        self.account_count = self.dynamicCall("GetLoginInfo(String)", "ACCOUNT_CNT")
        self.account_list = self.dynamicCall("GetLoginInfo(String)", "ACCNO")
        self.account_num = self.account_list.split(';')

    def detail_account_info(self):
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num[0])
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", json_data["Account_Password"])
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", '0', "2000")

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num[0])
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", json_data["Account_Password"])
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, "2000")

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        """스크린번호, 요청이름, tr코드, 사용안함, 다음페이지"""

        if sRQName == "예수금상세현황요청":
            print("test")
            self.deposit = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "예수금")
            
            self.ok_deposit = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "출금가능금액")

            self.detail_account_info_event_loop.exit()

        if sRQName == "계좌평가잔고내역요청":
            self.total_buy_money = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "총매입금액")

            self.total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "총수익률(%%)")

            self.stockcnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})


                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())

                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()
            



