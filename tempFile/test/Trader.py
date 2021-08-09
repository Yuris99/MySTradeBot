from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import scientific
from PyQt5.QtWidgets import QApplication
import logging
from kiwoom import *

from conf.errorCode import *
import MainTrade
import TradeAlgo
from conf import kiwoomType

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d',
    level=logging.DEBUG)

class Trader(API):
    def __init__(self):
        super().__init__()
        self.kw = Kiwoom()

        self.notify_fn = {}
        self.stock_dict = []
        
        self.realType = kiwoomType.RealType()


        ########## EventLoop
        #self.login_event_loop = None

        ########## ScreenNo
        self.screen_my_info = "1000"
        self.screen_my_stock_info = "2000"
        self.screen_real_search = "3000"
        self.screen_real_sise = "3500"
        self.screen_trade_stock = "4000"

        #logging.debug("test")

        self.event_slots()

        self.login()
        self.start_setting()
        self.start_realFind()

    def event_slots(self):
        #help(Kiwoom.connect)
        #self.OnEventConnect.connect(self.login_slot)
        self.kw.connect('on_event_connect', slot=self.login_slot)

        self.kw.connect('on_receive_tr_data', slot=self.on_receive_tr_data)
        #self.OnReceiveConditionVer.connect(self.recieve_condition_var)
        self.kw.connect('on_receive_condition_ver', slot=self.recieve_condition_ver)

        #self.OnReceiveRealData.connect(self.realdata_slot)
        self.kw.connect('on_receive_real_data', slot=self.realdata_slot)
        #self.OnReceiveRealCondition.connect(self.receive_real_condition)
        self.kw.connect('on_receive_real_condition', slot=self.receive_real_condition)
        #self.OnReceiveChejanData.connect(self.chejan_slot)
        self.kw.connect('on_receive_chejan_data', slot=self.chejan_slot)

        self.kw.connect('on_receive_msg', slot=self._on_receive_msg)
        
        logging.debug("function Out: event_slots")
    
    def login_slot(self, errCode):
        logging.debug(errors(errCode))

        self.kw.unloop()
        #self.login_event_loop.exit()

    def login(self):
        # Login
        err_code = self.kw.login()
        if err_code == 0:
            logging.error("Login Fail")
            return
        logging.debug("Login success")

    def start_setting(self):
        account = self.getAccount()
        logging.debug("계좌 정보 : " + str(account))
        deposit = self.getDeposit()
        logging.debug("예수금 : " + str(deposit))
        """
        balance = self.balance()
        logging.debug("계좌 잔고 : " + str(account))
        """
        pass

    def getAccount(self):
        #help(Kiwoom.get_login_info)
        accountCnt = int(self.kw.get_login_info('ACCOUNT_CNT'))
        accounts = self.kw.get_login_info('ACCLIST').split(';')[:accountCnt] #계좌 모음

        user_id = self.kw.get_login_info('USER_ID')  # 유저아이디
        user_name = self.kw.get_login_info('USER_NAME')  # 유저이름
        
        # 접속 서버 타입
        server = self.kw.get_login_info('GetServerGubun')
        server = '모의투자' if server.strip() == '1' else '실서버'

        # 첫번 째 계좌 사용 (거래종목에 따라 확인)
        self.account = accounts[0]

        return {  # 딕셔너리 리턴
            '계좌개수': accountCnt,
            '계좌번호': accounts,
            '유저아이디': user_id,
            '유저이름': user_name,
            '서버구분': server
        }
    def getDeposit(self):
        logging.debug("function: getDeposit")
        inputs = {
            '계좌번호': self.account,
            '비밀번호': MainTrade.json_data['Account_Password'],
            '비밀번호입력매체구분': "00",
            "조회구분": "2"
        }
        for key, val in inputs.items():
            self.kw.set_input_value(key, val)
        self.kw.comm_rq_data("예수금상세현황요청", "opw00001", '0', self.screen_my_info)
        
        self.kw.loop()


    def start_realFind(self):
        self.notify_fn["_on_receive_real_condition"] = self.search_condi
        condi_info = self.kw.get_condition_load()
        logging.debug(str(condi_info))

    def _on_receive_tr_data(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        """스크린번호, 요청이름, tr코드, 사용안함, 다음페이지"""
        logging.debug("function: trdata_slot")

        if sRQName == "예수금상세현황요청":
            self.deposit = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "예수금")
            
            self.ok_deposit = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "출금가능금액")
            
            MainTrade.dbgout(f"키움계좌에 로그인되었습니다.\n이름 : {self.user_name}\nID : {self.user_id}\n보유 계좌 수 : {self.account_count}\n계좌번호 : {self.account_num[0]}\n예수금 : {format(int(self.deposit), ',')}원\n출금가능금액 : {format(int(self.ok_deposit), ',')}원")

            self.kw.unloop()

        if sRQName == "계좌평가잔고내역요청":
            self.total_buy_money = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "총매입금액")

            self.total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "총수익률(%)")
            self.total_profit_loss_rate_result = float(self.total_profit_loss_rate)
            self.detail_account_info_event_loop.exit()


        if sRQName == "주식기본정보조회":
            print("종목불러오기 시작")
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()
            name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목명")
            name = name.strip()
            currprice = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "현재가")
            currprice = abs(int(currprice))
            startprice = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "시가")
            startprice = abs(int(startprice))
            tradeValue = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "거래량")
            tradeValue = abs(int(tradeValue))

            if code not in self.price_dict:
                self.stock_dict.update({code:{}})
            self.stock_dict[code].update({"종목명": name})
            self.stock_dict[code].update({"현재가": currprice})
            self.stock_dict[code].update({"시가": startprice})
            self.stock_dict[code].update({"거래량": tradeValue})


            #print(self.price_dict[code])
            logging.debug("Sucessful load StockData : " + str(self.stock_dict[code]))
            #elf.get_stock_info_event_loop.exit()
    
    def recieve_condition_ver(self, bRet, sMsg):
        logging.debug("function: recieve_condition_ver")
        conditionNameList = self.kw.get_condition_name_list()
        logging.debug(str(conditionNameList))
        condition_name = ""
        condition_index = 0
        condi_list = conditionNameList.split(';')

        del condi_list[-1]
        for data in condi_list: # 조건검색식 개수만큼 반복
            a = data.split("^")
            if a[1] == MainTrade.json_data["condi_search_name"]:
                condition_name = a[1]
                condition_index = a[0]
                #print(str(type(condition_name)) + "test " + str(condition_name) + " test " + str(condition_index) + " test ")

        if condition_index != "":
            #send = self.dynamicCall("SendCondition(QString, QString, int, int)", self.screen_real_search, condition_name, int(condition_index), 1)
            send = self.kw.send_condition(self.screen_real_search, condition_name, int(condition_index), 1)
            if send == 0:
                print("조건 검색 성공")
            else:
                print("조건신호 실패")

    def receive_real_condition(self, strCode, event_type, strConditionName, strConditionIndex):  
        try:
            logging.debug("function: receive_real_condition")
            movementData = [
                ("code", strCode),
                ("event_type", event_type),
                ("condi_name", strConditionName),
                ("condi_index", strConditionIndex)
            ]
            movementData = dict(movementData)
            movementData["kw_event"] = "OnReceiveRealCondition"
            if '_on_receive_real_condition' in self.notify_fn:
                self.notify_fn['_on_receive_real_condition'](movementData)
        
        except Exception as e:
            logging.error(e)
        finally:
            self.real_condition_search_result = []
        """
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
                            
        종목코드, 이벤트종류(I:편입, D:이탈), 조건식 이름, 조건명 인덱스"""
                        
    def search_condi(self, event_data):
        try:
            logging.debug("function: search_condi")
            if event_data["event_type"] == "I":
                logging.debug("search_condi: check Insert")
                strCode = event_data["code"]
                if TradeAlgo.checkstock(strCode) or True: #디버깅
                    logging.debug("search_condi: check condition")# 입력데이터

                    self.kw.set_input_value("종목코드", strCode)
                    checkfind = self.kw.comm_rq_data("주식기본정보조회", "opt10001", 0, self.screen_my_stock_info)
                    logging.debug(errors(checkfind))
                    if checkfind == 0:
                        print(strCode + " 종목 불러오기")
                    else:
                        print("에러발생!! " + str(checkfind))

                    if TradeAlgo.FindBuy(self.stock_dict[strCode]):
                        MainTrade.dbgout("[" + strCode + "] " + self.price_dict[strCode]['종목명'] + "  매수신호 발생")
                        logging.debug("check All Condition : " + strCode)
                        Account_num = MainTrade.SetAccount()
                        if(Account_num == -1):
                            MainTrade.dbgout("남은계좌 없음. 매수 실패")
                            logging.error("No more Account List: Fail to Buy")
                            return
                        buyStock_cnt = (MainTrade.vr_bank[Account_num]) / self.price_dict[strCode]["현재가"]
                        order_status = self.kw.send_order("시장가매수",self.screen_trade_stock, self.account, 1, strCode, buyStock_cnt, 0, '03', "")
                        
                        if order_status == 0:
                            logging.debug("Sucessful Call BuyFunction")
                        else:
                            logging.error("Fail to Call BuyFunction")

                            
        except Exception as e:
            logging.error(e)
        finally:
            self.real_condition_search_result = []
        
    

    def chejan_slot(self, sGubun, nItemCnt, sFidList):
        if int(sGubun) == 0:
            #주문체결
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])
            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            sName = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
            order_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])
            order_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)
            not_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['미체결수량'])
            not_quan = int(not_quan)
            buy_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량'])
            buy_quan = int(buy_quan)
            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])
            order_price = int(order_quan)
            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가'])
            if(chegual_price == ''):
                    chegual_price = 0
            else:
                    chegual_price = int(chegual_price)
            
            
            if order_gubun == "매수" and order_status == "접수":
                MainTrade.dbgout("매수 접수가 완료되었습니다 : " + sCode + "\n 종목명 : " + sName + "\n주문 수량 : " + str(order_quan))

            if order_gubun == "매수" and order_status == "체결":
                if(not_quan > 0):
                    MainTrade.dbgout("매수주문이 일부 체결되었습니다 : " + sCode + "\n 종목명 : " + sName + "\n체결량 : " + str(buy_quan) + "\n체결가 : " + str(chegual_price))
                else:
                    MainTrade.dbgout("모든 매수 체결이 완료되었습니다 : " + sCode + "\n 종목명 : " + sName + "\n주문 수량 : " + str(order_quan) + "\n체결가 : " + str(chegual_price))
                    self.my_stock_dict.update({sCode:{}})
                    self.my_stock_dict[sCode].update({"계좌번호": account_num})
                    self.my_stock_dict[sCode].update({"종목명": sName})
                    self.my_stock_dict[sCode].update({"목표가": (chegual_price + (chegual_price*0.035))})
                    self.my_stock_dict[sCode].update({"체결가": chegual_price})

                    self.kw.set_real_reg(self.screen_real_sise, sCode, '20', '1')

                

            if order_gubun == "매도" and order_status == "접수":
                MainTrade.dbgout("매도 접수가 완료되었습니다 : " + sCode)

            if order_gubun == "매도" and order_status == "체결":
                if(not_quan > 0):
                    MainTrade.dbgout("매도주문이 일부 체결되었습니다 : " + sCode + "\n 종목명 : " + sName + "\n체결량 : " + str(buy_quan) + "\n체결가 : " + str(chegual_price))
                else:
                    MainTrade.dbgout("모든 매도 체결이 완료되었습니다 : " + sCode + "\n 종목명 : " + sName + "\n주문 수량 : " + str(order_quan) + "\n체결가 : " + str(chegual_price))
                    
                    self.dynamicCall("SetRealRemove(QString, QString)", self.screen_real_sise, sCode)
                    del self.my_stock_dict[sCode]




        elif int(sGubun) == 1:            
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가']) # 계좌에 있는 종목의 총매입가
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})

            self.jango_dict[sCode].update({"현재가": current_price})
            self.jango_dict[sCode].update({"종목코드": sCode})
            self.jango_dict[sCode].update({"종목명": stock_name})
            self.jango_dict[sCode].update({"보유수량": stock_quan})
            self.jango_dict[sCode].update({"주문가능수량": like_quan})
            self.jango_dict[sCode].update({"매입단가": buy_price})
            self.jango_dict[sCode].update({"총매입가": total_buy_price})
            self.jango_dict[sCode].update({"매도매수구분": meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})
            #잔고

    def realdata_slot(self, sTrCode, realType, realData): 

        if realType == "주식체결":
            currprice = self.kw.get_comm_real_data(sTrCode, self.realType.REALTYPE[realType]['현재가'])
            currprice = abs(int(currprice))
            
            if(currprice >= self.my_stock_dict[sTrCode]["목표가"]):
                MainTrade.dbgout("[" + sTrCode + "] " + self.my_stock_dict[sTrCode]['종목명'] + "  매도신호 발생") 
                sellStock_cnt = self.jango_dict[sTrCode]["주문가능수량"]
                order_status = self.kw.send_order("시장가매도", self.screen_trade_stock, self.account, 2, sTrCode, sellStock_cnt, 0, self.realType.SENDTYPE['거래구분']['시장가'], "")
                
                if order_status == 0:
                    logging.debug("Sucessful Call SellFunction")
                else:
                    logging.error("Fail to Call SellFunction")

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """
        Kiwoom Receive Msg Callback, 서버통신 후 메시지를 받은 시점을 알려준다.

        오류가 발생하면, msg = '알수 없는 오류로 인해 서비스가 원할하지 않습니다.' 값이 들어가고,
        screen_no, rqname, trcode 모두 '' 이 입력된다.

        :param screen_no str: 화면번호
        :param rqname str: TR 요청명(commRqData() 메소드 호출시 사용된 requestName)
        :param trcode str: TRansaction name
        :param msg str: 서버 메시지
        :return:
        """
        try:
            logging.info("(!)[Callback] _on_receive_msg")
            logging.info("screen_no: {}".format(screen_no))
            logging.info("rqname: ".format(rqname))
            logging.info("trcode(TRansaction name): ".format(trcode))
            logging.info("msg: ".format(msg))
        except TypeError as e:
            logging.error("screen_no: " + str(type(screen_no)))
            logging.error("rqname: " + str(type(rqname)))
            logging.error("trcode: " + str(type(trcode)))
            logging.error("msg: " + msg)