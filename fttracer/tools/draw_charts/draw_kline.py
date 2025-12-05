import os
import time
import random
import warnings
import numpy as np
import pandas as pd
import tushare as ts
from tqdm import tqdm
from functools import wraps
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm
from matplotlib.pylab import date2num
from datetime import datetime, timedelta
from matplotlib import ticker as mticker
from mplfinance.original_flavor import candlestick_ohlc



warnings.filterwarnings("ignore")  # Ignore all warnings

# Set global parameters
plt.rcParams['font.sans-serif'] = ['Arial']  # Use Arial font for all text
plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

# Set tushare pro token
ts.set_token('b6f4cbd3e93129c51f89e5fb2aa47c3b9153b81a93b3d23c7427fcea')
pro = ts.pro_api()

#Set Target dirs
# images_mark="kline_images_202507130110_100"
# images_dir=os.path.join("F:\\AgenticFin_Lab\\fttracer\\kline_charts",images_mark)
# images_csv_dir="F:\\AgenticFin_Lab\\fttracer\\kline_charts\\stock_data_"+images_mark
images_mark=""
images_dir=""
images_csv_dir=""



# Create output directories
os.makedirs(images_dir, exist_ok=True)
os.makedirs(images_csv_dir, exist_ok=True)
images_csv=os.path.join(images_csv_dir,"data.csv")

# Set matplotlib style
plt.style.use('seaborn-v0_8')  # Modern matplotlib style


