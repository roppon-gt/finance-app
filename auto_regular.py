import streamlit as st
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os
import plotly.express as px

# .env読み込み
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

st.title("💰 家計簿ダッシュボード（定期支出含む）")

# データ取得（通常支出）
resp1 = supabase.table("Kakeibo").select("*").execute()
df1 = pd.DataFrame(resp1.data or [])
if not df1.empty:
    df1['date'] = pd.to_datetime(df1['date'])
    df1['month'] = df1['date'].dt.to_period('M').astype(str)
else:
    df1 = pd.DataFrame(columns=['amount', 'category', 'month'])

# データ取得（定期支出）
resp2 = supabase.table("regularexpenses").select("*").execute()
df2 = pd.DataFrame(resp2.data or [])
if not df2.empty:
    # 定期支出は「next_date」を日付として扱い、「month」を作成
    df2['next_date'] = pd.to_datetime(df2['next_date'])
    df2['month'] = df2['next_date'].dt.to_period('M').astype(str)
    # こっちは「amount」「category」ある想定
else:
    df2 = pd.DataFrame(columns=['amount', 'category', 'month'])

# 両テーブルを結合
df = pd.concat([df1[['amount','category','month']], df2[['amount','category','month']]], ignore_index=True)

# 月選択
month_list = sorted(df['month'].unique())
selected_month = st.selectbox("月を選択してください", month_list)

# 選択した月のデータ抽出
monthly_data = df[df['month'] == selected_month]

# カテゴリ別合計
category_sum = monthly_data.groupby('category')['amount'].sum().reset_index()

# 円グラフ
st.subheader("📊 カテゴリ別支出（円グラフ）")
fig_pie = px.pie(category_sum, names='category', values='amount', hole=0.4)
st.plotly_chart(fig_pie)

# 棒グラフ
st.subheader("📈 カテゴリ別支出（棒グラフ）")
fig_bar = px.bar(category_sum, x='category', y='amount', color='category')
st.plotly_chart(fig_bar)
