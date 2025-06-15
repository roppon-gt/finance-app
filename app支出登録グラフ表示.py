import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import datetime
import pandas as pd
import plotly.express as px
import calendar

# 環境変数読み込み
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🔁 家計簿アプリ - 単発＆定期支出登録＆支出分析")

# --- 単発支出登録フォーム ---
with st.form("single_expense_form"):
    st.header("単発支出登録")
    type_ = st.text_input("支出名（例：ランチ、書籍）")
    amount = st.number_input("金額", min_value=0, step=100, key="single_amount")
    category = st.selectbox("カテゴリ", ["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"], key="single_category")
    payment_method = st.selectbox("支払い方法", ["現金", "クレジットカード", "電子マネー", "その他"], key="payment_method")
    date = st.date_input("支払日", value=datetime.date.today(), key="single_date")
    memo = st.text_area("メモ（任意）", key="single_memo")

    submitted_single = st.form_submit_button("登録する（単発支出）")

    if submitted_single:
        data = {
            "type": type_,
            "amount": amount,
            "category": category,
            "payment_method": payment_method,
            "date": date.isoformat(),
            "memo": memo,
            # user_idは適宜設定してください。今はNoneにしてます
            "user_id": None,
        }
        try:
            supabase.table("Kakeibo").insert(data).execute()
            st.success("単発支出が登録されました！")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# --- 定期支出登録フォーム ---
with st.form("regularexpense_form"):
    st.header("定期支出登録")
    name = st.text_input("支出名（例：家賃、Netflix）", key="reg_name")
    amount_reg = st.number_input("金額", min_value=0, step=100, key="reg_amount")
    category_reg = st.selectbox("カテゴリ", ["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"], key="reg_category")
    cycle = st.selectbox("繰り返し周期", ["monthly", "yearly", "weekly", "custom"], key="reg_cycle")
    next_date = st.date_input("次の支払日", value=datetime.date.today(), key="reg_next_date")
    memo_reg = st.text_area("メモ（任意）", key="reg_memo")

    submitted_reg = st.form_submit_button("登録する（定期支出）")

    if submitted_reg:
        data = {
            "name": name,
            "amount": amount_reg,
            "category": category_reg,
            "cycle": cycle,
            "next_date": next_date.isoformat(),
            "memo": memo_reg,
        }
        try:
            supabase.table("regularexpenses").insert(data).execute()
            st.success("定期支出が登録されました！")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# --- Supabaseからデータ取得 ---
single_data = supabase.table("Kakeibo") \
    .select("id, user_id, date, type, amount, category, payment_method, memo, created_at") \
    .execute().data or []

regular_data = supabase.table("regularexpenses") \
    .select("id, name, amount, category, cycle, next_date, memo") \
    .execute().data or []

# --- DataFrame化 ---
df_single = pd.DataFrame(single_data)
if not df_single.empty:
    df_single["name"] = df_single["type"]  # typeを支出名として使う
    df_single["date"] = pd.to_datetime(df_single["date"])
    df_single["year"] = df_single["date"].dt.year
    df_single["month"] = df_single["date"].dt.month
    df_single["source"] = "単発"
else:
    df_single = pd.DataFrame(columns=["name", "amount", "category", "date", "year", "month", "source"])

df_regular = pd.DataFrame(regular_data)
if not df_regular.empty:
    df_regular["date"] = pd.to_datetime(df_regular["next_date"])
    df_regular["year"] = df_regular["date"].dt.year
    df_regular["month"] = df_regular["date"].dt.month
    df_regular["source"] = "定期"
else:
    df_regular = pd.DataFrame(columns=["name", "amount", "category", "date", "year", "month", "source"])

df_all = pd.concat([df_single, df_regular], ignore_index=True)

today = datetime.date.today()
df_filtered = df_all[(df_all["year"] == today.year) & (df_all["month"] == today.month)]

# --- カテゴリ別支出割合（円グラフ） ---
st.subheader("🧾 カテゴリ別支出割合")
if not df_filtered.empty:
    cat_sum = df_filtered.groupby("category")["amount"].sum().reset_index()
    fig = px.pie(cat_sum, names="category", values="amount", title=f"{today.year}年{today.month}月のカテゴリ別支出")
    st.plotly_chart(fig)
else:
    st.info("今月の支出データがありません。")

# --- 月別支出推移（棒グラフ） ---
st.subheader("📅 月別支出推移")
df_monthly = df_all[df_all["year"] == today.year].groupby("month")["amount"].sum().reset_index()
if not df_monthly.empty:
    df_monthly["month"] = df_monthly["month"].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else "")
    fig_bar = px.bar(df_monthly, x="month", y="amount", title=f"{today.year}年の月別支出推移", color_discrete_sequence=["#636EFA"])
    st.plotly_chart(fig_bar)
else:
    st.info("今年の支出データがありません。")
