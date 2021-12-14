from time import sleep
import datetime
from datetime import timedelta,datetime
import logging
from kiteconnect import KiteTicker
import pandas as pd
import numpy as np
import requests
import sys
from kiteconnect import KiteConnect
from req_token import get_token
import calendar
import csv

user_name = ''
password = ''
pin = ''
api_key = ''
api_secret = ''


#logging.basicConfig(level=logging.DEBUG)
kite = KiteConnect(api_key=api_key)      #https://kite.trade/connect/login?v=3&api_key=8v9r4men9xpk5gf5
Get_Token = get_token(user_name,password,pin,api_key)
request_token = Get_Token.get_request_token()

data = kite.generate_session(request_token, api_secret=api_secret)
kite.set_access_token(data["access_token"])
kws = KiteTicker(api_key, data["access_token"])


CE_ATM = None
PE_ATM = None
CE_OTM = None
PE_OTM = None
CE_ATM_ENTRY_PRICE = None
PE_ATM_ENTRY_PRICE = None
CE_OTM_ENTRY_PRICE = None
PE_OTM_ENTRY_PRICE = None
ATM_C = 0
ATM_P = 0
OTM_C = 0
OTM_P = 0
CE_TRIGGER = None
PE_TRIGGER = None
qty = 25
SL_LOT = 4
FIRST_TARGET_HIT = False
SECOND_TARGET_HIT = False
STOPLOSS_HIT = False
MAIN_ORDER_PLACED = False
ALLOW_FOR_TRADE = False
exit_triggered = False
data = {}
ORDER_IDS = {}
CE_strike_map = {}
PE_strike_map = {}
CE_name_map = {}
PE_name_map = {}
sym_to_name = {}
CE_sym_list = []
PE_sym_list = []


ORDER_IDS["CE"] = 0
ORDER_IDS["PE"] = 0


