import sys

from PyQt5.QAxContainer import *
from PyQt5.QtCore import QEventLoop
from singleton_decorator import singleton

from kiwoom.tr import TrManager
from kiwoom.condition import ConditionManager
from kiwoom.chejan import Chejan
from mydata import keyManager
from conf.errorCode import *
from telog import Telog


@singleton
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.logger = Telog().logger
        self.logger.debug("Class: Kiwoom")

        #variable
        self.real_list = []
        self.event_callback_fn = {
            "OnEventConnect": {},
            "OnReceiveTrData": {},
            "OnReceiveRealData": {},
            "OnReceiveRealCondition": {},
            "OnReceiveTrCondition": {},
            "OnReceiveConditionVer": {},
            "OnReceiveChejanData": {},
            "OnReceiveMsg": {},
            #custom
            "OnSellStock": {},
            "StartSetStock": {}
        }
        self.stock_info = {}

        #getClass
        self.transport = TrManager(self)
        self.condi = ConditionManager(self)
        self.chejan = Chejan(self)

        #eventLoop
        self.event_loop = QEventLoop()
        self.transportansport_event_loop = QEventLoop()

        #screenNo
        self.screen_info = "1000" #tr요청
        self.screen_real_search = "3000" #실시간조건검색
        self.screen_real_monitor = "3001" #실시간모니터링
        self.screen_trade_buy = "4001" #매수
        self.screen_trade_sell = "4002" #매도

        


        self.get_ocx_instance()
        self.set_event_slots()



    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def set_event_slots(self):
        self.OnEventConnect.connect(self.on_event_connect)
        self.OnReceiveMsg.connect(self.on_receive_msg)
        self.OnReceiveTrData.connect(self.transport.on_receive_tr_data)  # tr 수신 이벤트
        self.OnReceiveRealData.connect(self.on_receive_real_data)
        self.OnReceiveConditionVer.connect(self.condi.on_receive_condition_ver)
        self.OnReceiveRealCondition.connect(self.condi.on_receive_real_condition)
        self.OnReceiveChejanData.connect(self.chejan.on_receive_chejan_data)  # 주문 접수/확인 수신시 이벤트



    def on_event_connect(self, err_code):
        if err_code != 0:
            self.logger.error("로그인에 실패하였습니다.\n 에러코드 : " + errors(err_code))
        else:
            self.logger.info("키움API 접속 완료")

        self.event_loop.exit()

    def on_receive_msg(self, sScrNo, sRQName, sTrCode, sMsg):
        """
        Kiwoom Receive Msg Callback, 서버통신 후 메시지를 받은 시점을 알려준다.

        오류가 발생하면, msg = '알수 없는 오류로 인해 서비스가 원할하지 않습니다.' 값이 들어가고,
        screen_no, rqname, trcode 모두 '' 이 입력된다.
        
        OnReceiveMsg(
        BSTR sScrNo,   // 화면번호
        BSTR sRQName,  // 사용자 구분명
        BSTR sTrCode,  // TR이름
        BSTR sMsg     // 서버에서 전달하는 메시지
        )
        """
        self.logger.debug("Recieve Message")
        self.logger.debug("screen_no: {}".format(sScrNo))
        self.logger.debug("rqname: {}".format(sRQName))
        self.logger.debug("trcode: {}".format(sTrCode))
        self.logger.debug("msg: {}".format(sMsg))

    def on_receive_real_data(self, sCode, sRealType, sRealData):
        """
        OnReceiveRealData(
          BSTR sCode,        // 종목코드
          BSTR sRealType,    // 실시간타입
          BSTR sRealData    // 실시간 데이터 전문 (사용불가)
        )
        Kiwoom Receive Realtime Data Callback, 실시간데이터를 받은 시점을 알려준다.
        setRealReg() 메서드로 등록한 실시간 데이터도 이 이벤트 메서드에 전달됩니다.
        getCommRealData() 메서드를 이용해서 실시간 데이터를 얻을 수 있습니다.
        """
        """
        self.logger.debug("function: on_receive_real_data")
        self.logger.debug("code: {}".format(sCode))
        self.logger.debug("real_type: {}".format(sRealType))
        self.logger.debug("real_data: {}".format(sRealData))
        """

        if sRealType == "장시작시간":
            self.logger.debug("real_type: 장시작시간")
            market_gubun =  self.get_comm_real_data(sCode, 215)
            if market_gubun == '0':
                remained_time =  self.get_comm_real_data(sCode, 214)
                if int(remained_time) > 100:
                    self.logger.info("장 시작 전입니다"
                                    +"\n장 시작까지 남은시간 : " + remained_time[2:4] + "분")
                else:
                    self.logger.info("곧 장이 시작됩니다"
                                    +"\n장 시작까지 남은시간 : " + remained_time[4:6] + "초")
            elif market_gubun == '3':
                    self.logger.info("장이 시작되었습니다!")
            elif market_gubun == '2':
                remained_time =  self.get_comm_real_data(sCode, 214)
                if int(remained_time) > 100:
                    self.logger.info("장 마감 " + remained_time[2:4] + "분전 입니다")
                else:
                    self.logger.info("곧 장이 마감됩니다"
                                    +"\n장 마감까지 남은시간" + remained_time[4:6] + "초전")
            elif market_gubun == '4':
                self.logger.info("장이 마감되었습니다")
                self.logger.info("프로그램을 종료합니다")
                sys.exit(1)
            else:
                self.logger.debug("장 구분: " + market_gubun)
            return

        if sRealType == '주식체결':
            currprice = abs(int(self.get_comm_real_data(sCode, "10")))
            if sCode not in self.stock_info['종목정보']:
                self.stock_info['종목정보'].update({sCode:{}})
            self.stock_info['종목정보'][sCode]['현재가'] = currprice

            if '매도중' in self.stock_info['종목정보'][sCode] and not self.stock_info['종목정보'][sCode]['매도중']:
                if currprice >= self.stock_info['종목정보'][sCode]['목표가']:
                    self.logger.info("\n매도 종목 발생 : " + sCode)
                    #self.notify_callback('OnReceiveRealData', sRealData, "매도")
                    self.stock_info['종목정보'][sCode]['매도중'] = True
                    self.sell_marketPrice(sCode, int(self.stock_info['종목정보'][sCode]['주문가능수량']))
                    self.set_real_remove(self.screen_real_monitor, sCode)
                    self.logger.info("\n실시간 모니터링을 종료합니다"
                                    +"\n종목코드 : " + sCode
                                    +"\n종목명 : " + self.stock_info['종목정보'][sCode]['종목명'])

    

    #Public
    #Login Kiwoom API
    def login(self):
        self.logger.debug("function: login")
        self.comm_connect()
        self.event_loop.exec_()

    #Start Setting
    def init_trading(self):
        self.logger.debug("function: init_trading")
        self.get_account()
        self.get_deposit()
        self.get_balance()

        self.logger.info(f"환영합니다 {self.user_name}님!")

    def get_account(self):
        self.logger.debug("function: get_account")

        #Get Account count and List
        self.account_cnt = self.get_login_info("ACCOUNT_CNT")
        acclist = self.get_login_info("ACCNO").split(';')
        self.account_no = acclist[0]

        #Get UserInfo
        self.user_id = self.get_login_info("USER_ID")
        self.user_name = self.get_login_info("USER_NAME")

        #Get ServerType
        self.server_type = self.get_login_info("GetServerGubun").strip()

        #Log Info
        self.logger.info("\n접속 ID: " + self.user_id
                        +"\n계좌 개수: " + self.account_cnt
                        +"\n1번째 계좌를 사용합니다."
                        +"\n계좌 번호: " + self.account_no
        )
        if self.server_type == '1':
            self.logger.info("모의투자 서버에 접속하였습니다.")
        else:
            self.logger.info("실거래 서버에 접속하였습니다.")

    def get_deposit(self):
        self.logger.debug("function: get_deposit")
        self.deposit = ""
        self.pos_deposit = ""
        #call Deposit 
        inputs = {
            '계좌번호': self.account_no,
            '비밀번호': keyManager.getJsonData('account_password'),
            '비밀번호입력매체구분': "00",
            "조회구분": "2"
        }
        self.set_input_values(inputs)
        self.comm_rq_data("예수금요청", "opw00001", 0, self.screen_info)
        self.event_loop.exec_()

        #Log Deposit
        self.logger.info("\n예수금: " + format(int(self.deposit), ',')  + "원"
                        +"\n출금가능금액: " + format(int(self.pos_deposit), ',' ) + "원"
        )

    def get_balance(self):
        self.logger.debug("function: get_balance")
        
        #call Balance
        inputs = {
            '계좌번호': self.account_no,
            '비밀번호': keyManager.getJsonData('account_password'),
            '비밀번호입력매체구분': "00",
            "조회구분": "2"
        }
        self.set_input_values(inputs)
        self.comm_rq_data("계좌평가요청", "opw00018", 0, self.screen_info)
        self.event_loop.exec_()

        #log Balance
        if self.stock_info['종목정보']:
            self.logger.info("미매도 종목")
            for code, data in self.stock_info['종목정보'].items():
                self.logger.info( "\n종목코드: " + code
                                + "\n종목명: " + data["종목명"]
                                + "\n수익률: " + str(data["수익률(%)"]) + "%"
                                + "\n매입가: " + format(int(data["매입가"]), ',') + "원"
                                + "\n목표가: " + format(int(data["목표가"]), ',') + "원"
                                + "\n현재가: " + format(int(data["현재가"]), ',') + "원"
                                + "\n보유수량: " + str(data["보유수량"]) + "주"
                )
                #realdata 추가 
                if not self.real_list:
                    search_type = 0
                else:
                    search_type = 1
                self.set_real_reg(self.screen_real_monitor, code, '20', search_type)
                self.logger.info("\n실시간 모니터링을 시작합니다"
                        +"\n종목코드 : " + code
                        +"\n종목명 : " + data['종목명'])

                self.notify_callback("StartSetStock", code, "미매도종목")

    def get_curr_price(self, strCode):
        """특정종목의 현재 주식가격을 불러옴

        :param code:
        :return:
        """
        self.logger.debug("function: get_curr_price")
        self.set_input_value("종목코드", str(strCode))
        ret = self.comm_rq_data("현재가요청", "opt10001", 0, self.screen_info)
        return ret


    def reg_callback(self, event, key, fn):
        """특정 이벤트 발생시 호출한 callback 함수를 등록한다.

        :param event:
        :param key: 일반적으로 screen_no 를 사용하면 된다.
        :param fn:
        :return:
        """
        self.logger.debug("Set callback Function(" + event + " : " + str(fn) + " , key = " + key + ")")
        self.event_callback_fn[event][key] = fn

    def notify_callback(self, event, data, key):
        """
        특정 이벤트로 등록한 callback 함수를 호출한다.

        :param event:
        :param data:
        :param key: 일반적으로 screen_no 를 사용하면 된다.
        :return:
        """
        self.logger.debug("function: notify_callback")
        if key in self.event_callback_fn[event]:
            self.logger.debug("Find callback Function: " + event + ", Key : " + key)
            self.logger.debug(data)
            self.event_callback_fn[event][key](data)



    #API
    def comm_connect(self):
        self.dynamicCall("CommConnect()")

    def get_login_info(self, tag):
        """
        로그인한 사용자 정보를 반환한다.

        :return: str - 반환값
        BSTR sTag에 들어 갈 수 있는 값은 아래와 같음
        “ACCOUNT_CNT” – 전체 계좌 개수를 반환한다.
        "ACCNO" – 전체 계좌를 반환한다. 계좌별 구분은 ‘;’이다.
        “USER_ID” - 사용자 ID를 반환한다.
        “USER_NAME” – 사용자명을 반환한다.
        "GetServerGubun" : 접속서버 구분을 반환합니다.(1 : 모의투자, 나머지 : 실거래서버)
        “KEY_BSECGB” – 키보드보안 해지여부. 0:정상, 1:해지
        “FIREW_SECGB” – 방화벽 설정 여부. 0:미설정, 1:설정, 2:해지
        Ex) openApi.GetLoginInfo(“ACCOUNT_CNT”);
        """
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def set_input_value(self, sID, sValue):
        """
        SetInputValue(
            BSTR sID,     // TR에 명시된 Input이름
            BSTR sValue   // Input이름으로 지정한 값
        )
        조회요청시 TR의 Input값을 지정하는 함수입니다.
        CommRqData 호출 전에 입력값들을 셋팅합니다.
        각 TR마다 Input 항목이 다릅니다. 순서에 맞게 Input 값들을 셋팅해야 합니다.
        """
        self.dynamicCall("SetInputValue(QString, QString)", sID, sValue)

    def set_input_values(self, args):
        """
        다수의 Input값을 한번에 입력해주는 함수
        list형식으로 입력
        """
        self.logger.debug(args)
        for id, value in args.items():
            self.set_input_value(id, value)


    def comm_rq_data(self, sRQName, sTrCode, nPrevNext, sScreenNo):
        """
        CommRqData(
            BSTR sRQName,    // 사용자 구분명 (임의로 지정, 한글지원)
            BSTR sTrCode,    // 조회하려는 TR이름
            long nPrevNext,  // 연속조회여부
            BSTR sScreenNo  // 화면번호 (4자리 숫자 임의로 지정)
            )
            조회요청 함수입니다.
            리턴값 0이면 조회요청 정상 나머지는 에러
    
        """
        self.logger.debug("comm_rq_data")
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString)", sRQName, sTrCode, int(nPrevNext), sScreenNo)
        
        self.logger.debug("ret = " + str(ret))
        return ret

    def get_comm_data(self, sTrCode, sRQName, nIndex, strItem):
        """
        GetCommData(
            BSTR sTrCode,   // TR 이름
            BSTR sRQName,   // 레코드이름
            long nIndex,      // nIndex번째
            BSTR strItem) // TR에서 얻어오려는 출력항목이름

            OnReceiveTRData()이벤트가 발생될때 수신한 데이터를 얻어오는 함수입니다.
            이 함수는 OnReceiveTRData()이벤트가 발생될때 그 안에서 사용해야 합니다.
        """
        #self.logger.debug(f"getCommData({strItem})")
        ret = self.dynamicCall("GetCommData(String, String, int, String", sTrCode, sRQName, nIndex, strItem)
        return ret.strip()

    def get_repeat_cnt(self, sTrCode, sRecordName):
        """
        GetRepeatCnt(
            BSTR sTrCode, // TR 이름
            BSTR sRecordName // 레코드 이름
        )
        
        데이터 수신시 멀티데이터의 갯수(반복수)를 얻을수 있습니다. 
        예를들어 차트조회는 한번에 최대 900개 데이터를 수신할 수 있는데 
        이렇게 수신한 데이터갯수를 얻을때 사용합니다.
        이 함수는 OnReceiveTRData()이벤트가 발생될때 그 안에서 사용해야 합니다.
        """
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRecordName)
        self.logger.debug("function: get_repeat_cnt : " + str(ret))
        return ret

    

    def get_condition_load(self):
        """
        서버에 저장된 사용자 조건검색 목록을 요청합니다. 
        조건검색 목록을 모두 수신하면 OnReceiveConditionVer()이벤트가 발생됩니다.
        조건검색 목록 요청을 성공하면 1, 아니면 0을 리턴합니다.
        """
        ret = self.dynamicCall("GetConditionLoad()")
        self.event_loop.exec_()
        return ret

    def get_condition_name_list(self):
        """
        서버에서 수신한 사용자 조건식을 조건식의 고유번호와 조건식 이름을 한 쌍으로 하는 문자열들로 전달합니다.
        조건식 하나는 조건식의 고유번호와 조건식 이름이 구분자 '^'로 나뉘어져 있으며 각 조건식은 ';'로 나뉘어져 있습니다.
        이 함수는 OnReceiveConditionVer()이벤트에서 사용해야 합니다.
		
        예) "1^내조건식1;2^내조건식2;5^내조건식3;,,,,,,,,,,"
        """
        ret = self.dynamicCall("GetConditionNameList()")
        return ret
        
        
    def set_real_reg(self, sScrNo, sTrCode, sFids, strType):
        """
        SetRealReg(
            BSTR sScrNo,   // 화면번호
            BSTR strCode,   // 종목코드 리스트
            BSTR sFids,  // 실시간 FID리스트
            BSTR strType   // 실시간 등록 타입, 0또는 1
        )
        종목코드와 FID 리스트를 이용해서 실시간 시세를 등록하는 함수입니다.
        한번에 등록가능한 종목과 FID갯수는 100종목, 100개 입니다.
        실시간 등록타입을 0으로 설정하면 등록한 종목들은 실시간 해지되고 등록한 종목만 실시간 시세가 등록됩니다.
        실시간 등록타입을 1로 설정하면 먼저 등록한 종목들과 함께 실시간 시세가 등록됩니다
        실시간 데이터는 실시간 타입 단위로 receiveRealData() 이벤트로 전달되기 때문에,
        이 메서드에서 지정하지 않은 fid 일지라도, 실시간 타입에 포함되어 있다면, 데이터 수신이 가능하다.
        """
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", sScrNo, sTrCode, sFids, strType)
        self.real_list.append(sTrCode)
        return ret

    def set_real_remove(self, sScrNo, sTrCode):
        """
        SetRealRemove(
            BSTR strScrNo,    // 화면번호 또는 ALL
            BSTR strDelCode   // 종목코드 또는 ALL
        )
        실시간 데이터 중지 메서드
        ※ A종목에 대한 실시간이 여러화면번호로 중복등록되어 있는 경우 특정화면번호를 이용한
            SetRealRemove() 함수호출시 A종목의 실시간시세는 해지되지 않습니다.
        """
        self.logger.debug("function set_real_remove")
        self.dynamicCall("SetRealRemove(QString, QString)", sScrNo, sTrCode)
        if sTrCode in self.real_list:
            self.real_list.remove(sTrCode)


    def get_comm_real_data(self, strCode, nFid):
        """ 
        GetCommRealData(
          BSTR strCode,   // 종목코드
          long nFid   // 실시간 타입에 포함된FID (Feild ID)
        )
        실시간 데이터 획득 메서드
        이 메서드는 반드시 receiveRealData() 이벤트 메서드가 호출될 때, 그 안에서 사용해야 합니다.
        :return: string - fid에 해당하는 데이터
        """
        ret = self.dynamicCall("GetCommRealData(QString, int)", strCode, nFid)
        return ret



    def buy_marketPrice(self, code, quantity):
        self.logger.debug("function: buy_marketPrice")
        return self.send_order("시장가_신규매수", self.screen_trade_buy, self.account_no, 1, code, quantity, 0, "03", "")

    def sell_marketPrice(self, code, quantity):
        return self.send_order("시장가_신규매도", self.screen_trade_sell, self.account_no, 2, code, quantity, 0, "03", "")

    def send_order(self, sRQName, sScrNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGB, sOrgOrderNo):
        """
        SendOrder(
            BSTR sRQName, // 사용자 구분명
            BSTR sScreenNo, // 화면번호
            BSTR sAccNo,  // 계좌번호 10자리
            LONG nOrderType,  // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
            BSTR sCode, // 종목코드 (6자리)
            LONG nQty,  // 주문수량
            LONG nPrice, // 주문가격
            BSTR sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
            BSTR sOrgOrderNo  // 원주문번호. 신규주문에는 공백 입력, 정정/취소시 입력합니다.
        )
        
        서버에 주문을 전송하는 함수 입니다.
        9개 인자값을 가진 주식주문 함수이며 리턴값이 0이면 성공이며 나머지는 에러입니다.
        1초에 5회만 주문가능하며 그 이상 주문요청하면 에러 -308을 리턴합니다.
        ※ 시장가주문시 주문가격은 0으로 입력합니다.
        ※ 취소주문일때 주문가격은 0으로 입력합니다.

        매도/매수 주문 함수
        주문유형(order_type) (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
        hoga_gubun – 00:지정가,    03:시장가,    05:조건부지정가,   06:최유리지정가, 07:최우선지정가,
                    10:지정가IOC, 13:시장가IOC, 16:최유리IOC,      20:지정가FOK,
                    23:시장가FOK, 26:최유리FOK, 61:장전시간외종가,  62:시간외단일가, 81:장후시간외종가
        ※ 시장가, 최유리지정가, 최우선지정가, 시장가IOC, 최유리IOC, 시장가FOK, 최유리FOK, 장전시간외, 장후시간외 주문시
            주문가격을 입력하지 않습니다.
        """
        self.logger.debug("function: send_order")
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                            [sRQName, sScrNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGB, sOrgOrderNo])
        return ret

    def get_chejan_data(self, fid):
        """

        :return:
        """
        return self.dynamicCall("GetChejanData(int)", fid)


