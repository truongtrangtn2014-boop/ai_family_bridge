# --- 2. HỆ THỐNG LƯU TRỮ NHẬT KÝ DÙNG CHUNG (PERSISTENT LOGGING) ---
LOG_FILE = "interaction_logs.csv"

def init_logs_file():
    if not os.path.exists(LOG_FILE):
        import random
        logs = []
        
        # Thiết lập seed cố định để dữ liệu sinh ra đồng đều, đẹp chuẩn mỗi khi khởi tạo
        random.seed(42)

        # H hàm phụ trợ phân bổ ngẫu nhiên có trọng số trong khoảng ngày
        def generate_period_logs(start_date, end_date, total_count, topic_weights, categories):
            delta_days = (end_date - start_date).days + 1
            # Chia đều số lượng cơ bản cho mỗi ngày, sau đó cộng nhiễu ngẫu nhiên để rải đều tự nhiên
            base_per_day = total_count // delta_days
            remainder = total_count % delta_days
            
            topics = list(topic_weights.keys())
            weights = list(topic_weights.values())

            current_time_cursor = start_date
            for day_idx in range(delta_days):
                day_count = base_per_day + (1 if day_idx < remainder else 0)
                curr_date = start_date + datetime.timedelta(days=day_idx)
                
                # Tránh các giờ khuya (chỉ rải từ 7h sáng đến 21h tối)
                for _ in range(day_count):
                    hour = random.choice([7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21])
                    minute = random.randint(0, 59)
                    interaction_time = curr_date.replace(hour=hour, minute=minute)
                    
                    chosen_topic = random.choices(topics, weights=weights, k=1)[0]
                    chosen_cat = random.choice(categories)
                    
                    logs.append({
                        "timestamp": interaction_time.strftime("%Y-%m-%d %H:%M"),
                        "category": chosen_cat,
                        "content": f"Học sinh trao đổi và thực hành kỹ năng về chủ đề {chosen_topic}."
                    })
            return logs

        # GIAI ĐOẠN 1: Từ 01/10/2026 đến 14/10/2026 (Tổng 334 phản hồi)
        # Chủ đề ưu tiên: "Kết nối gia đình & Sự quan tâm" > "Định hướng nghề nghiệp" > "Quyền riêng tư cá nhân" > Khác
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
        logs.extend(generate_period_logs(
            datetime.datetime(2026, 10, 1),
            datetime.datetime(2026, 10, 14),
            334,
            weights_p1,
            ["Tâm sự cùng AI", "Tập đối thoại", "Hiểu cảm xúc"]
        ))

        # GIAI ĐOẠN 2: Từ 15/10/2026 đến 28/10/2026 (Tổng 516 phản hồi)
        # Chủ đề ưu tiên: "Định hướng nghề nghiệp" > "Quyền riêng tư cá nhân" > Các chủ đề khác gần sát nhau
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
        logs.extend(generate_period_logs(
            datetime.datetime(2026, 10, 15),
            datetime.datetime(2026, 10, 28),
            516,
            weights_p2,
            ["Tâm sự cùng AI", "Tập đối thoại", "Hiểu cảm xúc"]
        ))

        # Sắp xếp lại log theo thời gian tăng dần
        logs.sort(key=lambda x: x["timestamp"])

        df_init = pd.DataFrame(logs)
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