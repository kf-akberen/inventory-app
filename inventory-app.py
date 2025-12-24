import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- КОНФИГУРАЦИЯ ---
SHEET_NAME = "inventory_db" 
USER_LOGIN = "admin"
USER_PASSWORD = "123" # Смените на свой

LOCATIONS = ["Офис (Кызылорда)", "Склад", "Ремонт", "Ак Берен", "Кумколь", "Арыскум", "Амангельды"]
TYPES = ["Картридж", "Мышь", "Клавиатура", "Монитор", "Принтер", "МФУ", "Ноутбук"]

# --- СТИЛИЗАЦИЯ ПОД МОБИЛКУ ---
def local_css():
    st.markdown("""
        <style>
        /* Общий фон */
        .stApp { background-color: #0E1117; }
        
        /* Кнопки на весь экран */
        div.stButton > button:first-child {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: #2E7D32;
            border: none;
            font-weight: bold;
        }
        
        /* Карточки для Дашборда */
        .inventory-card {
            background-color: #1E1E1E;
            padding: 15px;
            border-radius: 12px;
            border-left: 5px solid #4CAF50;
            margin-bottom: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        }
        
        .card-title { color: #FFFFFF; font-size: 18px; font-weight: bold; }
        .card-subtitle { color: #AAAAAA; font-size: 14px; }
        .card-tag { 
            background: #333; padding: 2px 8px; border-radius: 5px; 
            font-size: 12px; color: #4CAF50; border: 1px solid #4CAF50;
        }

        /* Прячем лишние элементы интерфейса Streamlit на мобилках */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 1rem;}
        </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ПОДКЛЮЧЕНИЯ ---
def connect_to_gsheets():
    key_dict = json.loads(st.secrets["textkey"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    return gspread.authorize(creds).open(SHEET_NAME)

def add_log(action, details):
    sh = connect_to_gsheets()
    ws = sh.worksheet("history")
    ws.append_row([len(ws.col_values(1)), datetime.now().strftime("%d.%m %H:%M"), st.session_state.username, action, details])

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="AkBeren IT", layout="centered")
local_css()

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center;'>🔐 IT Inventory</h2>", unsafe_allow_html=True)
    with st.container():
        l = st.text_input("Логин")
        p = st.text_input("Пароль", type="password")
        if st.button("ВОЙТИ"):
            if l == USER_LOGIN and p == USER_PASSWORD:
                st.session_state.auth = True
                st.session_state.username = l
                st.rerun()
            else: st.error("Ошибка входа")
else:
    # Мобильное меню вверху вместо боковой панели
    menu = st.selectbox("📌 Раздел", ["📱 Склад", "➕ Добавить", "🚚 Переместить", "📜 Логи"])

    if menu == "📱 Склад":
        sh = connect_to_gsheets()
        df = pd.DataFrame(sh.worksheet("items").get_all_records())
        
        search = st.text_input("🔍 Поиск по S/N или названию")
        
        if not df.empty:
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
            for _, row in df.iloc[::-1].iterrows():
                st.markdown(f"""
                <div class="inventory-card">
                    <div class="card-title">{row['name']}</div>
                    <div class="card-subtitle">S/N: {row['serial_number']}</div>
                    <div style="margin-top:8px;">
                        <span class="card-tag">{row['location']}</span>
                        <span class="card-tag" style="color:#FFA000; border-color:#FFA000;">{row['status']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    elif menu == "➕ Добавить":
        with st.form("add_form", clear_on_submit=True):
            st.subheader("Новое устройство")
            n = st.text_input("Модель / Название")
            t = st.selectbox("Тип", TYPES)
            sn = st.text_input("Серийный номер")
            loc = st.selectbox("Локация", LOCATIONS)
            if st.form_submit_button("СОХРАНИТЬ"):
                ws = connect_to_gsheets().worksheet("items")
                ws.append_row([len(ws.col_values(1)), n, t, sn, "", loc, "Новый", datetime.now().strftime("%Y-%m-%d")])
                add_log("ДОБАВЛЕНИЕ", f"{n} ({sn})")
                st.success("Готово!")

    elif menu == "🚚 Переместить":
        sh = connect_to_gsheets()
        df = pd.DataFrame(sh.worksheet("items").get_all_records())
        if not df.empty:
            item_map = {f"{r['id']} | {r['name']}": r['id'] for _, r in df.iterrows()}
            selected = st.selectbox("Выберите устройство", list(item_map.keys()))
            to_loc = st.selectbox("Куда переместить", LOCATIONS)
            comm = st.text_input("Комментарий")
            if st.button("ПОДТВЕРДИТЬ ПЕРЕМЕЩЕНИЕ"):
                ws = sh.worksheet("items")
                cell = ws.find(str(item_map[selected]))
                ws.update_cell(cell.row, 6, to_loc)
                add_log("ПЕРЕМЕЩЕНИЕ", f"ID {item_map[selected]} -> {to_loc} ({comm})")
                st.success("Местоположение обновлено!")

    elif menu == "📜 Логи":
        st.subheader("История действий")
        sh = connect_to_gsheets()
        log_df = pd.DataFrame(sh.worksheet("history").get_all_records())
        st.write(log_df.iloc[::-1])

    if st.sidebar.button("Выход"):
        st.session_state.auth = False
        st.rerun()
