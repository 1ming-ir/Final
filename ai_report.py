import json
import os

import pandas as pd
import requests


DEEPSEEK_BASE_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"


def build_rule_report(metrics_df: pd.DataFrame) -> str:
    if metrics_df.empty:
        return "目前沒有可評估的交易結果。請先選擇至少一個策略。"

    ranked = metrics_df.sort_values(["score", "total_profit"], ascending=False).reset_index(drop=True)
    best = ranked.iloc[0]
    worst = ranked.iloc[-1]
    stable = ranked.sort_values(["max_drawdown", "total_profit"], ascending=[True, False]).iloc[0]

    return "\n\n".join(
        [
            "### 離線績效評估",
            f"- 綜合分數最高的是 **{best['strategy']}**，總損益為 `{best['total_profit']:.2f}`，勝率為 `{best['win_rate']:.2%}`，最大回撤為 `{best['max_drawdown']:.2f}`。",
            f"- 風險相對較低的是 **{stable['strategy']}**，最大回撤為 `{stable['max_drawdown']:.2f}`。",
            f"- 表現較弱的是 **{worst['strategy']}**，總損益為 `{worst['total_profit']:.2f}`。",
            "- 若重視報酬，可優先觀察總損益與 profit factor；若重視穩定性，應避免最大回撤過大的參數組合。",
            "- 這是未設定 DeepSeek API key 時的離線規則式分析；設定 key 後會改由生成式 AI 產生更完整的策略比較。",
        ]
    )


def build_ai_report(metrics_df: pd.DataFrame, api_key: str | None, temperature: float = 0.3) -> str:
    if metrics_df.empty:
        return "目前沒有可評估的交易結果。"
    if not api_key:
        return build_rule_report(metrics_df)

    payload = {
        "model": DEEPSEEK_MODEL,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": "你是台股量化交易課程助教。請用繁體中文客觀比較策略績效，避免承諾未來獲利。",
            },
            {
                "role": "user",
                "content": (
                    "請根據以下策略回測績效表，分析各策略的報酬、風險、勝率、最大回撤與改善方向。"
                    "請輸出 4 到 6 點條列式重點，最後補一句風險提醒。\n\n"
                    + metrics_df.to_json(orient="records", force_ascii=False)
                ),
            },
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(DEEPSEEK_BASE_URL, headers=headers, data=json.dumps(payload), timeout=40)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        return build_rule_report(metrics_df) + f"\n\nDeepSeek API 暫時無法使用，已改用離線分析。錯誤摘要：`{exc}`"


def get_api_key_from_streamlit(st_module=None) -> str | None:
    if st_module is not None:
        try:
            key = st_module.secrets.get("DEEPSEEK_API_KEY")
            if key:
                return key
        except Exception:
            pass
    return os.getenv("DEEPSEEK_API_KEY")
