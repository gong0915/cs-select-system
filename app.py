from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

app = FastAPI()

items = {
    "AWP | Asiimov (Field-Tested)": "AWP | 二西莫夫 (略有磨损)",
    "AK-47 | Redline (Field-Tested)": "AK-47 | 红线 (略有磨损)",
    "M4A4 | Neo-Noir (Field-Tested)": "M4A4 | 二次元 (略有磨损)",
    "Desert Eagle | Blaze (Factory New)": "沙漠之鹰 | 炽烈之炎 (崭新出厂)",
    "AWP | Lightning Strike (Factory New)": "AWP | 闪电打击 (崭新出厂)",
    "AK-47 | Vulcan (Field-Tested)": "AK-47 | 火神 (略有磨损)",
    "M4A1-S | Printstream (Field-Tested)": "M4A1-S | 印花集 (略有磨损)",
    "USP-S | Kill Confirmed (Field-Tested)": "USP-S | 杀意已决 (略有磨损)",
    "Operation Breakout Weapon Case": "突破行动武器箱",
    "Glove Case": "手套武器箱",
    "Spectrum Case": "光谱武器箱",
    "Prisma Case": "棱彩武器箱",
    "Danger Zone Case": "头号特训武器箱",
    "Fracture Case": "裂网武器箱",
    "Chroma 2 Case": "幻彩2号武器箱"
}

def get_price_data(item_name):
    url = f"https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name={item_name}"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://steamcommunity.com/market/"
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        if "prices" not in data:
            print("Steam返回异常:", data)
            return None

        prices = data["prices"]

        if not prices:
            return None
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

    score = 0
    latest_price = df.iloc[-1]["price"]

    seven_days = df[df["date"] >= datetime.now() - timedelta(days=7)]
    five_days = df[df["date"] >= datetime.now() - timedelta(days=5)]

    if len(seven_days) == 0:
        return None

    old_price = seven_days.iloc[0]["price"]
    change_7d = round((latest_price - old_price) / old_price * 100, 2)

    # 7天涨幅评分
    if 3 <= change_7d <= 15:
        score += 30

    prices_5 = five_days["price"].tolist()
    straight_up = all(x < y for x, y in zip(prices_5, prices_5[1:]))

    if not straight_up:
        score += 20

    vol_recent = df.iloc[-7:]["volume"].sum()
    vol_old = df.iloc[-14:-7]["volume"].sum()

    if vol_old == 0:
        vol_change = 0
    else:
        vol_change = round((vol_recent - vol_old) / vol_old * 100, 2)

    if vol_change > 0:
        score += 25

    # 最近3天是否有小回调
    last3 = df.iloc[-3:]["price"].tolist()
    if last3[-1] < last3[-2]:
        score += 10

    # 波动是否平稳
    if abs(change_7d) < 20:
        score += 15

    if score >= 80:
        advice = "重点关注"
    elif score >= 70:
        advice = "可考虑布局"
    else:
        advice = "观望"

    return latest_price, change_7d, straight_up, vol_change, advice, score

@app.get("/", response_class=HTMLResponse)
def home():
    rows = ""
    data_list = []
    for en_name, cn_name in items.items():
        df = get_price_data(en_name)
    result = analyze(df)

if result:
data_list.append((result[5], f"""
<tr>
    <td>{cn_name}</td>
    <td>{result[0]}</td>
    <td>{result[1]}%</td>
    <td>{"是" if result[2] else "否"}</td>
    <td>{result[3]}%</td>
    <td>{result[4]}</td>
    <td>{result[5]}</td>
</tr>
"""))

    data_list.sort(reverse=True)

    for _, row in data_list:
         rows += row
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
                <th>投资评分</th>
                <th>投资建议</th>
                
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return html

port = int(os.environ.get("PORT", 8000))
