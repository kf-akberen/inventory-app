import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.title("🧪 Тест подключения к Google")

try:
    # Пытаемся прочитать ключ
    key_dict = json.loads(st.secrets["textkey"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    
    # Пытаемся открыть таблицу
    sh = client.open("inventory_db")
    st.success("✅ Соединение с Google Таблицей установлено!")
    
    # Показываем список листов
    worksheets = sh.worksheets()
    st.write("Найдены листы:", [ws.title for ws in worksheets])

except Exception as e:
    st.error(f"❌ Ошибка: {e}")
    st.info("Проверь логи (Manage app -> Logs) для деталей.")