def round_it(x):
    x=(round(x, 2)*100//5*5)/100
    return x

def PlaceBuyOrder(symbolName,qty,order_type,condn_type,price=None):
    global data
    if order_type == "MKT" :
        order_type = kite.ORDER_TYPE_MARKET
    elif order_type == "SLM" :
        order_type = kite.ORDER_TYPE_SLM
    order_id = 0
    order_id = kite.place_order(tradingsymbol=symbolName,
                        exchange=kite.EXCHANGE_NFO,
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        trigger_price=price,
                        quantity=qty,
                        order_type=order_type,
                        product=kite.PRODUCT_MIS,
                        variety=kite.VARIETY_REGULAR)

    print(condn_type,"   BUY ",symbolName,"  ",qty,"  qty           ",datetime.now(),"                ",data[symbolName],"            ",order_type,"       @ ",price)

    return order_id

def PlaceSellOrder(symbolName,qty,order_type,condn_type,price=None):
    global data
    if order_type == "MKT" :
        order_type = kite.ORDER_TYPE_MARKET
    elif order_type == "SLM" :
        order_type = kite.ORDER_TYPE_SLM

    order_id = kite.place_order(tradingsymbol=symbolName,
                        exchange=kite.EXCHANGE_NFO,
                        transaction_type=kite.TRANSACTION_TYPE_SELL,
                        trigger_price=price,
                        quantity=qty,
                        order_type=order_type,
                        product=kite.PRODUCT_MIS,
                        variety=kite.VARIETY_REGULAR)

    print(condn_type,"   SELL ",symbolName,"  ",qty,"  qty           ",datetime.now(),"                ",data[symbolName],"            ",order_type,"       @ ",price)

    return order_id

def ModifyOrder(order_id , name , variety = kite.VARIETY_REGULAR , quantity = None ) :

    global data
    print("MODIFY  ORDER          ",order_id,"     TYPE    ",name,"     qty      ",quantity )

    
    kite.modify_order( variety, order_id , quantity=quantity )

def CANCEL_ORDER(order_id,type = None):

    print("Cancelling order   ",type)
    kite.cancel_order( kite.VARIETY_REGULAR , order_id)

def Place_main_order() :
    global CE_ATM , PE_ATM , CE_OTM , PE_OTM , data
    global CE_ATM_ENTRY_PRICE , PE_ATM_ENTRY_PRICE , CE_TRIGGER , PE_TRIGGER
    global ORDER_IDS
    print("Main order placed")
    PlaceSellOrder(CE_ATM,qty*SL_LOT,"MKT","ENTRY")
    PlaceSellOrder(PE_ATM,qty*SL_LOT,"MKT","ENTRY")
    ORDER_IDS["CE"] = PlaceBuyOrder(CE_OTM,qty*SL_LOT,"SLM","ENTRY",CE_TRIGGER)
    ORDER_IDS["PE"] = PlaceBuyOrder(PE_OTM,qty*SL_LOT,"SLM","ENTRY",PE_TRIGGER)
    CE_ATM_ENTRY_PRICE = data[CE_ATM]
    PE_ATM_ENTRY_PRICE = data[PE_ATM]

def profit_condn_check():

    global CE_ATM_ENTRY_PRICE , PE_ATM_ENTRY_PRICE , CE_OTM_ENTRY_PRICE , PE_OTM_ENTRY_PRICE , qty , SL_LOT
    global FIRST_TARGET_HIT , SECOND_TARGET_HIT , STOPLOSS_HIT , data
    global CE_OTM , PE_OTM , CE_ATM , PE_ATM , ORDER_IDS

    if STOPLOSS_HIT :
        SLM_PROFIT = ( data[CE_OTM] + data[PE_OTM] - CE_OTM_ENTRY_PRICE - PE_OTM_ENTRY_PRICE ) * qty
    else :
        SLM_PROFIT = 0
    ATM_PROFIT = (CE_ATM_ENTRY_PRICE + PE_ATM_ENTRY_PRICE - data[CE_ATM] - data[PE_ATM]) * qty
    NET_PROFIT = SLM_PROFIT + ATM_PROFIT
    print(NET_PROFIT)


    if FIRST_TARGET_HIT == True :
        if SECOND_TARGET_HIT == True :
            pass
        else :

            if NET_PROFIT > 1000 :
                SECOND_TARGET_HIT = True
                print()
                print("SECOND TARGET HIT     ",NET_PROFIT)
                print()

                if STOPLOSS_HIT == True :

                    # Exit 1 CE & PE SLM
                    PlaceSellOrder(CE_OTM,qty*1,"MKT","EXIT")
                    PlaceSellOrder(PE_OTM,qty*1,"MKT","EXIT")
                else :

                    #Modify 1 CE & PE SLM 
                    ModifyOrder(ORDER_IDS["CE"] , "CE" , quantity = qty*1)
                    ModifyOrder(ORDER_IDS["PE"] , "PE" , quantity = qty*1)
                SL_LOT = 1

                # Exit 1 CE & PE ATM
                PlaceBuyOrder(CE_ATM,qty*1,"MKT","EXIT")
                PlaceBuyOrder(PE_ATM,qty*1,"MKT","EXIT")

    else :
        if NET_PROFIT > 500 :
            FIRST_TARGET_HIT = True
            print()
            print("FIRST TARGET HIT     ",NET_PROFIT)
            print()
            if STOPLOSS_HIT == True :

                # Exit 2 CE & PE SLM
                PlaceSellOrder(CE_OTM,qty*2,"MKT","EXIT")
                PlaceSellOrder(PE_OTM,qty*2,"MKT","EXIT")
            else :

                #Modify 2 CE & PE SLM 
                ModifyOrder(ORDER_IDS["CE"] , "CE" , quantity = qty*2)
                ModifyOrder(ORDER_IDS["PE"] , "PE" , quantity = qty*2)

            SL_LOT = 2

            # Exit 2 CE & PE ATM
            PlaceBuyOrder(CE_ATM,qty*2,"MKT","EXIT")
            PlaceBuyOrder(PE_ATM,qty*2,"MKT","EXIT")

    if NET_PROFIT < -750 :
        print()
        print("STOP HIT     ",NET_PROFIT)
        print()
        Exit_program()



def stoploss_check():
    global data , PE_OTM , CE_OTM , PE_TRIGGER , CE_TRIGGER , SL_LOT , ORDER_IDS , qty
    global STOPLOSS_HIT , CE_OTM_ENTRY_PRICE , PE_OTM_ENTRY_PRICE
    if data[PE_OTM] > PE_TRIGGER :

        #CANCEL SLM CE_OTM  SL_LOT
        #PLACE MKT CE_OTM SL_LOT
        print("PE stop hit , converting CE stop to MKT order")
        CANCEL_ORDER(ORDER_IDS["CE"],"CE")
        PlaceBuyOrder(CE_ATM,qty*SL_LOT,"MKT","ENTRY")
        STOPLOSS_HIT = True
        CE_OTM_ENTRY_PRICE = data[CE_OTM]
        PE_OTM_ENTRY_PRICE = data[PE_OTM]
    
    elif data[CE_OTM] > CE_TRIGGER :
        #CANCEL SLM PE_OTM  SL_LOT
        #PLACE MKT PE_OTM SL_LOT
        print("CE stop hit , converting PE stop to MKT order")
        CANCEL_ORDER(ORDER_IDS["PE"],"PE")
        PlaceBuyOrder(PE_ATM,qty*SL_LOT,"MKT","ENTRY")
        STOPLOSS_HIT = True
        CE_OTM_ENTRY_PRICE = data[CE_OTM]
        PE_OTM_ENTRY_PRICE = data[PE_OTM]
    
    



def Exit_program():
    
    global CE_ATM , PE_ATM , CE_OTM , PE_OTM , ORDER_IDS , qty , SL_LOT , MAIN_ORDER_PLACED , exit_triggered
    
    if MAIN_ORDER_PLACED :
        # Exit all ATM positions
        PlaceBuyOrder(CE_ATM,qty*SL_LOT,"MKT","EXIT")
        PlaceBuyOrder(PE_ATM,qty*SL_LOT,"MKT","EXIT")

        if STOPLOSS_HIT :
            # Exit all SL positions
            PlaceSellOrder(CE_OTM,qty*SL_LOT,"MKT","EXIT")
            PlaceSellOrder(PE_OTM,qty*SL_LOT,"MKT","EXIT")
            
        else :
            # Cancel all SL positions
            CANCEL_ORDER(ORDER_IDS["CE"],"CE")
            CANCEL_ORDER(ORDER_IDS["PE"],"PE")
            

    
    print("Program exit")
    exit_triggered = True
    sys.exit()


def on_ticks(ws, ticks):
    # Callback to receive ticks.

    for tick in ticks:
        instrument=tick["instrument_token"]      

        # For any other timeframe. Simply change ltt_min_1 variable defination.
        # e.g.
        # ltt_min_15=datetime.datetime(ltt.year, ltt.month, ltt.day, ltt.hour,ltt.minute//15*15)

        ### Forming 1 Min Candles...
        global ATM_C , ATM_P , OTM_C , OTM_P 
        global data , MAIN_ORDER_PLACED 
        global CE_TRIGGER , PE_TRIGGER
        global ALLOW_FOR_TRADE , day_high , day_low , pday_high , pday_low , over_riding_condn , condn_start_time
        global BANKNIFTY_TOKEN , REQ_STOCK_LIST
        global CE_ATM , PE_ATM , CE_OTM , PE_OTM


        instrument=tick["instrument_token"]   
        if tick["tradable"] :
            ltp_time = tick["last_trade_time"]
        else :
            ltp_time = tick["timestamp"]
        ltp = round_it(tick["last_price"])

        data[sym_to_name[instrument]] = ltp

        if BANKNIFTY_TOKEN == instrument:
            if ltp_time > condn_start_time :
                if ( day_high < pday_high and day_low > pday_low ) or over_riding_condn:
                    ALLOW_FOR_TRADE = True

                    if ATM_C == 0:
                        ATM_C = int(ltp/100)*100
                        ATM_P = int(ltp/100)*100
                        ws.unsubscribe([instrument])
                else :
                    Exit_program()
                
                
            else :
                if ltp > day_high :
                    day_high = ltp
                elif ltp < day_low :
                    day_low = ltp

        elif MAIN_ORDER_PLACED == False:
            if ALLOW_FOR_TRADE :

                if data[CE_name_map[ATM_C]] != 0 and data[PE_name_map[ATM_P]] != 0 :
                    total_premium = data[CE_name_map[ATM_C]] + data[PE_name_map[ATM_P]]
                    out_points = int(total_premium/100)*100

                    OTM_C = ATM_C + out_points
                    OTM_P = ATM_P - out_points

                    if data[CE_name_map[OTM_C]] != 0 and data[PE_name_map[OTM_P]] != 0 :
                        CE_ATM = CE_name_map[ATM_C]
                        PE_ATM = PE_name_map[ATM_P]
                        CE_OTM = CE_name_map[OTM_C]
                        PE_OTM = PE_name_map[OTM_P]
                        CE_TRIGGER = data[CE_name_map[OTM_C]] * 1.3
                        PE_TRIGGER = data[PE_name_map[OTM_P]] * 1.3
                        REQ_STOCK_LIST = [CE_ATM,PE_ATM,CE_OTM,PE_OTM]
                        MAIN_ORDER_PLACED = True
                        Place_main_order()
            
    if MAIN_ORDER_PLACED :
        if data[sym_to_name[instrument]] not in REQ_STOCK_LIST :
            #ws.unsubscribe([instrument])
            pass

        if not STOPLOSS_HIT :
            stoploss_check()
        
        profit_condn_check()

    ltt=datetime.now()
    if ltt.hour==13 and ltt.minute==56:
        print("Day exit")
        Exit_program()
        

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    global tokens
    print("In connect")
    ws.subscribe(tokens)
    
    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, tokens)
    

