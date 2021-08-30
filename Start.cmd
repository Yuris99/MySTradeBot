set root=C:\Users\mose1\anaconda3
call %root%\Scripts\activate.bat %root% 

call conda env list

call conda activate pystock32
call cd C:\Users\mose1\Documents\TradeS
call python MainApp.py

pause