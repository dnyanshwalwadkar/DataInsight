import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import google.generativeai as genai
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Stock Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'ticker' not in st.session_state:
    st.session_state.ticker = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""


# --- Gemini API Call Functions ---
@st.cache_data
def get_model(model_name="gemini-1.5-flash"):
    """Initializes and returns the Gemini GenerativeModel."""
    return genai.GenerativeModel(model_name=model_name)


def call_gemini_api_with_backoff(prompt_text, retries=5, model_name="gemini-1.5-flash"):
    """Calls the Gemini API with exponential backoff for retries."""
    model = get_model(model_name)
    for i in range(retries):
        try:
            response = model.generate_content([{"text": prompt_text}])
            if response and response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                raise ValueError("Received an empty or invalid response from the API.")
        except Exception as e:
            if i < retries - 1:
                st.warning(f"API call failed, retrying in {2 ** i}s... Error: {e}")
                time.sleep(2 ** i)
            else:
                st.error(f"API call failed after multiple retries. Error: {e}")
                return None
    return None


# --- Stock Data Functions ---
def fetch_stock_data(ticker):
    """Fetches historical stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        # Fetch 1 year of historical data
        hist = stock.history(period="1y")
        if hist.empty:
            st.error(f"Could not fetch historical data for {ticker}. Please check the ticker symbol.")
            return None, None
        return stock, hist.reset_index()
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker}: {e}")
        return None, None


# --- Main Application Flow ---

st.title("📈 AI-Powered Stock Analyzer")
st.markdown(
    "Enter a stock ticker to get a comprehensive analysis, including key metrics, charts, and AI-driven insights.")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Setup")
    st.session_state.api_key = st.text_input("Enter your Gemini API Key:", type="password",
                                             help="Your key is used for this session only.")

    if st.session_state.api_key:
        try:
            genai.configure(api_key=st.session_state.api_key)
            st.success("Gemini API key configured!", icon="✅")
        except Exception as e:
            st.error(f"Invalid API Key: {e}")
    else:
        st.warning("Please enter your API key to enable analysis.")

    st.header("2. Analyze a Stock")
    ticker_input = st.text_input("Enter Stock Ticker (e.g., AAPL, GOOGL)", value="AAPL").upper()

    if st.button("Analyze Stock", key="analyze_button"):
        if not st.session_state.api_key:
            st.error("Please enter your Gemini API key first.")
        elif not ticker_input:
            st.error("Please enter a stock ticker.")
        else:
            st.session_state.ticker = ticker_input
            st.session_state.analysis_done = False  # Reset analysis state
            st.session_state.messages = []  # Clear previous chat
            with st.spinner(f"Fetching and analyzing data for {st.session_state.ticker}..."):
                stock_info, stock_hist = fetch_stock_data(st.session_state.ticker)
                if stock_hist is not None:
                    st.session_state.stock_data = {
                        "info": stock_info.info,
                        "history": stock_hist
                    }
                    st.session_state.analysis_done = True
                else:
                    st.session_state.stock_data = None
                    st.session_state.analysis_done = False

# --- Main Page Logic ---
if st.session_state.analysis_done and st.session_state.stock_data:
    info = st.session_state.stock_data["info"]
    df = st.session_state.stock_data["history"]

    st.header(f"Analysis for {info.get('longName', st.session_state.ticker)}")

    # --- Key Metrics ---
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Last Close", f"${info.get('previousClose', 0):.2f}")
    col2.metric("Market Cap", f"${(info.get('marketCap', 0) / 1_000_000_000):.2f}B")
    col3.metric("52-Week High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
    col4.metric("52-Week Low", f"${info.get('fiftyTwoWeekLow', 0):.2f}")

    # --- Interactive Charts ---
    st.subheader("Interactive Charts")
    fig_price = px.line(df, x='Date', y='Close', title=f'{st.session_state.ticker} Closing Price Over Time')
    fig_price.update_layout(xaxis_title="Date", yaxis_title="Closing Price (USD)")
    st.plotly_chart(fig_price, use_container_width=True)

    fig_vol = px.bar(df, x='Date', y='Volume', title=f'{st.session_state.ticker} Trading Volume')
    fig_vol.update_layout(xaxis_title="Date", yaxis_title="Volume")
    st.plotly_chart(fig_vol, use_container_width=True)

    # --- AI-Powered Analysis ---
    with st.spinner("🤖 Gemini is analyzing the data..."):
        st.subheader("Gemini's Analysis")

        # Prepare data summary for Gemini
        data_summary = f"""
        Here is the historical data for the last year for the stock {st.session_state.ticker}:
        - The data spans from {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}.
        - The closing price ranged from a low of {df['Close'].min():.2f} to a high of {df['Close'].max():.2f}.
        - The average daily trading volume was {df['Volume'].mean():,.0f} shares.
        - The most recent closing price is {df['Close'].iloc[-1]:.2f}.
        """

        analysis_prompt = f"""
        You are a financial analyst. Based on the following data summary for the stock {st.session_state.ticker}, provide a brief analysis.
        Your analysis should include:
        1.  A short summary of the stock's performance over the last year.
        2.  Two or three key observations from the data (e.g., trends, volatility, volume spikes).
        3.  A concluding thought on what this data might suggest to a potential investor.

        Keep the tone professional and accessible to a non-expert. Do not give financial advice.

        Data Summary:
        {data_summary}
        """

        ai_analysis = call_gemini_api_with_backoff(analysis_prompt)
        if ai_analysis:
            st.markdown(ai_analysis)
        else:
            st.error("The AI analysis could not be generated at this time.")

    # --- Data Table ---
    with st.expander("View Raw Historical Data"):
        st.dataframe(df)

    # --- Chat with Gemini ---
    st.header("💬 Chat About This Stock")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(f"Ask a follow-up question about {st.session_state.ticker}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_context = f"""
                You are a helpful AI assistant specializing in stock data analysis.
                You are answering questions about the stock {st.session_state.ticker}.
                Here is the data summary you have access to:
                {data_summary}

                Based ONLY on this context, provide a concise and insightful answer to the user's question. Do not hallucinate or use external knowledge. If the answer isn't in the provided data, state that clearly.
                User's question: {prompt}
                """
                response = call_gemini_api_with_backoff(chat_context)
                if response:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    response_text = "I'm sorry, I could not process that request at this time."
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

elif not st.session_state.analysis_done:
    st.info("Please enter a stock ticker in the sidebar and click 'Analyze Stock' to begin.")
