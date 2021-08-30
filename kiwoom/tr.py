import time

from telog import Telog
import TradeAlgo


class TrManager():
    def __init__(self, kw):
        self.kw = kw
        self.logger = Telog().logger
        
    def on_receive_tr_data(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        """
        void OnReceiveTrData(
            BSTR sScrNo,       // 화면번호
            BSTR sRQName,      // 사용자 구분명
            BSTR sTrCode,      // TR이름
            BSTR sRecordName,  // 레코드 이름
            BSTR sPrevNext,    // 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
            LONG nDataLength,  // 사용안함.
            BSTR sErrorCode,   // 사용안함.
            BSTR sMessage,     // 사용안함.
            BSTR sSplmMsg     // 사용안함.
        )
        
        요청했던 조회데이터를 수신했을때 발생됩니다.
        수신된 데이터는 이 이벤트내부에서 GetCommData()함수를 이용해서 얻어올 수 있습니다.
        """
        self.logger.debug("function: on_receive_tr_data")
        self.logger.debug("trcode: {}".format(sTrCode))

        if sRQName == "예수금요청":
            self.logger.debug("get Deposit()")
            self.kw.deposit = int(self.kw.get_comm_data(sTrCode, sRQName, 0, "예수금"))
            self.kw.pos_deposit = int(self.kw.get_comm_data(sTrCode, sRQName, 0, "출금가능금액"))
            
            self.kw.event_loop.exit()

        if sRQName == "계좌평가요청":
            self.logger.debug("get Balance()")
            stock_cnt = self.kw.get_repeat_cnt(sTrCode, sRQName)
            acc_info = {}
            stock_info = {}

            #data list
            fid_list1 = ["총매입금액", "총평가금액", "총평가손익금액", "총수익률(%)", "추정예탁자산", "총대출금",
                        "총융자금액", "총대주금액", "조회건수"]
            
            """
            fid_list2 = ["종목명", "평가손익", "수익률(%)", "매입가", "전일종가", "보유수량", "매매가능수량", "현재가", "전일매수수량",
                        "전일매도수량", "금일매수수량", "금일매도수량", "매입금액", "매입수수료", "평가금액", "평가수수료", "세금",
                        "수수료합", "보유비중(%)", "신용구분", "신용구분명", "대출일"]
            """
            fid_list2 = ["종목명", "평가손익", "수익률(%)", "매입가", "전일종가", "보유수량", "매매가능수량", "현재가", "전일매수수량",
                        "전일매도수량", "금일매수수량", "금일매도수량", "매입금액", "매입수수료", "평가금액", "평가수수료", "세금",
                        "수수료합", "보유비중(%)"]

            #get accInfo(single data)
            for f in fid_list1:
                data = self.kw.get_comm_data(sTrCode, sRQName, 0, f)
                if f == "총수익률(%)": data = float(data)
                else: data = int(data)
                acc_info[f] = data

            #get stockInfo(multi data)
            for i in range(stock_cnt):
                tmp = {}
                code = self.kw.get_comm_data(sTrCode, sRQName, i, "종목번호").strip()[1:]
                self.logger.debug("종목번호: " + code)
                for f in fid_list2:
                    data = self.kw.get_comm_data(sTrCode, sRQName, i, f)
                    if f == "종목명": data = str(data).strip()
                    elif f == "수익률(%)" or f == "보유비중(%)": data = float(data)
                    else: data = int(data)
                    tmp[f] = data
                tmp["목표가"] = tmp["매입가"] + (tmp["매입가"] * 0.07)
                tmp['매도중'] = False
                #self.logger.debug("디버깅용으로 목표가 == 현재가 이후 수정바람")
                #tmp["목표가"] = tmp["현재가"]
                tmp["매수가"] = tmp["매입가"]
                tmp["주문가능수량"] = tmp["매매가능수량"]
                stock_info[code] = tmp 
            

            self.kw.account_info = acc_info
            self.kw.stock_info = stock_info
            
            self.kw.event_loop.exit()

        if sRQName == "현재가요청":
            self.logger.debug("get currPrice()")
            self.kw.set_real_remove("self.kw.screen_info", 'ALL')
            
            code = self.kw.get_comm_data(sTrCode, sRQName, 0, "종목코드").strip()
            name = self.kw.get_comm_data(sTrCode, sRQName, 0, "종목명").strip()
            curr = abs(int(self.kw.get_comm_data(sTrCode, sRQName, 0, "현재가")))
            start = abs(int(self.kw.get_comm_data(sTrCode, sRQName, 0, "시가")))
            value = abs(int(self.kw.get_comm_data(sTrCode, sRQName, 0, "거래량")))

            if code not in self.kw.stock_info:
                self.kw.stock_info.update({code:{}})
            self.kw.stock_info[code].update({"종목코드": code})
            self.kw.stock_info[code].update({"종목명": name})
            self.kw.stock_info[code].update({"현재가": curr})
            self.kw.stock_info[code].update({"시가": start})
            self.kw.stock_info[code].update({"거래량": value})
            
            self.logger.debug(self.kw.stock_info[code])

            self.kw.notify_callback('OnReceiveTrData', self.kw.stock_info[code], sRQName) 


            

    

            


    
