from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
import logging
from kiwoom import *

from conf.errorCode import *
import MainTrade
import TradeAlgo

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d',
    level=logging.DEBUG)

class Trader(API):
    def __init__(self):
        super().__init__()
        self.kw = Kiwoom()

        self.notify_fn = {}


        ########## EventLoop
        #self.login_event_loop = None

        ########## ScreenNo
        self.screen_real_search = "3000"

        #logging.debug("test")

        self.event_slots()

        self.login()
        self.start_setting()
        self.start_realFind()

    def login(self):
        # Login
        err_code = self.kw.login()
        if err_code != 1:
            logging.error("Login Fail")
            return
        logging.debug("Login success")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.kw.connect('on_event_connect', slot=self.login_slot)
        #self.OnReceiveTrData.connect(self.trdata_slot)

        #self.OnReceiveConditionVer.connect(self.recieve_condition_var)

        #self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveRealCondition.connect(self.receive_real_condition)
        #self.OnReceiveChejanData.connect(self.chejan_slot)
    
    def login_slot(self, errCode):
        logging.debug(errors(errCode))

        self.kw.unloop()
        #self.login_event_loop.exit()

    def start_setting(self):
        """
        account = self.account()
        logging.debug("계좌 정보 : " + str(account))
        desposit = self.disposit()
        logging.debug("예수금 : " + str(account))
        balance = self.balance()
        logging.debug("계좌 잔고 : " + str(account))
        """
        pass

    def start_realFind(self):
        self.kw.notify_fn["_on_receive_real_condition"] = self.search_condi
        condi_info = self.kw.get_condition_load()
        logging.debug(str(condi_info))

        condition_name = ""
        condition_index = 0
        condi_list = condi_info.split(';')

        del condi_list[-1]
        for cond_name, cond_id in condi_info: # 조건검색식 개수만큼 반복
            if cond_name == MainTrade.json_data["condi_search_name"]:
                condition_name = cond_name
                condition_index = cond_id
                #print(str(type(condition_name)) + "test " + str(condition_name) + " test " + str(condition_index) + " test ")

        if condition_index != "":
            #send = self.dynamicCall("SendCondition(QString, QString, int, int)", self.screen_real_search, condition_name, int(condition_index), 1)
            send = self.kw.send_condition(self.screen_real_search, condition_name, int(condition_index), 1)
            if send == 1:
                print("조건 검색 성공")
            else:
                print("조건신호 실패")

    def receive_real_condition(self, strCode, event_type, strConditionName, strConditionIndex):  
        """종목코드, 이벤트종류(I:편입, D:이탈), 조건식 이름, 조건명 인덱스"""
        try:
            if strConditionName == MainTrade.json_data["condi_search_name"]:
                print(strCode + "조건검색 확인")
                if TradeAlgo.checkstock(strCode) or True:
                    #self.find_stock.append(get_data)
                    #self.getCommRealData(strCode, 10)
                    #self.dynamicCall("SetRealReg(QString, QString, QString, QString", self.screen_real_search, strCode, self.realType.REALTYPE[], "1")
                    print("조건 확인 완료")
                    
                    self.my_stock_dict.update({strCode:{}})
                    self.my_stock_dict[strCode].update({"상태": 0})

                    self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_real_sise, strCode, '20', '1')

                    print("종목 정보 불러오기 성공" + str(self.price_dict[strCode]))
                    if TradeAlgo.FindBuy(self.price_dict[strCode]):
                        MainTrade.dbgout("[" + strCode + "] " + self.price_dict[strCode]['종목명'] + "  매수신호 발생") 
                        Account_num = MainTrade.SetAccount()
                        if(Account_num == -1):
                            MainTrade.dbgout("남은계좌 없음. 매수 실패")
                            return
                        buyStock_cnt = (MainTrade.vr_bank[Account_num]) / self.price_dict[strCode]["현재가"]
                        order_status = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", 
                                        "시장가매수", self.screen_trade_stock, self.account_num, 1, strCode, buyStock_cnt, 0, self.realType.SENDTYPE['거래구분']['시장가'], "")
                        
                        if order_status == 0:
                            print("매도주문 전달 성공")
                        else:
                            print("매도주문 전달 실패")
                            
        except Exception as e:
            logging.error(e)
        finally:
            self.real_condition_search_result = []
                    
                        
    def search_condi(self, event_data):
        try:
            logging.debug("function: search_condi")
            if event_data["event_type"] == "I":
                logging.debug("search_condi: check Insert")
                if TradeAlgo.checkstock(event_data["code"]) or True: #디버깅
                    logging.debug("search_condi: check condition")


                            
        except Exception as e:
            logging.error(e)
        finally:
            self.real_condition_search_result = []
        