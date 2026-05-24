# 台股策略回測與 AI 評估 Streamlit APP

本專案依照期末作業要求，將老師提供的台股 KBar 回測程式整理成可部署的 Streamlit APP。APP 包含策略回測、策略績效比較、參數最佳化、風險調整指標、CSV 下載，以及 DeepSeek 生成式 AI 自動評估與追問聊天。

## 功能

- 支援策略：移動平均線、RSI 順勢、RSI 逆勢、布林通道、MACD、KDJ。
- 可設定回測日期、KBar 週期、每次交易數量、移動停損點數。
- 顯示策略交易邏輯，說明每個策略如何產生買賣訊號。
- 提供總損益、交易次數、勝率、平均損益、最大回撤、profit factor、報酬回撤比、類 Sharpe、每筆期望值與綜合分數。
- 可執行各策略模型參數最佳化，排序時同時考慮報酬與風險。
- 提供各策略最佳參數總表。
- 可下載策略績效、交易紀錄、價格資料與最佳化結果 CSV。
- 可使用 DeepSeek API 產生策略績效比較，也可針對目前回測結果即時追問。
- 沒有 API key 時會自動改用離線規則式分析，APP 仍可正常展示。

## 本機執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud 部署

1. 將此資料夾上傳到 GitHub repository。
2. 到 https://share.streamlit.io/ 建立新 APP。
3. Repository 選擇剛上傳的專案，Main file path 填入 `app.py`。
4. 若要啟用 DeepSeek AI 評估與聊天室，在 Streamlit Cloud 的 `Settings -> Secrets` 加入：

```toml
DEEPSEEK_API_KEY = "你的新 DeepSeek API key"
```

請不要把真實 API key 提交到 GitHub。

## 資料來源

資料由 `D:\FinTech\shioaji.db` 的 `stock_KBar_2330` 匯出，期間為 `2022-01-01` 到 `2024-04-09`，精簡後存放於：

```text
data/stock_KBar_2330_2022_2024.csv.gz
```

## 作業對應

- 已補上 MACD 策略程式交易。
- 已補上 KDJ 策略程式交易。
- 已製作 Streamlit APP。
- 已提供各策略參數最佳化功能。
- 已同時考慮風險與報酬，加入最大回撤、報酬回撤比、類 Sharpe 與綜合分數。
- 已提供生成式 AI 自動評估與即時追問聊天功能。
