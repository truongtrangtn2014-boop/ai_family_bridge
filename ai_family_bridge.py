# --- name=ai_family_bridge.py ---
import os
import csv
import base64
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# --- 2. HỆ THỐNG LƯU TRỮ NHẬT KÝ DÙNG CHUNG (PERSISTENT LOGGING) ---
LOG_FILE = "interaction_logs.csv"

def init_logs_file():
    if not os.path.exists(LOG_FILE):
        df_init = pd.DataFrame([
            {"timestamp": "2026-10-18 09:00", "category": "Đóng vai giả lập (Role-play)", "content": "Học sinh thực hành từ chối áp lực chọn ngành nghề."},
            {"timestamp": "2026-10-18 10:30", "category": "Huấn luyện NVC", "content": "Phân tích 4 bước Giao tiếp phi bạo lực khi mâu thuẫn về thời gian dùng điện thoại."},
        ])
        df_init.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

def append_log(timestamp, category, content):
    init_logs_file()
    try:
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, category, content])
    except Exception as e:
        print(f"Lỗi ghi log: {e}")

def load_all_logs():
    init_logs_file()
    try:
        return pd.read_csv(LOG_FILE, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame(columns=["timestamp", "category", "content"])

init_logs_file()

# --- 3. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="AI Family Bridge - Cầu nối Gia đình Số",
    page_icon="🌉",
    layout="centered"
)

# --- 4. HÀM MÃ HÓA ẢNH NỀN BASE64 ---
def get_base64_of_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return ""

img_base64 = get_base64_of_image("background.png")

