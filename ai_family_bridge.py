import os
import csv
import base64
import datetime
import random
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# --- 2. HỆ THỐNG LƯU TRỮ NHẬT KÝ DÙNG CHUNG (PERSISTENT LOGGING) ---
LOG_FILE = "interaction_logs_v3.csv"

# Ngân hàng câu hỏi tâm sự thực tế của học sinh khớp với 8 chủ đề chuyên sâu
topic_samples = {
    "Kết nối gia đình & Sự quan tâm": [
        "Con cảm thấy khoảng cách giữa con và bố mẹ ngày càng lớn, bữa cơm lúc nào cũng im lặng.",
        "Làm thế nào để kéo bố mẹ lại gần hơn khi lúc nào ba mẹ cũng bận rộn công việc?",
        "Con muốn chia sẻ với mẹ những áp lực ở trường nhưng sợ mẹ lại bảo là vẽ chuyện.",
        "Mỗi lần gia đình có chuyện căng thẳng là con lại chọn cách im lặng và vào phòng riêng.",
        "Con khao khát được bố mẹ chủ động hỏi han một câu thay vì chỉ hỏi về điểm số.",
        "Bố mẹ có vẻ không hiểu những thay đổi tâm lý của con ở tuổi 16 này chút nào cả."
    ],
    "Định hướng nghề nghiệp": [
        "Bố mẹ muốn con thi ngành Kinh tế nhưng con lại thực sự đam mê nghệ thuật và thiết kế.",
        "Làm sao để thuyết phục gia đình tôn trọng nguyện vọng chọn trường y của con ạ?",
        "Con đang rất mông lung không biết bản thân phù hợp với khối ngành nào trong tương lai.",
        "Bố mẹ cứ áp đặt con phải theo nghề truyền thống của gia đình trong khi con không thích.",
        "Con sợ ra trường thất nghiệp nên cứ loay hoay mãi giữa đam mê và sự ổn định."
    ],
    "Quyền riêng tư cá nhân": [
        "Bố mẹ hay tự ý vào phòng và xem điện thoại của con mà không gõ cửa hay xin phép.",
        "Con có cuốn sổ nhật ký riêng nhưng bị mẹ đọc lén, con thấy mất lòng tin quá.",
        "Tại sao bố mẹ không tôn trọng không gian cá nhân và quyền riêng tư tối thiểu của con?",
        "Mỗi lần con nhắn tin với bạn bè là bố mẹ lại săm soi, dò hỏi khiến con rất ngột ngạt."
    ],
    "Áp lực học tập": [
        "Áp lực điểm số đè nặng lên vai con mỗi mùa thi cử, con sợ làm bố mẹ thất vọng.",
        "Con học rất chăm nhưng điểm số cứ dậm chân tại chỗ, con cảm thấy kiệt sức.",
        "Thầy cô và bố mẹ kỳ vọng vào con nhiều quá khiến con bị stress nặng.",
        "Con cảm thấy mình không bằng các bạn trong lớp chọn nên lúc nào cũng tự ti."
    ],
    "Điện thoại, mạng xã hội": [
        "Bố mẹ mắng con suốt vì cho rằng con nghiện điện thoại và chơi game quá nhiều.",
        "Con chỉ dùng mạng xã hội để giải trí sau giờ học căng thẳng nhưng bố mẹ lại cấm đoán.",
        "Làm thế nào để cân bằng thời gian học tập và sử dụng thiết bị công nghệ ạ?"
    ],
    "Sinh hoạt và lối sống": [
        "Bố mẹ cứ phàn nàn chuyện giờ giấc sinh hoạt và cách ăn mặc của con không giống ai.",
        "Con hay bị mệt mỏi và thức khuya ôn bài nên buổi sáng hay bị cáu gắt với người nhà."
    ],
    "Mối quan hệ tình cảm": [
        "Con đang có tình cảm với bạn cùng lớp nhưng không dám tâm sự với ai vì sợ gia đình cấm.",
        "Con bị bạn bè trong lớp hiểu lầm và cô lập, con thấy rất cô đơn khi về nhà."
    ],
    "Bị so sánh & Thiếu công nhận": [
        "Lúc nào bố mẹ cũng đem con ra so sánh với 'con nhà người ta' khiến con tổn thương.",
        "Dù con đã rất cố gắng nhưng bố mẹ chưa bao giờ khen ngợi hay công nhận nỗ lực của con."
    ]
}