def on_close(ws, code, reason):
    #On connection close stop the main loop
    #Reconnection will not happen after executing `ws.stop()`
    global exit_triggered
    print("Close reason  :  ",reason)
    if exit_triggered:
        print("Program stopped")
        ws.stop()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

emty_list = []
with open(r"C:\Users\HP\Desktop\DATA_SOURCE.csv" ,  mode='r') as csv_file :
    csv_reader = csv.reader(csv_file, delimiter=',')
    
    for row in csv_reader:
        emty_list.append(row)

pday_high = float(emty_list[0][1])
pday_low = float(emty_list[1][1])

day_high = ( pday_high + pday_low ) / 2
day_low = ( pday_high + pday_low ) / 2

lower_limit = day_high - 2000
upper_limit = day_high + 2000
today = datetime.now()
if calendar.weekday(today.year, today.month, today.day) != 3 :
    condn_start_time = datetime.now().replace(hour = 9, minute=30,second=0,microsecond=0) 
    over_riding_condn = False
else :
    condn_start_time = datetime.now().replace(hour = 10, minute=0,second=0,microsecond=0) 
    over_riding_condn = True



InstrumentInfo=kite.instruments(exchange="NFO")
InstrumentID={}
tokens=[]

data1 = pd.DataFrame(InstrumentInfo)
print(data1.expiry)
data1['expiry'] = data1['expiry'].apply(lambda x: x.strftime("%Y-%m-%d"))
instrument_name = 'BANKNIFTY'

