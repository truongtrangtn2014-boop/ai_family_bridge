"""
AI Family Bridge – Cầu nối Gia đình Số
Bản giao diện được tổ chức lại theo 4 chức năng: Tâm sự, Phòng tập đối thoại,
Nhận diện cảm xúc và Tiến bộ của tôi.

Cấu trúc thư mục khuyến nghị:
  ai_family_bridge_redesigned.py
  background.png                         (hoặc assets/background.png / background.jpg)
  Co_so_ly_luan_Chuyen_sau.docx
  Luan_an_TS_Nguyen_Thi_Hong_Hanh_2023.pdf
  .streamlit/secrets.toml                (GEMINI_API_KEY = "...")
"""

from pathlib import Path
import base64
import datetime
import mimetypes
import os

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types


# ---------------------------------------------------------------------
# 1. CẤU HÌNH CHUNG VÀ ĐƯỜNG DẪN TÀI NGUYÊN
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="AI Family Bridge – Cầu nối Gia đình Số",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"

# Ưu tiên tên file chuẩn; hỗ trợ cả tên PDF cũ có đuôi .pdf.pdf.
DOCUMENT_CANDIDATES = {
    "Cơ sở lý luận chuyên sâu": [
        "Co_so_ly_luan_Chuyen_sau.docx",
        "Cơ sở lý luận chuyên sâu.docx",
    ],
    "Luận án TS Nguyễn Thị Hồng Hạnh (2023)": [
        "Luan_an_TS_Nguyen_Thi_Hong_Hanh_2023.pdf",
        "Luan_an_TS_Nguyen_Thi_Hong_Hanh_2023.pdf.pdf",
        "Luận án TS Nguyễn Thị Hồng Hạnh 2023.pdf",
    ],
}

BACKGROUND_CANDIDATES = [
    BASE_DIR / "background.png",
    ASSET_DIR / "background.png",
    BASE_DIR / "background.jpg",
    ASSET_DIR / "background.jpg",
    BASE_DIR / "background.jpeg",
    ASSET_DIR / "background.jpeg",
    BASE_DIR / "background.webp",
    ASSET_DIR / "background.webp",
]


def find_first_existing(candidates):
    """Trả về đường dẫn đầu tiên tồn tại, tránh phụ thuộc thư mục chạy lệnh."""
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    return None


def find_document(candidates):
    """Tìm tài liệu cạnh file Python hoặc trong thư mục assets/."""
    for filename in candidates:
        for folder in (BASE_DIR, ASSET_DIR):
            candidate = folder / filename
            if candidate.is_file():
                return candidate
    return None


def image_as_data_uri(path):
    if not path:
        return ""
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


background_path = find_first_existing(BACKGROUND_CANDIDATES)
background_uri = image_as_data_uri(background_path)


# ---------------------------------------------------------------------
# 2. GIAO DIỆN: NỀN XANH CÔNG NGHỆ, TRUNG TÂM DỄ ĐỌC
# ---------------------------------------------------------------------
if background_uri:
    background_css = f"""
    background-image:
      linear-gradient(135deg, rgba(5, 25, 58, .82), rgba(8, 54, 108, .76)),
      url("{background_uri}");
    background-position: center center;
    background-repeat: no-repeat;
    background-size: cover;
    background-attachment: fixed;
    """
else:
    # Dự phòng khi chưa đặt ảnh nền cạnh mã nguồn.
    background_css = """
    background:
      radial-gradient(circle at 8% 8%, rgba(22, 163, 255, .20), transparent 28%),
      radial-gradient(circle at 95% 20%, rgba(0, 229, 255, .13), transparent 25%),
      linear-gradient(135deg, #06172f 0%, #0a3470 55%, #06172f 100%);
    """

