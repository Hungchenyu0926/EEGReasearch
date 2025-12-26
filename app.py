import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- 1. 設定頁面資訊 ---
st.set_page_config(page_title="腦波儀研究個案管理系統", layout="wide")

# --- 2. 連接 Google Sheets 的函數 ---
@st.cache_resource
def connect_to_gsheet():
    # 定義 Scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 從 Secrets 讀取憑證
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # 請確認您的試算表名稱是否正確
        sheet = client.open("EEG_Research_Data").sheet1 
        return sheet
    except Exception as e:
        st.error(f"連線失敗，請檢查 Secrets 設定: {e}")
        return None

# --- 3. 讀取資料函數 (無快取) ---
def load_data():
    sheet = connect_to_gsheet()
    if sheet:
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        return df
    return pd.DataFrame()

# --- 4. 主程式介面 ---
st.title("🧠 腦波儀研究個案管理系統")

# 側邊欄
page = st.sidebar.radio("功能選單", ["📝 新增個案紀錄", "🔍 查詢與修改紀錄"])

# ==========================================
# 分頁一：新增個案紀錄
# ==========================================
if page == "📝 新增個案紀錄":
    st.header("新增個案資料")
    
    with st.form("case_record_form"):
        st.subheader("1. 基本資料")
        
        # --- 第一列：核心識別資料 (姓名、性別、分組) ---
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("個案姓名 (必填)")
        with c2:
            gender = st.selectbox("性別", ["男", "女", "其他"])
        with c3:
            # [修正重點] 將分組移到這裡，確保顯眼
            group = st.selectbox("📌 分組 (實驗/控制)", ["實驗組", "控制組"])

        # --- 第二列：背景資料 (生日、教育、職業) ---
        c4, c5, c6 = st.columns(3)
        with c4:
            dob = st.date_input("出生年月日", min_value=datetime(1920, 1, 1))
        with c5:
            edu_years = st.number_input("教育年數 (年)", min_value=0, max_value=30, value=6)
        with c6:
            occupation = st.text_input("職業經驗 (例如: 退休公務員)")

        # --- 第三列：聯絡與地點 ---
        c7, c8, c9 = st.columns(3)
        with c7:
            phone = st.text_input("連絡電話")
        with c8:
            location = st.text_input("據點位置")
        with c9:
            pre_test_date = st.date_input("前測時間")
            
        st.markdown("---")
        st.subheader("2. 前測數據")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            mmse = st.number_input("前測 MMSE 分數", min_value=0, max_value=30, step=1, key="new_pre_mmse")
        with pc2:
            qol_check = st.checkbox("前測-生活品質量表 完成", key="new_pre_qol")
        with pc3:
            cpt3_check = st.checkbox("前測-CPT3 測驗 完成", key="new_pre_cpt3")

        st.subheader("3. 初始訓練狀態 (新增時通常留白)")
        with st.expander("點擊展開 設定初始訓練資料", expanded=False):
            t_col1, t_col2 = st.columns(2)
            att_data = []
            rel_data = []
            
            with t_col1:
                st.markdown("**🧘 注意訓練 (Attention)**")
                for i in range(1, 9):
                    col_a, col_b = st.columns([1, 2])
                    done = col_a.checkbox(f"注意{i}", key=f"new_att_{i}")
                    d = col_b.date_input(f"D{i}", key=f"new_att_d_{i}", label_visibility="collapsed")
                    att_data.extend([done, str(d) if done else ""])
            
            with t_col2:
                st.markdown("**🌊 放鬆訓練 (Relaxation)**")
                for i in range(1, 9):
                    col_a, col_b = st.columns([1, 2])
                    done = col_a.checkbox(f"放鬆{i}", key=f"new_rel_{i}")
                    d = col_b.date_input(f"D{i}", key=f"new_rel_d_{i}", label_visibility="collapsed")
                    rel_data.extend([done, str(d) if done else ""])

        st.subheader("4. 後測資訊 (選填)")
        p1, p2, p3 = st.columns(3)
        with p1:
            post_done = st.checkbox("完成後測", key="new_p_done")
            post_date = st.date_input("後測日期", key="new_p_date")
        with p2:
            post_mmse = st.number_input("後測 MMSE 分數", min_value=0, max_value=30, key="new_p_mmse")
        with p3:
            post_qol = st.checkbox("後測-生活品質", key="new_p_qol")
            post_cpt3 = st.checkbox("後測-CPT3", key="new_p_cpt3")

        # --- 送出按鈕 ---
        submitted = st.form_submit_button("💾 確認新增個案", type="primary")

        if submitted:
            if not name:
                st.error("❌ 錯誤：請務必填寫個案姓名")
            else:
                try:
                    sheet = connect_to_gsheet()
                    if sheet:
                        # [重要] 這裡的順序必須跟 Google Sheet 的標題欄完全一致
                        # 目前設定：姓名, 生日, 性別, 分組, 教育, 職業, 電話...
                        row = [
                            name, 
                            str(dob), 
                            gender, 
                            group,          # 這裡寫入分組
                            str(edu_years), 
                            occupation,
                            phone, 
                            location, 
                            str(pre_test_date), 
                            mmse, 
                            "是" if qol_check else "否", 
                            "是" if cpt3_check else "否"
                        ]
                        
                        # 加入訓練與後測資料
                        row.extend(att_data)
                        row.extend(rel_data)
                        row.extend([
                            "是" if post_done else "否", 
                            str(post_date) if post_done else "",
                            post_mmse, 
                            "是" if post_qol else "否", 
                            "是" if post_cpt3 else "否",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                        
                        sheet.append_row(row)
                        st.success(f"✅ 成功新增：{name} ({group})")
                        # 強制清除快取，讓查詢頁面能馬上看到新資料
                        st.cache_data.clear()
                except Exception as e:
                    st.error(f"儲存失敗：{e}")

# ==========================================
# 分頁二：查詢與修改紀錄
# ==========================================
elif page == "🔍 查詢與修改紀錄":
    st.header("📋 個案資料管理儀表板")
    
    # 讀取完整資料
    all_data_df = load_data()
    
    if all_data_df.empty:
        st.warning("目前資料庫中沒有資料，請先新增個案。")
    else:
        # 搜尋功能
        st.markdown("##### 搜尋過濾器")
        search_term = st.text_input("輸入姓名或電話進行搜尋:", placeholder="例如: 王大明")
        
        if search_term:
            # 搜尋邏輯 (保留 Index)
            mask = all_data_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            filtered_df = all_data_df[mask]
        else:
            filtered_df = all_data_df

        st.info(f"顯示 {len(filtered_df)} 筆資料 (總計: {len(all_data_df)} 筆)")

        # 顯示編輯器
        # 設定 Column Config 讓 "分組" 變成選單
        edited_df = st.data_editor(
            filtered_df,
            num_rows="fixed", # 禁止在此模式新增刪除列，確保安全
            use_container_width=True,
            key="data_editor_main",
            height=500,
            column_config={
                "分組": st.column_config.SelectboxColumn(
                    "分組",
                    help="選擇實驗組或控制組",
                    width="medium",
                    options=[
                        "實驗組",
                        "控制組",
                    ],
                    required=True,
                )
            }
        )

        st.markdown("---")
        # 存檔按鈕
        if st.button("💾 確認修改並更新至資料庫", type="primary"):
            try:
                sheet = connect_to_gsheet()
                
                # 1. 更新邏輯：將編輯過的資料 (edited_df) 覆蓋回 總表 (all_data_df)
                # 使用 Index 對應，確保沒被搜尋到的資料不會遺失
                all_data_df.loc[edited_df.index] = edited_df
                
                # 2. 準備寫入
                headers = sheet.row_values(1) # 讀取原始標題
                
                # 將 DataFrame 轉為 List
                update_data = all_data_df.fillna("").values.tolist()
                
                final_data = []
                final_data.append(headers) # 放入標題
                for row in update_data:
                    clean_row = [str(x) if x is not None else "" for x in row]
                    final_data.append(clean_row)
                
                # 3. 安全檢查：防止資料意外歸零
                if len(final_data) >= len(all_data_df) + 1:
                    sheet.clear()
                    sheet.update(final_data)
                    st.success(f"✅ 更新成功！所有變更已儲存。")
                    st.cache_data.clear() # 清除快取
                else:
                    st.error("❌ 更新中止：偵測到資料量異常減少，為保護資料已停止寫入。請聯絡管理員。")
                
            except Exception as e:
                st.error(f"❌ 更新失敗：{e}")




