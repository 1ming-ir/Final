import pandas as pd
import streamlit as st

from ai_report import build_ai_report, get_api_key_from_streamlit
from backtest_engine import load_price_data, metrics_frame, resample_kbars
from strategies import STRATEGIES, buy_and_hold, optimize_strategy


DATA_PATH = "data/stock_KBar_2330_2022_2024.csv.gz"


st.set_page_config(page_title="台股策略回測與 AI 評估", layout="wide")
st.title("台股策略回測與 AI 評估")
st.caption("資料來源：shioaji.db / stock_KBar_2330，策略包含 MA、RSI、布林通道、MACD、KDJ 與參數最佳化。")


@st.cache_data
def load_data() -> pd.DataFrame:
    return load_price_data(DATA_PATH)


raw_df = load_data()

with st.sidebar:
    st.header("回測設定")
    min_date = raw_df["time"].min().date()
    max_date = raw_df["time"].max().date()
    date_range = st.date_input(
        "回測日期",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    kbar_rule = st.selectbox("KBar 週期", ["1min", "5min", "15min", "30min", "60min", "1D"], index=2)
    quantity = st.number_input("每次交易數量", min_value=1, max_value=100, value=1, step=1)
    stop_loss = st.number_input("移動停損點數（0 表示不使用）", min_value=0.0, value=0.0, step=1.0)
    selected_strategies = st.multiselect("策略", list(STRATEGIES.keys()), default=list(STRATEGIES.keys()))
    run_optimization = st.checkbox("執行參數最佳化", value=False)
    temperature = st.slider("AI temperature", 0.0, 1.0, 0.3, 0.1)

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
    filtered = raw_df[(raw_df["time"] >= start_date) & (raw_df["time"] < end_date)].copy()
else:
    filtered = raw_df.copy()

df = resample_kbars(filtered, kbar_rule)
if df.empty:
    st.error("目前日期區間沒有資料，請調整回測日期。")
    st.stop()

st.info(f"分析標的：2330 台積電；期間：{df['time'].min()} 至 {df['time'].max()}；K 棒數：{len(df):,}")

st.subheader("價格走勢")
st.line_chart(df.set_index("time")["close"], height=260)

base_params = {"quantity": int(quantity), "stop_loss": float(stop_loss)}
results = {}
for strategy_name in selected_strategies:
    results[strategy_name] = STRATEGIES[strategy_name](df, **base_params)

if not results:
    st.warning("請至少選擇一個策略。")
    st.stop()

comparison = metrics_frame(results)

st.subheader("策略績效比較")
display_comparison = comparison.copy()
for col in ["total_profit", "avg_profit", "max_drawdown", "profit_factor", "score"]:
    display_comparison[col] = display_comparison[col].map(lambda x: round(float(x), 4))
display_comparison["win_rate"] = display_comparison["win_rate"].map(lambda x: f"{x:.2%}")
st.dataframe(display_comparison, use_container_width=True)

equity_df = pd.DataFrame({"time": df["time"]})
for name, result in results.items():
    if not result.equity.empty:
        series = result.equity[["time", "equity"]].rename(columns={"equity": name})
        equity_df = equity_df.merge(series, on="time", how="left")

st.subheader("累積損益曲線")
st.line_chart(equity_df.set_index("time").ffill().fillna(0), height=300)

st.subheader("各策略交易紀錄")
tabs = st.tabs(list(results.keys()))
for tab, name in zip(tabs, results.keys()):
    with tab:
        result = results[name]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("總損益", f"{result.metrics['total_profit']:.2f}")
        c2.metric("交易次數", result.metrics["trade_count"])
        c3.metric("勝率", f"{result.metrics['win_rate']:.2%}")
        c4.metric("最大回撤", f"{result.metrics['max_drawdown']:.2f}")
        if result.trades.empty:
            st.write("此期間沒有完成交易。")
        else:
            st.dataframe(result.trades.tail(100), use_container_width=True)

if run_optimization:
    st.subheader("參數最佳化")
    opt_tabs = st.tabs(selected_strategies)
    for tab, name in zip(opt_tabs, selected_strategies):
        with tab:
            opt_df = optimize_strategy(name, df, base_params)
            if opt_df.empty:
                st.info("此策略沒有可顯示的最佳化結果。")
            else:
                st.dataframe(opt_df.head(20), use_container_width=True)

st.subheader("生成式 AI 自動評估")
api_key = get_api_key_from_streamlit(st)
report = build_ai_report(comparison, api_key=api_key, temperature=temperature)
st.markdown(report)

with st.expander("買進持有基準"):
    benchmark = buy_and_hold(df, quantity=int(quantity))
    st.json(benchmark.metrics)
