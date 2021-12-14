import requests
import json
import pandas as pd
from datetime import date,timedelta,datetime
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
import time
from time import sleep,mktime
from websocket import WebSocketApp
import ssl

file1 = open(r"C:\Users\Administrator\Desktop\FUTURES STOCK_LIST.txt","r+")
STOCK_LIST=file1.readlines()
for i in range(len(STOCK_LIST)):
    STOCK_LIST[i]=STOCK_LIST[i][:-1]
print(STOCK_LIST)
print(len(STOCK_LIST))
print()
file1.close()

# Live 
 
long_auth_token_list = ["d4b87efd-9e04-4feb-8e53-833088dd7cea","d4b87efd-9e04-4feb-8e53-833088dd7cea","d4b87efd-9e04-4feb-8e53-833088dd7cea","d4b87efd-9e04-4feb-8e53-833088dd7cea"]
short_auth_token_list = ["6a15d2c5-b05f-4c59-a94d-3dfd1a6c005d","6a15d2c5-b05f-4c59-a94d-3dfd1a6c005d","6a15d2c5-b05f-4c59-a94d-3dfd1a6c005d"] 

def unwrap(x):
    return json.loads(x)

def login():
    #    userId,password,yob
    global samco
    login=samco.login(body={"userId":"DS33710",'password':"Gineer@343",'yob':"1999"})
    login = unwrap(login)
    print("Login details \n",login)
    if str.lower(login['statusMessage'])=='invalid password':
        print("Mismatch of username and password")
    elif 'account blocked' in str.lower(login['statusMessage']):
        print("Account blocked")
    else:
        samco.set_session_token(sessionToken=login["sessionToken"])
    
    return login["sessionToken"]


samco=StocknoteAPIPythonBridge()
sessionToken = login()
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'x-session-token' : sessionToken
}

def is_between(a,b,c):
    return b>=a>=c or b<=a<=c

def telegram_bot_sendtext(bot_message,run=True):
    if run :
        bot_token = '1426720345:AAGCUk_sEPHoCciE5DdIbgPIwBSDjiyVoCY'
        bot_chatID = ['-1001352536294']
        
        for i in bot_chatID:
            send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + i + '&parse_mode=Markdown&text=' + bot_message
            response = requests.get(send_text)
        return response.json()

def listToString(s):  
    
    # initialize an empty string 
    str1 = " " 
    # return string   
    return (str1.join(s)) 

def split_and_snd(x):
    n=len(x)
    for i in range(n):
        x[i]=x[i].replace("&", "-")
    poi=int(n / 10) * 10+(10 if n%10!=0 else 0)
    for i in range(0,poi,10):
        #print(x[i:i+10])
        telegram_bot_sendtext(listToString(x[i:i+10]))
        
 
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

WHETHER_LIVE_DATA=""
while WHETHER_LIVE_DATA!=0 and WHETHER_LIVE_DATA!=1:
    try:
        WHETHER_LIVE_DATA=1
        if WHETHER_LIVE_DATA!=0 and WHETHER_LIVE_DATA!=1:
            raise Exception("Entered value is not 1 or 0")
    except Exception as e:
        print(e)
     
#symbolName=input('symbolName')
STOCK_LIST.extend(['NIFTY 50','NIFTY BANK'])
 
#STOCK_LIST=['RELIANCE','HDFCBANK','TATASTEEL','INFY','ACC', 'ADANIENT', 'ADANIPORTS', 'AMARAJABAT', 'AMBUJACEM', 'APOLLOHOSP', 'APOLLOTYRE', 'ASHOKLEY', 'ASIANPAINT', 'AUROPHARMA', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BALKRISIND', 'BANDHANBNK', 'BANKBARODA', 'BATAINDIA', 'BEL']
 
WHETHER_CHECKING_NEXT_DAY=0             #ENTER 1 IF YES ELSE 0
data=[]
#STOCK_LIST=['RELIANCE']
today = date.today()           #-timedelta(WHETHER_CHECKING_NEXT_DAY)
print(today.strftime("%Y-%m-%d"))
start_time=today.strftime("%Y-%m-%d")+' 09:15:00'
end_time=today.strftime("%Y-%m-%d")+' 15:30:00'
end_date=(today-timedelta(1)).strftime("%Y-%m-%d")
start_date=(today-timedelta(20)).strftime("%Y-%m-%d")
 
