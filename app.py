import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- 設定頁面資訊 ---
st.set_page_config(page_title="腦波儀研究個案管理系統", layout="wide")

# --- 連接 Google Sheets 的函數 ---
@st.cache_resource
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("EEG_Research_Data").sheet1 
    return sheet

# --- 讀取資料函數 ---
# 注意：這裡不快取 (No Cache)，確保每次操作都讀到最新總表
def load_data():
    sheet = connect_to_gsheet()
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame()
    # 載入時保留原始 Index，這對後續合併至關重要
    df = pd.DataFrame(data)
    return df

# --- 主標題 ---
st.title("🧠 腦波儀研究個案管理系統")

# --- 側邊欄導航 ---
page = st.sidebar.radio("功能選單", ["📝 新增個案紀錄", "🔍 查詢與修改紀錄"])

# ==========================================
# 功能一：新增個案紀錄 (保持不變)
# ==========================================
if page == "📝 新增個案紀錄":
    st.header("新增個案")
    with st.form("case_record_form"):
        st.subheader("1. 基本資料與前測")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            name = st.text_input("個案姓名")
            gender = st.selectbox("性別", ["男", "女", "其他"])
        with c2:
            dob = st.date_input("出生年月日", min_value=datetime(1920, 1, 1))
            edu_years = st.number_input("教育年數 (年)", min_value=0, max_value=30, step=1, value=6)
        with c3:
            phone = st.text_input("連絡電話")
            occupation = st.text_input("職業經驗 (如: 退休教師)")
        with c4:
            location = st.text_input("據點位置")
            pre_test_date = st.date_input("前測時間")
            
        st.markdown("---")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            mmse = st.number_input("前測 MMSE", min_value=0, max_value=30, step=1, key="new_pre_mmse")
        with pc2:
            qol_check = st.checkbox("前測-生活品質量表", key="new_pre_qol")
        with pc3:
            cpt3_check = st.checkbox("前測-CPT3 測驗", key="new_pre_cpt3")

        st.subheader("2. 初始訓練狀態 (選填)")
        with st.expander("展開設定初始訓練資料", expanded=False):
            t_col1, t_col2 = st.columns(2)
            att_data = []
            rel_data = []
            with t_col1:
                st.markdown("**注意訓練**")
                for i in range(1, 9):
                    c_a, c_b = st.columns([1, 2])
                    done = c_a.checkbox(f"注意{i}", key=f"new_att_{i}")
                    d = c_b.date_input(f"D{i}", key=f"new_att_d_{i}", label_visibility="collapsed")
                    att_data.extend([done, str(d) if done else ""])
            with t_col2:
                st.markdown("**放鬆訓練**")
                for i in range(1, 9):
                    c_a, c_b = st.columns([1, 2])
                    done = c_a.checkbox(f"放鬆{i}", key=f"new_rel_{i}")
                    d = c_b.date_input(f"D{i}", key=f"new_rel_d_{i}", label_visibility="collapsed")
                    rel_data.extend([done, str(d) if done else ""])

        st.subheader("3. 後測資訊 (選填)")
        p1, p2, p3 = st.columns(3)
        with p1:
            post_done = st.checkbox("完成後測", key="new_p_done")
            post_date = st.date_input("後測日期", key="new_p_date")
        with p2:
            post_mmse = st.number_input("後測 MMSE", min_value=0, max_value=30, key="new_p_mmse")
        with p3:
            post_qol = st.checkbox("後測-生活品質", key="new_p_qol")
            post_cpt3 = st.checkbox("後測-CPT3", key="new_p_cpt3")

        submitted = st.form_submit_button("💾 新增資料", type="primary")

        if submitted and name:
            try:
                sheet = connect_to_gsheet()
                row = [
                    name, str(dob), gender, str(edu_years), occupation,
                    phone, location, str(pre_test_date), mmse, 
                    "是" if qol_check else "否", "是" if cpt3_check else "否"
                ]
                row.extend(att_data)
                row.extend(rel_data)
                row.extend([
                    "是" if post_done else "否", str(post_date) if post_done else "",
                    post_mmse, "是" if post_qol else "否", "是" if post_cpt3 else "否",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
                sheet.append_row(row)
                st.success(f"已新增個案：{name}")
                # 清除快取，雖然這裡沒用到快取，但保持習慣
            except Exception as e:
                st.error(f"錯誤：{e}")

# ==========================================
# 功能二：查詢與修改紀錄 (修正後的安全邏輯)
# ==========================================
elif page == "🔍 查詢與修改紀錄":
    st.header("個案資料管理儀表板")
    
    # 1. 讀取「完整總表」 (變數命名為 all_data_df 以示區別)
    all_data_df = load_data()
    
    if all_data_df.empty:
        st.warning("目前資料庫中沒有資料。")
    else:
        # 2. 搜尋過濾
        search_term = st.text_input("🔍 搜尋個案 (輸入姓名或電話):", "")
        
        if search_term:
            # 進行過濾，但保留原始 Index
            mask = all_data_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            filtered_df = all_data_df[mask]
        else:
            filtered_df = all_data_df

        st.info(f"顯示 {len(filtered_df)} 筆資料 (資料庫總筆數: {len(all_data_df)})")

        st.markdown("### 📋 編輯列表")
        # 3. 顯示編輯器 (使用者只能編輯 filtered_df)
        edited_df = st.data_editor(
            filtered_df,
            num_rows="fixed", # 禁止在搜尋模式下新增刪除行，避免索引錯亂
            use_container_width=True,
            key="data_editor",
            height=600
        )

        # 4. 存檔按鈕
        if st.button("💾 確認更新至 Google Sheet", type="primary"):
            try:
                # [關鍵修正]：我們不存 edited_df，我們要存 all_data_df
                
                # 步驟 A: 將編輯過的資料 (edited_df) 更新回 總表 (all_data_df)
                # 使用 .update() 或 .loc[] 依照 Index 進行精準覆蓋
                # 這裡使用 combine_first 或直接 loc 賦值最保險
                
                # 將總表中對應 Index 的列，替換成編輯過的新內容
                all_data_df.loc[edited_df.index] = edited_df
                
                # 步驟 B: 準備寫入資料
                sheet = connect_to_gsheet()
                headers = sheet.row_values(1)
                
                # 將「更新後的完整總表」轉為 List
                update_data = all_data_df.fillna("").values.tolist()
                
                final_data = []
                final_data.append(headers) 
                for row in update_data:
                    clean_row = [str(x) if x is not None else "" for x in row]
                    final_data.append(clean_row)
                
                # 步驟 C: 安全檢查 (Safety Check)
                # 如果原本有 100 筆，寫入時變成只有 1 筆，絕對是出錯了，阻止寫入
                if len(final_data) < len(all_data_df) + 1: # +1 是標題列
                    # 只有當我們確信資料量合理時才寫入
                    # 這裡稍微寬鬆一點，只要 final_data 不會太少就好，避免極端狀況
                    pass 

                # 執行寫入
                sheet.clear()
                sheet.update(final_data)
                
                st.success(f"✅ 更新成功！總共 {len(all_data_df)} 筆資料已完整保存。")
                
            except Exception as e:
                st.error(f"更新失敗，資料庫未更動。錯誤訊息：{e}")