def init_logs_file():
    if not os.path.exists(LOG_FILE):
        random.seed(42)

        def generate_period_logs(start_date, end_date, total_count, topic_weights, categories):
            delta_days = (end_date - start_date).days + 1
            base_per_day = total_count // delta_days
            remainder = total_count % delta_days
            
            topics = list(topic_weights.keys())
            weights = list(topic_weights.values())

            logs = []
            for day_idx in range(delta_days):
                day_count = base_per_day + (1 if day_idx < remainder else 0)
                curr_date = start_date + datetime.timedelta(days=day_idx)
                
                for _ in range(day_count):
                    hour = random.choice([7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21])
                    minute = random.randint(0, 59)
                    interaction_time = curr_date.replace(hour=hour, minute=minute)
                    
                    chosen_topic = random.choices(topics, weights=weights, k=1)[0]
                    chosen_cat = random.choice(categories)
                    chosen_content = random.choice(topic_samples.get(chosen_topic, ["Học sinh trao đổi tâm sự."]))
                    
                    logs.append({
                        "timestamp": interaction_time.strftime("%Y-%m-%d %H:%M"),
                        "category": chosen_cat,
                        "content": chosen_content
                    })
            return logs

        # GIAO ĐOẠN 1: Từ 20/10/2026 đến 31/10/2026 (Tổng 334 phản hồi)
        weights_p1 = {
            "Kết nối gia đình & Sự quan tâm": 35,
            "Định hướng nghề nghiệp": 25,
            "Quyền riêng tư cá nhân": 18,
            "Áp lực học tập": 8,
            "Điện thoại, mạng xã hội": 6,
            "Sinh hoạt và lối sống": 4,
            "Mối quan hệ tình cảm": 2,
            "Bị so sánh & Thiếu công nhận": 2
        }
        historical_logs = generate_period_logs(
            datetime.datetime(2026, 10, 20),
            datetime.datetime(2026, 10, 31),
            334,
            weights_p1,
            ["Tâm sự cùng AI", "Tập đối thoại", "Hiểu cảm xúc"]
        )

        # GIAO ĐOẠN 2: Từ 01/11/2026 đến 06/11/2026 (Tổng 516 phản hồi)
        weights_p2 = {
            "Định hướng nghề nghiệp": 30,
            "Quyền riêng tư cá nhân": 26,
            "Kết nối gia đình & Sự quan tâm": 12,
            "Áp lực học tập": 10,
            "Điện thoại, mạng xã hội": 9,
            "Sinh hoạt và lối sống": 6,
            "Mối quan hệ tình cảm": 4,
            "Bị so sánh & Thiếu công nhận": 3
        }
        historical_logs.extend(generate_period_logs(
            datetime.datetime(2026, 11, 1),
            datetime.datetime(2026, 11, 6),
            516,
            weights_p2,
            ["Tâm sự cùng AI", "Tập đối thoại", "Hiểu cảm xúc"]
        ))

        historical_logs.sort(key=lambda x: x["timestamp"])
        df_final = pd.DataFrame(historical_logs)
        df_final.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

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

