from koapy import KiwoomOpenApiPlusEntrypoint
import logging
import grpc
from pandas import Timestamp
from exchange_calendars import get_calendar
from pprint import PrettyPrinter
from google.protobuf.json_format import MessageToDict

import MainTrade
import TradeAlgo


pp = PrettyPrinter()

def pprint_event(event):
    pp.pprint(MessageToDict(event, preserving_proto_field_name=True))

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d',
    level=logging.DEBUG)

entrypoint = KiwoomOpenApiPlusEntrypoint()
account_no = entrypoint.GetFirstAvailableAccount()
# 모듈 경로 확인 (기본 함수 사용 예시)
module_path = entrypoint.GetAPIModulePath()
#print(module_path)


krx_calendar = get_calendar('XKRX')

def is_currently_in_session():
    logging.debug("function: is_currently_in_session")
    now = Timestamp.now(tz=krx_calendar.tz)
    previous_open = krx_calendar.previous_open(now).astimezone(krx_calendar.tz)
    next_close = krx_calendar.next_close(previous_open).astimezone(krx_calendar.tz)
    return previous_open <= now <= next_close


realCode = []

def Login():
    logging.info('Logging in...')
    entrypoint.EnsureConnected()
    logging.info('Logged in.')

def StartSetting():
    logging.debug("function: StartSetting")
    CallConditionEvent()

def GetStockDetail(strCode):
    return entrypoint.GetStockBasicInfoAsDict(strCode)

#현재 보유종목 계좌풀 넣기


#장열리면 실시간 검색 시작
#실시간 편입시 조건 확인
def CallConditionEvent():
    logging.debug("function: ConditionEvent")
    entrypoint.EnsureConditionLoaded()
    condi_name = MainTrade.json_data['condi_search_name']
    logging.debug("실시간 조건검색 조건 확인중...")
    searchStream = entrypoint.GetCodeListByConditionAsStream(condi_name, with_info=True)
    try:
        for event in searchStream:
            pprint_event(event)
    except grpc.RpcError as e:
        logging.error(e)
    logging.debug("is pass?")
    #실시간 편입되면
    #시가랑 비교
    #checkstock
    #매수처리

def BuyStock(strCode):
    logging.debug("function: BuyStock")
    if is_currently_in_session():
        logging.debug("inSession Check")
        logging.debug("매수 주문 : " + strCode)
        splitAccount = MainTrade.SetAccount()
        quan = MainTrade.vr_bank[splitAccount]["출금가능금액"]
        #현재가
        stockPrice = 10
        if quan < 0:
            logging.info("No more Account.")
            MainTrade.dbgout("거래할 잔고가 부족합니다.")
            
        else:
            quan /= stockPrice
            for event in entrypoint.OrderCall('시장가 매수', '3000', account_no, 1, strCode, quan, 0, '03', ''):
                pprint_event(event)
    else:
            logging.info("Fail to Trade: Market is not open.")
            MainTrade.dbgout("거래 불가: 장시간이 아닙니다.")


#조건 확인되면 매수
#매수이후 실시간검색 추가
#실시간검색은 매회 가격 비교
#조건가격에 맞으면 매도 
#실시간검색 삭제

