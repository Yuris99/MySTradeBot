from PyQt5.QAxContainer import *
from singleton_decorator import singleton

from mydata import keyManager
import telog

logger = telog.Telog().logger

@singleton
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        logger.debug("Class: Kiwoom")
        