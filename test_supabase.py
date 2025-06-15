from supabase import create_client, Client
import pandas as pd

url = "https://oebjijzmczviyjsarswl.supabase.co"  # 自分のURLに書き換えてね
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9lYmppanptY3p2aXlqc2Fyc3dsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxNTc2MjMsImV4cCI6MjA2NDczMzYyM30.sotZOMAiIOK25dHp-2k0T8pNuF6UA-NrCwIewyElud0"              # anonキーをここに！

supabase: Client = create_client(url, key)

# データ取得
response = supabase.table("Kakeibo").select("*").execute()
data = response.data

# DataFrame化
df = pd.DataFrame(data)

# 日付列を日付型に変換（もしあれば）
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])

# 月単位で集計（カテゴリごと）
if 'date' in df.columns and 'category' in df.columns and 'amount' in df.columns:
    df['month'] = df['date'].dt.to_period('M')
    summary = df.groupby(['month', 'category'])['amount'].sum().reset_index()
    print(summary)
else:
    print("必要な列が足りません😢")