print("TODAY'S DATE   =   ",today.strftime("%Y-%m-%d"))
print("start_time     =   ",start_time)
print("end_time       =   ",end_time)
print("start_date     =   ",start_date)
print("end_date       =   ",end_date)
 
 
for i in STOCK_LIST:
    #print(i,end="   ")
    try:
        if 'NIFTY' in i:
            url="https://api.stocknote.com/history/indexCandleData"
            response = requests.get(url,params={
            "indexName": i,
            'exchange' : 'NSE',
            'fromDate' : start_date,
            'toDate' : end_date
            }, headers = headers)
            #print(response.json());
            df=pd.DataFrame(response.json()['indexCandleData'])


        else:
            url="https://api.stocknote.com/history/candleData"
            response = requests.get(url,params={
            "symbolName": i,
            'exchange' : 'NSE',
            'fromDate' : start_date,
            'toDate' : end_date
            }, headers = headers)
            #print(response.json());
            df=pd.DataFrame(response.json()['historicalCandleData'])


        #print(df.tail(15))
        #print("test1")
        df["high"] = pd.to_numeric(df["high"], downcast="float")
        df["low"] = pd.to_numeric(df["low"], downcast="float")
        df['DayRange']=df.high-df.low
        df['DayRange'].round(decimals=2)
        
        #print(df.tail())
        DayRange=df.DayRange.tolist()
        DayRange=DayRange[-10:]
        DayRange = [round(x,2) for x in DayRange]
        if len(DayRange)!=10:
            raise Exception("Length of DayRange is not 10")
        #print("test2")
        prvdayh=round(df.iloc[-1,2],2)
        prvdayl=round(df.iloc[-1,3],2)
        open=round(float(df.iloc[-1,4]),2)
    
        #print("Intraday data  :  ")
    
        if WHETHER_LIVE_DATA==1:
            if 'NIFTY' in i:
                url="https://api.stocknote.com/intraday/indexCandleData"
                response = requests.get(url,params={
                "indexName": i,
                'exchange' : 'NSE',
                'fromDate' : start_time,
                'toDate' : end_time
                }, headers = headers)
                
                #print (response.text);
                df=pd.DataFrame(response.json()['indexIntraDayCandleData'])  
                
            else:

                url="https://api.stocknote.com/intraday/candleData"
                response = requests.get(url,params={
                "symbolName": i,
                'exchange' : 'NSE',
                'fromDate' : start_time,
                'toDate' : end_time
                }, headers = headers)
                
                #print (response.text);
                df=pd.DataFrame(response.json()['intradayCandleData'])  
        
            open=round(float(df.iloc[0,1]),2)
            """
            print("prvdayh  =  ",prvdayh)
            print("prvdayl  =  ",prvdayl)
            print("open     =  ",open)
            """
        #print(DayRange,len(DayRange))
        adr_10=sum(DayRange)/10
        adr_5=sum(DayRange[-5:])/5
        
        #print(DayRange)
        #print(adr_10)
        #print(adr_5)
        #print("test3")
        adrhigh_10=round(open+adr_10/2,2)
        adrlow_10=round(open-adr_10/2,2)
        adrhigh_5=round(open+adr_5/2,2)
        adrlow_5=round(open-adr_5/2,2)
        resist_1 = round(prvdayh + (prvdayh - prvdayl) * (0.25),2)
        resist_2 = round(prvdayh + (prvdayh - prvdayl) * (0.42),2)
        support_1 = round(prvdayl - (prvdayh - prvdayl) * (0.25),2)
        support_2 = round(prvdayl -(prvdayh - prvdayl) * (0.42),2)
    
        """
        print("adrhigh_10 =   ",adrhigh_10)
        print("adrhigh_5  =   ",adrhigh_5)
        print("adrlow_10  =   ",adrlow_10)
        print("adrlow_5  =   ",adrlow_5)
        print("resist_1   =   ",resist_1)
        print("resist_2   =   ",resist_2)
        print("support_1  =   ",support_1)
        print("support_2  =   ",support_2)
        """
    
        temp=[i,open,adrhigh_10,adrhigh_5,adrlow_10,adrlow_5,resist_1,resist_2,support_1,support_2]
        
        RES1_BET_ADR_HIGH=is_between(resist_1,adrhigh_10,adrhigh_5)
        RES2_BET_ADR_HIGH=is_between(resist_2,adrhigh_10,adrhigh_5)
        ADR_HIGH10_BET_RES=is_between(adrhigh_10,resist_1,resist_2)
        ADR_HIGH5_BET_RES=is_between(adrhigh_5,resist_1,resist_2)
    
        SUP1_BET_ADR_LOW=is_between(support_1,adrlow_10,adrlow_5)
        SUP2_BET_ADR_LOW=is_between(support_2,adrlow_10,adrlow_5)
        ADR_LOW10_BET_SUP=is_between(adrlow_10,support_1,support_2)
        ADR_LOW5_BET_SUP=is_between(adrlow_5,support_1,support_2)
    
    
    
        if ADR_HIGH10_BET_RES and ADR_HIGH5_BET_RES:
            temp.append(1)
        else:
            temp.append(0)  
    
        if adrhigh_10>=resist_2 and adrhigh_5>=resist_2:
            if min(adrhigh_10,adrhigh_5)<1.005*resist_2:      
                temp.append(1)
            else:
                temp.append(0)
        else:
            temp.append(0)  
        
    
        if (adrhigh_10>=resist_2 and ADR_HIGH5_BET_RES) or (adrhigh_5>=resist_2 and ADR_HIGH10_BET_RES):
            temp.append(1)
        else:
            temp.append(0)  
    
        if ADR_LOW10_BET_SUP and ADR_LOW5_BET_SUP:
            temp.append(1)
        else:
            temp.append(0)  
    
        if adrlow_10<=support_2 and adrlow_5<=support_2:
            if max(adrlow_10,adrlow_5)<1.005*support_2:      
                temp.append(1)
            else:
                temp.append(0)
        else:
            temp.append(0)  
        
        if (adrlow_10<=support_2 and ADR_LOW5_BET_SUP) or (adrlow_5<=support_2 and ADR_LOW10_BET_SUP):
            temp.append(1)
        else:
            temp.append(0)  
    
        """
        print(is_between(resist_1,adrhigh_10,adrhigh_5))
        print(is_between(resist_1,adrhigh_10,adrhigh_5))
        print(is_between(adrhigh_10,resist_1,resist_2))
        print(is_between(adrhigh_5,resist_1,resist_2))
        """
        data.append(temp)
        
    except Exception as e:
        print(i,"     ",e)
    
