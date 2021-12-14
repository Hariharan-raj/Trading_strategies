from time import sleep
from datetime import timedelta,datetime,date
import logging
from kiteconnect import KiteTicker
import pandas as pd
import numpy as np
import requests
from indicators import indicators
from kiteconnect import KiteConnect
from req_token import get_token
import calendar
import csv
import sys
import socket
logging.basicConfig(filename=r'C:\Users\HP\Desktop\INVESTGINEER ARBITRAGE.txt', level=logging.DEBUG, format="%(asctime)s;%(levelname)s;%(message)s",datefmt="%Y-%m-%d %H:%M:%S")


user_name = 'SF6246'
password = 'zsxdcfvgb#987654'
pin = '987654'
api_key = 'vwokz2axbzu9auqk'
api_secret = 'yez9c74cwj2iy3lnyyoij9yssmiewd6b'

kite = KiteConnect(api_key=api_key)      #https://kite.trade/connect/login?v=3&api_key=8v9r4men9xpk5gf5
Get_Token = get_token(user_name,password,pin,api_key)
request_token = Get_Token.get_request_token()

data = kite.generate_session(request_token, api_secret=api_secret)
kite.set_access_token(data["access_token"])
kws = KiteTicker(api_key, data["access_token"])

threshold_input1 = 0.9
threshold_input2 = 1.25
threshold_exit = 0.3
TRADE_LIMIT = 5
lots = 1
between_time = datetime.now().replace(hour=15, minute=15 , second=0 , microsecond=0)
exit_time = datetime.now().replace(hour=15, minute=30 , second=0 , microsecond=0)
def buy(symbol,qty1):
    global live
    telegram_bot_sendtext("BUY {}".format(symbol))
    logging.debug("BUY {}  qty {} ".format(symbol,qty1))
    if live == 1 :
        kite.place_order(tradingsymbol=symbol,
                            exchange=kite.EXCHANGE_NFO,
                            transaction_type=kite.TRANSACTION_TYPE_BUY,
                            quantity=qty1,
                            order_type=kite.ORDER_TYPE_MARKET,
                            product=kite.PRODUCT_MIS,
                            variety=kite.VARIETY_REGULAR)
        
def sell(symbol,qty1):
    global live
    logging.debug("SELL {}  qty {}  ".format(symbol,qty1))
    if live == 1 :
        kite.place_order(tradingsymbol=symbol,
                            exchange=kite.EXCHANGE_NFO,
                            transaction_type=kite.TRANSACTION_TYPE_SELL,
                            quantity=qty1,
                            order_type=kite.ORDER_TYPE_MARKET,
                            product=kite.PRODUCT_MIS,
                            variety=kite.VARIETY_REGULAR)

def PlaceEntryOrder(name) :
    global name_to_FUT_sym , name_to_STK_sym  , find_qty , lots
    
    net_qty = find_qty[name] * lots
    sell(name_to_FUT_sym[name],net_qty)
    buy(name_to_STK_sym[name],net_qty)

    

def PlaceExitOrder(name) :
    global name_to_FUT_sym , name_to_STK_sym  , find_qty , lots
    
    net_qty = find_qty[name] * lots
    buy(name_to_FUT_sym[name],net_qty)
    sell(name_to_STK_sym[name],net_qty)

    
def telegram_bot_sendtext(bot_message,cont=2):
    if cont%2==0:
            bot_token = ''
            bot_chatID = ['']
            for i in bot_chatID:
                send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + i + '&parse_mode=Markdown&text=' + bot_message
                response = requests.get(send_text)
                
            return response.json()



exit_triggered = False
tokens = []
TRADE_LIST = []
data_source = {}
name_to_STK_sym = {}
InstrumentID = {}
token_to_name = {}
name_to_FUT_sym = {}
find_fut_or_stk = {}
find_qty = {}
live = 1


data_received = False
while not data_received :
    try :
        InstrumentInfo=kite.instruments(exchange='NFO')
        data_received = True
    except Exception as e :
        pass

data1 = pd.DataFrame(InstrumentInfo)
data1 = data1[data1["segment"]=="NFO-FUT"]
data1 = data1[data1['tradingsymbol'].str.contains('NIFTY') != True]
data1['expiry'] = data1['expiry'].apply(lambda x: x.strftime("%Y-%m-%d"))


expiry_list = list(set(data1.expiry.values.tolist()))
expiry_list.sort()
expiry = expiry_list[0]
data1 = data1[data1["expiry"]==expiry]
STOCK_LIST = data1.name.values.tolist()

