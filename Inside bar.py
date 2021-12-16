from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
import pandas as pd
import numpy as np
import json
import requests
from datetime import datetime,timedelta
from time import mktime,sleep
import time
import websocket
from websocket import *
import ssl

ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
print("Initial wait")
for i in range(3700):
    sleep(10)
    pass

def unwrap(x):
    return json.loads(x)

def login():
    #    userId,password,yob
    global samco
    login=samco.login(body={"userId":"DA66547",'password':"@dvik2020P",'yob':"1987"})
    login = unwrap(login)
    print("Login details \n",login)
    if str.lower(login['statusMessage'])=='invalid password':
        print("Mismatch of username and password")
    elif 'account blocked' in str.lower(login['statusMessage']):
        print("Account blocked")
    else:
        samco.set_session_token(sessionToken=login["sessionToken"])
    
    return login["sessionToken"]
    
    
def place_order(x,CONT = 1):
    global symbol_name,qty
    if CONT==1:
        if x=='BUY':
            body = {"symbolName":symbol_name,
                    "exchange":samco.EXCHANGE_NFO,
                    "transactionType":samco.TRANSACTION_TYPE_BUY,
                    "orderType":samco.ORDER_TYPE_MARKET,
                    "quantity": str(qty),
                    "disclosedQuantity":"",
                    "orderValidity":samco.VALIDITY_DAY,
                    "productType":samco.PRODUCT_MIS,
                    "afterMarketOrderFlag":"NO"}
        else :
            body = {"symbolName":symbol_name,
                    "exchange":samco.EXCHANGE_NFO,
                    "transactionType":samco.TRANSACTION_TYPE_SELL,
                    "orderType":samco.ORDER_TYPE_MARKET,
                    "quantity": str(qty),
                    "disclosedQuantity":"",
                    "orderValidity":samco.VALIDITY_DAY,
                    "productType":samco.PRODUCT_MIS,
                    "afterMarketOrderFlag":"NO"}
        data = unwrap(samco.place_order(body=body))
        print(data)
        


print(datetime.now().strftime("%H-%M-%S"))
samco=StocknoteAPIPythonBridge()
sessionToken = login()


#scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
#
## add credentials to the account
#creds = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\Administrator\Desktop\credentials.json', scope)
#
## authorize the clientsheet 
#client = gspread.authorize(creds)
#sheet = client.open('CLIENT STRATEGY VARIABLES')
#
## get the first sheet of the Spreadsheet
#sheet_instance = sheet.get_worksheet(0)
#
#
## get all the records of the data
#records_data = sheet_instance.get_all_records()
#
## view the data
#records_df = pd.DataFrame.from_dict(records_data)
#
#df=records_df.values.tolist()


break_out = None
target = 100
stoploss = 60
qty =200
mark_time = datetime.now().replace(hour=9, minute=20,second=0,microsecond=0)
mark_time1 = datetime.now().replace(hour=10, minute=0,second=0,microsecond=0)
start_time = datetime.now().replace(hour=9, minute=14,second=30,microsecond=0) 
end_time = datetime.now().replace(hour=15, minute=10,second=0,microsecond=0)
entry_condn_time = datetime.now().replace(hour=9, minute=15,second=0,microsecond=0)
program_start_time = datetime.now().replace(hour=9, minute=15,second=0,microsecond=0)
day_high = None
day_low = None
position_taken = None
net_target = None
current_5_min_bucket = None
prev_can_open = None
prev_can_close = None
current_can_open = None 
current_can_close = None
trailing_stoploss_check = True
stop_revision = 20
entry_price = None
val = 1
BUY_TAKEN = 0
SELL_TAKEN = 0