# Retry decorator for API calls
def retry(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator


@retry(max_retries=3, delay=1)
def get_random_stocks(n=10):
    """Get random stock list from tushare"""
    stocks = pro.stock_basic(exchange='', list_status='L')
    stocks = stocks[~stocks['name'].str.contains('ST')]  # Exclude ST stocks
    stocks = stocks[stocks['list_date'] < '20200101']  # Listed before 2020
    return stocks.sample(min(n, len(stocks)))


@retry(max_retries=3, delay=1)
def get_stock_data(ts_code, start_date, end_date):
    """Fetch stock data and calculate technical indicators"""
    try:
        # Get daily data
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df.empty:
            return pd.DataFrame(), None

        df = df.sort_values('trade_date')

        # Get stock basic info
        try:
            stock_info = pro.stock_basic(ts_code=ts_code).iloc[0].to_dict()
        except:
            stock_info = {
                'ts_code': ts_code,
                'name': 'Unknown',
                'industry': 'Unknown',
                'area': 'Unknown',
                'market': 'Unknown',
                'list_date': 'Unknown',
                'pe': np.nan,
                'pb': np.nan,
                'total_share': np.nan,
                'float_share': np.nan
            }

        # Convert to datetime and set as index
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)

        # Calculate adjusted prices (simplified version)
        df['adj_close'] = df['close']
        df['adj_open'] = df['open']
        df['adj_high'] = df['high']
        df['adj_low'] = df['low']

        # Moving Averages
        df['ma5'] = df['adj_close'].rolling(5).mean()
        df['ma10'] = df['adj_close'].rolling(10).mean()
        df['ma20'] = df['adj_close'].rolling(20).mean()
        df['ma30'] = df['adj_close'].rolling(30).mean()
        df['ma60'] = df['adj_close'].rolling(60).mean()
        df['ma120'] = df['adj_close'].rolling(120).mean()
        df['ma250'] = df['adj_close'].rolling(250).mean()

        # MACD Calculation
        exp12 = df['adj_close'].ewm(span=12, adjust=False).mean()
        exp26 = df['adj_close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['hist'] = df['macd'] - df['signal']

        # RSI Calculation
        delta = df['adj_close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['upper_band'] = df['ma20'] + 2 * df['adj_close'].rolling(20).std()
        df['lower_band'] = df['ma20'] - 2 * df['adj_close'].rolling(20).std()

        # KDJ Calculation
        low_min = df['adj_low'].rolling(9).min()
        high_max = df['adj_high'].rolling(9).max()
        rsv = (df['adj_close'] - low_min) / (high_max - low_min) * 100
        df['k'] = rsv.ewm(com=2).mean()
        df['d'] = df['k'].ewm(com=2).mean()
        df['j'] = 3 * df['k'] - 2 * df['d']

        # Volume Moving Averages
        df['vol_ma5'] = df['vol'].rolling(5).mean()
        df['vol_ma10'] = df['vol'].rolling(10).mean()

        return df, stock_info

    except Exception as e:
        print(f"Error getting stock data: {e}")
        return pd.DataFrame(), None


@retry(max_retries=3, delay=1)
def get_future_prices(df, end_date, days_list):
    """Get future prices for specified days after end_date"""
    future_data = {}
    if df.empty:
        return future_data

    last_close = df.iloc[-1]['adj_close']
    ts_code = df.iloc[0]['ts_code']
    end_datetime = pd.to_datetime(end_date)

    for days in days_list:
        try:
            target_date = (end_datetime + timedelta(days=days)).strftime('%Y%m%d')
            future_df = pro.daily(ts_code=ts_code,
                                  start_date=(end_datetime + timedelta(days=1)).strftime('%Y%m%d'),
                                  end_date=target_date)

            if not future_df.empty:
                # Find the exact date we're looking for
                target_dt = end_datetime + timedelta(days=days)
                future_df['trade_date'] = pd.to_datetime(future_df['trade_date'])
                exact_day_df = future_df[future_df['trade_date'] == target_dt]

                if not exact_day_df.empty:
                    future_close = exact_day_df.iloc[0]['close']
                    pct_change = (future_close - last_close) / last_close * 100
                else:
                    # If exact date not found (market closed), use the last available date
                    future_close = future_df.iloc[-1]['close']
                    pct_change = (future_close - last_close) / last_close * 100

                future_data[f'{days}d_close'] = future_close
                future_data[f'{days}d_pct_change'] = pct_change
            else:
                future_data[f'{days}d_close'] = np.nan
                future_data[f'{days}d_pct_change'] = np.nan
        except Exception as e:
            print(f"Error getting {days} day future price: {e}")
            future_data[f'{days}d_close'] = np.nan
            future_data[f'{days}d_pct_change'] = np.nan

        time.sleep(0.3)  # API rate limit

    return future_data


def plot_kline(df, stock_info, start_date, end_date, save_path):
    """Plot high-quality candlestick chart with technical indicators"""
    if df.empty:
        return

    try:
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12), dpi=1000)
        gs = fig.add_gridspec(6, 4, hspace=0.4, wspace=0.2)
        ax1 = fig.add_subplot(gs[:4, :])  # Price chart
        ax2 = fig.add_subplot(gs[4, :], sharex=ax1)  # Volume chart
        ax3 = fig.add_subplot(gs[5, :], sharex=ax1)  # MACD/KDJ chart

        # Prepare OHLC data for candlestick
        df_plot = df.copy()
        df_plot['date_num'] = df_plot.index.map(mdates.date2num)
        ohlc = df_plot[['date_num', 'adj_open', 'adj_high', 'adj_low', 'adj_close']].values

        # Plot candlesticks with correct colors
        candlestick_ohlc(ax1, ohlc, width=0.6, colorup='red', colordown='green', alpha=1)

        # Plot Moving Averages with clear labels
        ax1.plot(df_plot.index, df_plot['ma5'], label='MA5 (5-day)', color='blue', linewidth=1.2)
        ax1.plot(df_plot.index, df_plot['ma10'], label='MA10 (10-day)', color='orange', linewidth=1.2)
        ax1.plot(df_plot.index, df_plot['ma20'], label='MA20 (20-day)', color='purple', linewidth=1.2)
        ax1.plot(df_plot.index, df_plot['ma60'], label='MA60 (60-day)', color='cyan', linewidth=1.2)

        # Plot Bollinger Bands
        ax1.plot(df_plot.index, df_plot['upper_band'], label='Upper Band', color='red', linestyle='--', linewidth=0.8)
        ax1.plot(df_plot.index, df_plot['lower_band'], label='Lower Band', color='green', linestyle='--', linewidth=0.8)
        ax1.fill_between(df_plot.index, df_plot['upper_band'], df_plot['lower_band'], color='gray', alpha=0.1)

        # Price chart formatting
        ax1.set_title(f"{stock_info['ts_code']} {start_date} - {end_date}",
                      fontsize=14, pad=25)
        ax1.set_ylabel('Price', fontsize=10)
        ax1.legend(loc='upper left', bbox_to_anchor=(0.01, 0.99),
                   fontsize=8, framealpha=0.5, borderaxespad=0.)

        # Grid settings for price chart
        ax1.grid(True, linestyle='--', alpha=0.5, which='both')
        ax1.yaxis.set_minor_locator(mticker.AutoMinorLocator())
        ax1.tick_params(which='both', width=1)
        ax1.tick_params(which='major', length=6)
        ax1.tick_params(which='minor', length=3, color='gray')

        # Set x-axis format with clear ticks
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df) // 10)))
        plt.setp(ax1.get_xticklabels(), visible=False)

        # Add horizontal grid lines at major ticks
        ax1.yaxis.grid(True, linestyle='-', alpha=0.3, color='gray')
        ax1.xaxis.grid(True, linestyle='-', alpha=0.3, color='gray')

        # Plot Volume bars with correct colors
        colors = ['red' if x['adj_close'] >= x['adj_open'] else 'green' for _, x in df_plot.iterrows()]
        ax2.bar(df_plot.index, df_plot['vol'], color=colors, width=0.6, alpha=0.8)
        ax2.plot(df_plot.index, df_plot['vol_ma5'], label='Volume MA5', color='blue', linewidth=1.2)
        ax2.plot(df_plot.index, df_plot['vol_ma10'], label='Volume MA10', color='orange', linewidth=1.2)
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.legend(loc='upper left', bbox_to_anchor=(0.01, 0.99),
                   fontsize=8, framealpha=0.5, borderaxespad=0.)

        # Grid settings for volume chart
        ax2.grid(True, linestyle='--', alpha=0.5, which='both')
        ax2.yaxis.set_minor_locator(mticker.AutoMinorLocator())
        ax2.tick_params(which='both', width=1)
        ax2.tick_params(which='major', length=6)
        ax2.tick_params(which='minor', length=3, color='gray')
        plt.setp(ax2.get_xticklabels(), visible=False)

        # Plot MACD
        macd_colors = ['red' if x >= 0 else 'green' for x in df_plot['hist']]
        ax3.bar(df_plot.index, df_plot['hist'], color=macd_colors, width=0.6, alpha=0.8)
        ax3.plot(df_plot.index, df_plot['macd'], label='MACD (12,26,9)', color='blue', linewidth=1.2)
        ax3.plot(df_plot.index, df_plot['signal'], label='Signal Line', color='orange', linewidth=1.2)
        ax3.axhline(0, color='gray', linestyle='--', linewidth=0.8)

        # Plot KDJ on secondary y-axis
        ax3_kdj = ax3.twinx()
        ax3_kdj.plot(df_plot.index, df_plot['k'], label='K line', color='purple', linewidth=1, alpha=0.8)
        ax3_kdj.plot(df_plot.index, df_plot['d'], label='D line', color='brown', linewidth=1, alpha=0.8)
        ax3_kdj.plot(df_plot.index, df_plot['j'], label='J line', color='cyan', linewidth=1, alpha=0.8)
        ax3_kdj.set_ylabel('KDJ', fontsize=8)

        # Format MACD/KDJ chart
        ax3.set_ylabel('MACD', fontsize=10)
        ax3.legend(loc='upper left', bbox_to_anchor=(0.01, 0.99),
                   fontsize=8, framealpha=0.5, borderaxespad=0.)
        ax3_kdj.legend(loc='upper right', bbox_to_anchor=(0.99, 0.99),
                       fontsize=8, framealpha=0.5, borderaxespad=0.)

        # Grid settings for MACD chart
        ax3.grid(True, linestyle='--', alpha=0.5, which='both')
        ax3.yaxis.set_minor_locator(mticker.AutoMinorLocator())
        ax3.tick_params(which='both', width=1)
        ax3.tick_params(which='major', length=6)
        ax3.tick_params(which='minor', length=3, color='gray')

        # Rotate and format x-axis labels for the bottom chart
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax3.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df) // 10)))
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right', fontsize=8)

        # Add minor ticks to x-axis
        ax3.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        ax3.tick_params(axis='x', which='minor', length=2, color='gray')

        # Adjust layout to prevent overlap
        plt.subplots_adjust(left=0.08, right=0.92, bottom=0.15, top=0.9, hspace=0.1, wspace=0.2)

        # Save high-quality image
        plt.savefig(save_path, dpi=1000, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close()

    except Exception as e:
        print(f"Error plotting K-line: {e}")
        plt.close()


def generate_random_date_range():
    """Generate random date range ending at least 1 year ago"""
    end_date = datetime.now() - timedelta(days=365)
    start_date = end_date - timedelta(days=random.randint(60, 250))
    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')


def generate_kline_images(num_images=100, random_mode=True, custom_stocks=None, custom_date_ranges=None):
    """Generate K-line images with metadata"""
    future_days = [1, 2, 3, 4, 5, 10, 20, 30, 60, 90, 180, 360]
    meta_data = []
    pbar = tqdm(total=num_images, desc='Generating K-line charts')

    count = 0
    failed_count = 0
    max_failures = 20

    while count < num_images and failed_count < max_failures:
        try:
            if random_mode:
                stocks = get_random_stocks(min(10, num_images - count))
                for _, stock in stocks.iterrows():
                    if count >= num_images:
                        break

                    start_date, end_date = generate_random_date_range()
                    df, stock_info = get_stock_data(stock['ts_code'], start_date, end_date)

                    if df.empty or len(df) < 30:
                        failed_count += 1
                        continue

                    future_data = get_future_prices(df, end_date, future_days)
                    img_name = f"{stock_info['ts_code']}_{start_date}_{end_date}.png"
                    # img_path = os.path.join(r"F:\AgenticFin_Lab\fttracer\kline_images_10000_202507120037", img_name)
                    img_path = os.path.join(images_dir, img_name)
                    plot_kline(df, stock_info, start_date, end_date, img_path)

                    record = {
                        'ts_code': stock_info['ts_code'],
                        'stock_name': stock_info['name'],
                        'industry': stock_info.get('industry', 'Unknown'),
                        'area': stock_info.get('area', 'Unknown'),
                        'market': stock_info.get('market', 'Unknown'),
                        'list_date': stock_info.get('list_date', 'Unknown'),
                        'pe': stock_info.get('pe', np.nan),
                        'pb': stock_info.get('pb', np.nan),
                        'total_share': stock_info.get('total_share', np.nan),
                        'float_share': stock_info.get('float_share', np.nan),
                        'start_date': start_date,
                        'end_date': end_date,
                        'period_days': len(df),
                        'start_price': df.iloc[0]['adj_close'],
                        'end_price': df.iloc[-1]['adj_close'],
                        'period_pct_change': (df.iloc[-1]['adj_close'] - df.iloc[0]['adj_close']) / df.iloc[0][
                            'adj_close'] * 100,
                        'max_price': df['adj_high'].max(),
                        'min_price': df['adj_low'].min(),
                        'avg_volume': df['vol'].mean(),
                        'image_path': img_path,
                        'has_macd': True,
                        'has_rsi': True,
                        'has_boll': True,
                        'has_kdj': True
                    }
                    record.update(future_data)
                    meta_data.append(record)

                    count += 1
                    failed_count = 0
                    pbar.update(1)
                    time.sleep(0.3)
            else:
                for i, stock in enumerate(custom_stocks):
                    if count >= num_images:
                        break

                    start_date, end_date = custom_date_ranges[i]
                    df, stock_info = get_stock_data(stock, start_date, end_date)

                    if df.empty or len(df) < 30:
                        failed_count += 1
                        continue

                    future_data = get_future_prices(df, end_date, future_days)
                    img_name = f"{stock_info['ts_code']}_{start_date}_{end_date}.png"
                    # img_path = os.path.join(r"F:\AgenticFin_Lab\fttracer\kline_images_10000_202507120037", img_name)
                    img_path = os.path.join(images_dir, img_name)

                    plot_kline(df, stock_info, start_date, end_date, img_path)

                    record = {
                        'ts_code': stock_info['ts_code'],
                        'stock_name': stock_info['name'],
                        'industry': stock_info.get('industry', 'Unknown'),
                        'area': stock_info.get('area', 'Unknown'),
                        'market': stock_info.get('market', 'Unknown'),
                        'list_date': stock_info.get('list_date', 'Unknown'),
                        'pe': stock_info.get('pe', np.nan),
                        'pb': stock_info.get('pb', np.nan),
                        'total_share': stock_info.get('total_share', np.nan),
                        'float_share': stock_info.get('float_share', np.nan),
                        'start_date': start_date,
                        'end_date': end_date,
                        'period_days': len(df),
                        'start_price': df.iloc[0]['adj_close'],
                        'end_price': df.iloc[-1]['adj_close'],
                        'period_pct_change': (df.iloc[-1]['adj_close'] - df.iloc[0]['adj_close']) / df.iloc[0][
                            'adj_close'] * 100,
                        'max_price': df['adj_high'].max(),
                        'min_price': df['adj_low'].min(),
                        'avg_volume': df['vol'].mean(),
                        'image_path': img_path,
                        'has_macd': True,
                        'has_rsi': True,
                        'has_boll': True,
                        'has_kdj': True
                    }
                    record.update(future_data)
                    meta_data.append(record)

                    count += 1
                    failed_count = 0
                    pbar.update(1)
                    time.sleep(0.3)
        except Exception as e:
            print(f"Error generating chart: {e}")
            failed_count += 1
            time.sleep(5)
            continue

    pbar.close()

    if meta_data:
        meta_df = pd.DataFrame(meta_data)
        os.makedirs('stock_data', exist_ok=True)
        meta_df.to_csv(images_csv, index=False, encoding='utf_8_sig')
        print(f"Completed {len(meta_data)} K-line charts with metadata")
    else:
        print("No charts generated")

    if failed_count >= max_failures:
        print(f"Warning: Stopped after {max_failures} consecutive failures")


if __name__ == '__main__':
    mode = input("Select mode (1:Random, 2:Custom): ").strip()

    if mode == '1':
        num = int(input("Number of charts to generate (default 100): ") or 100)
        generate_kline_images(num_images=num, random_mode=True)
    elif mode == '2':
        custom_stocks = [x.strip() for x in input("Stock codes (e.g. 600000.SH,000001.SZ): ").split(',') if x.strip()]
        start_dates = [x.strip() for x in input("Start dates (YYYYMMDD): ").split(',') if x.strip()]
        end_dates = [x.strip() for x in input("End dates (YYYYMMDD): ").split(',') if x.strip()]

        if len(custom_stocks) != len(start_dates) or len(custom_stocks) != len(end_dates):
            print("Error: Number of stocks, start dates and end dates must match")
        else:
            custom_date_ranges = list(zip(start_dates, end_dates))
            generate_kline_images(num_images=len(custom_stocks), random_mode=False,
                                  custom_stocks=custom_stocks, custom_date_ranges=custom_date_ranges)
    else:
        print("Invalid mode selection")