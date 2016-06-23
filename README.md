
A simple python framework to analyze trade execution

Points to note:
1. Works with python 2.7
2. Minute bars in datafiles are all of date 20150325. So while running backtesting,mention the date as 20160325.
3. MeanRev, Momentum are two execution algorithms which one can mention as algorithm.
4. B should be for Buy and S for Sell.
5. starttime is hhmmss in UTC time zone.
6. Example command: python  execution/simulate_execution.py 20150325 VWO S 12 MeanRev 173500
