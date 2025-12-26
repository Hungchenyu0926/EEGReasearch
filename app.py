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

# --- 讀取資料函數 (不快取，確保拿到最新資料) ---
def load_data():
    sheet = connect_to_gsheet()
    # 取得所有資料，expected_headers 確保欄位順序正確
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    return df

# --- 主標題 ---
st.title("🧠 腦波儀研究個案管理系統")

# --- 側邊欄導航 ---
page = st.sidebar.radio("功能選單", ["📝 新增個案紀錄", "🔍 查詢與修改紀錄"])

# ==========================================
# 功能一：新增個案紀錄 (維持原本邏輯，稍作精簡)
# ==========================================
if page == "📝 新增個案紀錄":
    st.header("新增個案")
    with st.form("case_record_form"):
        st.subheader("1. 基本資料與前測")
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("個案姓名")
            gender = st.selectbox("性別", ["男", "女", "其他"])
            location = st.text_input("據點位置")
        with c2:
            dob = st.date_input("出生年月日", min_value=datetime(1920, 1, 1))
            phone = st.text_input("連絡電話")
            pre_test_date = st.date_input("前測時間")
        with c3:
            mmse = st.number_input("前測 MMSE", min_value=0, max_value=30, step=1, key="new_pre_mmse")
            qol_check = st.checkbox("前測-生活品質量表", key="new_pre_qol")
            cpt3_check = st.checkbox("前測-CPT3 測驗", key="new_pre_cpt3")

        st.subheader("2. 初始訓練狀態 (選填)")
        with st.expander("展開設定初始訓練資料 (通常新增時留白)", expanded=False):
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
                # 建構資料列 (請確保順序與 Google Sheet 欄位一致)
                row = [
                    name, str(dob), gender, phone, location, str(pre_test_date), 
                    mmse, "是" if qol_check else "否", "是" if cpt3_check else "否"
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
                st.cache_data.clear() # 清除快取以確保查詢頁面看到新資料
            except Exception as e:
                st.error(f"錯誤：{e}")

# ==========================================
# 功能二：查詢與修改紀錄 (儀表板 + 編輯器)
# ==========================================
elif page == "🔍 查詢與修改紀錄":
    st.header("個案資料管理儀表板")
    
    # 1. 讀取資料
    df = load_data()
    
    if df.empty:
        st.warning("目前資料庫中沒有資料。")
    else:
        # 2. 搜尋過濾器
        search_term = st.text_input("🔍 搜尋個案 (輸入姓名或電話):", "")
        
        if search_term:
            # 簡單的模糊搜尋
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            filtered_df = df[mask]
        else:
            filtered_df = df

        st.info(f"共找到 {len(filtered_df)} 筆資料 (總數: {len(df)})")

        # 3. 資料編輯器 (Data Editor)
        # 這是一個強大的元件，允許像 Excel 一樣編輯
        st.markdown("### 📋 編輯列表 (直接點擊儲存格修改)")
        st.markdown("*提示：修改完畢後，請務必點擊下方的「確認更新」按鈕以寫入資料庫*")
        
        edited_df = st.data_editor(
            filtered_df,
            num_rows="dynamic", # 允許新增刪除行
            use_container_width=True,
            key="data_editor",
            height=600
        )

        # 4. 更新按鈕邏輯
        if st.button("💾 確認更新至 Google Sheet", type="primary"):
            try:
                sheet = connect_to_gsheet()
                
                # 為了安全起見，我們採取「全量更新」或「尋找更新」
                # 這裡示範最簡單的：將 DataFrame 轉回 List 並覆蓋 Sheet
                # 注意：這適合資料量在幾千筆以內。如果資料量巨大，需要改用 Cell Update。
                
                # 取得原本的標題 (Headers)
                headers = sheet.row_values(1)
                
                # 準備要寫入的資料 (將 DataFrame 轉為 List of Lists)
                # 處理 NaN 或 NaT 的空值問題
                update_data = edited_df.fillna("").values.tolist()
                
                # 確保格式正確 (全是字串或數字)
                final_data = []
                final_data.append(headers) # 先放標題
                for row in update_data:
                    # 將每個元素轉為適合寫入的格式
                    clean_row = [str(x) if x is not None else "" for x in row]
                    final_data.append(clean_row)
                
                # 清空舊資料並寫入新資料
                sheet.clear()
                sheet.update(final_data)
                
                st.success("✅ 資料庫已更新完畢！")
                st.cache_resource.clear() # 清除連線快取
                
            except Exception as e:
                st.error(f"更新失敗：{e}")

    # (選擇性) 簡單統計儀表板
    st.markdown("---")
    st.subheader("📊 快速統計")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("總個案數", len(df))
        
        # 計算前測平均 MMSE (排除空值或非數字)
        try:
            mmse_avg = pd.to_numeric(df["前測MMSE分數"], errors='coerce').mean()
            c2.metric("前測 MMSE 平均", f"{mmse_avg:.1f}")
        except:
            c2.metric("前測 MMSE 平均", "N/A")
            
        # 計算完訓人數 (假設第8次注意訓練完成即算完訓)
        # 注意：需確認您的欄位名稱是否為 '注意訓練8_完成' (請依實際 Google Sheet 標題調整)
        try:
            # 這裡假設您 Google Sheet 裡標題叫做 "注意訓練8_完成" 且值為 "TRUE"/"FALSE"
            # 您可能需要根據實際欄位名稱調整
            completed = df[df.columns[df.columns.str.contains("注意訓練8_完成")]].isin(["TRUE", "True", "是", True]).sum().sum()
            c3.metric("完成8次注意訓練人數", int(completed))
        except:
            pass
