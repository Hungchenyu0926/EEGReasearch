import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- 1. 設定頁面資訊 (強制寬版模式) ---
st.set_page_config(page_title="腦波儀研究個案管理系統", layout="wide")

# --- 2. 連接 Google Sheets 的函數 ---
@st.cache_resource
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("EEG_Research_Data").sheet1 
        return sheet
    except Exception as e:
        st.error(f"連線失敗，請檢查 Secrets: {e}")
        return None

# --- 3. 讀取資料函數 ---
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
        c1, c2, c3 = st.columns(3)
        with c1: name = st.text_input("個案姓名 (必填)")
        with c2: gender = st.selectbox("性別", ["男", "女", "其他"])
        with c3: group = st.selectbox("📌 分組", ["實驗組", "控制組"])

        c4, c5, c6 = st.columns(3)
        with c4: dob = st.date_input("出生年月日", min_value=datetime(1920, 1, 1))
        with c5: edu_years = st.number_input("教育年數", min_value=0, value=6)
        with c6: occupation = st.text_input("職業經驗")

        c7, c8, c9 = st.columns(3)
        with c7: phone = st.text_input("連絡電話")
        with c8: location = st.text_input("據點位置")
        with c9: pre_test_date = st.date_input("前測時間")
            
        st.markdown("---")
        st.subheader("2. 前測數據")
        pc1, pc2, pc3 = st.columns(3)
        with pc1: mmse = st.number_input("前測 MMSE", min_value=0, max_value=30, step=1, key="new_pre_mmse")
        with pc2: qol_check = st.checkbox("前測-生活品質量表", key="new_pre_qol")
        with pc3: cpt3_check = st.checkbox("前測-CPT3 測驗", key="new_pre_cpt3")

        st.markdown("---")
        # =========================================================
        # [修正重點] 訓練紀錄區塊 - 強制 6 欄位排版
        # =========================================================
        st.subheader("3. 訓練紀錄 (含時間)")
        st.info("填寫說明：請依序填寫 [是否完成] -> [日期] -> [時間長度]")
        
        training_data_list = []

        with st.expander("點擊展開 詳細訓練紀錄表", expanded=True):
            # 標題列 (讓使用者知道欄位是什麼)
            h1, h2, h3, h_space, h4, h5, h6 = st.columns([0.7, 1.2, 1.2, 0.2, 0.7, 1.2, 1.2])
            h1.markdown("**🧘 注意-完成**")
            h2.markdown("**日期**")
            h3.markdown("**時間/長度**")
            h4.markdown("**🌊 放鬆-完成**")
            h5.markdown("**日期**")
            h6.markdown("**時間/長度**")

            for i in range(1, 9):
                # 這裡將一行切成 7 份 (中間加一個 0.2 的空白間隔，區分左右)
                # 比例：[勾選框, 日期, 時間] ---空白--- [勾選框, 日期, 時間]
                cols = st.columns([0.7, 1.2, 1.2, 0.2, 0.7, 1.2, 1.2])
                
                # --- 左側：注意訓練 ---
                with cols[0]:
                    att_done = st.checkbox(f"注意{i}", key=f"att_done_{i}")
                with cols[1]:
                    att_date = st.date_input(f"d{i}", key=f"att_date_{i}", label_visibility="collapsed")
                with cols[2]:
                    # 這裡就是消失的欄位，現在強制給它空間
                    att_time = st.text_input(f"t{i}", placeholder="例如:30min", key=f"att_time_{i}", label_visibility="collapsed")
                
                # --- 右側：放鬆訓練 ---
                with cols[4]:
                    rel_done = st.checkbox(f"放鬆{i}", key=f"rel_done_{i}")
                with cols[5]:
                    rel_date = st.date_input(f"rd{i}", key=f"rel_date_{i}", label_visibility="collapsed")
                with cols[6]:
                    rel_time = st.text_input(f"rt{i}", placeholder="例如:30min", key=f"rel_time_{i}", label_visibility="collapsed")

                # 收集資料 (順序很重要：注意完成 -> 注意日期 -> 注意時間 -> 放鬆完成 -> 放鬆日期 -> 放鬆時間)
                training_data_list.extend([
                    "是" if att_done else "", 
                    str(att_date) if att_done else "", 
                    att_time if att_done else "",
                    "是" if rel_done else "", 
                    str(rel_date) if rel_done else "", 
                    rel_time if rel_done else ""
                ])
                
                # 視覺分隔線
                st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #444;'>", unsafe_allow_html=True)

        st.subheader("4. 後測資訊")
        p1, p2, p3 = st.columns(3)
        with p1:
            post_done = st.checkbox("完成後測", key="new_p_done")
            post_date = st.date_input("後測日期", key="new_p_date")
        with p2:
            post_mmse = st.number_input("後測 MMSE", min_value=0, max_value=30, key="new_p_mmse")
        with p3:
            post_qol = st.checkbox("後測-生活品質", key="new_p_qol")
            post_cpt3 = st.checkbox("後測-CPT3", key="new_p_cpt3")

        submitted = st.form_submit_button("💾 確認新增個案", type="primary")

        if submitted:
            if not name:
                st.error("請填寫姓名")
            else:
                try:
                    sheet = connect_to_gsheet()
                    if sheet:
                        # 1. 基本資料
                        row = [
                            name, str(dob), gender, group, str(edu_years), occupation,
                            phone, location, str(pre_test_date), 
                            mmse, "是" if qol_check else "否", "是" if cpt3_check else "否"
                        ]
                        
                        # 2. 加入交錯的訓練資料 (包含時間)
                        row.extend(training_data_list)
                        
                        # 3. 加入後測資料
                        row.extend([
                            "是" if post_done else "否", str(post_date) if post_done else "",
                            post_mmse, "是" if post_qol else "否", "是" if post_cpt3 else "否",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                        
                        sheet.append_row(row)
                        st.success(f"✅ 成功新增：{name}")
                        st.cache_data.clear()
                except Exception as e:
                    st.error(f"錯誤：{e}")

# ==========================================
# 分頁二：查詢與修改紀錄
# ==========================================
elif page == "🔍 查詢與修改紀錄":
    st.header("📋 個案資料管理儀表板")
    
    all_data_df = load_data()
    
    if all_data_df.empty:
        st.warning("資料庫無資料")
    else:
        search_term = st.text_input("輸入姓名或電話搜尋:", "")
        
        if search_term:
            mask = all_data_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
            filtered_df = all_data_df[mask]
        else:
            filtered_df = all_data_df

        st.info(f"顯示 {len(filtered_df)} 筆")

        # 這裡的 data_editor 會自動抓取您 Google Sheet 的所有欄位 (包含新的時間欄位)
        edited_df = st.data_editor(
            filtered_df,
            num_rows="fixed", 
            use_container_width=True,
            key="data_editor_main",
            height=600,
            column_config={
                "分組": st.column_config.SelectboxColumn(
                    "分組",
                    options=["實驗組", "控制組"],
                    required=True,
                )
            }
        )

        if st.button("💾 確認修改並更新至資料庫", type="primary"):
            try:
                sheet = connect_to_gsheet()
                all_data_df.loc[edited_df.index] = edited_df
                
                headers = sheet.row_values(1)
                update_data = all_data_df.fillna("").values.tolist()
                
                final_data = []
                final_data.append(headers)
                for row in update_data:
                    clean_row = [str(x) if x is not None else "" for x in row]
                    final_data.append(clean_row)
                
                if len(final_data) >= len(all_data_df) + 1:
                    sheet.clear()
                    sheet.update(final_data)
                    st.success("✅ 更新成功！")
                    st.cache_data.clear()
                else:
                    st.error("資料量異常，已中止更新。")
                
            except Exception as e:
                st.error(f"更新失敗：{e}")




