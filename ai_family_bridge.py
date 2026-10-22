import os
import base64
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

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

/* Ép toàn bộ chữ trong khung chat thành MÀU TRẮNG SÁNG */
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

# Khởi tạo Client Gemini
client = genai.Client()

# --- 5. KHỞI TẠO TRẠNG THÁI ỨNG DỤNG ---
if "interaction_logs" not in st.session_state:
    st.session_state.interaction_logs = [
        {"timestamp": "2026-10-18 09:00", "category": "Tập đối thoại (Role-play)", "content": "Học sinh thực hành từ chối áp lực chọn ngành nghề."},
        {"timestamp": "2026-10-18 10:30", "category": "Hiểu cảm xúc", "content": "Phân tích và thấu cảm khi mâu thuẫn về thời gian dùng điện thoại."},
    ]

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "Home"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- 6. THANH BÊN (SIDEBAR) & CỔNG QUẢN TRỊ ---
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

# --- 7. GIAO DIỆN TÀI LIỆU NGHIÊN CỨU ---
if st.session_state.current_mode == "Tài liệu nghiên cứu":
    st.title("📚 Cơ sở lý luận và tài liệu nghiên cứu")
    st.markdown("Hệ thống đã tích hợp trực tiếp tri thức cốt lõi từ 6 công trình nghiên cứu khoa học vào bộ não AI:")
    st.markdown("""
    - **1. Nghiên cứu thực trạng Hà Nội (2025):** Các yếu tố tác động đến xung đột tâm lý giữa HS THPT và cha mẹ (vai trò 'cái tôi', phong cách làm cha mẹ).
    - **2. Luận án Tiến sĩ Xã hội học (Nguyễn Thị Hồng Hạnh, 2023):** Thực trạng mâu thuẫn học tập, đời sống cá nhân, tự lập tài chính và cơ chế phản ứng.
    - **3. Tạp chí Giáo dục lý luận (Lê Xuân Đức, 2023):** Phát huy vai trò giáo dục gia đình thông qua tình cảm và nêu gương.
    - **4. 'Thế hệ lo âu' (Jonathan Haidt):** Tác động của điện thoại thông minh, mạng xã hội, thiếu ngủ và suy giảm sự chú ý.
    - **5. Tạp chí Tâm lý - Giáo dục (2026):** Thực trạng gắn bó với cha, mẹ và bạn bè ở học sinh THPT.
    - **6. Nghiên cứu bảo vệ trẻ trước MXH (Phạm Thị Khánh):** Trách nhiệm gia đình và rủi ro trực tuyến.
    """)
    if st.button("⬅ Quay lại trang chủ"):
        st.session_state.current_mode = "Home"
        st.rerun()
    st.stop()

