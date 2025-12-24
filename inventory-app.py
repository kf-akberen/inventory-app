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
    # Данные берутся из Secrets в настройках Streamlit Cloud
    try:
        key_dict = json.loads(st.secrets["textkey"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME)
    except Exception as e:
        st.error(f"Ошибка авторизации Google: {e}")
        return None

# --- ИНИЦИАЛИЗАЦИЯ ТАБЛИЦЫ ---
def init_db():
    sh = connect_to_gsheets()
    if sh:
        # Лист предметов
        try:
            sh.worksheet("items")
        except:
            ws = sh.add_worksheet(title="items", rows=1000, cols=10)
            ws.append_row(["id", "name", "item_type", "serial_number", "specs", "location", "status", "created_at"])

        # Лист истории
        try:
            sh.worksheet("history")
        except:
            ws = sh.add_worksheet(title="history", rows=1000, cols=10)
            ws.append_row(["id", "item_id", "item_name", "from_loc", "to_loc", "date_time", "comment"])

# --- ФУНКЦИИ УПРАВЛЕНИЯ ---
def get_items():
    sh = connect_to_gsheets()
    if sh:
        data = sh.worksheet("items").get_all_records()
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_history():
    sh = connect_to_gsheets()
    if sh:
        data = sh.worksheet("history").get_all_records()
        df = pd.DataFrame(data)
        return df.iloc[::-1] if not df.empty else df
    return pd.DataFrame()

def add_item(name, item_type, serial, specs, location, status):
    sh = connect_to_gsheets()
    if sh:
        ws = sh.worksheet("items")
        new_id = len(ws.col_values(1))
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([new_id, name, item_type, str(serial), str(specs), location, status, created_at])
        st.success(f"Добавлено: {name}")

def move_item(item_id, new_location, comment):
    sh = connect_to_gsheets()
    if sh:
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
            st.success(f"Перемещено: {name} -> {new_location}")

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Ak Beren Inventory", layout="wide")
st.title("📦 IT Учет: Ак Берен (Cloud)")

if "textkey" not in st.secrets:
    st.error("Настройте 'Secrets' в Streamlit Cloud! Вставьте туда ваш JSON ключ.")
else:
    init_db()
    menu = st.sidebar.radio("Навигация", ["Дашборд", "Переместить", "Добавить новое", "История"])

    if menu == "Дашборд":
        df = get_items()
        if not df.empty:
            st.subheader("Текущее наличие")
            search = st.text_input("Поиск (Модель, S/N)")
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("База данных пуста.")

    elif menu == "Добавить новое":
        st.subheader("Регистрация оборудования")
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Модель")
            type_ = c1.selectbox("Тип", TYPES)
            sn = c1.text_input("Серийный номер")
            loc = c2.selectbox("Местоположение", LOCATIONS)
            stat = c2.selectbox("Статус", ["Новый", "Рабочий", "В ремонте", "Пустой"])
            inf = c2.text_input("Характеристики / IP")
            if st.form_submit_button("Сохранить"):
                add_item(name, type_, sn, inf, loc, stat)

    elif menu == "Переместить":
        st.subheader("Отправка на месторождение / Ремонт")
        df = get_items()
        if not df.empty:
            options = df.apply(lambda x: f"{x['id']} | {x['name']} ({x['location']})", axis=1).tolist()
            selected = st.selectbox("Что перемещаем?", options)
            with st.form("move_form"):
                to_loc = st.selectbox("Куда", LOCATIONS)
                comm = st.text_input("Комментарий (Накладная / ФИО)")
                if st.form_submit_button("Подтвердить"):
                    move_item(selected.split(" | ")[0], to_loc, comm)

    elif menu == "История":
        st.subheader("Журнал событий")
        df_h = get_history()
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True)