# --- 5. CSS TÙY CHỈNH ---
custom_css = f"""
<style>
.stApp {{
    background: linear-gradient(rgba(5, 15, 35, 0.2), rgba(5, 15, 35, 0.2)), 
                url("data:image/png;base64,{img_base64}") no-repeat top center fixed;
    background-size: cover;
}}

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

.custom-card {{
    background-color: rgba(255, 255, 255, 0.94);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}}

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

# --- 6. KHỞI TẠO CLIENT GEMINI ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

if not API_KEY:
    st.error("Chưa tìm thấy GEMINI_API_KEY. Vui lòng cấu hình trong Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.5-flash-lite"

# --- 7. KHỞI TẠO TRẠNG THÁI PHIÊN ---
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "Home"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# --- 8. THANH BÊN (SIDEBAR) & CỔNG QUẢN TRỊ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=50)
    st.markdown("### 🌉 AI Family Bridge")
    st.markdown("**Giải quyết khoảng trống giao tiếp gia đình**")
    st.markdown("---")
    
    if st.button("🏠 Về trang chủ", use_container_width=True):
        st.session_state.current_mode = "Home"
        st.rerun()

    if st.button("📚 Cơ sở lý luận", use_container_width=True):
        st.session_state.current_mode = "Tài liệu nghiên cứu"
        st.rerun()

    st.markdown("---")
    st.markdown("🔒 **Cổng Admin**")
    admin_password_input = st.text_input("Mật khẩu quản trị:", type="password", placeholder="Nhập mật khẩu...")
    if admin_password_input == "admin2026":
        st.session_state.admin_logged_in = True
    
    if st.session_state.admin_logged_in:
        st.success("🔓 Đã đăng nhập quản trị")
        if st.button("📊 Mở Bảng điều khiển", type="primary", use_container_width=True):
            st.session_state.current_mode = "Quản trị"
            st.rerun()

# --- 9. GIAO DIỆN TÀI LIỆU NGHIÊN CỨU ---
if st.session_state.current_mode == "Tài liệu nghiên cứu":
    st.title("📚 Cơ sở lý luận và tài liệu nghiên cứu")
    st.markdown("Hệ thống tích hợp sẵn các tri thức nền tảng:")
    st.markdown("- **Giao tiếp bất bạo động (NVC)** của Marshall B. Rosenberg (4 bước: Quan sát không phán xét, Nhận diện cảm xúc, Nhận diện nhu cầu, Đề nghị cụ thể).")
    st.markdown("- **Thế hệ lo âu** của Jonathan Haidt (Tác động của điện thoại, mạng xã hội và không gian số đến tuổi thiếu niên).")
    st.markdown("- **Luận án tiến sĩ** về mâu thuẫn giữa học sinh THPT và cha mẹ (vấn đề Internet, học tập, tài chính, bạn bè).")
    
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.current_mode = "Home"
        st.rerun()
    st.stop()

# --- 10. GIAO DIỆN ADMIN DASHBOARD (TỔNG HỢP TOÀN BỘ DỮ LIỆU) ---
if st.session_state.current_mode == "Quản trị":
    if not st.session_state.admin_logged_in:
        st.warning("Bạn cần đăng nhập quản trị từ thanh bên.")
        st.stop()
    st.title("📊 Hệ thống Quản trị Thực nghiệm - Admin Dashboard")
    st.markdown("##### Theo dõi dữ liệu tương tác và đánh giá tác động của trợ lý AI đối với học sinh.")
    st.markdown("---")

    # Đọc dữ liệu từ file dùng chung
    logs_df = load_all_logs()

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng lượt thực nghiệm", len(logs_df) if not logs_df.empty else 0)
    col2.metric("Chủ đề xung đột phổ biến", "Sử dụng Internet & Học tập")
    col3.metric("Mô hình can thiệp", "NVC (4 bước)")

    if not logs_df.empty:
        st.markdown("### 📈 Biểu đồ phân bổ phiên tương tác")
        if "category" in logs_df.columns:
            st.bar_chart(logs_df["category"].value_counts())
        
        st.markdown("### 📋 Nhật ký thực nghiệm toàn hệ thống")
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Xuất nhật ký CSV",
            data=logs_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="ai_family_bridge_logs.csv",
            mime="text/csv",
        )
    else:
        st.info("Chưa có lượt tương tác nào được ghi nhận.")
    
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.current_mode = "Home"
        st.rerun()
    st.stop()

# --- 11. GIAO DIỆN TRANG CHỦ ---
if st.session_state.current_mode == "Home":
    st.markdown("""
    <div class="hero-banner">
        <div style="font-size: 13px; opacity: 0.8; margin-bottom: 6px; letter-spacing: 1px;">📁 KHÔNG GIAN KẾT NỐI</div>
        <h3 style="margin: 0 0 10px 0; font-size: 24px;">Hiểu mình. Hiểu bố mẹ. Gần nhau hơn.</h3>
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">Lắng nghe cảm xúc, luyện tập đối thoại và xây dựng kết nối gia đình tích cực dựa trên nguyên lý NVC.</p>
        <div style="background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 10px; margin-top: 15px; font-size: 13px;">
            💬 <b>Xin chào! Hôm nay bạn muốn bắt đầu từ đâu?</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Chọn hoạt động")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 **Tâm sự cùng AI**\n\n Chia sẻ điều khó nói", use_container_width=True):
            st.session_state.current_mode = "Tâm sự cùng AI"
            st.session_state.messages = [{"role": "assistant", "content": "AI Family Bridge luôn ở đây lắng nghe mọi tâm tư của cậu. Hãy chia sẻ với mình nhé..."}]
            st.rerun()
        
        if st.button("💙 **Hiểu cảm xúc**\n\n Gọi tên cảm xúc cá nhân", use_container_width=True):
            st.session_state.current_mode = "Hiểu cảm xúc"
            st.session_state.messages = [{"role": "assistant", "content": "Cảm xúc của cậu lúc này thế nào? Hãy kể cho mình nghe một sự việc vừa xảy ra nhé..."}]
            st.rerun()

    with col2:
        if st.button("👥 **Tập đối thoại**\n\n Thử vai bố hoặc mẹ (Role-play)", use_container_width=True):
            st.session_state.current_mode = "Tập đối thoại"
            st.session_state.messages = [{"role": "assistant", "content": "Chúng ta bắt đầu nhé! Cậu muốn mình đóng vai **Bố** hay **Mẹ**, và tình huống cần gỡ rối là gì nhỉ?"}]
            st.rerun()

        if st.button("📈 **Xem tiến bộ**\n\n Đánh giá kỹ năng ứng xử", use_container_width=True):
            st.session_state.current_mode = "Xem tiến bộ"
            st.session_state.messages = [{"role": "assistant", "content": "Hệ thống ghi nhận cậu đã tham gia rất nghiêm túc. Việc duy trì đối thoại chính là cây cầu nối ngắn nhất giữa các thế hệ..."}]
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
            {"role": "assistant", "content": "Cảm giác bị hạn chế không gian riêng hẳn là rất khó chịu đúng không cậu? Nhưng đằng sau sự nghiêm khắc ấy đôi khi là nỗi lo lắng chưa biết giãi bày của cha mẹ. Nếu cậu sẵn sàng, chúng ta cùng thử tập dượt cách trò chuyện nhé!"}
        ]
        st.rerun()

    st.stop()