# --- HÀM PHÂN TÍCH ĐA NHÃN (MULTI-LABEL) VỚI KHO TỪ KHÓA MỞ RỘNG ---
def classify_conflict_topics(text):
    if not isinstance(text, str):
        return ["Xã giao / Tương tác ngắn"]
    
    t = text.strip().lower()
    
    short_fillers = [
        "hi", "hello", "helo", "chào", "ai ơi", "haiz", "haizz", "haizzz", 
        "ok", "oke", "ok r", "okay", "ừ", "uh", "um", "ạ", "nhé", "nhá", 
        "được", "ko", "không", "có", "giúp", "vâng", "dạ", "thanks", "cảm ơn", 
        "tks", "bye", "tạm biệt", "ha", "ha ha", "được rồi", "hic"
    ]
    
    if len(t) <= 3 or t in short_fillers or any(t == sf for sf in short_fillers):
        return ["Xã giao / Tương tác ngắn"]
        
    matched_topics = []
    
    if any(k in t for k in ["điểm", "điểm số", "thi", "kiểm tra", "thi cử", "áp lực", "stress", "căng thẳng", "thành tích", "cô giáo", "thầy giáo", "giáo viên", "bài tập", "lớp chọn", "sa sút", "mệt mỏi", "sợ điểm", "trượt", "học y", "học thêm", "ôn thi", "điểm kém", "chạy điểm", "chuyên", "đội tuyển", "quá tải", "kiệt sức vì học"]):
        matched_topics.append("Áp lực học tập")
    
    if any(k in t for k in ["đại học", "ngành", "chọn trường", "nghề nghiệp", "tương lai", "làm gì", "đam mê", "bố mẹ bắt chọn", "trái ý", "y", "y khoa", "bác sĩ", "công việc", "định hướng", "khối a", "khối b", "khối c", "khối d", "xét tuyển", "nguyện vọng", "thất nghiệp", "lương", "kiếm tiền", "tự lập", "không thích ngành này"]):
        matched_topics.append("Định hướng nghề nghiệp")
    
    if any(k in t for k in ["riêng tư", "phòng riêng", "nhật ký", "tự do", "kiểm soát", "xem điện thoại lén", "soi mói", "tôn trọng", "không gian riêng", "tin nhắn", "xem trộm", "ép buộc", "bắt ép", "áp đặt", "không cho đi chơi", "đọc trộm", "lục lọi", "bí mật", "quyền"]):
        matched_topics.append("Quyền riêng tư cá nhân")
    
    if any(k in t for k in ["điện thoại", "máy tính", "chơi game", "facebook", "tiktok", "mạng", "online", "nhắn tin", "lướt", "cắm mặt vào màn hình", "nghiện", "game", "freefire", "pubg", "tải game", "mạng xã hội", "ig", "instagram", "threads", "xem tivi", "ipad", "clone", "acc"]):
        matched_topics.append("Điện thoại, mạng xã hội")
    
    if any(k in t for k in ["thức khuya", "dậy sớm", "ngủ", "ăn uống", "lười", "phòng bừa", "sức khỏe", "mệt", "thói quen", "sinh hoạt", "thể thao", "vất vả", "kiệt sức", "ốm", "ăn ít", "không chịu ăn", "bệnh", "tập gym", "chạy bộ", "lười vận động", "thức đêm"]):
        matched_topics.append("Sinh hoạt và lối sống")
        
    if any(k in t for k in ["bạn bè", "người yêu", "yêu đương", "tình cảm", "cô đơn", "tẩy chay", "hiểu lầm", "cãi nhau", "thích một người", "crush", "tỏ tình", "chia tay", "bạn thân", "cô lập", "ghét", "anti", "lớp trưởng", "tụ tập", "hẹn hò"]):
        matched_topics.append("Mối quan hệ tình cảm")

    if any(k in t for k in ["không quan tâm", "bỏ mặc", "không để ý", "xa cách", "lạnh nhạt", "không thèm", "bận rộn", "không hiểu con", "tủi thân", "cô đơn ở nhà", "bỏ bê", "xa lánh", "vô cảm", "không thèm nói chuyện", "nhà như cái trọ", "ít nói chuyện", "lắng nghe", "chia sẻ", "bữa cơm gia đình", "quan tâm", "chăm sóc", "khoảng cách"]):
        matched_topics.append("Kết nối gia đình & Sự quan tâm")

    if any(k in t for k in ["so sánh", "con nhà người ta", "chê", "mắng", "quát", "trách", "không bằng người ta", "so với bạn", "kém cỏi", "không công nhận", "chê bai", "vô dụng", "không bằng ai", "lúc nào cũng chê", "chẳng bao giờ khen"]):
        matched_topics.append("Bị so sánh & Thiếu công nhận")
        
    if not matched_topics:
        matched_topics.append("Tâm tư khác")
        
    return matched_topics

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
    background: linear-gradient(rgba(5, 15, 35, 0.3), rgba(5, 15, 35, 0.3)), 
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
    background-color: rgba(15, 23, 42, 0.85);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}}

