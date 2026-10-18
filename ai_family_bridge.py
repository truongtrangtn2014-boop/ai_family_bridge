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
