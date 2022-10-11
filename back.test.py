import pyupbit
import numpy as np

#OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터 #KRW-HBAR
df = pyupbit.get_ohlcv("KRW-BTC", count=10)
 

#변동성 돌파 기준 범위 계산: (고가 - 저가) * k 값 
df['range'] = (df['high'] - df['low']) * 0.3

#target(매수가), range 칼럼을 한칸씩 밑으로 내림(shift(1))
df['target'] = df['open'] + df['range'].shift(1)

#ror(수익율), np.where(조건문, 참일대 값, 거짓일대 값_그대로 있는 값)
df['ror(수익율)'] = np.where(df['high'] > df['target'],
                     df['close'] / df['target'] ,
                     1)
#누적 곱 계산(cumpro) => 누적 수익률
df['hpr[누적수익율(%)]'] = 100*df['ror(수익율)'].cumprod() - 100

#drawdown calculate (누적 최대 값과 현재 hpr 차이 / 누적 최대값 *100)
df['dd'] = (df['hpr(누적수익율)'].cummax() - df['hpr(누적수익율)']) / df['hpr(누적수익율)'].cummax() * 100

#MDD calculate
print("MDD(%): ", df['dd'].max())
print(df['hpr(누적수익율)'])
df.to_excel("dd.xlsx")