data=pd.DataFrame(data,columns=('STOCK','OPEN' if WHETHER_LIVE_DATA==1 else 'CLOSE','ADRHIGH_10','ADRHIGH_5','ADRLOW_10','ADRLOW_5','RESIST1','RESIST2','SUPPORT1','SUPPORT2','BOTH ADR_HIGH BET RES','BOTH ADR_HIGH ABV RES','ONE ADR_HIGH BET RES','BOTH ADR_LOW BET SUP','BOTH ADR_LOW ABV SUP','ONE ADR_LOW BET SUP'))
data['SUMH']=data['BOTH ADR_HIGH BET RES']+data['BOTH ADR_HIGH ABV RES']+data['ONE ADR_HIGH BET RES']
data['SUML']=data['BOTH ADR_LOW BET SUP']+data['BOTH ADR_LOW ABV SUP']+data['ONE ADR_LOW BET SUP']
data["MAX"] = data[['ADRHIGH_10','ADRHIGH_5','RESIST1','RESIST2']].max(axis=1)
data["MIN"] = data[['ADRLOW_10','ADRLOW_5','SUPPORT1','SUPPORT2']].min(axis=1)
#data.drop(data[data.SUMH == 0].index, inplace=True)
#print(data.head())
#print(data.tail())

data.sort_values(by=['BOTH ADR_HIGH BET RES','BOTH ADR_HIGH ABV RES','ONE ADR_HIGH BET RES'], inplace=True,ascending=False)
telegram_bot_sendtext("Date  :  "+today.strftime("%Y-%m-%d"))
rslt_df1 = data[data['SUMH'] == 1]
data.sort_values(by=['BOTH ADR_LOW BET SUP','BOTH ADR_LOW ABV SUP','ONE ADR_LOW BET SUP'], inplace=True,ascending=False)
rslt_df2 = data[data['SUML'] == 1]

telegram_bot_sendtext("LONG STOCKS :  "+str(len(rslt_df1)))
split_and_snd(rslt_df1['STOCK'].to_list())
telegram_bot_sendtext("--------------")
telegram_bot_sendtext("--------------")
telegram_bot_sendtext("SHORT STOCKS :  "+str(len(rslt_df2)))
split_and_snd(rslt_df2['STOCK'].to_list())


total_sel = rslt_df1['STOCK'].to_list() + rslt_df2['STOCK'].to_list()
BUY_LIST = rslt_df1['STOCK'].to_list()
SELL_LIST = rslt_df2['STOCK'].to_list()
buy_max = rslt_df1['MAX'].to_list()
sell_min = rslt_df2['MIN'].to_list()

