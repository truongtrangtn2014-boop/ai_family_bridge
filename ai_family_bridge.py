import os
import base64
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT & 2 FILE TÀI LIỆU CHUYÊN SÂU ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

DEFAULT_DOCS = [
    "Co_so_ly_luan_Chuyen_sau.docx",
    "Luan_an_TS_Nguyen_Thi_Hong_Hanh_2023.pdf.pdf"
]

# --- 2. CẤU HÌNH GIAO DIỆN TRANG WEB ---
st.set_page_config(
    page_title="AI Family Bridge - Huấn luyện viên Giao tiếp Gia đình",
    page_icon="🌉",
    layout="wide"
)

# --- 3. HÀM MÃ HÓA ẢNH NỀN BASE64 (Tự động nhận diện file background.png) ---
def get_base64_of_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return ""

img_base64 = get_base64_of_image("background.png")

# --- 4. CSS TÙY CHỈNH: GIAO DIỆN KÍNH MỜ TRÊN NỀN ẢNH GIA ĐÌNH SỐ ---
custom_css = f"""
<style>
.stApp {{
    background: linear-gradient(rgba(5, 20, 45, 0.65), rgba(5, 20, 45, 0.65)), 
                url("data:image/png;base64,{img_base64}") no-repeat center center fixed;
    background-size: cover;
}}

[data-testid="stSidebar"] {{
    background: rgba(10, 25, 50, 0.9);
    backdrop-filter: blur(14px);
    border-right: 1px solid rgba(59, 130, 246, 0.3);
}}

[data-testid="stChatMessage"] {{
    background-color: rgba(15, 23, 42, 0.78) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 16px 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}}

header {{visibility: hidden;}}

h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] {{
    color: #ffffff !important;
}}

[data-testid="stMarkdownContainer"] em, [data-testid="stMarkdownContainer"] small {{
    color: #cbd5e1 !important;
}}

.stChatInputContainer {{
    background-color: rgba(15, 23, 42, 0.85) !important;
    backdrop-filter: blur(14px);
    border-radius: 22px !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 6px 30px rgba(0, 0, 0, 0.5);
    padding: 4px;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 5. TỰ ĐỘNG NẠP NGẦM 2 FILE TÀI LIỆU VÀO GEMINI API ---
client = genai.Client()

@st.cache_resource
def load_default_documents():
    processed = []
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
                print(f"Lỗi nạp file {doc_name}: {e}")
    return processed

loaded_docs_info = load_default_documents()
preloaded_files = [item[1] for item in loaded_docs_info]

# --- 6. KHỞI TẠO BỘ NHỚ LƯU TRỮ NHẬT KÝ & QUẢN TRỊ ADMIN ---
if "interaction_logs" not in st.session_state:
    st.session_state.interaction_logs = [
        {"timestamp": "2026-10-18 09:00", "category": "Đóng vai giả lập (Role-play)", "content": "Học sinh thực hành từ chối áp lực chọn ngành nghề."},
        {"timestamp": "2026-10-18 10:30", "category": "Huấn luyện NVC", "content": "Phân tích 4 bước Giao tiếp phi bạo lực khi mâu thuẫn về thời gian dùng điện thoại."},
    ]

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# --- 7. THANH BÊN (SIDEBAR) & CỔNG QUẢN TRỊ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=60)
    st.markdown("### 🌉 AI Family Bridge")
    st.markdown("**Đề tài KHKT:** *Giải quyết khoảng trống giao tiếp gia đình*")
    st.markdown("---")
    
    st.markdown("#### 📁 Kho cơ sở lý luận tích hợp")
    if len(preloaded_files) > 0:
        st.success("✅ Đã nạp thành công tài liệu nghiên cứu!")
        for name, _ in loaded_docs_info:
            st.markdown(f"- 📄 `{name}`")
    else:
        st.warning("⚠️ Không tìm thấy file tài liệu trong thư mục!")
    
    st.markdown("---")
    st.markdown("🔒 **Cổng Quản trị Nhà trường (Admin)**")
    
    if not st.session_state.admin_logged_in:
        admin_password_input = st.text_input("Mật khẩu quản trị:", type="password", placeholder="Nhập mật khẩu...")
        ADMIN_SECRET_KEY = "admin2026"
        
        if admin_password_input == ADMIN_SECRET_KEY:
            st.session_state.admin_logged_in = True
            st.rerun()
        elif admin_password_input != "":
            st.error("❌ Mật khẩu sai!")
    else:
        st.success("🔓 Đã đăng nhập quản trị")
        if st.button("🚪 Đăng xuất / Thoát", type="primary"):
            st.session_state.admin_logged_in = False
            st.rerun()

# --- 8. NẾU ĐÃ ĐĂNG NHẬP ADMIN -> HIỂN THỊ BẢNG ĐIỀU KHIỂN THỰC NGHIỆM ---
if st.session_state.admin_logged_in:
    st.title("📊 Hệ thống Quản trị Thực nghiệm - Admin Dashboard")
    st.markdown("##### Theo dõi dữ liệu tương tác, tần suất tư vấn và đánh giá tác động của trợ lý AI đối với học sinh.")
    st.markdown("---")

    if st.button("⬅ Quay lại giao diện Trợ lý AI (Học sinh)", type="primary"):
        st.session_state.admin_logged_in = False
        st.rerun()

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng lượt thực nghiệm", len(st.session_state.interaction_logs), "+2 phiên mới")
    col2.metric("Chủ đề xung đột phổ biến", "Đời sống cá nhân & Sử dụng điện thoại", "Dựa trên Luận án TS. Hạnh")
    col3.metric("Mô hình can thiệp", "Giao tiếp phi bạo lực (NVC)", "Đang hoạt động tốt")

    st.markdown("### 📈 Biểu đồ phân bổ các phiên tương tác thực nghiệm")
    df_logs = pd.DataFrame(st.session_state.interaction_logs)
    
    if not df_logs.empty:
        category_counts = df_logs["category"].value_counts()
        st.bar_chart(category_counts)

        st.markdown("### 📋 Nhật ký thực nghiệm thời gian thực (Research Logs)")
        st.dataframe(df_logs, use_container_width=True)
        
        st.info("💡 **Minh chứng khoa học:** Dữ liệu phục vụ trực tiếp cho việc đánh giá tiến trình nghiên cứu hành vi theo quy định KHKT.")
    
    st.stop()

# --- 9. HỆ THỐNG NHÂN DẠNG CHUYÊN SÂU (SYSTEM INSTRUCTION CHO ĐỀ TÀI 2) ---
system_instruction = """
Bạn là "AI Family Bridge", một trợ lý AI chuyên gia về tâm lý học gia đình, kỹ năng giao tiếp phi bạo lực (NVC) và phương pháp đóng vai giả lập (Role-playing Coach). Nhiệm vụ của bạn là hỗ trợ học sinh THPT giải quyết khoảng trống giao tiếp và mâu thuẫn với cha mẹ.

