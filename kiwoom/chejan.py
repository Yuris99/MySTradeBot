
from telog import Telog
from telog import TradeLog

class Chejan(object):
    """receiveChejanData() 이벤트 메서드로 전달되는 FID 목록
    """
    """
    fid_table = {
        9201: '계좌번호',
        9203: '주문번호',
        9205: '관리자사번',
        9001: '종목코드',
        912: '주문업무분류',
        913: '주문상태',
        302: '종목명',
        900: '주문수량',
        901: '주문가격',
        902: '미체결수량',
        903: '체결누계금액',
        904: '원주문번호',
        905: '주문구분',
        906: '매매구분',
        907: '매도수구분',
        908: '주문/체결시간',
        909: '체결번호',
        910: '체결가',
        911: '체결량',
        10: '현재가',
        11: '전일대비',
        12: '등락율',
        25: '전일대비기호',
        27: '(최우선)매도호가',
        28: '(최우선)매수호가',
        914: '단위체결가',
        915: '단위체결량',
        938: '당일매매수수료',
        939: '당일매매세금',
        919: '거부사유',
        920: '화면번호',
        921: '921',
        922: '922',
        923: '923',
        949: '949',
        10010: '10010',
        917: '신용구분',
        916: '대출일',
        930: '보유수량',
        931: '매입단가',
        932: '총매입가',
        933: '주문가능수량',
        945: '당일순매수수량',
        946: '매도/매수구분',
        950: '당일총매도손일',
        951: '예수금',
        307: '기준가',
        8019: '손익율',
        957: '신용금액',
        958: '신용이자',
        959: '담보대출수량',
        924: '924',
        918: '만기일',
        990: '당일실현손익(유가)',
        991: '당일신현손익률(유가)',
        992: '당일실현손익(신용)',
        993: '당일실현손익률(신용)',
        397: '파생상품거래단위',
        305: '상한가',
        306: '하한가'
    }
    """
    fid_use = {
        9201: '계좌번호',
        9203: '주문번호',
        9001: '종목코드',
        912: '주문업무분류', #(jj:주식주문)
        913: '주문상태',#(접수, 확인, 체결) (10:원주문, 11:정정주문, 12:취소주문, 20:주문확인, 21:정정확인, 22:취소확인, 90,92:주문거부) #https://bbn.kiwoom.com/bbn.openAPIQnaBbsDetail.do
        302: '종목명',
        900: '주문수량',
        901: '주문가격',
        902: '미체결수량',
        903: '체결누계금액',
        904: '원주문번호',
        905: '주문구분', #(+매수, -매도, -매도정정, +매수정정, 매수취소, 매도취소)
        906: '매매구분',#(보통, 시장가등)
        907: '매도수구분',# 매도(매도정정, 매도취도 포함)인 경우 1, 매수(매수정정, 매수취소 포함)인 경우 2
        908: '주문/체결시간',#(HHMMSS)
        909: '체결번호',
        910: '체결가',
        911: '체결량',
        10: '현재가',
        12: '등락율',
        914: '단위체결가',
        915: '단위체결량',
        938: '당일매매수수료',
        939: '당일매매세금',
        919: '거부사유',
        920: '화면번호',
        930: '보유수량',
        931: '매입단가',
        932: '총매입가',
        933: '주문가능수량',
        945: '당일순매수수량',
        946: '매도/매수구분',
        950: '당일총매도손익',
        951: '예수금',
        307: '기준가',
        8019: '손익율',
        990: '당일실현손익(유가)',
        991: '당일신현손익률(유가)',
        305: '상한가',
        306: '하한가'
    }

    def __init__(self, kw):
        self.kw = kw
        self.logger = Telog().logger
        self.tlog = TradeLog().logger
        self.gubun = ""

        self.set_callback()

    def set_callback(self):
        self.logger.debug("function: set_callback in chejan")
        self.kw.reg_callback("OnReceiveChejanData", '0', self.chejan_order_callback)
        self.kw.reg_callback("OnReceiveChejanData", '1', self.chejan_jango_callback)

    def on_receive_chejan_data(self, sGubun, nItemCnt, sFidList):
        """
        OnReceiveChejanData(
            BSTR sGubun, // 체결구분. 접수와 체결시 '0'값, 국내주식 잔고변경은 '1'값, 파생잔고변경은 '4'
            LONG nItemCnt,
            BSTR sFIdList
        )
        
        주문전송 후 주문접수, 체결통보, 잔고통보를 수신할 때 마다 발생됩니다.
        GetChejanData()함수를 이용해서 FID항목별 값을 얻을수 있습니다.
        
        """
        try:
            gubun = int(sGubun)
            self.logger.debug("function: on_receive_chejan_data")
            self.logger.debug("gubun(0:주문체결통보, 1:잔고통보, 3:특이신호): {}".format(gubun))
            self.logger.debug("item_cnt: {}".format(nItemCnt))
            self.logger.debug("fid_list: {}".format(sFidList))

            #주문 / 체결 통보
            if gubun == 0:
                self.logger.debug("주문통보/체결통보")
            elif gubun == 1:
                self.logger.debug("잔고통보")
                
            data = self.make_data(gubun, nItemCnt, sFidList)

            # callback
            self.logger.info("[OnReceiveChejanData] Notify callback method..")
            self.notify_callback('OnReceiveChejanData', data, str(gubun))


        except Exception as e:
            self.logger.error("ERROR IN 'on_receive_chejan_data'")
            self.logger.error(e)

    def make_data(self, gubun, item_cnt, fid_list):
        data = {"gubun": gubun}

        for fid in fid_list.split(";"):
            fid = int(fid)
            key = self.fid_table[fid]
            value = self.kw.get_chejan_data(fid)
            data[key] = value
        return data

    def chejan_order_callback(self, event_data):
        self.logger.debug("function: chejan_order_callback")
        event_data['주문구분'] = event_data['주문구분'].strip().lstrip('+').lstrip('-')

        if event_data['주문구분'] == '매수':
            self.chejan_buy(event_data)
        elif event_data['주식구분'] == '매도':
            self.chejan_sell(event_data)

    #매수주문시
    def chejan_buy(self, event_data):
        self.logger.debug("function: chejan_buy")
        if event_data['주문상태'] == '접수':
            self.logger.info("매수 접수가 완료되었습니다"
                            +"\n종목번호 : " + event_data['종목코드']
                            +"\n종목명 : " + event_data['종목명']
                            +"\n현재가 : " + event_data['현재가'] + "원"
                            +"\n주문수량 : " + event_data['주문수량'])
        
        if event_data['주문상태'] == '체결':
            if int(event_data['미체결수량']) > 0:
                self.logger.info("매수 주문이 일부 체결되었습니다" 
                                +"\n종목번호 : " + event_data['종목코드']
                                +"\n종목명 : " + event_data['종목명']
                                +"\n체결량 : " + event_data['단위체결량'] + "주"
                                +"\n체결가 : " + event_data['단위체결가'] + "원"
                                +"\n남은 미체결수량: " + event_data['미체결수량'] + "주")
            else:
                
                self.logger.info("매수 주문이 체결되었습니다 : " 
                                +"\n종목번호 : " + event_data['종목코드']
                                +"\n종목명 : " + event_data['종목명']
                                +"\n주문수량 : " + event_data['주문수량']
                                +"\n체결가 : " + event_data['체결가'] + "원")
                goal = int(event_data['체결가']) + (int(event_data['체결가']) * 0.035)
                self.kw.stock_info['종목정보'][event_data['종목코드']].update({"목표가": goal})
                self.kw.stock_info['종목정보'][event_data['종목코드']].update({"매수가": int(event_data['체결가'])})
                #현재가정보만 가져옴
                if not self.kw.real_list:
                    search_type = 0
                else:
                    search_type = 1
                self.kw.set_real_reg(self.kw.screen_real_monitor, event_data['종목코드'], '10;20', search_type)
                self.logger.info("\n실시간 모니터링을 시작합니다"
                                +"\n목표가 : " + str(goal) + "원")

                #파일저장
                logmsg = "매수\n"
                for key, value in self.kw.stock_info['종목정보'][event_data['종목코드']].items():
                    logmsg += key + " : " + value + "\n"
                self.tlog.info(logmsg)
                                


    #매도주문시
    def chejan_sell(self, event_data):
        self.logger.debug("function: chejan_sell")
        if event_data['주문상태'] == '접수':
            self.logger.info("매도 접수가 완료되었습니다"
                            +"\n종목번호 : " + event_data['종목코드']
                            +"\n종목명 : " + event_data['종목명']
                            +"\n매수가 : " + event_data['매수가'] + "원"
                            +"\n현재가 : " + event_data['현재가'] + "원"
                            +"\n주문수량 : " + event_data['주문수량'])
        
        if event_data['주문상태'] == '체결':
            if int(event_data['미체결수량']) > 0:
                self.logger.info("매도 주문이 일부 체결되었습니다" 
                                +"\n종목번호 : " + event_data['종목코드']
                                +"\n종목명 : " + event_data['종목명']
                                +"\n매수가 : " + event_data['매수가'] + "원"
                                +"\n체결량 : " + event_data['단위체결량'] + "주"
                                +"\n체결가 : " + event_data['단위체결가'] + "원"
                                +"\n남은 미체결수량: " + event_data['미체결수량'] + "주")
            else:
                
                self.logger.info("매도 주문이 체결되었습니다 : " 
                                +"\n종목번호 : " + event_data['종목코드']
                                +"\n종목명 : " + event_data['종목명']
                                +"\n매수가 : " + event_data['매수가'] + "원"
                                +"\n주문수량 : " + event_data['주문수량']
                                +"\n체결가 : " + event_data['체결가'] + "원"
                                +"\n손익률 : " + event_data['손익률'] + "%")
                goal = int(event_data['체결가']) + (int(event_data['체결가']) * 0.035)
                self.kw.stock_info['종목정보'][event_data['종목코드']].update({"목표가": goal})

                self.logger.info("\n당일실현손익 : "  + self.kw.stock_info['종목정보'][event_data['종목코드']['당일실현손익(유가)']]
                                +"\n당일신현손익률 : " + self.kw.stock_info['종목정보'][event_data['종목코드']['당일신현손익률(유가)']])


                #파일저장
                logmsg = "매도\n"
                for key, value in self.kw.stock_info['종목정보'][event_data['종목코드']].items():
                    logmsg += key + " : " + value + "\n"
                self.tlog.info(logmsg)
                
                # callback
                self.logger.info("[SellStock CallBack] Notify callback method..")
                self.notify_callback('OnSellStock', event_data['종목코드'], "매도완료")




    def chejan_jango_callback(self):
        self.logger.debug("function: chejan_jango_callback")
