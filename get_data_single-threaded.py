import pandas as pd
import traceback
import sys
sys.path.append("./yfinance")
sys.path.append("./yahooquery")
import yfinance as yf
import yahooquery as yq
import time

t_start = time.time()
print(f"yfinance version: {yf.__version__}")
print(f"yahooquery version: {yq.__version__}")
print()

# list of tickers to be searched
tickers =["AAPL", "GOOG", "BABA"]
print('tickers:', tickers)
print()

# retrieve each company's stock price using yfinance
print("=== retrieve each company's stock price using yfinance ===")
df_price = pd.DataFrame()
for ticker in tickers:
    attempt = 1  # initialize attempt counter
    while True:
        try:
            print(f"Attempt {attempt} for {ticker}")
            # download the data for the ticker
            df = yf.download(ticker, start="2023-01-01", end="2023-07-30", threads=True, proxy="http://127.0.0.1:8001")
            # resample the data by month start
            ms_adj = df.resample("MS").first()
            # print(ms_adj)
            # add the resampled data to the df_price dataframe
            df_price[ticker] = ms_adj['Adj Close']
            break  # if the download was successful, break the while loop and move to the next ticker
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
            continue  # if an error occurred, skip the rest of the loop and retry
            # traceback.print_exc()
df_price.insert(0, 'data_type', 'Adj Close')
print("df_price:\n", df_price)
print("=== retrieve stock price done === \n")

# retrieve each company's diluted average shares using yahooquery
print("=== retrieve each company's diluted average shares using yahooquery ===")
df_list = []  # list to store DataFrames

for ticker in tickers:
    attempt = 1  # initialize attempt counter
    while True:
        t = yq.Ticker(ticker, validate=True, status_forcelist=[404], retry=10, timeout=10, proxies={
                'http': 'http://127.0.0.1:8001 ',
                'https': 'http://127.0.0.1:8001',
                }, frequency='q')
        try:
            print(f"Attempt {attempt} for {ticker}")
            df = t.income_statement()
            df = df[df['periodType'] != 'TTM']
            df['asOfDate'] = pd.to_datetime(df['asOfDate'])  # convert 'asOfDate' to datetime
            df = df.rename(columns={'asOfDate': 'Date'})
            df.set_index('Date', inplace=True)  # set 'Date' as the index
            df = df[['DilutedAverageShares']]  # keep only the 'DilutedAverageShares' column
            df.columns = [ticker]  # rename the column to the ticker
            df_list.append(df)  # add the DataFrame to the list
            break  # if the download was successful, break the while loop and move to the next ticker
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
            continue  # if an error occurred, skip the rest of the loop and retry

# Concatenate the DataFrames along the columns axis
df_shares = pd.concat(df_list, axis=1)
df_shares.insert(0, 'data_type', 'Diluted Average Shares')
print("df_shares:\n", df_shares)
print("=== retrieve stock price done === \n")

# Concatenate df_price and df_shares
df_combined = pd.concat([df_price, df_shares])
print("df_combined:\n", df_combined)
# save he df_combined as an Excel file in the current directory
df_combined.to_excel('results.xlsx', index=True)
t_end = time.time()
print(f"Execution time: {t_end - t_start} seconds for {len(tickers)} companies")
