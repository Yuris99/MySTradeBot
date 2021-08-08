import sys
import time
import logging
from datetime import datetime
import json

from PyQt5.QtWidgets import *
import telegram

#import Trader
from kiwoom import kiwoom


logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d',
    level=logging.DEBUG)

with open('.mydata/key.json') as json_file:
    json_data = json.load(json_file)

telbot = telegram.Bot(token=json_data["telegram_Token"])
chatid = json_data["telegram_chatid"]

logger = telbot.logger
logger.setLevel(logging.INFO)

#formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')

#stream_handler = logging.StreamHandler()
#stream_handler.setFormatter(formatter)


def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 텔레그램으로 동시에 출력한다."""
    strbuf = datetime.now().strftime("[%m/%d %H:%M:%S.%f] ") + message
    telbot.sendMessage(chat_id=chatid, text=strbuf)
    logging.info(message)


vr_bank = {}
use_account = []

def SetAccount():
    for i, data in use_account:
        if(data == False):
            data = True
            return i
    return -1


def Main():
    logging.debug("function: main")
    """
    app = QApplication(sys.argv)

    trader = Trader.Trader()
    #trader.run()

    app.exec()
    """
    #python/kiwoom/kiwoom.py
    app = QApplication(sys.argv)
    stockbank = kiwoom.Kiwoom()

    target_buy_count = 1
    Max_bought_money = 1000000
    for i in range(target_buy_count):
        vr_bank.update({i:{}})
        vr_bank[i].update({"출금가능금액":min(Max_bought_money, int(stockbank.ok_deposit)/target_buy_count)})
        use_account.append(False)
    print(vr_bank)
    dbgout(f"계좌 현황\n총매입금액 : {format(int(stockbank.total_buy_money), ',')}원\n총수익률 : {stockbank.total_profit_loss_rate_result}")

    #TEST 
    try:
        dbgout("Debuging mode")
        

    except Exception as ex:
        dbgout('`main -> exception! ' + str(ex) + '`')



    """
    try:
        have_list = []
        target_buy_count = 2
        Max_bought_money = 1000000
        dbgout("test")

        while True:
            t_now = datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=30, second=0,microsecond=0)
            today = datetime.today().weekday()
            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                printlog('Today is', 'Saturday.' if today == 5 else 'Sunday.')
                sys.exit(0)
            if t_9 < t_now < t_start and soldout == False:
                soldout = True
                sell_all()
            if t_start < t_now < t_sell :  # AM 09:05 ~ PM 03:20 : 매수
                for sym in symbol_list:
                    if len(bought_list) < target_buy_count:
                        buy_etf(sym)
                        time.sleep(1)
                if t_now.minute == 30 and 0 <= t_now.second <= 5: 
                    get_stock_balance('ALL')
                    time.sleep(5)
            if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 정리
                if sell_all() == True:
                    dbgout('`sell_all() returned True -> self-destructed!`')
                    sys.exit(0)
            if t_exit < t_now:  # PM 03:25 ~ :프로그램 종료
                dbgout('`self-destructed!`')
                sys.exit(0)
            time.sleep(3)
    except Exception as ex:
        dbgout('`main -> exception! ' + str(ex) + '`')
    """
    



if __name__=='__main__':
    Main()