BUY_TRIGGER = {}
SELL_TRIGGER = {}
BUY_ENTRY = {}
SELL_ENTRY = {}
BUY_MAX = {}
SELL_MIN = {}
c_min = {}
p_min = {}
c_close = {}
p_close = {}
c_high = {}
p_high = {}
c_low = {}
p_low = {}
program_start_time = datetime.now().replace(hour=9, minute=18,second=0,microsecond=0)
token = []
rev = {}
for i in total_sel:
    try:
        X = unwrap(samco.get_quote(symbol_name=i,exchange=samco.EXCHANGE_NSE))['listingId']
        token.append({"symbol":X})
        rev[X] = i
        sleep(0.3)
    except Exception as e:
        print(i,"       ",e)


for i in total_sel :
    c_min[i] = 0
    p_min[i] = 0
    c_close[i] = 0
    p_close[i] = 0
    c_high[i] = 0
    p_high[i] = 0
    c_low[i] = 0
    p_low[i] = 0


for i in BUY_LIST:
    BUY_TRIGGER[i] = None
    BUY_ENTRY[i] = None
for i in SELL_LIST:
    SELL_TRIGGER[i] = None
    SELL_ENTRY[i] = None

for i in range(len(buy_max)):
    BUY_MAX[BUY_LIST[i]] = buy_max[i]*1.0003
for i in range(len(sell_min)):
    SELL_MIN[SELL_LIST[i]] = sell_min[i]*0.9997

print(BUY_MAX)
print()
print(SELL_MIN)
def on_message(ws, msg):
    global program_start_time,rev,c_min,c_close,c_high,c_low,p_min,p_close,p_high,p_low
    global BUY_ENTRY,BUY_LIST,BUY_MAX,BUY_TRIGGER,SELL_ENTRY,SELL_LIST,SELL_MIN,SELL_TRIGGER
    tick = json.loads(msg)
    #print(tick)
    #print(type(tick))
    #print()
    #for tick in ticks :
    ltp_time = datetime.fromtimestamp(mktime(time.strptime(tick['response']['data']['ltt'],"%d %b %Y, %I:%M:%S %p")))
    ltp = float(tick['response']['data']['ltp'])
    instrument = rev[tick['response']['data']['sym']]
    
    if ltp_time > program_start_time :
        if c_min[instrument] == ltp_time.minute//3*3:
            c_close[instrument] = ltp
            if c_low[instrument] > ltp :
                c_low[instrument] = ltp
            if c_high[instrument] < ltp :
                c_high[instrument] = ltp
        else :
            p_min[instrument] = c_min[instrument]
            c_min[instrument] = ltp_time.minute//3*3
            p_close[instrument] = c_close[instrument]
            p_high[instrument] = c_high[instrument]
            p_low[instrument] = c_low[instrument]
            c_close[instrument] = ltp
            c_high[instrument] = ltp
            c_low[instrument] = ltp
        
        try:
            if instrument in BUY_LIST:
                #inside buy list
                if BUY_TRIGGER[instrument] == None :
                    #High not determined
                    if p_close[instrument] > BUY_MAX[instrument] :
                        BUY_TRIGGER[instrument] = p_high[instrument]
                elif BUY_ENTRY[instrument] == None :
                    if ltp > BUY_TRIGGER[instrument] :
                        # Take buy entry 
                        BUY_ENTRY[instrument] = ltp
                        telegram_bot_sendtext(instrument+"     BUY    @"+str(ltp))
        except Exception as e:
            print(e,"        ",instrument,"         ",ltp_time)

        try:
            if instrument in SELL_LIST:
                #inside sell list
                if SELL_TRIGGER[instrument] == None :
                    #Low not determined
                    if p_close[instrument] < SELL_MIN[instrument] :
                        SELL_TRIGGER[instrument] = p_low[instrument]
                elif SELL_ENTRY[instrument] == None :
                    if ltp < SELL_TRIGGER[instrument] :
                        # Take sell entry 
                        SELL_ENTRY[instrument] = ltp
                        telegram_bot_sendtext(instrument+"     SELL    @",str(ltp))
        except Exception as e:
            print(e,"        ",instrument,"         ",ltp_time)

def on_error(ws, error):
    print (error)

def on_close(ws):
    print ("Connection Closed")
    ws.close()

def on_open(ws):
    global token
    print ("Sending json")
    data = {"request" : 
            {"streaming_type":"quote",
             "data":{"symbols":token},
             "request_type":"subscribe",
             "response_format":"json"
            }
       }
    data = json.dumps(data)
    print("data    ",data)
    ws.send(data)
    ws.send("\n")

print()
print(rev)
headers = {'x-session-token':sessionToken}
ws = WebSocketApp("wss://stream.stocknote.com", on_open = on_open, on_message = on_message, on_error = on_error, on_close = on_close, header = headers)

ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
