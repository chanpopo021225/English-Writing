import streamlit as st
import pandas as pd
import io

# --- 页面基础设置 ---
st.set_page_config(
    page_title="英语作文交互式批改工具",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ 英语作文交互式批改工具")

# --- 初始化 Session State ---
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'scores' not in st.session_state:
    st.session_state.scores = {}
if 'df' not in st.session_state:
    st.session_state.df = None
# --- 新增 ---: 初始化作文题目存储
if 'essay_prompt' not in st.session_state:
    st.session_state.essay_prompt = ""

# --- 新增功能：输入作文题目 ---
st.header("第一步：输入作文题目")
# 使用 text_area 允许输入多行文本，更适合作文要求
# 将输入框的值与 session_state 绑定，这样即使页面刷新，输入的内容也不会丢失
prompt_input = st.text_area(
    "在此处粘贴或输入本次作文的题目和要求：",
    height=150,
    value=st.session_state.essay_prompt, # 绑定值
    help="在这里输入作文题目、写作要求、字数限制等信息。"
)
# 实时更新 session_state 中的作文题目
st.session_state.essay_prompt = prompt_input


st.header("第二步：上传学生作文文件")
st.write("请在下方上传包含学生作文信息的 XLSX 文件开始批改。")
# --- 文件上传 ---
uploaded_file = st.file_uploader("上传XLSX文件", type=["xlsx"])

if uploaded_file is not None:
    # 避免重复加载和重置
    # 只有当上传了新文件时，才重新加载和重置状态
    try:
        temp_df = pd.read_excel(uploaded_file)
        # 检查是否是新文件，或者 session_state.df 还未初始化
        if st.session_state.df is None or not st.session_state.df.equals(temp_df):
            df = temp_df
            required_columns = ['学生作答图片1', '学生作答图片2', '评分标准']
            if not all(col in df.columns for col in required_columns):
                st.error(f"上传的文件缺少必要的列。请确保文件包含以下中文列: {', '.join(required_columns)}")
                st.stop()
            
            st.session_state.df = df
            st.session_state.current_index = 0
            st.session_state.scores = [-1] * len(df)
            st.success("文件加载成功！现在可以开始批改。")
            st.rerun() # 成功加载后立即刷新，以确保界面显示正确
    except Exception as e:
        st.error(f"文件读取失败: {e}")
        st.stop()

# --- 主批改界面 ---
if st.session_state.df is not None:
    df = st.session_state.df
    total_students = len(df)
    
    # 检查索引是否有效，防止切换文件后索引越界
    if st.session_state.current_index >= total_students:
        st.session_state.current_index = 0

    current_student = df.iloc[st.session_state.current_index]

    col1, col2 = st.columns([3, 1])

    with col1:
        st.header(f"批改中：第 {st.session_state.current_index + 1} / {total_students} 份")
        
        # --- 修改点：在这里展示作文题目 ---
        if st.session_state.essay_prompt: # 仅当用户输入了题目时才显示
            with st.expander("📌 查看作文题目", expanded=True):
                st.markdown(st.session_state.essay_prompt)
        
        with st.expander("📝 点击查看评分标准", expanded=False): # 默认折叠评分标准，节省空间
            st.markdown(current_student['评分标准'])

        st.subheader("学生作答图片 1")
        st.image(current_student['学生作答图片1'], use_container_width=True)

        st.subheader("学生作答图片 2")
        st.image(current_student['学生作答图片2'], use_container_width=True)
        
    with col2:
        st.header("评分操作区")

        tier_options = {
            "差 (2分档)": 2,
            "中下 (5分档)": 5,
            "中等 (8分档)": 8,
            "中上 (11分档)": 11,
            "优 (14分档)": 14
        }
        
        selected_tier_label = st.radio(
            "第一步：选择评分档位",
            options=tier_options.keys(),
            key=f"tier_radio_{st.session_state.current_index}"
        )
        
        default_score = tier_options[selected_tier_label]

        current_score_val = st.session_state.scores[st.session_state.current_index]
        
        final_score = st.slider(
            "第二步：选择具体分数 (0-15分)", 
            min_value=0, 
            max_value=15, 
            value=default_score if current_score_val == -1 else int(current_score_val), 
            step=1,
            key=f"slider_{st.session_state.current_index}" # 添加独立的key以避免状态混淆
        )
        
        st.session_state.scores[st.session_state.current_index] = final_score

        # --- 修改点：修复分数显示 ---
        st.metric(label="当前作文最终得分", value=f"{final_score} 分")

        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("⬅️ 上一份", use_container_width=True, disabled=(st.session_state.current_index == 0)):
                st.session_state.current_index -= 1
                st.rerun()

        with nav_col2:
            if st.button("下一份 ➡️", use_container_width=True, disabled=(st.session_state.current_index >= total_students - 1)):
                st.session_state.current_index += 1
                st.rerun()
        
        # --- 新增功能：跳转到指定份数 ---
        with nav_col3:
            jump_to = st.number_input(
                "跳转至", 
                min_value=1, 
                max_value=total_students, 
                value=st.session_state.current_index + 1,
                step=1,
                label_visibility="collapsed",
                key=f"jump_{st.session_state.current_index}"
            )
            if jump_to != st.session_state.current_index + 1:
                st.session_state.current_index = jump_to - 1
                st.rerun()

    # --- 导出功能 ---
    st.sidebar.header("完成与导出")
    progress_text = f"已批改 {len([s for s in st.session_state.scores if s != -1])} / {total_students} 份"
    st.sidebar.progress(len([s for s in st.session_state.scores if s != -1]) / total_students, text=progress_text)

    if st.sidebar.button("导出批改结果"):
        result_df = df.copy()
        result_df['得分'] = st.session_state.scores
        result_df['得分'] = result_df['得分'].apply(lambda x: "未批改" if x == -1 else x)
        
        # --- 新增 ---: 将作文题目也加入导出文件
        result_df['作文题目'] = st.session_state.essay_prompt

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='批改结果')
        
        st.sidebar.download_button(
            label="✅ 点击下载Excel文件",
            data=output.getvalue(),
            file_name="作文批改结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.sidebar.success("导出文件已生成！")
        