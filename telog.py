import logging
import telegram
from singleton_decorator import singleton
from datetime import datetime

from mydata import keyManager


"""
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d',
    level=logging.DEBUG)
"""

#logger print info message
@singleton
class Telog():
    def __init__(self):
        self.logger = logging.getLogger("AppInfoText")
        self.logger.setLevel(logging.DEBUG)
        
        #set debugging file handler
        debugformat = '[%(asctime)s|{}|%(levelname)s|%(filename)s:%(funcName)s:%(lineno)s] %(message)s'. \
            format(self.logger.name)
        debugformatter = logging.Formatter(debugformat)
        #log_path = "log/app_{}.log".format(self.logger.name)
        debug_log_path = datetime.now().strftime("debug/Debugger %Y-%m-%d %H-%M-%S.log")
        debug_handler = logging.FileHandler(filename = debug_log_path, encoding="utf-8")
        debug_handler.suffix = '%Y%m%d'
        debug_handler.setFormatter(debugformatter)
        debug_handler.setLevel(logging.DEBUG)

        #set file handler
        fileformat = '[%(asctime)s|{}|%(levelname)s|%(filename)s:%(funcName)s:%(lineno)s] %(message)s'. \
            format(self.logger.name)
        fileformatter = logging.Formatter(fileformat)
        #log_path = "log/app_{}.log".format(self.logger.name)
        file_log_path = datetime.now().strftime("log/AppLog %Y-%m-%d.log")
        file_handler = logging.FileHandler(filename = file_log_path, encoding="utf-8")
        file_handler.suffix = '%Y%m%d'
        file_handler.setFormatter(fileformatter)
        file_handler.setLevel(logging.INFO)

        #set console handler
        streamformat='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d'
        streamformatter = logging.Formatter(streamformat)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(streamformatter)
        stream_handler.setLevel(logging.DEBUG) #for test 
        
        #set telegram handler
        telformat= datetime.now().strftime("[%m/%d %H:%M:%S.%f] ") + '%(message)s'
        telformatter = logging.Formatter(telformat)
        telegram_handler = LogTelHandler()
        telegram_handler.setFormatter(telformatter)
        telegram_handler.setLevel(logging.INFO)

        # Add Formatters
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(telegram_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(debug_handler)



#telegram handler
class LogTelHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.telbot = telegram.Bot(token=keyManager.getJsonData("telegram_token"))
        self.chatid = keyManager.getJsonData("telegram_chatid")
    
    def emit(self, record):
        if self.formatter is None: 
            text = record.msg
        else:
            text = self.formatter.format(record)
        
        self.telbot.sendMessage(chat_id=self.chatid, text=text)


#거래 로그
@singleton
class TradeLog():
    def __init__(self):
        self.logger = logging.getLogger("TradeLog")
        self.logger.setLevel(logging.INFO)
        

        #set file handler
        fileformat = '[%(asctime)s] %(message)s'
        fileformatter = logging.Formatter(fileformat)
        #log_path = "log/app_{}.log".format(self.logger.name)
        file_log_path = datetime.now().strftime("log/TradeLog %Y-%m-%d.log")
        file_handler = logging.FileHandler(filename = file_log_path, encoding="utf-8")
        file_handler.suffix = '%Y%m%d'
        file_handler.setFormatter(fileformatter)
        file_handler.setLevel(logging.INFO)

        # Add Formatters
        self.logger.addHandler(file_handler)