# --- 12. GIAO DIỆN TRÒ CHUYỆN VÀ GHI DỮ LIỆU ---
st.markdown(f"### 🌉 Đang ở chế độ: {st.session_state.current_mode}")
if st.button("⬅ Quay lại danh sách hoạt động"):
    st.session_state.current_mode = "Home"
    st.session_state.messages = []
    st.rerun()
st.markdown("---")

system_instruction = f"""
Bạn là "AI Family Bridge", trợ lý AI chuyên gia tâm lý học gia đình và kỹ năng Giao tiếp phi bạo lực (NVC). Người dùng đang ở chế độ: {st.session_state.current_mode}.

NỀN TẢNG TRI THỨC TÍCH HỢP NGẦM:
- Phương pháp NVC (Marshall B. Rosenberg): 4 bước gồm Quan sát không phán xét, Nhận diện cảm xúc, Nhận diện nhu cầu (được tôn trọng, thấu hiểu, tự chủ) và Đưa ra đề nghị cụ thể.
- Nghiên cứu "Thế hệ lo âu" (Jonathan Haidt): Thấu hiểu áp lực từ màn hình điện thoại, mạng xã hội, thiếu ngủ và xu hướng thu rút của tuổi trẻ.
- Luận án mâu thuẫn gia đình: Nắm bắt các nguyên nhân xung đột phổ biến ở học sinh THPT (sử dụng Internet, học tập, tài chính, quan hệ bạn bè) để đưa ra lời khuyên thấu đáo.

QUY TẮC PHẢN HỒI:
1. **Độ dài:** Phản hồi NGẮN GỌN, súc tích (tối đa 3-4 câu), đi thẳng vào trọng tâm, tuyệt đối không dài dòng như bài văn.
2. **Ngữ điệu:** Ấm áp, chân thành, thấu cảm sâu sắc.
3. **LINH HOẠT CÁCH MỞ ĐẦU (QUAN TRỌNG):**
   - Đọc kỹ thông điệp của người dùng để phản hồi đúng trọng tâm cảm xúc thực tế.
   - KHÔNG ĐƯỢC lặp lại dập khuôn câu mở đầu cố định. Mỗi câu trả lời phải có cách diễn đạt cảm xúc riêng phù hợp với ngữ cảnh.
4. **Mẫu câu gợi ý giải pháp:**
   - "Em có muốn thử..."
   - "Nếu em cảm thấy sẵn sàng, chúng ta có thể..."
   - "Liệu có cách nào để bố mẹ hiểu lòng em hơn không nhỉ?"
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
    # Lưu vào session để hiển thị UI
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # GHI THẲNG VÀO FILE CHUNG DÀNH CHO ADMIN
    append_log(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        category=st.session_state.current_mode,
        content=prompt
    )

    with st.chat_message("assistant"):
        with st.spinner("AI Family Bridge đang lắng nghe và phản hồi..."):
            try:
                api_history = []
                started = False

                for item in st.session_state.messages:
                    role = item.get("role")
                    content = item.get("content", "")

                    if role == "user":
                        started = True
                        api_role = "user"
                    elif role == "assistant":
                        if not started:
                            continue
                        api_role = "model"
                    else:
                        continue

                    if content and content.strip():
                        api_history.append(
                            types.Content(
                                role=api_role,
                                parts=[types.Part.from_text(text=content)]
                            )
                        )

                api_history = api_history[-12:]
                while api_history and api_history[0].role != "user":
                    api_history.pop(0)

                if not api_history:
                    raise ValueError("Không tạo được lịch sử hội thoại hợp lệ.")

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=api_history,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    )
                )

                answer = response.text
                if not answer or not answer.strip():
                    raise ValueError("Gemini không trả về nội dung văn bản.")

                st.markdown(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                if (
                    st.session_state.messages
                    and st.session_state.messages[-1].get("role") == "user"
                    and st.session_state.messages[-1].get("content") == prompt
                ):
                    st.session_state.messages.pop()

                st.error(f"Đã có lỗi khi kết nối Gemini: {type(e).__name__}: {e}")