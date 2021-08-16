
from os import truncate
from mydata import keyManager
from telog import Telog
import TradeAlgo


class ConditionManager():
    def __init__(self, kw):
        self.kw = kw
        self.logger = Telog().logger
        self.logger.debug("class: ConditionManager")

    def on_receive_condition_ver(self, IRet, sMsg):
        """
        OnReceiveConditionVer(
            LONG lRet, // 호출 성공여부, 1: 성공, 나머지 실패
            BSTR sMsg  // 호출결과 메시지
        )
        
        저장된 사용자 조건식 불러오기 요청에 대한 응답 수신시 발생되는 이벤트입니다.
        """
        try:
            self.logger.debug("function: receive_condition_ver")
            condi_list = self.kw.get_condition_name_list()
            condi_list_array = condi_list.split(';')[:-1]
            condi_index = ""
            condi_name = ""
            self.logger.debug(condi_list_array)
            for data in condi_list_array:
                index, name = data.split("^")
                if name.strip() == keyManager.getJsonData("condi_search_name"):
                    condi_index = index.strip()
                    condi_name = name.strip()
                    break
                
            if condi_index != "":
                    send = self.send_condition(self.kw.screen_real_search, condi_name, condi_index, 1)
                    if send == 1:
                        self.logger.info("성공적으로 조건식을 실행했습니다: " + condi_name)
                    else:
                        self.logger.error("조건식 검색 실패")

            self.kw.event_loop.exit()
        except Exception as e:
            self.logger.error("on_receive_condition_ver Error")
            self.logger.error(e)
        finally:
            if self.kw.event_loop.isRunning():
                self.kw.event_loop.exit()

    def on_receive_real_condition(self, strCode, event_type, condi_name, condi_index):
        """
        OnReceiveRealCondition(
            BSTR strCode,   // 종목코드
            BSTR event_type,   //  이벤트 종류, "I":종목편입, "D", 종목이탈
            BSTR condi_name,    // 조건식 이름 
            BSTR condi_index    // 조건식 고유번호
        )
        
        실시간 조건검색 요청으로 신규종목이 편입되거나 기존 종목이 이탈될때 마다 발생됩니다.
        ※ 편입되었다가 순간적으로 다시 이탈되는 종목에대한 신호는 조건검색 서버마다 차이가 발생할 수 있습니다.
        """
        self.logger.debug("function: on_receive_real_condition")
        
        if event_type == "I":
            if TradeAlgo.checkstock(strCode): #디버깅
                data = [
                    ("code", strCode),
                    ("event_type", event_type),
                    ("condi_name", condi_name),
                    ("condi_index", condi_index)
                ]
                self.logger.debug(str(data))

                #callback
                self.kw.notify_callback('OnReceiveRealCondition', dict(data), self.kw.screen_real_search)

        



    def send_condition(self, strScrNo, condi_name, condi_index, nSearch):
        """
        SendCondition(
            BSTR strScrNo,    // 화면번호
            BSTR condi_name,  // 조건식 이름
            int condi_index,     // 조건식 고유번호
            int nSearch   // 실시간옵션. 0:조건검색만, 1:조건검색+실시간 조건검색
        )
        
        서버에 조건검색을 요청하는 함수입니다.
        마지막 인자값으로 조건검색만 할것인지 실시간 조건검색도 수신할 것인지를 지정할 수 있습니다.
        GetConditionNameList()함수로 얻은 조건식 이름과 고유번호의 쌍을 맞춰서 사용해야 합니다.
        리턴값 1이면 성공이며, 0이면 실패입니다.
        요청한 조건식이 없거나 조건 고유번호와 조건명이 서로 안맞거나 조회횟수를 초과하는 경우 실패하게 됩니다.
        """
        ret = self.kw.dynamicCall("SendCondition(QString, QString, int, int)",
                                strScrNo, condi_name, int(condi_index), nSearch)

        return ret

