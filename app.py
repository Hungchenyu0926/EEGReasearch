import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- 設定頁面資訊 ---
st.set_page_config(page_title="腦波儀研究個案紀錄", layout="wide")

# --- 連接 Google Sheets 的函數 ---
@st.cache_resource
def connect_to_gsheet():
    # 定義 Scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 從 Streamlit Secrets 讀取憑證
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # 開啟試算表
    sheet = client.open("EEG_Research_Data").sheet1 
    return sheet

# --- 主標題 ---
st.title("🧠 腦波儀研究個案紀錄系統")
st.markdown("---")

# --- 建立表單 ---
with st.form("case_record_form"):
    st.subheader("📋 基本資料與前測")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("個案姓名")
        gender = st.selectbox("性別", ["男", "女", "其他"])
        location = st.text_input("據點位置")
    with col2:
        dob = st.date_input("出生年月日", min_value=datetime(1920, 1, 1))
        phone = st.text_input("連絡電話")
        pre_test_date = st.date_input("前測時間")
    with col3:
        mmse = st.number_input("前測 MMSE 分數", min_value=0, max_value=30, step=1, key="pre_mmse")
        qol_check = st.checkbox("已做過 前測-生活品質量表", key="pre_qol")
        cpt3_check = st.checkbox("已做過 前測-CPT3 測驗", key="pre_cpt3")

    st.markdown("---")
    st.subheader("🏋️ 訓練紀錄 (第1次 - 第8次)")

    with st.expander("點擊展開/收合 詳細訓練紀錄", expanded=True):
        t_col1, t_col2 = st.columns(2)
        
        att_data = [] 
        rel_data = [] 

        with t_col1:
            st.markdown("#### 🧘 注意訓練 (Attention)")
            for i in range(1, 9):
                c1, c2 = st.columns([1, 2])
                done = c1.checkbox(f"注意第 {i} 次", key=f"att_done_{i}")
                date = c2.date_input(f"日期", key=f"att_date_{i}", label_visibility="collapsed")
                att_data.extend([done, str(date) if done else ""]) 

        with t_col2:
            st.markdown("#### 🌊 放鬆訓練 (Relaxation)")
            for i in range(1, 9):
                c1, c2 = st.columns([1, 2])
                done = c1.checkbox(f"放鬆第 {i} 次", key=f"rel_done_{i}")
                date = c2.date_input(f"日期", key=f"rel_date_{i}", label_visibility="collapsed")
                rel_data.extend([done, str(date) if done else ""])

    st.markdown("---")
    st.subheader("🏁 後測資訊")
    
    # 修改處：重新佈局後測欄位，分為「狀態」與「測驗結果」
    p_col1, p_col2, p_col3 = st.columns(3)
    
    with p_col1:
        post_test_done = st.checkbox("是否完成後測")
        post_test_date = st.date_input("後測時間")
        
    with p_col2:
        # 新增後測 MMSE
        post_mmse = st.number_input("後測 MMSE 分數", min_value=0, max_value=30, step=1, key="post_mmse")
    
    with p_col3:
        # 新增後測量表狀態
        post_qol_check = st.checkbox("已做過 後測-生活品質量表", key="post_qol")
        post_cpt3_check = st.checkbox("已做過 後測-CPT3 測驗", key="post_cpt3")

    # --- 送出按鈕 ---
    submitted = st.form_submit_button("💾 儲存資料至 Google Sheet", type="primary")

    if submitted:
        if not name:
            st.error("請填寫個案姓名！")
        else:
            try:
                sheet = connect_to_gsheet()
                
                # 整理基本資料與前測
                row_data = [
                    name, 
                    str(dob), 
                    gender, 
                    phone, 
                    location,
                    str(pre_test_date),
                    mmse,
                    "是" if qol_check else "否",
                    "是" if cpt3_check else "否"
                ]
                
                # 加入訓練資料
                row_data.extend(att_data)
                row_data.extend(rel_data)
                
                # 修改處：加入完整的後測資料邏輯
                # 這裡的順序必須對應 Google Sheet 新的標題列順序
                row_data.extend([
                    "是" if post_test_done else "否",
                    str(post_test_date) if post_test_done else "",
                    post_mmse,                            # 新增：後測 MMSE
                    "是" if post_qol_check else "否",     # 新增：後測 QoL
                    "是" if post_cpt3_check else "否",    # 新增：後測 CPT3
                    str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) # 填表時間
                ])

                sheet.append_row(row_data)
                st.success(f"✅ 個案 {name} 的資料（含後測數據）已成功儲存！")
                
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# 資料預覽區塊
with st.expander("查看目前已存資料"):
    try:
        sheet = connect_to_gsheet()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        st.dataframe(df)
    except:
        st.info("尚無資料或連線未建立")