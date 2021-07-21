from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from conf.errorCode import *
import MainTrade
import TradeAlgo
import json
import time
from conf import kiwoomType

with open('.mydata/key.json') as json_file:
    json_data = json.load(json_file)


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        

        print("Kiwoom 클래스 호출")

        self.realType = kiwoomType.RealType()

        ########## 변수모음
        self.account_stock_dict = {}
        self.find_stock = []
        self.price_dict = {}

        ########## 이벤트루프 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.get_stock_info_event_loop = QEventLoop()

        ########## 스크린 번호 모음
        self.screen_my_info = "2000"
        self.screen_my_stock_info = "1000"
        self.screen_real_search = "3000"
        self.screen_real_sise = "3001"
        self.screen_trade_stock = "4000"




        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.start_real_find()
        self.test("042420")



    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

        self.OnReceiveConditionVer.connect(self.recieve_condition_var)

        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveRealCondition.connect(self.receive_real_condition)
        self.OnReceiveChejanData.connect(self.chejan_slot)

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
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", '0', self.screen_my_info)
        

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num[0])
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", json_data["Account_Password"])
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)
        

        self.detail_account_info_event_loop.exec_()


    def start_real_find(self):
        isLoad = self.dynamicCall("GetConditionLoad()")
        if not isLoad:
            print("조건 불러오기 실패")
        else:
            print("조건 불러오기 성공")
        self.conditionLoop = QEventLoop()
        self.conditionLoop.exec_()

    def recieve_condition_var(self, bRet, sMsg):
        print("[recieve]")
        condition_list = {'index': [], 'name': []}
        condition_name = ""
        condition_index = 0
        conditionNameList = self.dynamicCall("GetConditionNameList()")
        print(conditionNameList)
        conditionNameListArray = conditionNameList.split(';')
        print(conditionNameListArray)
        del conditionNameListArray[-1]
        for data in conditionNameListArray: # 조건검색식 개수만큼 반복
            a = data.split("^")
            condition_list['index'].append(a[0])
            condition_list['name'].append(a[1])
            if str(a[1]) == json_data["condi_search_name"]:
                condition_name = a[1]
                condition_index = a[0]
                #print(str(type(condition_name)) + "test " + str(condition_name) + " test " + str(condition_index) + " test ")

        if condition_index != "":
            send = self.dynamicCall("SendCondition(QString, QString, int, int)", self.screen_real_search, condition_name, int(condition_index), 1)
            if send == 1:
                print("조건 검색 성공")
            else:
                print("조건신호 실패")
        
        self.conditionLoop.exit()



    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        """스크린번호, 요청이름, tr코드, 사용안함, 다음페이지"""

        if sRQName == "예수금상세현황요청":
            self.deposit = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "예수금")
            
            self.ok_deposit = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "출금가능금액")
            
            MainTrade.dbgout(f"키움계좌에 로그인되었습니다.\n이름 : {self.user_name}\nID : {self.user_id}\n보유 계좌 수 : {self.account_count}\n계좌번호 : {self.account_num[0]}\n예수금 : {format(int(self.deposit), ',')}원\n출금가능금액 : {format(int(self.ok_deposit), ',')}원")

            self.detail_account_info_event_loop.exit()

        if sRQName == "계좌평가잔고내역요청":
            self.total_buy_money = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "총매입금액")

            self.total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, 0, "총수익률(%)")
            self.total_profit_loss_rate_result = float(self.total_profit_loss_rate)
            self.detail_account_info_event_loop.exit()
            
        """
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

        """

        if sRQName == "주식기본정보조회":
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
                self.price_dict.update({code:{}})
            self.price_dict[code].update({"종목명": name})
            self.price_dict[code].update({"현재가": currprice})
            self.price_dict[code].update({"시가": startprice})
            self.price_dict[code].update({"거래량": tradeValue})

            #print(self.price_dict[code])
            print("종목정보 호출 성공")
            self.get_stock_info_event_loop.exit()


    def realdata_slot(self, sTrCode, realType, realData): 

        if realType == "주식체결":
            t = self.dynamicCall("GetCommRealData(QString, int)", sTrCode, self.realType.REALTYPE[realType]['체결시간(HHMMSS)'])
            currprice = self.dynamicCall("GetCommRealData(QString, int)", sTrCode, self.realType.REALTYPE[realType]['현재가'])
            currprice = abs(int(currprice))

            startprice = self.dynamicCall("GetCommRealData(QString, int)", sTrCode, self.realType.REALTYPE[realType]['시가'])
            startprice = abs(int(startprice))

            if sTrCode not in self.my_stock_dict:
                self.my_stock_dict.update({sTrCode:{}})
            
            self.my_stock_dict[sTrCode].update({"체결시간": t})
            self.my_stock_dict[sTrCode].update({"현재가": currprice})
            self.my_stock_dict[sTrCode].update({"시가": startprice})

    def chejan_slot(self, sGubun, nItemCnt, sFidList):
        if int(sGubun) == 0:
            #주문체결
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            order_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])
            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])
            order_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])
            order_quan = int(order_quan)
            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])
            order_price = int(order_quan)
            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['매도수구분'])
            
            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가'])
            if(chegual_price == ''):
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)


        elif int(sGubun) == 1:
            print("잔고")
            #잔고



            
    def receive_real_condition(self, strCode, event_type, strConditionName, strConditionIndex):  
        """종목코드, 이벤트종류(I:편입, D:이탈), 조건식 이름, 조건명 인덱스"""
        try:
            if str(event_type) == "I" and strConditionName == "Auto3dot5":
                print(strCode + "조건검색 확인")
                if TradeAlgo.checkstock(strCode):
                    #self.find_stock.append(get_data)
                    #self.getCommRealData(strCode, 10)
                    #self.dynamicCall("SetRealReg(QString, QString, QString, QString", self.screen_real_search, strCode, self.realType.REALTYPE[], "1")
                    print("조건 확인 완료")

                    self.getPrice(strCode)
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
                            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_real_sise, strCode, '20', '1')
                        else:
                            print("매도주문 전달 실패")
                    
                        
                        

                    print(self.stock_sise_dict(strCode))
        except Exception as e:
            MainTrade.dbgout(e)
        finally:
            self.real_condition_search_result = []

    def test(self, strCode):
        self.getPrice(strCode)
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
    
    def getPrice(self, strCode):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", strCode)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보조회", "opt10001", 0, self.screen_my_stock_info)
        print("종목 불러오기")
        self.get_stock_info_event_loop.exec_()

    
