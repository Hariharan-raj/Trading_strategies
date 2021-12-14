import numpy as np
import pandas as pd
import math as m
class indicators():
    
    def SMA(self,data,periods=14):
        res = data.rolling(periods).mean()
        return res

    def EMA(self,data,periods=14):
        res = data.ewm(span=periods,adjust=False).mean()
        return res

    def RMA(self,data,periods=14):
        res = data.ewm(alpha=1/periods,adjust=False).mean()
        return res

    def WMA(self,data,periods=14):
        weights = np.array([i+1 for i in range(periods)])
        sum_weights = np.sum(weights)
        res = (data.rolling(window=periods).apply(lambda x: np.sum(weights*x) / sum_weights, raw=False))
        return res

    def HMA(self,data,periods=14):
        res = self.WMA(2*self.WMA(data, int(periods/2))
              -self.WMA(data, periods), round(m.sqrt(periods)))
        return res

    def RSI(self,data,periods=14):
        change = data-data.shift(1)
        um = change.copy()
        dm = change.copy()
        um.loc[um<0] = 0
        dm.loc[dm>0] = 0
        dm = -1*dm
        aum = self.SMA(um,periods=periods)
        adm = self.SMA(dm,periods=periods)
        rs = aum/adm
        res = 100 - 100/(1+rs)
        return res
    


    def ATR_all(self,data,periods=14):
        assert isinstance(data,pd.DataFrame) , "Datatype of data should be pandas Dataframe "
        data.columns = data.columns.str.lower()
        assert set(['high','low','close']).issubset(set(data.columns.tolist())) , "Dataframe didn't consist either of high , low or close"
        
        data['tr0'] = abs(data.high - data.low)
        data['tr1'] = abs(data.high - data.close.shift())
        data['tr2'] = abs(data.low - data.close.shift())
        tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
        tr[0] = np.NaN
        res = self.RMA(tr,periods=periods)
        return tr,res

    def ATR(self,data,periods=14):
        _ , res = self.ATR_all(data,periods)
        return res

    def TR(self,data,periods=14):
        res , _ = self.ATR_all(data,periods)
        return res

    def SUPERTREND(self,data,periods=14,multiplier=3):
        assert isinstance(data,pd.DataFrame) , "Datatype of data should be pandas Dataframe "
        data.columns = data.columns.str.lower()
        assert set(['high','low','close']).issubset(set(data.columns.tolist())) , "Dataframe didn't consist either of high , low or close"

        """
        SuperTrend Algorithm :
        
            BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
            BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
            
            FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
                                THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
            FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND)) 
                                THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)
            
            SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                            Current FINAL UPPERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                                Current FINAL LOWERBAND
                            ELSE
                                IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                                    Current FINAL LOWERBAND
                                ELSE
                                    IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                        Current FINAL UPPERBAND
        """
        
        atr = 'ATR_' + str(periods)
        st = 'ST_' + str(periods) + '_' + str(multiplier)
        stx = 'STX_' + str(periods) + '_' + str(multiplier)
        ohlc = ['open','high','low','close']

        data['hl2'] = (data.high + data.low)/2
        data[atr] = self.ATR(data,periods)


        # Compute basic upper and lower bands
        data['basic_ub'] = data['hl2'] + multiplier * data[atr]
        data['basic_lb'] = data['hl2'] - multiplier * data[atr]
        
        # Compute final upper and lower bands
        data['final_ub'] = 0.00
        data['final_lb'] = 0.00
        for i in range(periods, len(data)):
            data['final_ub'].iat[i] = data['basic_ub'].iat[i] if data['basic_ub'].iat[i] < data['final_ub'].iat[i - 1] or data[ohlc[3]].iat[i - 1] > data['final_ub'].iat[i - 1] else data['final_ub'].iat[i - 1]
            data['final_lb'].iat[i] = data['basic_lb'].iat[i] if data['basic_lb'].iat[i] > data['final_lb'].iat[i - 1] or data[ohlc[3]].iat[i - 1] < data['final_lb'].iat[i - 1] else data['final_lb'].iat[i - 1]
        
        # Set the Supertrend value
        data[st] = 0.00
        
        for i in range(periods, len(data)):
            data[st].iat[i] = data['final_ub'].iat[i] if data[st].iat[i - 1] == data['final_ub'].iat[i - 1] and data[ohlc[3]].iat[i] <= data['final_ub'].iat[i] else \
                            data['final_lb'].iat[i] if data[st].iat[i - 1] == data['final_ub'].iat[i - 1] and data[ohlc[3]].iat[i] >  data['final_ub'].iat[i] else \
                            data['final_lb'].iat[i] if data[st].iat[i - 1] == data['final_lb'].iat[i - 1] and data[ohlc[3]].iat[i] >= data['final_lb'].iat[i] else \
                            data['final_ub'].iat[i] if data[st].iat[i - 1] == data['final_lb'].iat[i - 1] and data[ohlc[3]].iat[i] <  data['final_lb'].iat[i] else 0.00 
            
        
        # Mark the trend direction up/down
        data[stx] = np.where((data[st] > 0.00), np.where((data[ohlc[3]] < data[st]), 'down',  'up'), np.NaN)
        # Remove basic and final bands from the columns
        data.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)
        #data.fillna(0, inplace=True)
        x = data[st].copy()
        y = data[stx].copy()
        return x,y

    def MACD(self,data, fastEMA=12, slowEMA=26, signal=9):

        # Compute fast and slow EMA    
        fast_ema = self.EMA(data, fastEMA)
        slow_ema = self.EMA(data, slowEMA)
        # Compute MACD
        macd = fast_ema - slow_ema
        # Compute MACD Signal
        macd_signal = self.EMA(macd,signal)
        # Compute MACD Histogram
        hist = macd - macd_signal
        return macd,macd_signal,hist

    def BOLLINGER_BAND(self,data, periods=20, multiplier=2):
    
        sma = data.rolling(window=periods).mean()
        sd = data.rolling(window=periods).std()
        UPPER_BAND = sma + (multiplier * sd)
        LOWER_BAND = sma - (multiplier * sd)
        return UPPER_BAND,sma,LOWER_BAND



