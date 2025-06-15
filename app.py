import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import date

# --- 環境変数からSupabase接続 ---
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- Streamlitタイトル ---
st.set_page_config(page_title="Kakeibo", layout="wide")
st.title("🌸 Kakeibo 家計簿アプリ")

# --- タブUI（単発支出 / 定期支出 / 集計） ---
tab1, tab2, tab3 = st.tabs(["💸 単発支出", "🔁 定期支出", "📊 集計"])

# --- タブ1: 単発支出 登録・表示 ---
with tab1:
    st.header("💸 単発支出 登録")

    with st.form("single_expense_form"):
        se_date = st.date_input("日付", value=date.today())
        se_category = st.selectbox("カテゴリ", ["食費", "交通費", "日用品", "娯楽", "その他"])
        se_amount = st.number_input("金額", min_value=0, step=100)
        se_memo = st.text_input("メモ", "")
        submitted = st.form_submit_button("登録")
        if submitted:
            supabase.table("Kakeibo").insert({
                "date": str(se_date),
                "category": se_category,
                "amount": se_amount,
                "memo": se_memo
            }).execute()
            st.success("単発支出を登録しました！")

    # 表示
    st.subheader("📄 単発支出一覧")
    expenses = supabase.table("Kakeibo").select("*").execute().data
    if expenses:
        df = pd.DataFrame(expenses)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)
        st.dataframe(df[["date", "category", "amount", "memo"]])
    else:
        st.info("まだ登録がありません")

# --- タブ2: 定期支出 登録・編集・削除 ---
with tab2:
    st.header("🔁 定期支出 登録")

    with st.form("recurring_expense_form"):
        re_date = st.date_input("日付（次回発生日）", value=date.today())
        re_category = st.selectbox("カテゴリ", ["家賃", "サブスク", "保険", "公共料金", "その他"])
        re_amount = st.number_input("金額", min_value=0, step=100, key="recurring_amount")
        re_memo = st.text_input("メモ", "", key="recurring_memo")
        re_submit = st.form_submit_button("登録")
        if re_submit:
            supabase.table("regularexpenses").insert({
                "date": str(re_date),
                "category": re_category,
                "amount": re_amount,
                "memo": re_memo
            }).execute()
            st.success("定期支出を登録しました！")

    # 一覧表示・編集・削除
    st.subheader("📄 定期支出一覧")
    r_data = supabase.table("regularexpenses").select("*").execute().data
    if r_data:
        r_df = pd.DataFrame(r_data)
        r_df["date"] = pd.to_datetime(r_df["date"])
        r_df = r_df.sort_values("date")

        for i, row in r_df.iterrows():
            with st.expander(f"{row['category']} - {row['amount']}円（{row['date'].date()}）"):
                new_date = st.date_input("日付", value=row["date"].date(), key=f"date_{row['id']}")
                new_cat = st.text_input("カテゴリ", value=row["category"], key=f"cat_{row['id']}")
                new_amt = st.number_input("金額", value=row["amount"], key=f"amt_{row['id']}")
                new_memo = st.text_input("メモ", value=row["memo"] or "", key=f"memo_{row['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("更新", key=f"update_{row['id']}"):
                        supabase.table("regularexpenses").update({
                            "date": str(new_date),
                            "category": new_cat,
                            "amount": new_amt,
                            "memo": new_memo
                        }).eq("id", row["id"]).execute()
                        st.success("更新しました")
                        st.experimental_rerun()
                with col2:
                    if st.button("削除", key=f"delete_{row['id']}"):
                        supabase.table("regularexpenses").delete().eq("id", row["id"]).execute()
                        st.warning("削除しました")
                        st.experimental_rerun()
    else:
        st.info("定期支出はまだ登録されていません")

# --- タブ3: 集計 ---
with tab3:
    st.header("📊 月別集計")

    # 単発支出
    df = pd.DataFrame(expenses)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.to_period("M").astype(str)

        st.subheader("📅 月ごとの合計支出")
        month_sum = df.groupby("month")["amount"].sum().reset_index()
        st.dataframe(month_sum)

        st.subheader("📂 月×カテゴリ別")
        month_cat_sum = df.groupby(["month", "category"])["amount"].sum().reset_index()
        st.dataframe(month_cat_sum)
    else:
        st.info("単発支出がまだ登録されていません")