# --- 8. GIAO DIỆN ADMIN DASHBOARD ---
if st.session_state.current_mode == "Quản trị":
    if not st.session_state.admin_logged_in:
        st.warning("Bạn cần đăng nhập quản trị từ thanh bên.")
        st.stop()
    st.title("📊 Hệ thống Quản trị Thực nghiệm - Admin Dashboard")
    st.markdown("##### Theo dõi dữ liệu tương tác và đánh giá tác động của trợ lý AI đối với học sinh THPT.")
    st.markdown("---")

    logs_df = pd.DataFrame(st.session_state.interaction_logs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng lượt thực nghiệm", len(logs_df) if not logs_df.empty else 0)
    col2.metric("Chủ đề xung đột phổ biến", "Thiết bị số & Học tập")
    col3.metric("Mô hình can thiệp", "NVC & Thấu cảm đa thế hệ")

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

# --- 9. GIAO DIỆN TRANG CHỦ ---
if st.session_state.current_mode == "Home":
    st.markdown("""
    <div class="hero-banner">
        <div style="font-size: 13px; opacity: 0.8; margin-bottom: 6px; letter-spacing: 1px;">📁 KHÔNG GIAN KẾT NỐI GIA ĐÌNH SỐ</div>
        <h3 style="margin: 0 0 10px 0; font-size: 24px;">Hiểu mình. Hiểu bố mẹ. Gần nhau hơn.</h3>
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">Lắng nghe cảm xúc, xoa dịu khoảng cách thế hệ và xây dựng yêu thương dưới mái nhà chung.</p>
        <div style="background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 10px; margin-top: 15px; font-size: 13px;">
            💬 <b>Xin chào bạn! Hôm nay mái nhà nhỏ của bạn thế nào?</b><br>
            Hãy cùng ngồi lại, chia sẻ những tâm sự giấu kín hoặc thử trải lòng để kết nối sâu sắc hơn với đấng sinh thành nhé.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Chọn hoạt động đồng hành")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 **Tâm sự cùng AI**\n\n Trút bỏ tâm sự, gỡ rối lòng", use_container_width=True):
            st.session_state.current_mode = "Tâm sự cùng AI"
            st.session_state.messages = [{"role": "assistant", "content": "Nghe cậu kể, mình cảm nhận được rằng chuyện ấy đã khiến cậu buồn lòng nhiều lắm... Cứ thong thả trút hết bầu tâm sự với mình nhé, mái nhà luôn là nơi để về mà."}]
            st.rerun()
        
        if st.button("💙 **Hiểu cảm xúc**\n\n Lắng nghe nhịp đập trái tim", use_container_width=True):
            st.session_state.current_mode = "Hiểu cảm xúc"
            st.session_state.messages = [{"role": "assistant", "content": "Dạo này những ngọn gió nào đã làm lòng cậu hơi chênh vênh thế? Hãy kể cho mình nghe đôi chút, chúng ta cùng thắp lên một ngọn đèn soi chiếu cảm xúc nhé."}]
            st.rerun()

    with col2:
        if st.button("👥 **Tập đối thoại**\n\n Nhập vai thấu hiểu (Role-play)", use_container_width=True):
            st.session_state.current_mode = "Tập đối thoại"
            st.session_state.messages = [{"role": "assistant", "content": "Sẵn sàng mở cánh cửa đối thoại chưa cậu? Cậu muốn mình đóng vai **Bố** hay **Mẹ**, và khúc mắc giữa nhà mình đang ở ngã rẽ nào thế nhỉ?"}]
            st.rerun()

        if st.button("📈 **Xem tiến bộ**\n\n Nhìn lại hành trình trưởng thành", use_container_width=True):
            st.session_state.current_mode = "Xem tiến bộ"
            st.session_state.messages = [{"role": "assistant", "content": "Thật tuyệt vời khi thấy cậu đang từng bước vun đắp cho nhịp cầu gia đình. “Nhà là nơi để về” - những nỗ lực nhỏ hôm nay sẽ thắp sáng cả khoảng trời mai sau đấy!"}]
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="custom-card">
        <small style="color: #64748b; font-weight: 600;">GỢI Ý BẮT ĐẦU</small>
        <p style="margin: 8px 0 12px 0; font-weight: 500; color: #1e293b;">“Bố mẹ lo lắng khi mình dùng điện thoại nhiều, mình nên mở lời thế nào để bố mẹ an tâm?”</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Luyện tình huống này ➔", type="primary"):
        st.session_state.current_mode = "Tập đối thoại"
        st.session_state.messages = [
            {"role": "assistant", "content": "Chuyện thiết bị công nghệ là nỗi niềm quen thuộc dưới mái nhà hiện đại lắm nè! Giờ mình nhập vai Phụ huynh đang lo lắng nhé. Liệu có cách nào để bố mẹ hiểu lòng cậu hơn không nhỉ? Thử mở lời với mình xem sao nào."}
        ]
        st.rerun()

    st.markdown("<p style='text-align: center; color: #64748b; font-size: 12px; margin-top: 30px;'>AI đồng hành thấu cảm, không phán xét. Bạn có thể chia sẻ bất cứ lúc nào.</p>", unsafe_allow_html=True)
    st.stop()

# --- 10. GIAO DIỆN TRÒ CHUYỆN ---
st.markdown(f"### 🌉 Đang ở chế độ: {st.session_state.current_mode}")
if st.button("⬅ Quay lại danh sách hoạt động"):
    st.session_state.current_mode = "Home"
    st.rerun()
st.markdown("---")

# CÁCH KHẮC PHỤC THỨ 3: NÉN TOÀN BỘ TRI THỨC 6 TÀI LIỆU VÀO SYSTEM INSTRUCTION
system_instruction = f"""
Bạn là "AI Family Bridge" - người bạn đồng hành tâm lý ấm áp, tinh tế dành cho học sinh THPT. Người dùng đang ở chế độ: {st.session_state.current_mode}.

CƠ SỞ DỮ LIỆU & LÝ LUẬN KHOA HỌC BẠN PHẢI NẮM VỮNG VÀ VẬN DỤNG:
1. Bản chất xung đột THPT (Nghiên cứu Hà Nội & Luận án TS 2023):
   - 'Cái tôi' (ego) là nhân tố tác động mạnh nhất đến xung đột tâm lý giữa con và cha mẹ. Mỗi bên thường nhìn thấy 'cái tôi' của người kia lớn hơn của mình.
   - Các chủ đề mâu thuẫn hàng đầu: Học tập (điểm số, học ở nhà, học thêm), Thiết bị công nghệ/Internet (thời gian sử dụng, nội dung mạng), Quan hệ bạn bè, và Tự lập tài chính (tiêu tiền).
   - Tỷ lệ mâu thuẫn với mẹ thường cao hơn với bố do mẹ dành nhiều thời gian chăm sóc, nhắc nhở trực tiếp hơn.
   - Phản ứng phổ biến nhất của học sinh khi có xung đột là 'Im lặng/Lảng tránh' (chiếm hơn 46%), tuy nhiên lảng tránh kéo dài dễ để lại tổn thương cảm xúc tiêu cực.
2. Tác động của thiết bị số (Jonathan Haidt & Phạm Thị Khánh):
   - Điện thoại thông minh và mạng xã hội gây ra 4 tổn hại cốt lõi: Thiếu giao tiếp xã hội trực tiếp, Thiếu ngủ, Phân tán sự chú ý, và Gây nghiện (vòng lặp dopamine). Phụ huynh lo lắng thường vì muốn bảo vệ con khỏi những rủi ro này.
3. Giáo dục gia đình và sự gắn bó (Lê Xuân Đức & Đặng Hoàng Phúc):
   - Giáo dục gia đình có sức mạnh lớn nhất khi diễn ra thông qua tình cảm và sự nêu gương, không phải áp đặt độc đoán.
   - Vị thành niên vẫn gắn bó và tin cậy mẹ cao nhất, tiếp đến là cha. Gia đình là bến đỗ an toàn nhất.

QUY TẮC PHẢN HỒI (BẮT BUỘC TUÂN THỦ):
1. **Phong cách ngữ điệu:** Mềm mại, ấm áp, gần gũi như lời thủ thỉ tâm tình của tri kỷ. Chân thành, kiên nhẫn, tuyệt đối không phán xét.
2. **Hình ảnh văn chương:** Lồng ghép tự nhiên hình ảnh ngọn đèn, mái nhà, dòng sông, cánh cửa, khoảng lặng, mùa yêu thương. Vận dụng ca dao, tục ngữ phù hợp (ví dụ: 'Công cha như núi Thái Sơn...', 'Nhà là nơi để về', 'Đi khắp thế gian không ai tốt bằng mẹ...').
3. **Mẫu câu gợi ý:**
   - “Em có muốn thử…”
   - “Nếu em cảm thấy sẵn sàng, chúng ta có thể…”
   - “Liệu có cách nào để bố mẹ hiểu lòng em hơn không nhỉ?”
   - “Nghe cậu kể, mình cảm nhận được rằng chuyện ấy đã khiến cậu buồn lòng nhiều lắm…. Nhưng bình tâm suy nghĩ, thử đặt mình vào vị trí của cha mẹ…”
4. **Định dạng:** Trả lời súc tích, ngắt đoạn ngắn, dùng gạch đầu dòng rõ ràng để dễ đọc trên điện thoại.
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

    # PHẢN HỒI STREAMING KHÔNG CẦN GỬI KÈM 6 FILE NẶNG - TỐC ĐỘ GÕ CHỮ TỨC THÌ
    with st.chat_message("assistant"):
        try:
            def response_generator():
                # Chỉ truyền [prompt], không gửi file kèm theo mỗi tin nhắn
                response_stream = client.models.generate_content_stream(
                    model='gemini-3.8-flash',
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    )
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text

            answer = st.write_stream(response_generator)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Lỗi kết nối AI: {e}")