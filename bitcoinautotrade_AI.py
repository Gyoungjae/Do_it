import time
import pyupbit
import datetime
import schedule
from tqdm import tqdm
from fbprophet import Prophet
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

#4시간 간격

access = "dP0bqp0hOQd62Ka02eilzQKxWrxrEz1YeyIf0FeJ"
secret = "Ut5nk2SMA8xkxGGHPW7TZ5hTgm6MkzAfN0IjjC5L"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] - (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def predicted_price_AI():
    coin_list = pyupbit.get_tickers(fiat="KRW")
    coin_list100 = coin_list[0:100]
    current_price = pyupbit.get_current_price(coin_list100)
    current_price = pd.DataFrame([current_price])
    current_price=current_price.transpose()
    coin_predict_price = []
    for coin in tqdm(coin_list100):
        df = pyupbit.get_ohlcv(coin, interval="minute60", count=200)
        df = df.reset_index()
        df['ds'] = df['index']
        df['y'] = df['close']
        data = df[['ds','y']]
        model = Prophet()
        model.fit(data)
        future = model.make_future_dataframe(periods=24, freq='H') #periods = 이게 어느정도 시간을 예측할것인지, freq = 시간간격
        forecast = model.predict(future)
        closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
        if len(closeDf) == 0:
            closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
        closeValue = closeDf['yhat'].values[0]
        coin_predict_price.append(closeValue)
    coin_df = pd.DataFrame(coin_predict_price, columns=['Coin_predict_price'])
    predict_price = coin_df
    predict_price.columns = ["predict_price"]
    current_price.columns = ["current_price"]
    current_price = current_price.reset_index(level=0)
    result = current_price.join(predict_price, how='inner')
    result['ror'] = (result['predict_price'] - result['current_price'])/result['current_price']
    result.max(level=0)
    a = result['ror'] == result['ror'].max()
    b=result[a]
    c = str(b['index'].values)
    c = c[2:-2]
    c_balance = c[4:]
    current_price_AI = int(b['current_price'])
    predict_price_AI = int(b['predict_price'])
    ror_AI = float(b['ror'])
    predicted_AI = (c, current_price_AI, predict_price_AI, ror_AI, c_balance)
    return predicted_AI
predicted_AI = predicted_price_AI()
schedule.every().hour.do(lambda: predicted_price_AI())

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(predicted_AI[0])
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(minutes=10):
            target_price = get_target_price(predicted_AI[0], 0.1)
            current_price = get_current_price(predicted_AI[0])
            if target_price >= current_price and current_price < predicted_AI[2]:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order(predicted_AI[0], krw*0.9995)
                    btc = get_balance(predicted_AI[4])
                    if btc > 0.00008 and (current_price >= 1.2*predicted_AI[2] or current_price <= 0.98*target_price):
                        upbit.sell_market_order(predicted_AI[0], btc*0.9995)
        
        else:
            btc = get_balance(predicted_AI[4])
            if btc > 0.00008 :
                upbit.sell_market_order(predicted_AI[0], btc*0.9995)
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
        
