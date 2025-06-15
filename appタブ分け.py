import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import datetime
import pandas as pd
import plotly.express as px
import calendar

# --- Supabase接続 ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="家計簿アプリ", layout="wide")
st.title("💰 家計簿アプリ")

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(["単発支出", "定期支出", "グラフ分析"])

# =========================
# 🔹 Tab1: 単発支出
# =========================
with tab1:
    st.header("📝 単発支出登録")

    with st.form("single_expense_form"):
        date = st.date_input("日付", value=datetime.date.today())
        type_ = st.text_input("支出名")
        amount = st.number_input("金額", min_value=0, step=100)
        category = st.selectbox("カテゴリ", ["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"])
        payment_method = st.selectbox("支払い方法", ["現金", "クレジット", "電子マネー", "口座振替"])
        memo = st.text_area("メモ", "")
        submit = st.form_submit_button("登録する")

        if submit:
            data = {
                "date": date.isoformat(),
                "type": type_,
                "amount": amount,
                "category": category,
                "payment_method": payment_method,
                "memo": memo,
            }
            try:
                supabase.table("Kakeibo").insert(data).execute()
                st.success("単発支出を登録しました！")
            except Exception as e:
                st.error(f"登録エラー: {e}")

# =========================
# 🔹 Tab2: 定期支出
# =========================
with tab2:
    st.header("🔁 定期支出 登録・編集・削除")

    # --- 登録フォーム ---
    with st.form("regularexpense_form"):
        name = st.text_input("支出名（例：家賃、Netflix）")
        amount = st.number_input("金額", min_value=0, step=100)
        category = st.selectbox("カテゴリ", ["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"])
        cycle = st.selectbox("繰り返し周期", ["monthly", "yearly", "weekly", "custom"])
        next_date = st.date_input("次の支払日", value=datetime.date.today())
        memo = st.text_area("メモ", "")
        submit_regular = st.form_submit_button("登録する")

        if submit_regular:
            data = {
                "name": name,
                "amount": amount,
                "category": category,
                "cycle": cycle,
                "next_date": next_date.isoformat(),
                "memo": memo,
            }
            try:
                supabase.table("regularexpenses").insert(data).execute()
                st.success("定期支出を登録しました！")
            except Exception as e:
                st.error(f"登録エラー: {e}")

    # --- 定期支出一覧と編集・削除 ---
    st.subheader("📋 登録済みの定期支出")

    result = supabase.table("regularexpenses").select("*").execute()
    regulars = result.data or []

    for item in regulars:
        with st.expander(f"{item['name']} | ¥{item['amount']} | {item['category']} | {item['cycle']}"):
            new_name = st.text_input(f"支出名 (ID: {item['id']})", item['name'], key=f"name_{item['id']}")
            new_amount = st.number_input("金額", value=item['amount'], key=f"amount_{item['id']}")
            new_category = st.selectbox("カテゴリ", ["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"], index=["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"].index(item['category']), key=f"cat_{item['id']}")
            new_cycle = st.selectbox("周期", ["monthly", "yearly", "weekly", "custom"], index=["monthly", "yearly", "weekly", "custom"].index(item['cycle']), key=f"cycle_{item['id']}")
            new_next_date = st.date_input("次の支払日", datetime.date.fromisoformat(item['next_date']), key=f"date_{item['id']}")
            new_memo = st.text_area("メモ", item['memo'] or "", key=f"memo_{item['id']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("更新する", key=f"update_{item['id']}"):
                    supabase.table("regularexpenses").update({
                        "name": new_name,
                        "amount": new_amount,
                        "category": new_category,
                        "cycle": new_cycle,
                        "next_date": new_next_date.isoformat(),
                        "memo": new_memo,
                    }).eq("id", item["id"]).execute()
                    st.success("更新しました ✅")
                    st.experimental_rerun()

            with col2:
                if st.button("削除する", key=f"delete_{item['id']}"):
                    supabase.table("regularexpenses").delete().eq("id", item["id"]).execute()
                    st.warning("削除しました 🗑️")
                    st.experimental_rerun()

# =========================
# 🔹 Tab3: グラフ分析
# =========================
with tab3:
    st.header("📊 支出グラフ分析")

    # --- データ取得 ---
    single_data = supabase.table("Kakeibo").select("*").execute().data or []
    regular_data = supabase.table("regularexpenses").select("*").execute().data or []

    # 単発
    df_single = pd.DataFrame(single_data)
    if not df_single.empty:
        df_single["name"] = df_single["type"]
        df_single["date"] = pd.to_datetime(df_single["date"])
        df_single["year"] = df_single["date"].dt.year
        df_single["month"] = df_single["date"].dt.month
        df_single["source"] = "単発"
    else:
        df_single = pd.DataFrame(columns=["name", "amount", "category", "date", "year", "month", "source"])

    # 定期
    df_regular = pd.DataFrame(regular_data)
    if not df_regular.empty:
        df_regular["date"] = pd.to_datetime(df_regular["next_date"])
        df_regular["year"] = df_regular["date"].dt.year
        df_regular["month"] = df_regular["date"].dt.month
        df_regular["source"] = "定期"
    else:
        df_regular = pd.DataFrame(columns=["name", "amount", "category", "date", "year", "month", "source"])

    # --- 結合 ---
    df_all = pd.concat([df_single, df_regular], ignore_index=True)
    today = datetime.date.today()
    df_filtered = df_all[(df_all["year"] == today.year) & (df_all["month"] == today.month)]

    # --- 円グラフ ---
    st.subheader("📌 カテゴリ別支出（今月）")
    if not df_filtered.empty:
        cat_sum = df_filtered.groupby("category")["amount"].sum().reset_index()
        fig = px.pie(cat_sum, names="category", values="amount", title=f"{today.year}年{today.month}月のカテゴリ別支出")
        st.plotly_chart(fig)
    else:
        st.info("今月の支出がまだありません。")

    # --- 月別支出（棒グラフ） ---
    st.subheader("📆 月別支出推移")
    df_monthly = df_all[df_all["year"] == today.year].groupby("month")["amount"].sum().reset_index()
    if not df_monthly.empty:
        df_monthly["month"] = df_monthly["month"].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else "")
        fig_bar = px.bar(df_monthly, x="month", y="amount", title=f"{today.year}年の月別支出", color_discrete_sequence=["#636EFA"])
        st.plotly_chart(fig_bar)
    else:
        st.info("今年の支出がまだありません。")
