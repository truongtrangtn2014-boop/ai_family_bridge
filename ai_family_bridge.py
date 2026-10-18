import os
import base64
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT & TÀI LIỆU ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

DEFAULT_DOCS = [
    "Co_so_ly_luan_Chuyen_sau.docx",
    "Luan_an_TS_Nguyen_Thi_Hong_Hanh_2023.pdf.pdf"
]

# --- 2. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="AI Family Bridge - Cầu nối Gia đình Số",
    page_icon="🌉",
    layout="centered"
)

# --- 3. HÀM MÃ HÓA ẢNH NỀN BASE64 ---
def get_base64_of_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return ""

img_base64 = get_base64_of_image("background.png")

# --- 4. CSS TÙY CHỈNH: GIAO DIỆN SÁNG SỦA, MÀU CHỮ TRẮNG RÕ RÀNG ---
custom_css = f"""
<style>
.stApp {{
    background: linear-gradient(rgba(5, 15, 35, 0.2), rgba(5, 15, 35, 0.2)), 
                url("data:image/png;base64,{img_base64}") no-repeat top center fixed;
    background-size: cover;
}}

/* Thanh bên Sidebar */
[data-testid="stSidebar"] {{
    background: rgba(10, 25, 50, 0.98);
    backdrop-filter: blur(14px);
    border-right: 1px solid rgba(245, 158, 11, 0.3);
}}

[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {{
    color: #fef08a !important;
}}

[data-testid="stSidebar"] .stButton button {{
    background-color: #b45309 !important;
    color: #fef08a !important;
    border: 1px solid #f59e0b !important;
    border-radius: 10px;
    font-weight: 600;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    background-color: #d97706 !important;
    color: #ffffff !important;
}}

header {{visibility: hidden;}}

/* Card tùy chỉnh phong cách Dashboard */
.custom-card {{
    background-color: rgba(255, 255, 255, 0.94);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}}

/* Header Banner tối màu sang trọng */
.hero-banner {{
    background: #0f172a;
    color: #ffffff;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}}

h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] {{
    color: #1e293b;
}}

.hero-banner *, .hero-banner h3, .hero-banner p {{
    color: #ffffff !important;
}}

/* Ép toàn bộ chữ trong khung chat (cả tin nhắn hỏi và câu trả lời) thành MÀU TRẮNG SÁNG TUYỆT ĐỐI */
[data-testid="stChatMessage"], [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] strong, [data-testid="stChatMessage"] em {{
    color: #ffffff !important;
}}

[data-testid="stChatMessage"] {{
    background-color: rgba(15, 23, 42, 0.9) !important;
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 5. TỰ ĐỘNG NẠP TÀI LIỆU NGẦM VÀO GEMINI ---
client = genai.Client()

@st.cache_resource
def load_default_documents():
    processed = []
    missing = []
    errors = []
    for doc_name in DEFAULT_DOCS:
        if os.path.exists(doc_name):
            try:
                mime_type = "application/pdf" if doc_name.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                with open(doc_name, "rb") as f_to_upload:
                    gemini_file = client.files.upload(
                        file=f_to_upload,
                        config=types.UploadFileConfig(mime_type=mime_type)
                    )
                processed.append((doc_name, gemini_file))
            except Exception as e:
                errors.append(f"Lỗi file {doc_name}: {e}")
        else:
            missing.append(doc_name)
    return processed, missing, errors

loaded_docs_info, missing_documents, document_errors = load_default_documents()
preloaded_files = [item[1] for item in loaded_docs_info]

# --- 6. KHỞI TẠO TRẠNG THÁI ỨNG DỤNG ---
if "interaction_logs" not in st.session_state:
    st.session_state.interaction_logs = [
        {"timestamp": "2026-10-18 09:00", "category": "Đóng vai giả lập (Role-play)", "content": "Học sinh thực hành từ chối áp lực chọn ngành nghề."},
        {"timestamp": "2026-10-18 10:30", "category": "Huấn luyện NVC", "content": "Phân tích 4 bước Giao tiếp phi bạo lực khi mâu thuẫn về thời gian dùng điện thoại."},
    ]

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "Home"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- 7. THANH BÊN (SIDEBAR) & CỔNG QUẢN TRỊ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=50)
    st.markdown("### 🌉 AI Family Bridge")
    st.markdown("**Giải quyết khoảng trống giao tiếp gia đình**")
    st.markdown("---")
    
    if st.button("🏠 Về trang chủ", use_container_width=True):
        st.session_state.current_mode = "Home"
        st.rerun()

    if st.button("📚 Tài liệu nghiên cứu", use_container_width=True):
        st.session_state.current_mode = "Tài liệu nghiên cứu"
        st.rerun()

    st.markdown("---")
    st.markdown("🔒 **Cổng Quản trị Nhà trường (Admin)**")
    admin_password_input = st.text_input("Mật khẩu quản trị:", type="password", placeholder="Nhập mật khẩu...")
    if admin_password_input == "admin2026":
        st.session_state.admin_logged_in = True
    
    if st.session_state.admin_logged_in:
        st.success("🔓 Đã đăng nhập quản trị")
        if st.button("📊 Mở Bảng điều khiển", type="primary", use_container_width=True):
            st.session_state.current_mode = "Quản trị"
            st.rerun()

# --- 8. GIAO DIỆN TÀI LIỆU NGHIÊN CỨU ---
if st.session_state.current_mode == "Tài liệu nghiên cứu":
    st.title("📚 Cơ sở lý luận và tài liệu nghiên cứu")
    st.markdown("Các tài liệu này được dùng làm ngữ cảnh tham khảo cho phản hồi của AI.")
    if loaded_docs_info:
        for name, remote_file in loaded_docs_info:
            st.markdown(f"**📄 {name}**")
            st.caption(f"Trạng thái: đã tải lên Gemini")
    else:
        st.warning("Chưa có tài liệu nào được tải lên Gemini.")
    
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.current_mode = "Home"
        st.rerun()
    st.stop()

# --- 9. GIAO DIỆN ADMIN DASHBOARD ---
if st.session_state.current_mode == "Quản trị":
    if not st.session_state.admin_logged_in:
        st.warning("Bạn cần đăng nhập quản trị từ thanh bên.")
        st.stop()
    st.title("📊 Hệ thống Quản trị Thực nghiệm - Admin Dashboard")
    st.markdown("##### Theo dõi dữ liệu tương tác và đánh giá tác động của trợ lý AI đối với học sinh.")
    st.markdown("---")

    logs_df = pd.DataFrame(st.session_state.interaction_logs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng lượt thực nghiệm", len(logs_df) if not logs_df.empty else 0)
    col2.metric("Chủ đề xung đột phổ biến", "Sử dụng điện thoại")
    col3.metric("Mô hình can thiệp", "NVC (4 bước)")

    if not logs_df.empty:
        st.markdown("### 📈 Biểu đồ phân bổ phiên tương tác")
        st.bar_chart(logs_df["category"].value_counts())
        st.markdown("### 📋 Nhật ký thực nghiệm")
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Xuất nhật ký CSV",
            data=logs_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="ai_family_bridge_logs.csv",
            mime="text/csv",
        )
    
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.current_mode = "Home"
        st.rerun()
    st.stop()

# --- 10. GIAO DIỆN TRANG CHỦ (DASHBOARD CHỌN HOẠT ĐỘNG) ---
if st.session_state.current_mode == "Home":
    st.markdown("""
    <div class="hero-banner">
        <div style="font-size: 13px; opacity: 0.8; margin-bottom: 6px; letter-spacing: 1px;">📁 KHÔNG GIAN KẾT NỐI</div>
        <h3 style="margin: 0 0 10px 0; font-size: 24px;">Hiểu mình. Hiểu bố mẹ. Gần nhau hơn.</h3>
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">Lắng nghe cảm xúc, luyện tập đối thoại và xây dựng kết nối gia đình tích cực.</p>
        <div style="background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 10px; margin-top: 15px; font-size: 13px;">
            💬 <b>Xin chào! Hôm nay bạn muốn bắt đầu từ đâu?</b><br>
            Bạn có thể chia sẻ điều đang băn khoăn hoặc luyện thử một cuộc trò chuyện với bố mẹ.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Chọn hoạt động")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 **Tâm sự cùng AI**\n\n Chia sẻ điều khó nói", use_container_width=True):
            st.session_state.current_mode = "Tâm sự cùng AI"
            st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Mình ở đây để lắng nghe mọi tâm tư, áp lực hay cảm xúc khó nói của bạn mà không hề phán xét. Hãy chia sẻ với mình nhé!"}]
            st.rerun()
        
        if st.button("💙 **Hiểu cảm xúc**\n\n Gọi tên cảm xúc cá nhân", use_container_width=True):
            st.session_state.current_mode = "Hiểu cảm xúc"
            st.session_state.messages = [{"role": "assistant", "content": "Cảm xúc của bạn lúc này thế nào? Hãy kể cho mình nghe một sự việc vừa xảy ra, mình sẽ giúp bạn gọi tên cảm xúc và tìm hiểu nhu cầu sâu kín bên trong nhé!"}]
            st.rerun()

    with col2:
        if st.button("👥 **Tập đối thoại**\n\n Thử vai bố hoặc mẹ (Role-play)", use_container_width=True):
            st.session_state.current_mode = "Tập đối thoại"
            st.session_state.messages = [{"role": "assistant", "content": "Chúng ta bắt đầu tập dượt nhé! Bạn muốn mình đóng vai **Bố** hay **Mẹ**, và tình huống bất đồng hiện tại giữa bạn với phụ huynh là gì?"}]
            st.rerun()

        if st.button("📈 **Xem tiến bộ**\n\n Đánh giá kỹ năng ứng xử", use_container_width=True):
            st.session_state.current_mode = "Xem tiến bộ"
            st.session_state.messages = [{"role": "assistant", "content": "Hệ thống ghi nhận bạn đã tham gia các phiên luyện tập Giao tiếp phi bạo lực (NVC). Việc duy trì đối thoại trực diện giúp giảm đáng kể căng thẳng gia đình theo nghiên cứu khoa học!"}]
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card">
        <small style="color: #64748b; font-weight: 600;">GỢI Ý BẮT ĐẦU</small>
        <p style="margin: 8px 0 12px 0; font-weight: 500; color: #1e293b;">“Bố mẹ không cho mình dùng điện thoại nhiều, mình nên nói thế nào?”</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Luyện tình huống này ➔", type="primary"):
        st.session_state.current_mode = "Tập đối thoại"
        st.session_state.messages = [
            {"role": "assistant", "content": "Tuyệt vời, chúng ta cùng xử lý tình huống này nhé. Mình sẽ đóng vai Phụ huynh đang lo lắng về việc bạn dùng điện thoại nhiều. Bạn hãy thử mở lời với mình theo cách của bạn xem sao!"}
        ]
        st.rerun()

    st.markdown("<p style='text-align: center; color: #64748b; font-size: 12px; margin-top: 30px;'>AI đồng hành, không phán xét. Bạn có thể dừng bất cứ lúc nào.</p>", unsafe_allow_html=True)
    st.stop()

# --- 11. GIAO DIỆN TRÒ CHUYỆN (KHI CHỌN CÁC HOẠT ĐỘNG) ---
st.markdown(f"### 🌉 Đang ở chế độ: {st.session_state.current_mode}")
if st.button("⬅ Quay lại danh sách hoạt động"):
    st.session_state.current_mode = "Home"
    st.rerun()
st.markdown("---")

system_instruction = f"""
Bạn là "AI Family Bridge", một trợ lý AI chuyên gia về tâm lý học gia đình, kỹ năng giao tiếp phi bạo lực (NVC) và phương pháp đóng vai giả lập (Role-playing Coach). Người dùng đang chọn chế độ: {st.session_state.current_mode}.
Hãy luôn giữ thái độ thấu cảm, ấm áp, định hướng học sinh vượt qua xu hướng "trốn chạy tương tác thực" để tự tin mở lời đối thoại trực diện với cha mẹ.
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.interaction_logs.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": st.session_state.current_mode,
        "content": prompt
    })

    with st.chat_message("assistant"):
        with st.spinner("AI Family Bridge đang phân tích..."):
            try:
                contents = preloaded_files + [prompt]
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    )
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")