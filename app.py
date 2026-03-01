from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

app = FastAPI()

items = {
    "AWP | Dragon Lore (Factory New)": "AWP | 龙狙 (崭新出厂)",
    "AK-47 | Fire Serpent (Field-Tested)": "AK-47 | 火蛇 (略有磨损)",
    "Operation Breakout Weapon Case": "突破行动武器箱",
    "Glove Case": "手套武器箱"
}

def get_price_data(item_name):
    url = f"https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name={item_name}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        data = response.json()
        prices = data["prices"]
        df = pd.DataFrame(prices, columns=["date", "price", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        df["price"] = df["price"].astype(float)
        df["volume"] = df["volume"].astype(int)
        return df
    except:
        return None

def analyze(df):
    if df is None or len(df) < 20:
        return None

    latest_price = df.iloc[-1]["price"]

    seven_days = df[df["date"] >= datetime.now() - timedelta(days=7)]
    five_days = df[df["date"] >= datetime.now() - timedelta(days=5)]

    if len(seven_days) == 0:
        return None

    old_price = seven_days.iloc[0]["price"]
    change_7d = round((latest_price - old_price) / old_price * 100, 2)

    prices_5 = five_days["price"].tolist()
    straight_up = all(x < y for x, y in zip(prices_5, prices_5[1:]))

    vol_recent = df.iloc[-7:]["volume"].sum()
    vol_old = df.iloc[-14:-7]["volume"].sum()

    if vol_old == 0:
        vol_change = 0
    else:
        vol_change = round((vol_recent - vol_old) / vol_old * 100, 2)

    if 3 <= change_7d <= 15 and not straight_up and vol_change > 0:
        advice = "建议买入"
    else:
        advice = "观望"

    return latest_price, change_7d, straight_up, vol_change, advice

@app.get("/", response_class=HTMLResponse)
def home():
    rows = ""

    for en_name, cn_name in items.items():
        df = get_price_data(en_name)
        result = analyze(df)

        if result:
            rows += f"""
            <tr>
                <td>{cn_name}</td>
                <td>{result[0]}</td>
                <td>{result[1]}%</td>
                <td>{"是" if result[2] else "否"}</td>
                <td>{result[3]}%</td>
                <td>{result[4]}</td>
            </tr>
            """

    html = f"""
    <html>
    <head>
        <title>CS 饰品选品系统</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h2>CS 自动选品系统</h2>
        <table border="1" cellpadding="8">
            <tr>
                <th>饰品名称</th>
                <th>当前价格</th>
                <th>7天涨跌%</th>
                <th>5天直线暴涨</th>
                <th>成交量变化%</th>
                <th>投资建议</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return html

port = int(os.environ.get("PORT", 8000))