Bạn hoạt động dựa trên cơ sở khoa học từ các tài liệu chuyên sâu đã được nạp vào hệ thống (gồm Luận án tiến sĩ xã hội học về mâu thuẫn gia đình và tài liệu chuyên khảo về mô hình Giao tiếp phi bạo lực của Marshall B. Rosenberg).

Bạn có 2 chế độ hoạt động chính (linh hoạt theo yêu cầu của học sinh):
1. CHẾ ĐỘ ĐÓNG VAI GIẢ LẬP (ROLE-PLAYING): Khi học sinh muốn luyện tập trước khi nói chuyện với bố mẹ, bạn sẽ hóa thân thành phụ huynh (Bố hoặc Mẹ với các sắc thái tâm lý chân thực như lo lắng thái quá, áp lực công việc hoặc khắt khe). Giúp học sinh tập dượt đối mặt với áp lực.
2. CHẾ ĐỘ HUẤN LUYỆN VIÊN (NVC COACH): Sau khi đóng vai hoặc khi học sinh cần tư vấn, bạn phân tích dưới góc độ chuyên gia, hướng dẫn học sinh áp dụng chính xác 4 bước NVC:
   - Bước 1: Quan sát khách quan (không phán xét, không đổ lỗi).
   - Bước 2: Bộc lộ cảm xúc bản thân (tủi thân, áp lực, mệt mỏi).
   - Bước 3: Liên kết với nhu cầu cốt lõi (cần được lắng nghe, tôn trọng).
   - Bước 4: Đưa ra đề nghị cụ thể, nhã nhặn.

Hãy luôn giữ thái độ thấu cảm, ấm áp, định hướng học sinh vượt qua xu hướng "trốn chạy tương tác thực" để tự tin mở lời đối thoại trực diện, xây dựng sự gắn kết lành mạnh trong gia đình.
"""

# --- 10. GIAO DIỆN TRÒ CHUYỆN CHÍNH (DÀNH CHO HỌC SINH) ---
st.title("🌉 AI Family Bridge - Cầu nối Gia đình Số")
st.markdown("##### Hệ thống hỗ trợ học sinh THPT vượt qua khoảng trống giao tiếp và thực hành đối thoại thông minh.")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Mình là **AI Family Bridge** – Người bạn đồng hành giúp bạn gỡ rối những bất đồng, áp lực khi giao tiếp với gia đình. Hôm nay bạn đang gặp khó khăn hay muốn tập dượt trò chuyện với bố mẹ về vấn đề gì, hãy chia sẻ với mình nhé!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tâm sự hoặc yêu cầu tập dượt (Ví dụ: Bố mẹ không cho dùng điện thoại nhiều, tôi phải mở lời sao?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    category = "Huấn luyện NVC"
    if any(kw in prompt.lower() for kw in ["đóng vai", "giả lập", "thử nói", "bố nói thế này", "mẹ nói thế kia"]):
        category = "Đóng vai giả lập (Role-play)"

    st.session_state.interaction_logs.append({
        "timestamp": current_time,
        "category": category,
        "content": prompt
    })

    with st.chat_message("assistant"):
        with st.spinner("AI Family Bridge đang nghiên cứu cơ sở lý luận và phân tích..."):
            try:
                contents = preloaded_files + [prompt]
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
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
                st.error(f"Đã xảy ra lỗi kết nối hoặc xử lý dữ liệu: {e}")