expiry_list = list(set(data1.expiry.values.tolist()))
print(expiry_list)
expiry_list.sort()
expiry = expiry_list[0]

CE_SET = data1[(data1['name']==instrument_name) & (data1["strike"] >=lower_limit) & (data1["strike"] <= upper_limit) & (data1["instrument_type"] == 'CE')  & (data1["expiry"] == expiry)]
PE_SET = data1[(data1['name']==instrument_name) & (data1["strike"] >=lower_limit) & (data1["strike"] <= upper_limit) & (data1["instrument_type"] == 'PE')  & (data1["expiry"] == expiry)]

print(CE_SET.head())



CE_SET = CE_SET[["instrument_token","strike","tradingsymbol"]].values.tolist()
for i in CE_SET:
    CE_strike_map[i[0]] = int(i[1])    #symbol   to strike
    CE_name_map[int(i[1])] = i[2]      #strike to name
    sym_to_name[i[0]] = i[2]           #symbol to name
    CE_sym_list.append(i[0])
    tokens.append(i[0])
    data[i[2]]=0

print(CE_strike_map)
print(CE_name_map)

PE_SET = PE_SET[["instrument_token","strike","tradingsymbol"]].values.tolist()
for i in PE_SET:
    PE_strike_map[i[0]] = int(i[1])   #symbol   to strike
    PE_name_map[int(i[1])] = i[2]     #strike to name
    sym_to_name[i[0]] = i[2]           #symbol to name
    PE_sym_list.append(i[0])
    tokens.append(i[0])
    data[i[2]]=0

InstrumentInfo=kite.instruments(exchange="NSE")

for i in InstrumentInfo:
    if i['tradingsymbol']=='NIFTY BANK' and i['segment']=='INDICES':
        BANKNIFTY_TOKEN = i['instrument_token']
        tokens.append(BANKNIFTY_TOKEN)
        sym_to_name.update({i['instrument_token']:i['tradingsymbol']})
        data[i['tradingsymbol']]=0
        print(i)



StartTime =  datetime.now().replace(hour=9, minute=15,second=0,microsecond=0) 

while datetime.now() < StartTime :
    pass



print("Program Starts")

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.


kws.connect()




