import sys
from typing import Text

from PyQt5.QtWidgets import QApplication

from mydata import keyManager
import telog

from kiwoom import kw

logger = telog.Telog().logger

def Main():
    try:
        logger.debug("function: Main")
        app = QApplication(sys.argv)
        trader = kw.Kiwoom()
        
        
    except Exception as ex:
        logger.error('main -> exception! ' + str(ex))
    


if __name__=='__main__':
    Main()