st.markdown(
    f"""
    <style>
    :root {{
      --afb-navy: #071a35;
      --afb-blue: #0b3470;
      --afb-cyan: #75d7ff;
      --afb-white: #f7fbff;
      --afb-muted: #d5e4f7;
    }}
    .stApp {{
      {background_css}
      color: var(--afb-white);
    }}
    [data-testid="stHeader"] {{
      background: rgba(5, 20, 45, .18);
    }}
    [data-testid="stSidebar"] {{
      background: rgba(4, 19, 41, .94);
      border-right: 1px solid rgba(117, 215, 255, .25);
    }}
    [data-testid="stSidebar"] * {{
      color: #f3f8ff;
    }}
    .block-container {{
      padding-top: 2rem;
      padding-bottom: 3rem;
      max-width: 1450px;
    }}
    h1, h2, h3 {{
      color: #ffffff !important;
      letter-spacing: -.02em;
    }}
    p, li, label, [data-testid="stMarkdownContainer"] {{
      color: #f0f6ff;
    }}
    .afb-eyebrow {{
      color: #85ddff;
      font-size: .82rem;
      font-weight: 800;
      letter-spacing: .14em;
      text-transform: uppercase;
      margin-bottom: .4rem;
    }}
    .afb-hero-title {{
      color: #ffffff;
      font-size: clamp(2rem, 4vw, 3.25rem);
      font-weight: 850;
      line-height: 1.12;
      margin: .15rem 0 .75rem 0;
    }}
    .afb-subtitle {{
      color: #d6e7fb;
      font-size: 1.06rem;
      line-height: 1.7;
      max-width: 900px;
    }}
    .afb-panel {{
      background: rgba(7, 25, 52, .82);
      border: 1px solid rgba(184, 220, 255, .22);
      border-radius: 20px;
      padding: 1.15rem 1.25rem;
      box-shadow: 0 12px 34px rgba(0, 0, 0, .18);
      backdrop-filter: blur(10px);
    }}
    .afb-card {{
      min-height: 170px;
      background: rgba(7, 27, 56, .84);
      border: 1px solid rgba(135, 205, 255, .30);
      border-radius: 18px;
      padding: 1.05rem;
      margin-bottom: .55rem;
      backdrop-filter: blur(10px);
    }}
    .afb-card-icon {{
      font-size: 1.8rem;
      margin-bottom: .35rem;
    }}
    .afb-card-title {{
      color: #ffffff;
      font-size: 1.05rem;
      font-weight: 800;
      margin-bottom: .35rem;
    }}
    .afb-card-desc {{
      color: #d5e4f7;
      font-size: .92rem;
      line-height: 1.5;
    }}
    .afb-chip {{
      display: inline-block;
      border: 1px solid rgba(117, 215, 255, .42);
      background: rgba(20, 94, 150, .25);
      color: #bcecff;
      border-radius: 999px;
      padding: .28rem .7rem;
      font-size: .78rem;
      font-weight: 700;
    }}
    [data-testid="stChatMessage"] {{
      background: rgba(7, 25, 52, .86);
      border: 1px solid rgba(184, 220, 255, .22);
      border-radius: 18px;
      padding: 1rem 1.15rem;
      margin-bottom: .8rem;
      backdrop-filter: blur(10px);
    }}
    [data-testid="stChatInput"] {{
      background: rgba(245, 249, 255, .97);
      border: 1px solid rgba(117, 215, 255, .5);
      border-radius: 16px;
    }}
    [data-testid="stChatInput"] textarea {{
      color: #12233d !important;
    }}
    [data-testid="stMetric"] {{
      background: rgba(7, 25, 52, .78);
      border: 1px solid rgba(184, 220, 255, .18);
      border-radius: 15px;
      padding: .9rem;
    }}
    .stButton > button {{
      border-radius: 12px;
      font-weight: 700;
      min-height: 2.7rem;
      border: 1px solid rgba(117, 215, 255, .42);
    }}
    div[data-testid="stAlert"] {{
      border-radius: 14px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# 3. API KEY VÀ TÀI LIỆU NGHIÊN CỨU
# ---------------------------------------------------------------------
def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


API_KEY = get_api_key()
client = genai.Client(api_key=API_KEY) if API_KEY else None


@st.cache_resource(show_spinner=False)
def upload_research_documents(api_key, file_signatures):
    """Tải tài liệu lên Gemini một lần theo phiên cache."""
    if not api_key:
        return [], ["Chưa cấu hình GEMINI_API_KEY."]
    api_client = genai.Client(api_key=api_key)
    uploaded = []
    errors = []
    for display_name, path_string in file_signatures:
        path = Path(path_string)
        if not path.is_file():
            errors.append(f"Không tìm thấy: {display_name}")
            continue
        mime_type = (
            "application/pdf" if path.suffix.lower() == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        try:
            with path.open("rb") as file_handle:
                remote_file = api_client.files.upload(
                    file=file_handle,
                    config=types.UploadFileConfig(mime_type=mime_type),
                )
            uploaded.append((display_name, remote_file))
        except Exception as exc:
            errors.append(f"{display_name}: {exc}")
    return uploaded, errors


found_documents = []
missing_documents = []
for display_name, candidates in DOCUMENT_CANDIDATES.items():
    found_path = find_document(candidates)
    if found_path:
        found_documents.append((display_name, str(found_path)))
    else:
        missing_documents.append(display_name)

if API_KEY:
    loaded_docs_info, document_errors = upload_research_documents(
        API_KEY,
        tuple(found_documents),
    )
else:
    loaded_docs_info, document_errors = [], ["Chưa cấu hình GEMINI_API_KEY."]

preloaded_files = [item[1] for item in loaded_docs_info]


# ---------------------------------------------------------------------
# 4. SESSION STATE
# ---------------------------------------------------------------------
if "active_page" not in st.session_state:
    st.session_state.active_page = "Trang chủ"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interaction_logs" not in st.session_state:
    st.session_state.interaction_logs = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "roleplay_scenario" not in st.session_state:
    st.session_state.roleplay_scenario = "Sử dụng điện thoại"
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = ""


# ---------------------------------------------------------------------
# 5. HƯỚNG DẪN CHO AI
# ---------------------------------------------------------------------
SYSTEM_INSTRUCTION = """
Bạn là AI Family Bridge – trợ lý hỗ trợ học sinh THPT thực hành giao tiếp tích cực
với gia đình. Bạn không thay thế chuyên gia tâm lý và không đưa ra chẩn đoán.

Nguyên tắc:
- Lắng nghe, thấu cảm, không phán xét và không mặc định bố mẹ hay học sinh luôn sai.
- Khuyến khích học sinh hướng tới đối thoại trực tiếp an toàn, không phụ thuộc vào AI.
- Áp dụng 4 bước Giao tiếp phi bạo lực (NVC):
  1. Quan sát khách quan, không phán xét.
  2. Gọi tên cảm xúc của bản thân.
  3. Xác định nhu cầu cốt lõi.
  4. Đưa ra đề nghị cụ thể, nhã nhặn.
- Khi nhập vai, chỉ nói một lượt trong vai bố hoặc mẹ, rồi chờ học sinh trả lời.
  Không tự viết câu trả lời thay học sinh. Giữ tình huống chân thực nhưng không xúc phạm,
  đe dọa hoặc gây tổn thương.
- Sau khi học sinh kết thúc lượt nhập vai hoặc yêu cầu nhận xét, phản hồi theo các tiêu chí:
  nhận diện cảm xúc, diễn đạt nhu cầu, lắng nghe, tôn trọng và tìm giải pháp chung.
  Nêu điểm mạnh, một điểm cần cải thiện và một câu gợi ý để luyện lại; không chấm điểm
  như một kết luận tâm lý.
- Nếu học sinh nói về bạo lực, bị đe dọa hoặc nguy cơ mất an toàn, ưu tiên an toàn:
  khuyên em tìm người lớn đáng tin cậy hoặc hỗ trợ chuyên môn phù hợp; không coi đó
  chỉ là bất đồng thông thường.
- Chỉ khẳng định nội dung được tài liệu cung cấp hỗ trợ. Nếu không đủ căn cứ, hãy nói rõ.
"""


def switch_page(page_name):
    st.session_state.active_page = page_name


def log_interaction(category, content):
    st.session_state.interaction_logs.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": category,
        "content": content[:500],
    })


def run_ai(prompt, category="Tâm sự cùng AI"):
    if not client:
        st.error(
            "Chưa kết nối Gemini. Hãy cấu hình GEMINI_API_KEY trong "
            "Secrets hoặc biến môi trường rồi khởi động lại ứng dụng."
        )
        return

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    log_interaction(category, prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI Family Bridge đang suy nghĩ..."):
            try:
                # Gửi cả lịch sử hội thoại để nhập vai được liên tục qua nhiều lượt.
                prior_messages = st.session_state.messages[:-1]
                history_text = "\\n".join(
                    f'{"Học sinh" if item["role"] == "user" else "AI Family Bridge"}: {item["content"]}'
                    for item in prior_messages[-12:]
                )
                contextual_prompt = (
                    "LỊCH SỬ HỘI THOẠI GẦN ĐÂY (nếu có):\\n"
                    + (history_text if history_text else "(Chưa có lượt trước.)")
                    + "\\n\\nYÊU CẦU HIỆN TẠI:\\n"
                    + prompt
                )
                contents = preloaded_files + [contextual_prompt]
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.65,
                    ),
                )
                answer = response.text or (
                    "Mình chưa tạo được phản hồi lần này. Bạn thử diễn đạt lại nhé."
                )
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
                st.session_state.last_feedback = answer
            except Exception as exc:
                st.error(
                    "Không thể xử lý yêu cầu lúc này. Hãy kiểm tra kết nối, "
                    f"API key và cấu hình tài liệu. Chi tiết: {exc}"
                )


def show_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# ---------------------------------------------------------------------
# 6. THANH ĐIỀU HƯỚNG
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="font-size:2.8rem; margin-bottom:.2rem">🌉</div>
        <div style="font-size:1.35rem;font-weight:850;line-height:1.25">
          AI Family Bridge
        </div>
        <div style="color:#b9cce5;font-style:italic;margin-top:.45rem">
          Cầu nối Gia đình Số
        </div>
        <div style="color:#8edfff;font-size:.8rem;margin-top:.8rem">
          ĐỀ TÀI KHOA HỌC KỸ THUẬT
        </div>
        <div style="font-size:.9rem;line-height:1.5">
          Giải quyết khoảng trống giao tiếp gia đình
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("#### 🧭 Không gian của bạn")
    nav_items = [
        ("🏠", "Trang chủ"),
        ("💬", "Tâm sự cùng AI"),
        ("🎭", "Phòng tập đối thoại"),
        ("💙", "Nhận diện cảm xúc"),
        ("📈", "Tiến bộ của tôi"),
        ("📚", "Tài liệu nghiên cứu"),
    ]
    for icon, page in nav_items:
        if st.button(
            f"{icon}  {page}",
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if st.session_state.active_page == page else "secondary",
        ):
            switch_page(page)
            st.rerun()

    st.markdown("---")
    with st.expander("📁 Tình trạng tài liệu nghiên cứu", expanded=False):
        if loaded_docs_info:
            st.success(f"Đã tải lên Gemini: {len(loaded_docs_info)} tài liệu")
            for name, _ in loaded_docs_info:
                st.caption(f"📄 {name}")
        else:
            st.warning("Chưa có tài liệu nào được tải lên Gemini.")
        for name in missing_documents:
            st.caption(f"Chưa tìm thấy file: {name}")
        for err in document_errors:
            if "Chưa cấu hình GEMINI_API_KEY" not in err:
                st.caption(f"⚠️ {err}")
        if not background_path:
            st.warning(
                "Chưa tìm thấy ảnh nền. Đặt background.png cạnh file Python "
                "hoặc trong thư mục assets/."
            )
        else:
            st.caption(f"Ảnh nền: {background_path.name}")

    st.markdown("---")
    with st.expander("🔒 Cổng quản trị nhà trường", expanded=False):
        if not st.session_state.admin_logged_in:
            admin_password = st.text_input(
                "Mật khẩu quản trị",
                type="password",
                key="admin_password_input",
                placeholder="Nhập mật khẩu...",
            )
            try:
                expected_admin_password = str(
                    st.secrets.get("ADMIN_PASSWORD", "")
                ).strip()
            except Exception:
                expected_admin_password = ""
            if st.button("Đăng nhập quản trị", use_container_width=True):
                if expected_admin_password and admin_password == expected_admin_password:
                    st.session_state.admin_logged_in = True
                    st.session_state.active_page = "Quản trị"
                    st.rerun()
                elif not expected_admin_password:
                    st.error(
                        "Chưa cấu hình ADMIN_PASSWORD trong Secrets. "
                        "Không nên đặt mật khẩu quản trị trực tiếp trong mã nguồn."
                    )
                else:
                    st.error("Mật khẩu chưa chính xác.")
        else:
            st.success("Đã đăng nhập quản trị")
            if st.button("Đăng xuất", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.session_state.active_page = "Trang chủ"
                st.rerun()


# ---------------------------------------------------------------------
# 7. TRANG CHỦ
# ---------------------------------------------------------------------
page = st.session_state.active_page

if page == "Trang chủ":
    st.markdown('<div class="afb-eyebrow">Không gian kết nối gia đình</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="afb-hero-title">Hiểu mình. Hiểu bố mẹ.<br>Kết nối bằng đối thoại.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="afb-subtitle">AI Family Bridge đồng hành cùng học sinh THPT '
        'nhận diện cảm xúc, luyện tập cách diễn đạt và chuẩn bị cho những cuộc trò chuyện '
        'khó khăn với gia đình trong đời sống thực.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="afb-panel">
          <div style="display:flex;gap:14px;align-items:flex-start">
            <div style="font-size:2rem">🤖</div>
            <div>
              <div style="font-size:1.12rem;font-weight:800;margin-bottom:.35rem">
                Chào bạn! Hôm nay bạn muốn bắt đầu từ đâu?
              </div>
              <div style="color:#d5e4f7;line-height:1.6">
                Bạn có thể chia sẻ điều đang băn khoăn, hoặc luyện thử một cuộc trò chuyện
                với bố mẹ trước khi nói chuyện ngoài đời. Mình sẽ lắng nghe mà không phán xét.
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown("### ✨ Chọn hoạt động")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown(
            '<div class="afb-card"><div class="afb-card-icon">💬</div>'
            '<div class="afb-card-title">Tâm sự cùng AI</div>'
            '<div class="afb-card-desc">Chia sẻ bất đồng, áp lực hoặc điều bạn chưa biết '
            'mở lời với gia đình như thế nào.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Bắt đầu tâm sự  →", key="home_talk", use_container_width=True):
            switch_page("Tâm sự cùng AI")
            st.rerun()
    with col2:
        st.markdown(
            '<div class="afb-card"><div class="afb-card-icon">🎭</div>'
            '<div class="afb-card-title">Phòng tập đối thoại</div>'
            '<div class="afb-card-desc">AI vào vai bố hoặc mẹ để bạn thực hành từng lượt '
            'và nhận phản hồi kỹ năng giao tiếp.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Vào phòng tập  →", key="home_roleplay", use_container_width=True):
            switch_page("Phòng tập đối thoại")
            st.rerun()
    col3, col4 = st.columns(2, gap="medium")
    with col3:
        st.markdown(
            '<div class="afb-card"><div class="afb-card-icon">💙</div>'
            '<div class="afb-card-title">Nhận diện cảm xúc</div>'
            '<div class="afb-card-desc">Gọi tên cảm xúc, tìm nhu cầu phía sau và chọn '
            'cách diễn đạt bình tĩnh hơn.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Khám phá cảm xúc  →", key="home_emotion", use_container_width=True):
            switch_page("Nhận diện cảm xúc")
            st.rerun()
    with col4:
        st.markdown(
            '<div class="afb-card"><div class="afb-card-icon">📈</div>'
            '<div class="afb-card-title">Tiến bộ của tôi</div>'
            '<div class="afb-card-desc">Xem lại lượt thực hành và tự đánh giá những kỹ năng '
            'bạn muốn cải thiện.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Xem tiến bộ  →", key="home_progress", use_container_width=True):
            switch_page("Tiến bộ của tôi")
            st.rerun()

    st.write("")
    st.markdown("### 💡 Gợi ý bắt đầu")
    st.info("“Bố mẹ không cho mình dùng điện thoại nhiều, mình nên nói thế nào?”")
    if st.button("Luyện tình huống này", key="home_suggestion", use_container_width=False):
        st.session_state.roleplay_scenario = "Sử dụng điện thoại"
        switch_page("Phòng tập đối thoại")
        st.rerun()
    st.caption("AI là công cụ hỗ trợ thực hành, không thay thế người lớn đáng tin cậy hoặc chuyên gia khi bạn cần giúp đỡ.")


# ---------------------------------------------------------------------
# 8. TÂM SỰ CÙNG AI
# ---------------------------------------------------------------------
elif page == "Tâm sự cùng AI":
    st.title("💬 Tâm sự cùng AI")
    st.markdown("Mình sẽ lắng nghe và cùng bạn tìm cách mở lời phù hợp, không phán xét.")
    st.markdown('<div class="afb-chip">Lắng nghe · Thấu cảm · Tìm hướng giải quyết</div>', unsafe_allow_html=True)
    show_chat_history()
    if prompt := st.chat_input("Bạn đang băn khoăn điều gì khi giao tiếp với gia đình?"):
        run_ai(prompt, "Tâm sự cùng AI")


# ---------------------------------------------------------------------
# 9. PHÒNG TẬP ĐỐI THOẠI – ROLE-PLAYING
# ---------------------------------------------------------------------
elif page == "Phòng tập đối thoại":
    st.title("🎭 Phòng tập đối thoại")
    st.markdown(
        "Luyện tập trong không gian an toàn: AI vào vai phụ huynh, bạn trả lời bằng lời của mình."
    )
    scenario_options = [
        "Sử dụng điện thoại",
        "Điểm số và học tập",
        "Bất đồng quan điểm",
        "Khó mở lời tâm sự",
        "Chọn ngành nghề tương lai",
        "Thời gian đi chơi và giờ về nhà",
        "Tình huống của riêng tôi",
    ]
    selected_scenario = st.selectbox(
        "① Chọn tình huống",
        scenario_options,
        key="roleplay_scenario",
    )
    parent_role = st.radio("② AI sẽ đóng vai", ["Bố", "Mẹ"], horizontal=True)
    intensity = st.select_slider(
        "③ Mức độ thử thách",
        options=["Nhẹ nhàng", "Vừa phải", "Khó hơn"],
        value="Vừa phải",
        help="Mức độ thể hiện sự lo lắng hoặc bất đồng; không sử dụng lời lẽ xúc phạm hay đe dọa.",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Bắt đầu nhập vai", type="primary", use_container_width=True):
            roleplay_prompt = (
                f"Hãy bắt đầu một phiên role-playing về tình huống: {selected_scenario}. "
                f"Bạn đóng vai {parent_role}; mức thử thách: {intensity}. "
                "Mở đầu bằng đúng một câu nói tự nhiên của phụ huynh, sau đó dừng lại chờ "
                "học sinh phản hồi. Không đưa lời khuyên trước khi học sinh trả lời."
            )
            st.session_state.messages = []
            run_ai(roleplay_prompt, "Đóng vai giả lập (Role-play)")
    with col_b:
        if st.button("Nhận xét lượt vừa rồi", use_container_width=True):
            review_prompt = (
                "Hãy nhận xét các lượt hội thoại role-play gần nhất trong lịch sử đang có. "
                "Dùng 4 bước NVC và các tiêu chí: nhận diện cảm xúc, diễn đạt nhu cầu, "
                "lắng nghe, tôn trọng và tìm giải pháp chung. Nêu điểm mạnh, một điều cần "
                "cải thiện và một câu gợi ý để học sinh luyện lại. Nếu chưa có đủ hội thoại, "
                "hãy đề nghị học sinh thực hành trước."
            )
            run_ai(review_prompt, "Phản hồi sau nhập vai")
    st.markdown("---")
    show_chat_history()
    if prompt := st.chat_input("Đến lượt bạn trả lời phụ huynh..."):
        run_ai(
            f"Tiếp tục phiên nhập vai {selected_scenario}. Hãy tiếp tục đúng vai {parent_role}, "
            f"mức thử thách {intensity}. Học sinh vừa nói: {prompt}. "
            "Phản hồi tự nhiên trong vai phụ huynh, chỉ một lượt rồi chờ học sinh.",
            "Đóng vai giả lập (Role-play)",
        )


# ---------------------------------------------------------------------
# 10. NHẬN DIỆN CẢM XÚC
# ---------------------------------------------------------------------
elif page == "Nhận diện cảm xúc":
    st.title("💙 Nhận diện cảm xúc")
    st.markdown(
        "Dành một phút để hiểu điều đang diễn ra bên trong bạn trước khi bắt đầu đối thoại."
    )
    with st.form("emotion_form"):
        emotion = st.selectbox(
            "① Hiện tại bạn cảm thấy thế nào?",
            ["Buồn", "Tức giận", "Lo lắng", "Tủi thân", "Bối rối", "Thất vọng", "Cô đơn", "Bình tĩnh", "Khác"],
        )
        situation = st.text_area(
            "② Chuyện gì đã xảy ra?",
            placeholder="Bạn có thể kể ngắn gọn, không cần ghi tên thật hoặc thông tin riêng tư...",
            height=120,
        )
        need = st.selectbox(
            "③ Điều bạn mong muốn nhất lúc này là gì?",
            [
                "Được lắng nghe",
                "Được tôn trọng",
                "Được giải thích rõ ràng",
                "Có thêm quyền tự chủ",
                "Được hỗ trợ",
                "Tìm giải pháp cùng nhau",
                "Mình chưa rõ",
            ],
        )
        submitted = st.form_submit_button("Cùng AI tìm cách diễn đạt", type="primary")
    if submitted:
        if not situation.strip():
            st.warning("Bạn hãy mô tả ngắn gọn tình huống để AI có thể hỗ trợ.")
        else:
            emotion_prompt = (
                f"Học sinh đang cảm thấy {emotion}. Tình huống: {situation}. "
                f"Nhu cầu em đang nghĩ tới: {need}. Hãy giúp em phân biệt sự kiện và suy diễn, "
                "xác nhận cảm xúc mà không kết luận thay em, rồi gợi ý một câu theo 4 bước NVC. "
                "Không chẩn đoán tâm lý."
            )
            run_ai(emotion_prompt, "Nhận diện cảm xúc")
    st.markdown("---")
    st.markdown("#### Bốn bước NVC")
    nvc_cols = st.columns(4)
    nvc_steps = [
        ("1. Quan sát", "Điều gì đã xảy ra, không phán xét?"),
        ("2. Cảm xúc", "Mình đang cảm thấy thế nào?"),
        ("3. Nhu cầu", "Điều gì quan trọng với mình?"),
        ("4. Đề nghị", "Mình có thể đề nghị điều gì cụ thể?"),
    ]
    for col, (heading, description) in zip(nvc_cols, nvc_steps):
        with col:
            st.markdown(
                f'<div class="afb-card" style="min-height:145px">'
                f'<div class="afb-card-title">{heading}</div>'
                f'<div class="afb-card-desc">{description}</div></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------
# 11. TIẾN BỘ CỦA TÔI
# ---------------------------------------------------------------------
elif page == "Tiến bộ của tôi":
    st.title("📈 Tiến bộ của tôi")
    st.markdown(
        "Trang này hiện theo dõi các lượt tương tác trong phiên chạy ứng dụng. "
        "Chưa phải hồ sơ cá nhân lưu bền vững giữa các lần truy cập."
    )
    total = len(st.session_state.interaction_logs)
    roleplay_count = sum(
        "Đóng vai" in row["category"] for row in st.session_state.interaction_logs
    )
    emotion_count = sum(
        row["category"] == "Nhận diện cảm xúc"
        for row in st.session_state.interaction_logs
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Lượt tương tác", total)
    col2.metric("Lượt nhập vai", roleplay_count)
    col3.metric("Lượt nhận diện cảm xúc", emotion_count)

    st.markdown("### 🧭 Tự đánh giá sau luyện tập")
    with st.form("self_assessment_form"):
        st.caption("Đánh giá theo cảm nhận của bạn, từ 1 (chưa tự tin) đến 5 (rất tự tin).")
        self_confidence = st.slider("Mức tự tin khi mở lời", 1, 5, 3)
        self_empathy = st.slider("Khả năng nói về cảm xúc và nhu cầu", 1, 5, 3)
        self_listening = st.slider("Khả năng lắng nghe và tôn trọng", 1, 5, 3)
        saved_assessment = st.form_submit_button("Lưu đánh giá trong phiên này")
    if saved_assessment:
        st.session_state.interaction_logs.append({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "Tự đánh giá",
            "content": (
                f"Mở lời: {self_confidence}/5; "
                f"Cảm xúc và nhu cầu: {self_empathy}/5; "
                f"Lắng nghe và tôn trọng: {self_listening}/5"
            ),
        })
        st.success("Đã ghi nhận tự đánh giá trong phiên hiện tại.")
        st.rerun()

    if st.session_state.interaction_logs:
        st.markdown("### Nhật ký tương tác trong phiên")
        logs_df = pd.DataFrame(st.session_state.interaction_logs)
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Tải nhật ký CSV",
            data=logs_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="ai_family_bridge_nhat_ky.csv",
            mime="text/csv",
        )
    else:
        st.info("Bạn chưa có lượt tương tác nào trong phiên này.")


# ---------------------------------------------------------------------
# 12. TÀI LIỆU NGHIÊN CỨU
# ---------------------------------------------------------------------
elif page == "Tài liệu nghiên cứu":
    st.title("📚 Cơ sở lý luận và tài liệu nghiên cứu")
    st.markdown(
        "Các tài liệu này được dùng làm ngữ cảnh tham khảo cho phản hồi của AI khi đã "
        "được tìm thấy và tải lên Gemini thành công."
    )
    if loaded_docs_info:
        for name, remote_file in loaded_docs_info:
            st.markdown(f"**📄 {name}**")
            st.caption(f"Trạng thái: đã tải lên Gemini · Tên tệp từ API: {getattr(remote_file, 'name', 'đã tải lên')}")
    else:
        st.warning(
            "Hiện chưa có tài liệu nào được tải lên Gemini. Kiểm tra tên file, vị trí "
            "tài liệu và GEMINI_API_KEY."
        )
    if missing_documents:
        st.markdown("#### Tài liệu chưa tìm thấy trên máy chủ")
        for name in missing_documents:
            st.write(f"- {name}")
    if document_errors:
        st.markdown("#### Thông báo")
        for err in document_errors:
            st.caption(f"⚠️ {err}")
    st.markdown("---")
    st.markdown("#### Nguyên tắc sử dụng tài liệu")
    st.write(
        "AI được yêu cầu ưu tiên căn cứ có trong tài liệu đã nạp. Việc tải file lên Gemini "
        "không đồng nghĩa với việc hệ thống đã kiểm chứng độc lập mọi nội dung trong file."
    )


# ---------------------------------------------------------------------
# 13. BẢNG ĐIỀU KHIỂN QUẢN TRỊ
# ---------------------------------------------------------------------
elif page == "Quản trị":
    if not st.session_state.admin_logged_in:
        st.warning("Bạn cần đăng nhập quản trị từ thanh bên.")
        st.stop()
    st.title("📊 Quản trị thực nghiệm")
    st.markdown(
        "Bảng tổng hợp nhật ký tương tác đang lưu trong bộ nhớ phiên Streamlit."
    )
    logs_df = pd.DataFrame(st.session_state.interaction_logs)
    total_logs = len(logs_df)
    roleplay_logs = (
        int(logs_df["category"].str.contains("Đóng vai", na=False).sum())
        if not logs_df.empty else 0
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng lượt tương tác", total_logs)
    col2.metric("Lượt nhập vai", roleplay_logs)
    col3.metric("Tài liệu đã nạp", len(loaded_docs_info))
    if not logs_df.empty:
        st.markdown("### Phân bổ lượt tương tác")
        st.bar_chart(logs_df["category"].value_counts())
        st.markdown("### Nhật ký")
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Xuất nhật ký thực nghiệm CSV",
            data=logs_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="ai_family_bridge_admin_logs.csv",
            mime="text/csv",
        )
    else:
        st.info("Chưa có dữ liệu tương tác trong phiên này.")

    st.caption(
        "Lưu ý nghiên cứu: dữ liệu trong bản này nằm trong session_state, "
        "có thể mất khi phiên kết thúc hoặc ứng dụng khởi động lại. "
        "Không nên xem đây là kho dữ liệu thực nghiệm lâu dài."
    )


# ---------------------------------------------------------------------
# 14. CHÂN TRANG VÀ CẢNH BÁO CẤU HÌNH
# ---------------------------------------------------------------------
if page != "Quản trị":
    st.markdown("---")
    footer_left, footer_right = st.columns([3, 2])
    with footer_left:
        st.caption("🌉 AI Family Bridge · Hiểu mình – Hiểu bố mẹ – Kết nối bằng đối thoại")
    with footer_right:
        if not API_KEY:
            st.caption("⚙️ Gemini chưa kết nối: cần cấu hình GEMINI_API_KEY.")
        elif not loaded_docs_info:
            st.caption("📚 Chưa nạp được tài liệu nghiên cứu.")
        else:
            st.caption(f"📚 Đã nạp {len(loaded_docs_info)} tài liệu nghiên cứu.")
