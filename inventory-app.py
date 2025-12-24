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

# --- ПОДКЛЮЧЕНИЕ ---
def connect_to_gsheets():
    key_dict = json.loads(st.secrets["textkey"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME)

# --- ФУНКЦИИ ---
def get_items():
    sh = connect_to_gsheets()
    data = sh.worksheet("items").get_all_records()
    return pd.DataFrame(data)

def add_item(name, item_type, serial, specs, location, status):
    sh = connect_to_gsheets()
    ws = sh.worksheet("items")
    new_id = len(ws.col_values(1))
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([new_id, name, item_type, str(serial), str(specs), location, status, created_at])
    st.success(f"✅ Добавлено: {name}")

def move_item(item_id, new_location, comment):
    sh = connect_to_gsheets()
    ws_items = sh.worksheet("items")
    ws_hist = sh.worksheet("history")
    cell = ws_items.find(str(item_id))
    if cell:
        row = cell.row
        name = ws_items.cell(row, 2).value
        old_loc = ws_items.cell(row, 6).value
        ws_items.update_cell(row, 6, new_location)
        hist_id = len(ws_hist.col_values(1))
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws_hist.append_row([hist_id, item_id, name, old_loc, new_location, date_now, comment])
        st.success(f"🚚 Перемещено: {name} на {new_location}")

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Inventory Cloud", layout="wide")
st.title("📦 IT Учет: Ак Берен (Cloud)")

menu = st.sidebar.radio("Меню", ["Дашборд", "Переместить", "Добавить новое"])

if menu == "Дашборд":
    df = get_items()
    if not df.empty:
        st.subheader("Текущее оборудование")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Таблица пуста.")

elif menu == "Добавить новое":
    with st.form("add"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Модель")
        type_ = c1.selectbox("Тип", TYPES)
        sn = c1.text_input("S/N")
        loc = c2.selectbox("Где", LOCATIONS)
        stat = c2.selectbox("Статус", ["Новый", "Рабочий", "Ремонт"])
        inf = c2.text_input("Инфо")
        if st.form_submit_button("Сохранить"):
            add_item(name, type_, sn, inf, loc, stat)

elif menu == "Переместить":
    df = get_items()
    if not df.empty:
        opts = df.apply(lambda x: f"{x['id']} | {x['name']} ({x['location']})", axis=1).tolist()
        sel = st.selectbox("Что перемещаем?", opts)
        with st.form("move"):
            to_loc = st.selectbox("Куда", LOCATIONS)
            comm = st.text_input("Комментарий")
            if st.form_submit_button("Подтвердить"):
                move_item(sel.split(" | ")[0], to_loc, comm)
