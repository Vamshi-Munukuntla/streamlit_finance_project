import streamlit as st
import pandas as pd
from pandas_datareader import data as pdr
import plotly.express as px
from PIL import Image
import yfinance as yf


def display_image():
    image = Image.open('stock.jpeg')
    st.image(image, caption='@austindistel')


def parameter(df_sp, sector_default_value, cap_default_value):
    # Sector Widget
    sector_default = [sector_default_value]
    sector_values = sector_default + list(df_sp.sector.unique())
    option_sector = st.sidebar.selectbox('Sector', sector_values, index=0)

    # Market Cap
    cap_default = [cap_default_value]
    cap_value_list = cap_default + ['Small', 'Medium', 'Large']
    cap_value = st.sidebar.selectbox('Company Capitalization', cap_value_list, index=0)

    # Dividend Widget
    dividend_value = st.sidebar.slider('Dividend rate between than (%):', 0.0, 10.0, value=(0.0, 10.0))

    # Profit Widget
    min_profit_value = float(df_sp['profitMargins_%'].min())
    max_profit_value = float(df_sp['profitMargins_%'].max())
    profit_value = st.sidebar.slider('Profit margin rate greater than (%):',
                                     min_profit_value, max_profit_value, step=10.0)

    return option_sector, dividend_value, profit_value, cap_value


def filtering(df_sp, sector_default_value, cap_default_value, option_sector, dividend_value, profit_value, cap_value):
    # Profit Filtering
    df_sp = df_sp[(df_sp['profitMargins_%'] >= profit_value)]

    # Dividend Filtering
    df_sp = df_sp[(df_sp['dividendYield_%'] >= dividend_value[0])
                  & (df_sp['dividendYield_%'] <= dividend_value[1])]

    # Sector Filtering
    if option_sector != sector_default_value:
        df_sp = df_sp[(df_sp['sector'] == option_sector)]

    # Cap market filtering
    if cap_value != cap_default_value:
        if cap_value == "Small":
            df_sp = df_sp[(df_sp['marketCap'] >= 0)
                          & (df_sp['marketCap'] <= 20e9)]

        elif cap_value == 'Medium':
            df_sp = df_sp[(df_sp['marketCap'] > 20e9)
                          & (df_sp['marketCap'] <= 100e9)]

        else:
            df_sp = df_sp[(df_sp['marketCap'] > 100e9)]

    return df_sp


def company_price(df_sp, option_company):
    if option_company is not None:
        ticker_company = df_sp.loc[df_sp['name'] == option_company, 'ticker'].values[0]
        data_price = pdr.get_data_yahoo(ticker_company, start='2012-12-31', end='2022-12-31')['Adj Close']
        data_price = data_price.reset_index(drop=False)
        data_price.columns = ['ds', 'y']
        return data_price
    else:
        return None


def show_stock_price(data_price):
    fig = px.line(data_price, x='ds', y='y', title='10 years stock price')
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Stock Price')
    st.plotly_chart(fig)


def metrics(data_price):
    stock_price_2013 = data_price['y'].values[0]
    stock_price_2023 = data_price['y'].values[-1]

    performance = round(((stock_price_2023 / stock_price_2013) - 1) * 100, 2)

    return stock_price_2023, performance


@st.cache
def read_data():
    try:
        path_dat = "s&p500.csv"
        df_sp = pd.read_csv(path_dat)
        return df_sp
    except Exception as e:
        st.error("Data is not read properly. Please check the path.")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Stock Screener",
        initial_sidebar_state='expanded'
    )
    st.title('S&P 500 Screener & Stock Analysis')
    st.sidebar.title('Search Criteria')

    yf.pdr_override()

    # Display Hero Image
    display_image()

    # Read Data
    df_sp = read_data()

    sector_default_value = "All"
    cap_default_value = 'All'
    option_sector, dividend_value, profit_value, cap_value = parameter(df_sp, sector_default_value, cap_default_value)

    # Filtering
    df_sp = filtering(df_sp, sector_default_value, cap_default_value, option_sector,
                      dividend_value, profit_value, cap_value)

    st.subheader("Part 1 - S&P500 Screener")
    with st.expander("Part 1 explanation", expanded=False):
        st.write("""
            In the table below, you will find most of the companies in the S&P500 (stock market index of the 500 largest American companies) with certain criteria such as :

                - The name of the company
                - The sector of activity
                - Market capitalization
                - Dividend payout percentage (dividend/stock price)
                - The company's profit margin in percentage

            ⚠️ This data is scrapped in real time from the yahoo finance API. ⚠️

            ℹ️ You can filter / search for a company with the filters on the left. ℹ️
        """)

    st.write('Number of companies found:', len(df_sp))
    st.dataframe(df_sp.iloc[:, 1:])

    # Part 2 - Company Selection
    st.subheader('Part 2 - Choose a company')
    option_company = st.selectbox("Choose a company:", df_sp.name.unique())

    # Part 3 - Stock Analysis
    st.subheader(f"Part 3 - {option_company} Stock Analysis")
    data_price = company_price(df_sp, option_company)

    # Part 4 - Show Stock Price
    show_stock_price(data_price)
    stock_price_2023, performance = metrics(data_price)

    col_prediction_1, col_prediction_2 = st.columns([1, 2])

    with col_prediction_1:
        st.metric(label='Stock Price 31 Dec 2022',
                  value=round(stock_price_2023, 2),
                  delta=str(performance) + " %",
                  delta_color='normal'
                  )

        st.write('*Compared to 31 Dec, 2012*')

    with col_prediction_2:
        with st.expander("Prediction explanation", expanded=True):
            st.write("""
                The graph above shows the evolution of the selected stock price between 31st dec. 2011 and 31 dec. 2021.
                The indicator on the left is the stock price value in 31st dec. 2021 for the selected company and its evolution between 31st dec. 2011 and 31st dec. 2021.

                ⚠️⚠️ These values are computed based on what the Yahoo Finance API returns !
            """)