data1 = data1[["instrument_token","name","tradingsymbol","lot_size"]].values.tolist()
for i in data1 :
    tokens.append(i[0])
    InstrumentID[i[2]] = i[0]
    token_to_name[i[0]] = i[1]
    name_to_FUT_sym[i[1]] = i[2]
    find_fut_or_stk[i[0]] = "FUT"
    find_qty[i[1]] = i[3]
    data_source[i[1]] = {}
    data_source[i[1]]["FUT"] = {}
    data_source[i[1]]["STK"] = {}
    data_source[i[1]]["FUT"]["BID"] = None
    data_source[i[1]]["FUT"]["ASK"] = None
    data_source[i[1]]["STK"]["BID"] = None
    data_source[i[1]]["STK"]["ASK"] = None



data_received = False
while not data_received :
    try :
        InstrumentInfo=kite.instruments(exchange='NSE')
        data_received = True
    except Exception as e :
        pass

data1 = pd.DataFrame(InstrumentInfo)
data1 = data1[["instrument_token","name","tradingsymbol"]].values.tolist()

for i in data1 :
    if i[2] in STOCK_LIST :
        tokens.append(i[0])
        InstrumentID[i[2]] = i[0]
        token_to_name[i[0]] = i[2]
        name_to_STK_sym[i[2]] = i[2]
        find_fut_or_stk[i[0]] = "STK"

def on_ticks(ws,ticks) :
    global token_to_name , find_fut_or_stk , data_source

    for tick in ticks:
        
        instrument_type=tick["instrument_token"]
        buy_side = tick["depth"]["buy"]
        sell_side = tick["depth"]["sell"]

        buy_side = pd.DataFrame(buy_side)
        del buy_side["orders"]
        buy_side = buy_side.values.tolist()

        sell_side = pd.DataFrame(sell_side)
        del sell_side["orders"]
        sell_side = sell_side.values.tolist()


        data_source[token_to_name[instrument_type]][find_fut_or_stk[instrument_type]]["BID"] = buy_side
        data_source[token_to_name[instrument_type]][find_fut_or_stk[instrument_type]]["ASK"] = sell_side



def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(tokens)
    print(tokens)
    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, tokens)

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    global exit_triggered
    if exit_triggered :
        print("Exit time  : ",datetime.now())
        ws.stop()


kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

kws.connect(threaded=True)

while datetime.now() < exit_time :
     
    for instrument in STOCK_LIST :
        if len(TRADE_LIST) < TRADE_LIMIT and instrument not in TRADE_LIST:
            try :
                data_set = data_source[instrument]["STK"]["ASK"] 
                net_req_qty = find_qty[instrument]
                count = 0
                weighted_price = 0

                while net_req_qty > 0 or count < 5:
                    if data_set[count][0] > net_req_qty :
                        weighted_price = weighted_price + data_set[count][1] * net_req_qty
                        net_req_qty = 0
                    else :
                        weighted_price = weighted_price + data_set[count][1] * data_set[count][0]
                        net_req_qty = net_req_qty - data_set[count][0]
                    count = count + 1
                
                if net_req_qty > 0 :
                    continue    

                stk_price = weighted_price / find_qty[instrument]
                fut_price = data_source[instrument]["FUT"]["BID"][0][1]
                

                print("Taking Entry trade {}".format(instrument))
                print("FUT at {}".format(fut_price))
                print("STK at {}".format(stk_price))
                print("Required qty = {}".format(find_qty[instrument]))
                print("STK ASK details")
                print(data_source[instrument]["STK"]["ASK"])
                print("FUT BID details")
                print(data_source[instrument]["FUT"]["BID"])
                

                
                

                val = ( fut_price - stk_price ) / stk_price *100
                if datetime.now() > between_time  :
                    threshold = threshold_input2 
                else :
                    threshold = threshold_input1
                if val > threshold and instrument not in TRADE_LIST:
                    
                    PlaceEntryOrder(instrument)
                    TRADE_LIST.append(instrument)

                    print(TRADE_LIST)
                    print()
                    print()
                    
                    

                    
            except Exception as e :
                pass
    
    if len(TRADE_LIST) > 0 :
        for instrument in TRADE_LIST :
            try :
                data_set = data_source[instrument]["STK"]["BID"] 
                net_req_qty = find_qty[instrument]
                count = 0
                weighted_price = 0

                while net_req_qty > 0 or count < 5:
                    if data_set[count][0] > net_req_qty :
                        weighted_price = weighted_price + data_set[count][1] * net_req_qty
                        net_req_qty = 0
                    else :
                        weighted_price = weighted_price + data_set[count][1] * data_set[count][0]
                        net_req_qty = net_req_qty - data_set[count][0]
                    count = count + 1
                
                if net_req_qty > 0 :
                    continue    

                stk_price = weighted_price / find_qty[instrument]
                fut_price = data_source[instrument]["FUT"]["ASK"][0][1]

                val = ( fut_price - stk_price ) / stk_price *100
                if val < threshold_exit :
                    PlaceExitOrder(instrument)
                    TRADE_LIST.remove(instrument)

                    print("Taking Exit trade {}".format(instrument))
            except Exception as e :
                pass




