from os import stat
import sys

from PyQt5.QtWidgets import QApplication

from mydata import keyManager
from telog import Telog
import TradeAlgo

from kiwoom.kw import Kiwoom


class MainApp:
    def __init__(self):
        self.logger = Telog().logger
        self.logger.debug("Class: MainApp")
        self.kw = Kiwoom()

        #Account
        self.vr_bank = [] #분할매매 변수

        self.SetStart() #vrbank 변수를 초기화해줌
        self.StartApp() #키움 로그인하고 기본설정을 해주는 함수
        self.PriceSetting() #로그인한 정보를 가지고 가상변수를 초기화 / 콜백함수를 설정해주는 함수
        self.Trade() #실제 매매를 시작할 함수

    def SetStart(self):
        self.target_buy_count = keyManager.getJsonData("target_buy_count")
        self.max_bought_money = keyManager.getJsonData("max_bought_money")
        
        # add callback function
        self.kw.reg_callback("OnReceiveRealCondition", self.kw.screen_real_search, self.search_condi)
        self.kw.reg_callback("OnReceiveTrData", "현재가요청", self.check_start_trade)
        self.kw.reg_callback("OnSellStock", "매도완료", self.reset_vr_bank)
        self.kw.reg_callback("StartSetStock", "미매도종목", self.set_vrbank)
        for i in range(self.target_buy_count):
            self.vr_bank.append({"사용여부" : False,
                                "사용종목" : ""})
        self.logger.debug("vr_bank = " + str(self.vr_bank))
        
    def PriceSetting(self):
        for i in range(self.target_buy_count):
            self.vr_bank[i]["출금가능금액"] = min(self.max_bought_money, int(self.kw.pos_deposit)/self.target_buy_count)


    def set_vrbank(self, code):
        for i in range(self.target_buy_count):
            if self.vr_bank[i]['사용여부'] is False:
                self.vr_bank[i]['사용여부'] = True
                self.vr_bank[i]['사용종목'] = code
                return i
        return -1

    def StartApp(self):
        self.logger.debug("function: StartApp")
        self.kw.login()
        self.kw.init_trading()
        
        #실시간 검색(장시작구분)
        self.kw.set_real_reg("1001", "", "215;20;214", 0) 
        #self.kw.real_list.append("market")

    def Trade(self):
        self.logger.debug("function: Trade")
        #self.logger.info("단타 자동매매를 시작합니다.")

        #start timer?

        #condi_info = self.kw.get_condition_load()
        self.kw.get_condition_load() #Call realCondition


    def search_condi(self, event_data):
        self.logger.debug("function: search_condi")
        """키움모듈의 OnReceiveRealCondition 이벤트 수신되면 호출되는 callback함수
        이벤트 정보는 event_data 변수로 전달된다.

            ex)
            event_data = {
                "code": strCode, # "066570"
                "event_type": event_type, # "I"(종목편입), "D"(종목이탈)
                "condi_name": condi_name, # "스켈핑"
                "condi_index": condi_index # "004"
            }
        :param dict event_data:
        :return:
        """

        self.logger.debug("Condition check")
        strCode = event_data["code"]
        #Get TR data (start, curr)
        status = self.kw.get_curr_price(strCode)

        if status == 0:
            self.logger.debug("request check")
        else:
            self.logger.error("request error")

    def check_start_trade(self, event_data):
        self.logger.debug("function: check_start_trade")
    
        if TradeAlgo.FindBuy(event_data):
            self.logger.info("\n매수 종목 발생 : " + event_data['종목코드'])
            
            vr_cnt = self.set_vrbank(event_data['종목코드'])
            if vr_cnt == -1:
                self.logger.info("\n모든 계좌가 사용중입니다")
                self.logger.info("\n매수에 실패하였습니다")
                return
            buy_stock_cnt = (self.vr_bank[vr_cnt]['출금가능금액'] / event_data["현재가"]) - 1
            order_status = self.kw.buy_marketPrice(event_data['종목코드'], buy_stock_cnt)
            self.logger.info("매수를 시도합니다"
                            +"\n종목번호 : " + event_data['종목코드'])
                            
            
            if order_status == 0:
                self.logger.debug("Sucessful Call BuyFunction")
            else:
                self.logger.error("Fail to Call BuyFunction")

    def reset_vr_bank(self, code):
        del(self.kw.stock_info[code])
        check = False
        for i in range(self.target_buy_count):
            if self.vr_bank[i]['사용종목'] == code:
                self.vr_bank[i]['사용여부'] = False
                self.logger.debug("Reset vr_bank " + str(i))
                check = True
        if not check:
            self.logger.error("분할계좌를 초기화하지 못했습니다.")








if __name__=='__main__':
    app = QApplication(sys.argv)
    Main = MainApp()
    sys.exit(app.exec_())