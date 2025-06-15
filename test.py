# check_supabase.py

from supabase import create_client
from dotenv import load_dotenv
import os

# .env を読み込む
load_dotenv()

# 環境変数から URL と KEY を取得
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# 接続してみる
if not url or not key:
    print("❌ SUPABASE_URL または SUPABASE_KEY が .env に設定されてません！")
else:
    try:
        supabase = create_client(url, key)
        response = supabase.table("Kakeibo").select("*").limit(1).execute()
        print("✅ Supabase に接続できました！")
        print("サンプルデータ:", response.data)
    except Exception as e:
        print("❌ 接続に失敗しました:", e)