def on_message(ws, msg):
    global break_out,target,stoploss,mark_time,mark_time1,start_time,end_time,day_high,day_low,prev_high,prev_low
    global position_taken,net_target,net_stoploss,current_5_min_bucket,entry_condn_time,program_start_time
    global prev_can_open,prev_can_close,current_can_open,current_can_close
    global trailing_stoploss_check,stop_revision,val,entry_price,BUY_TAKEN,SELL_TAKEN
    tick = json.loads(msg)
    #print(tick)
    #print(type(tick))
    #print()
    #for tick in ticks :
    ltp_time = datetime.fromtimestamp(mktime(time.strptime(tick['response']['data']['ltt'],"%d %b %Y, %I:%M:%S %p")))
    ltp = float(tick['response']['data']['ltp'])
    
    if ltp_time > program_start_time :
        if mark_time>ltp_time:
            if day_high == None :
                day_high = ltp
                day_low = ltp
            else : 
                if ltp > day_high :
                    day_high = ltp
                if ltp < day_low :
                    day_low = ltp
        else :
            if True :
                if break_out == None :
                    if day_low > prev_high or day_high < prev_low :
                        break_out = True
                    else :
                        break_out = False
                    print("break_out   ",break_out)
                else :
                    if break_out == False and mark_time1 > ltp_time :
                        if ltp > day_high :
                            day_high = ltp
                        if ltp < day_low :
                            day_low = ltp
                    else :
                        if current_5_min_bucket == None :
                            print("day_high  ",day_high)
                            print("day_low  ",day_low)
                            current_5_min_bucket = int(ltp_time.minute/5)*5
                            current_can_open = ltp
                            current_can_close = ltp

                        if current_5_min_bucket == int(ltp_time.minute/5)*5 :
                            current_can_close = ltp
                        else :
                            current_5_min_bucket = int(ltp_time.minute/5)*5
                            prev_can_open = current_can_open
                            prev_can_close = current_can_close
                            current_can_open = ltp

                    if ltp_time > entry_condn_time :
                        try :
                            if prev_can_close > day_high > prev_can_open and BUY_TAKEN == 0:
                                BUY_TAKEN = 1
                                print("prev_can_close   ",prev_can_close)
                                print("prev_can_open    ",prev_can_open)
                                position_taken = "BUY"
                                place_order("BUY")
                                print("Buy postion taken @",ltp,"    ",datetime.now())
                                entry_price = ltp
                                net_target = ltp + target
                                net_stoploss = ltp - stoploss
                            elif prev_can_close < day_low < prev_can_open and SELL_TAKEN == 0:
                                SELL_TAKEN = 1
                                print("prev_can_close   ",prev_can_close)
                                print("prev_can_open    ",prev_can_open)
                                position_taken = "SELL"
                                place_order("SELL")
                                print("Sell postion taken @",ltp,"    ",datetime.now())
                                entry_price = ltp
                                net_target = ltp - target
                                net_stoploss = ltp + stoploss
                        except Exception as e :
                            pass


            if position_taken != None :
                if position_taken == "BUY" :
                    #TRAILING STOP LOSS CODE
                    if trailing_stoploss_check == True :
                        if ltp - entry_price > stop_revision :
                            stop_revision = stop_revision + 10
                            if val == 1 :
                                val = val + 1
                                net_stoploss = net_stoploss + 20
                            else :
                                net_stoploss = net_stoploss +10
                            
                    #TARGET STOP LOSS CODE
                    if ltp > net_target :
                        print("Target achieved  @",ltp,"    ",datetime.now())
                        position_taken = None
                        place_order("SELL")
                        #on_close(ws)
                    elif ltp < net_stoploss :
                        print("Stoploss hit   @",ltp,"    ",datetime.now())
                        position_taken = None
                        place_order("SELL")
                        #on_close(ws)
                else :
                    #TRAILING STOP LOSS CODE
                    if trailing_stoploss_check == True :
                        if entry_price - ltp > stop_revision :
                            stop_revision = stop_revision + 10
                            if val == 1 :
                                val = val + 1
                                net_stoploss = net_stoploss - 20
                            else :
                                net_stoploss = net_stoploss - 10
                            
                    #TARGET STOP LOSS CODE
                    if ltp < net_target :
                        print("Target achieved  @",ltp,"    ",datetime.now())
                        position_taken = None
                        place_order("BUY")
                        #on_close(ws)
                    elif ltp > net_stoploss :
                        print("Stoploss hit   @",ltp,"    ",datetime.now())
                        position_taken = None
                        place_order("BUY")
                        #on_close(ws)
            if BUY_TAKEN == 1 and SELL_TAKEN == 1 and position_taken == None :
                print("Both entry taken")
                on_close(ws)
            if ltp_time > end_time :
                if position_taken != None:
                    if position_taken == "BUY" :
                        place_order('SELL')
                    else :
                        place_order('BUY')
                print("Day exit   ",ltp_time)
                on_close(ws)


def on_error(ws, error):
    print (error)

def on_close(ws):
    print ("Connection Closed")
    ws.close()

def on_open(ws):
    global symbol
    print ("Sending json")
    data = {"request" : 
            {"streaming_type":"quote",
             "data":{"symbols":[{"symbol":symbol}]},
             "request_type":"subscribe",
             "response_format":"json"
            }
       }
    data = json.dumps(data)
    print("data    ",data)
    ws.send(data)
    ws.send("\n")

    
# SELECTING BNF CURRENT MONTH SYMBOL (LISTING ID)
data = unwrap(samco.search_equity_derivative(search_symbol_name="BANKNIFTY",exchange=samco.EXCHANGE_NFO))
temp = pd.DataFrame(data['searchResults'])
temp = temp[temp['instrument']=='FUTIDX']
temp = temp["tradingSymbol"].values.tolist()
emp = []
for i in temp:
    data = unwrap(samco.get_quote(symbol_name=i,exchange=samco.EXCHANGE_NFO))
    emp.append(time.strptime(data["expiryDate"],"%d %b %y").tm_yday)
symbol_name = temp[emp.index(min(emp))]
print("symbol_name       ",symbol_name)
symbol = unwrap(samco.get_quote(symbol_name=temp[emp.index(min(emp))],exchange=samco.EXCHANGE_NFO))['listingId']

# SELECT from_date and to_date
to_date = datetime.now() #- timedelta(days=1)
to_date = to_date.strftime('%Y-%m-%d')
from_date = datetime.now() - timedelta(days=7)
from_date = from_date.strftime('%Y-%m-%d')
data = unwrap(samco.get_historical_candle_data(symbol_name=symbol_name,exchange=samco.EXCHANGE_NFO, from_date=from_date,to_date=to_date))
data = pd.DataFrame(data['historicalCandleData'])
prev_high = float(np.array(data.high)[-1])
prev_low = float(np.array(data.low)[-1])
print("prev_high    ",prev_high)
print("prev_low     ",prev_low)


headers = {'x-session-token':sessionToken}

#websocket.enableTrace(True)

#ws = websocket.WebSocket("wss://stream.stocknote.com", on_open = on_open, on_message = on_message, on_error = on_error, on_close = on_close, header = headers,sslopt={"cert_reqs": ssl.CERT_NONE})
ws = WebSocketApp("wss://stream.stocknote.com", on_open = on_open, on_message = on_message, on_error = on_error, on_close = on_close, header = headers)
print('hi')
while datetime.now() < start_time :
    pass
print("started")
ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

