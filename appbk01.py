import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import calendar

# 環境変数からSupabase接続情報を取得
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔁 定期支出の自動反映処理
def process_regular_expenses():
    today = datetime.date.today()
    res = supabase.table("regularexpenses").select("*").execute()
    regulars = res.data

    for reg in regulars:
        reg_date = datetime.date.fromisoformat(reg["next_date"])
        if reg_date <= today:
            # 重複チェック（name + date）
            check = supabase.table("Kakeibo").select("*").eq("name", reg["name"]).eq("date", reg["next_date"]).execute().data
            if check:
                continue

            # Kakeiboに登録
            insert_data = {
                "name": reg["name"],
                "amount": reg["amount"],
                "category": reg["category"],
                "date": reg["next_date"],
                "memo": f"[定期] {reg['memo']}" if reg["memo"] else "[定期]"
            }
            supabase.table("Kakeibo").insert(insert_data).execute()

            # next_date更新
            if reg["cycle"] == "monthly":
                next_date = reg_date + relativedelta(months=1)
            elif reg["cycle"] == "yearly":
                next_date = reg_date + relativedelta(years=1)
            elif reg["cycle"] == "weekly":
                next_date = reg_date + relativedelta(weeks=1)
            else:
                next_date = reg_date + relativedelta(months=1)  # 仮対応

            supabase.table("regularexpenses").update({"next_date": next_date.isoformat()}).eq("id", reg["id"]).execute()

# 🔁 毎回起動時に実行
process_regular_expenses()

# 🌟 Streamlit UI
st.title("🔁 定期支出の登録")

with st.form("regularexpense_form"):
    name = st.text_input("支出名（例：家賃、Netflix）")
    amount = st.number_input("金額", min_value=0, step=100)
    category = st.selectbox("カテゴリ", ["住居", "食費", "サブスク", "交通", "医療", "娯楽", "その他"])
    cycle = st.selectbox("繰り返し周期", ["monthly", "yearly", "weekly", "custom"])
    next_date = st.date_input("次の支払日", value=datetime.date.today())
    memo = st.text_area("メモ（任意）")

    submitted = st.form_submit_button("登録する")

    if submitted:
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
            st.success("定期支出が登録されました！")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# 📊 支出データのグラフ化
# データ取得
single_data = supabase.table("Kakeibo").select("*").execute().data
regular_data = supabase.table("regularexpenses").select("*").execute().data

df_single = pd.DataFrame(single_data)
df_regular = pd.DataFrame(regular_data)

today = datetime.date.today()
this_month = today.month
this_year = today.year

# regularexpensesの仮展開
if not df_regular.empty:
    df_regular["date"] = pd.to_datetime(f"{this_year}-{this_month}-01")
    df_regular["year"] = this_year
    df_regular["month"] = this_month
    df_regular["source"] = "定期"
else:
    df_regular = pd.DataFrame(columns=["name", "amount", "category", "date", "year", "month", "source"])

# Kakeiboの整形
if not df_single.empty:
    df_single["date"] = pd.to_datetime(df_single["date"])
    df_single["year"] = df_single["date"].dt.year
    df_single["month"] = df_single["date"].dt.month
    df_single["source"] = "単発"
else:
    df_single = pd.DataFrame(columns=["name", "amount", "category", "date", "year", "month", "source"])

# 単発＋定期結合
df_all = pd.concat([df_single, df_regular])

# 📊 カテゴリ別支出（円グラフ）
st.subheader("🧾 カテゴリ別支出割合")
df_filtered = df_all[(df_all["year"] == this_year) & (df_all["month"] == this_month)]

if not df_filtered.empty:
    cat_sum = df_filtered.groupby("category")["amount"].sum().reset_index()
    fig = px.pie(cat_sum, names="category", values="amount", title=f"{this_year}年{this_month}月のカテゴリ別支出")
    st.plotly_chart(fig)
else:
    st.info("今月の支出データがありません。")

# 📅 月別支出（棒グラフ）
st.subheader("📅 月別支出推移")
df_monthly = df_all[df_all["year"] == this_year].groupby("month")["amount"].sum().reset_index()
df_monthly["month"] = df_monthly["month"].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else "")

fig_bar = px.bar(df_monthly, x="month", y="amount", title=f"{this_year}年の月別支出推移", color_discrete_sequence=["#636EFA"])
st.plotly_chart(fig_bar)

import streamlit as st

import streamlit as st

st.header("🧹 データリセット（全削除）")

# チェックボックスで確認
confirm = st.checkbox("⚠️ 本当に全てのデータを削除することに同意します")

delete_btn = st.button("🚨 全データを削除", disabled=not confirm)

if delete_btn and confirm:
    try:
        # 条件なし delete().execute() で全件削除（integer IDでもOK）
        supabase.table("Kakeibo").delete().execute()
        supabase.table("regularexpenses").delete().execute()
        st.success("✅ すべてのデータを削除しました！（Kakeibo / regularexpenses）")
    except Exception as e:
        st.error(f"❌ 削除中にエラーが発生しました: {e}")
elif delete_btn and not confirm:
    st.warning("チェックボックスをオンにしないと削除できません⚠️")
