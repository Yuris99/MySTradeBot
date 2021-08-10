from PyQt5.QAxContainer import *
from PyQt5.QtCore import QEventLoop
from singleton_decorator import singleton

from kiwoom.tr import TrManager
from kiwoom.condition import ConditionManager
from mydata import keyManager
from conf.errorCode import *
from telog import Telog


@singleton
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.logger = Telog().logger
        self.logger.debug("Class: Kiwoom")

        self.tr = TrManager(self)
        self.condi = ConditionManager(self)

        #eventLoop
        self.event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()

        #screenNo
        self.screen_info = "1000"
        self.screen_real_search = "3000"
        self.screen_trade = "4000"

        #variable
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
            

        }


        self.get_ocx_instance()
        self.set_event_slots()



    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def set_event_slots(self):
        self.OnEventConnect.connect(self.on_event_connect)
        self.OnReceiveMsg.connect(self.on_receive_msg)
        self.OnReceiveTrData.connect(self.tr.on_receive_tr_data)  # tr 수신 이벤트
        self.OnReceiveConditionVer.connect(self.condi.on_receive_condition_ver)
        self.OnReceiveRealCondition.connect(self.condi.on_receive_real_condition)



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
        self.stock_info = {}
        
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
            self.logger.debug("Find callback Function: " + event)
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
        self.logger.debug(f"getCommData({strItem})")
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
        return self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRecordName)

    

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

    def buyMarketPrice(self, code, quantity):
        self.send_order("시장가_신규매 수", self.screen_trade, self.acc_no, 1, code, quantity, 0, "03", "")

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
        """
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                            [sRQName, sScrNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGB, sOrgOrderNo])
        return ret