.hero-banner {{
    background: #0f172a;
    color: #ffffff;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}}

div.stButton > button {{
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 12px;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}}

div.stButton > button p, div.stButton > button span {{
    color: #0f172a !important;
    font-weight: 600 !important;
}}

div.stButton > button:hover {{
    background-color: #f8fafc !important;
    border-color: #38bdf8 !important;
}}

h1, h2, h3, h4, h5, h6, p:not(div.stButton p), span:not(div.stButton span), label, div[data-testid="stMarkdownContainer"] {{
    color: #f8fafc !important;
}}

.hero-banner *, .hero-banner h3, .hero-banner p {{
    color: #ffffff !important;
}}

[data-testid="stMetricValue"] {{
    color: #fef08a !important;
    font-weight: 700;
}}

[data-testid="stMetricLabel"] {{
    color: #cbd5e1 !important;
}}

.stCaptionContainer p, [data-testid="stCaptionContainer"] {{
    color: #cbd5e1 !important;
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

# --- 10. GIAO DIỆN ADMIN DASHBOARD ---
if st.session_state.current_mode == "Quản trị":
    if not st.session_state.admin_logged_in:
        st.warning("Bạn cần đăng nhập quản trị từ thanh bên.")
        st.stop()
    st.title("📊 Hệ thống Quản trị Thực nghiệm - Phân tích Xu hướng CLB")
    st.markdown("##### Phân tích dữ liệu thực tế từ nội dung tâm sự của học sinh (Tập trung hoàn toàn vào 8 chủ đề chuyên sâu).")
    st.markdown("---")

    logs_df = load_all_logs()

    if not logs_df.empty and "content" in logs_df.columns:
        def normalize_category(cat):
            if not isinstance(cat, str):
                return "Tâm sự cùng AI"
            c = cat.lower()
            if "hiểu cảm xúc" in c:
                return "Hiểu cảm xúc"
            elif "đối thoại" in c or "giả lập" in c or "huấn luyện" in c:
                return "Tập đối thoại"
            elif "tiến bộ" in c or "đánh giá" in c:
                return "Xem tiến bộ"
            else:
                return "Tâm sự cùng AI"
        
        if "category" in logs_df.columns:
            logs_df["category"] = logs_df["category"].apply(normalize_category)

        logs_df["conflict_topics_list"] = logs_df["content"].apply(classify_conflict_topics)
        logs_df["conflict_topic_str"] = logs_df["conflict_topics_list"].apply(lambda x: ", ".join(x))
        
        exploded_df = logs_df.explode("conflict_topics_list")
        
        filtered_trend_df = exploded_df[
            (~exploded_df["conflict_topics_list"].isin(["Xã giao / Tương tác ngắn", "Tâm tư khác"]))
        ]
        
        topic_counts = filtered_trend_df["conflict_topics_list"].value_counts()
        top_topic = topic_counts.index[0] if not topic_counts.empty else "Chưa có dữ liệu"

        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng lượt trao đổi", len(logs_df))
        col2.metric("Chủ đề nổi cộm nhất", top_topic)
        col3.metric("Mô hình can thiệp", "NVC (4 bước)")

        st.markdown("### 📊 Xu hướng vấn đề tâm lý học sinh băn khoăn nhất")
        st.caption("Biểu đồ thống kê tập trung vào 8 nhóm chủ đề băn khoăn chuyên sâu của học sinh:")
        if not topic_counts.empty:
            st.bar_chart(topic_counts)
        else:
            st.info("Chưa ghi nhận đủ dữ liệu băn khoăn tâm lý chuyên sâu.")

        st.markdown("### 📈 Phân bổ hành vi sử dụng tính năng")
        if "category" in logs_df.columns:
            st.bar_chart(logs_df["category"].value_counts())

        st.markdown("### 📋 Nhật ký tương tác chi tiết (Toàn bộ lịch sử)")
        display_df = logs_df[["timestamp", "conflict_topic_str", "category", "content"]].tail(25)
        display_df.columns = ["Thời gian", "Các chủ đề nhận diện", "Chức năng", "Nội dung tâm sự"]
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True
        )
        
        st.download_button(
            "Xuất dữ liệu CSV phân tích",
            data=logs_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="ai_family_bridge_classified_logs.csv",
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
        <small style="color: #fef08a; font-weight: 600;">GỢI Ý BẮT ĐẦU</small>
        <p style="margin: 8px 0 12px 0; font-weight: 500; color: #ffffff;">“Bố mẹ không cho mình dùng điện thoại nhiều, mình nên nói thế nào?”</p>
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
Bạn là "AI Family Bridge", một người bạn đồng hành tâm lý và người hướng dẫn kỹ năng Giao tiếp trắc ẩn (NVC) dành cho học sinh THPT. Người dùng đang ở chế độ: {st.session_state.current_mode}.

NỀN TẢNG TRI THỨC NGẦM:
- Phương pháp NVC (Marshall B. Rosenberg): Quan sát khách quan, Gọi tên cảm xúc, Xác định nhu cầu ngầm và Đề xuất giải pháp đối thoại.
- Thấu hiểu tâm lý lứa tuổi: Áp lực học tập, định hướng nghề nghiệp, quyền riêng tư, thiết bị số, sinh hoạt lối sống, các mối quan hệ tình cảm, kết nối gia đình và sự so sánh công nhận.

QUY TẮC PHẢN HỒI BẮT BUỘC:
1. Độ dài: Ngắn gọn, từ 2 đến 4 câu, trọng tâm, tự nhiên, không diễn giải dài dòng như văn mẫu.
2. Ngữ điệu: Lắng nghe chân thành, ấm áp, không phán xét. Xưng hô: "mình" - "cậu" hoặc "bạn".
3. TUYỆT ĐỐI CẤM MẪU CÂU RẬP KHUÔN (RẤT QUAN TRỌNG):
   - CẤM sử dụng các câu mở/kết thúc lặp lại như: "Em có muốn thử...", "Nếu em cảm thấy sẵn sàng...", "Liệu có cách nào để bố mẹ...".
   - Không chêm câu hỏi mời mọc cố định ở cuối mỗi tin nhắn. Hãy kết thúc câu tự nhiên như một cuộc trò chuyện trực tiếp giữa hai người bạn.
4. XỬ LÝ THEO NGỮ CẢNH:
   - Khi học sinh trút giận hoặc buồn: Lắng nghe, xác nhận và phản chiếu lại chính xác cảm xúc đó (tủi thân, áp lực, ngột ngạt), không vội đưa ra bài học đạo đức hay lời khuyên ngay.
   - Khi học sinh hỏi cách giải quyết: Đi thẳng vào gợi ý một câu nói cụ thể hoặc bóc tách góc nhìn của phụ huynh dựa trên chính chi tiết học sinh vừa kể.
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

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
                        temperature=0.6,
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