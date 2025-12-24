import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- НАСТРОЙКИ ---
SHEET_NAME = "inventory_db" 

LOCATIONS = [
    "Офис (Кызылорда)", "Склад", "Ремонт/Заправка",
    "Месторождение «Ак Берен»", "Месторождение «Кумколь»", "Месторождение «Арыскум»",
    "Месторождение «Акыртобе, Полторацкое»", "Месторождение «Амангельды»",
    "Месторождение «Акшабулак / Сев.зап. Коныс / Таур»", "Месторождение «Бектас и Коныс»",
    "Месторождение «Сарыбулак / Арысское»", "Месторождение «Ащисай»", "Месторождение «Сарыбулак ВКО»"
]

TYPES = ["Картридж", "Мышь", "Клавиатура", "Монитор", "Принтер", "МФУ", "Системный блок", "Ноутбук", "Прочее"]

# --- ПОДКЛЮЧЕНИЕ К GOOGLE SHEETS ---
def connect_to_gsheets():
    try:
        # Берем ключ из Secrets
        key_dict = json.loads(st.secrets["textkey"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME)
    except Exception as e:
        st.error(f"Ошибка подключения к Google: {e}")
        return None

# --- ИНИЦИАЛИЗАЦИЯ (Создание листов, если их нет) ---
def init_db():
    sh = connect_to_gsheets()
    if sh:
        try:
            sh.worksheet("items")
        except:
            ws = sh.add_worksheet(title="items", rows=1000, cols=10)
            ws.append_row(["id", "name", "item_type", "serial_number", "specs", "location", "status", "created_at"])
        try:
            sh.worksheet("history")
        except:
            ws = sh.add_worksheet(title="history", rows=1000, cols=10)
            ws.append_row(["id", "item_id", "item_name", "from_loc", "to_loc", "date_time", "comment"])

# --- ФУНКЦИИ ---
def get_items():
    sh = connect_to_gsheets()
    if sh:
        return pd.DataFrame(sh.worksheet("items").get_all_records())
    return pd.DataFrame()

def add_item(name, item_type, serial, specs, location, status):
    sh = connect_to_gsheets()
    if sh:
        ws = sh.worksheet("items")
        new_id = len(ws.col_values(1))
        ws.append_row([new_id, name, item_type, str(serial), str(specs), location, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        st.success(f"Добавлено: {name}")

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Ak Beren Cloud", layout="wide")
st.title("📦 IT Учет: Ак Берен (Облако)")

if "textkey" not in st.secrets:
    st.error("⚠️ Ошибка: Не настроены Secrets! Вставьте JSON-ключ в настройки Streamlit.")
else:
    init_db()
    menu = st.sidebar.radio("Меню", ["Дашборд", "Добавить новое", "История"])

    if menu == "Дашборд":
        df = get_items()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("База данных пуста.")

    elif menu == "Добавить новое":
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Модель")
            t = c1.selectbox("Тип", TYPES)
            sn = c1.text_input("S/N (Серийник)")
            loc = c2.selectbox("Локация", LOCATIONS)
            stt = c2.selectbox("Статус", ["Новый", "Рабочий", "Ремонт"])
            sp = c2.text_input("Характеристики")
            if st.form_submit_button("Сохранить"):
                add_item(name, t, sn, sp, loc, stt)
