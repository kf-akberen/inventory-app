import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- КОНФИГУРАЦИЯ ---
SHEET_NAME = "inventory_db" 
# Задайте ваши данные для входа здесь
USER_LOGIN = "admin"
USER_PASSWORD = "it_admin_password" # Измените на свой

LOCATIONS = [
    "Офис (Кызылорда)", "Склад", "Ремонт/Заправка",
    "Месторождение «Ак Берен»", "Месторождение «Кумколь»", "Месторождение «Арыскум»",
    "Месторождение «Акыртобе, Полторацкое»", "Месторождение «Амангельды»",
    "Месторождение «Акшабулак»", "Месторождение «Бектас и Коныс»"
]

TYPES = ["Картридж", "Мышь", "Клавиатура", "Монитор", "Принтер", "МФУ", "Ноутбук", "Прочее"]

# --- ПОДКЛЮЧЕНИЕ ---
def connect_to_gsheets():
    key_dict = json.loads(st.secrets["textkey"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME)

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def get_items():
    sh = connect_to_gsheets()
    return pd.DataFrame(sh.worksheet("items").get_all_records())

def add_log(action_type, details):
    """Записывает действие пользователя в лист истории"""
    sh = connect_to_gsheets()
    ws_hist = sh.worksheet("history")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = st.session_state.get("username", "Unknown")
    ws_hist.append_row([len(ws_hist.col_values(1)), timestamp, user, action_type, details])

def add_item(name, item_type, serial, specs, location, status):
    sh = connect_to_gsheets()
    ws = sh.worksheet("items")
    new_id = len(ws.col_values(1))
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([new_id, name, item_type, str(serial), str(specs), location, status, created_at])
    add_log("ДОБАВЛЕНИЕ", f"Добавлен {name} (SN: {serial}) в {location}")
    st.success(f"✅ Добавлено: {name}")

def move_item(item_id, new_location, comment):
    sh = connect_to_gsheets()
    ws_items = sh.worksheet("items")
    cell = ws_items.find(str(item_id))
    if cell:
        row = cell.row
        name = ws_items.cell(row, 2).value
        old_loc = ws_items.cell(row, 6).value
        ws_items.update_cell(row, 6, new_location)
        add_log("ПЕРЕМЕЩЕНИЕ", f"{name} перемещен из {old_loc} в {new_location}. Коммент: {comment}")
        st.success(f"🚚 {name} успешно перемещен!")

# --- СИСТЕМА АВТОРИЗАЦИИ ---
def check_password():
    """Возвращает True, если пароль верный"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Вход в систему")
        login = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        if st.button("Войти"):
            if login == USER_LOGIN and password == USER_PASSWORD:
                st.session_state["authenticated"] = True
                st.session_state["username"] = login
                st.rerun()
            else:
                st.error("❌ Неверный логин или пароль")
        return False
    return True

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
st.set_page_config(page_title="Cloud Inventory", layout="wide")

if check_password():
    st.title("📦 IT Учет: Ак Берен (Защищенный)")
    
    menu = st.sidebar.radio("Меню", ["Дашборд", "Переместить", "Добавить новое", "Логи (История)"])

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

    elif menu == "Логи (История)":
        st.subheader("📜 Журнал действий пользователей")
        sh = connect_to_gsheets()
        log_df = pd.DataFrame(sh.worksheet("history").get_all_records())
        if not log_df.empty:
            st.dataframe(log_df.iloc[::-1], use_container_width=True) # Показываем свежие записи сверху
