# Travelbot-ComputationalThinking-Group_06
The Intelligent Travel Chatbot uses the Google Gemini API to understand natural language, invoke suitable tools, and provide context-aware responses. Built with a Tkinter GUI for easy interaction, it also saves chat history, enabling seamless conversation continuity across sessions.
# Sơ đồ Hệ thống Chatbot Du lịch

Sơ đồ này mô tả luồng thông tin từ khi người dùng nhập câu hỏi đến khi nhận được câu trả lời. Hệ thống bao gồm 7 thành phần chính:

1. Người dùng (User): Người tương tác với ứng dụng.

2. Giao diện Tkinter (UI): Cửa sổ đồ họa nơi người dùng nhập và xem tin nhắn.

3. Bộ điều khiển ứng dụng (Main App Logic): "Trái tim" của code Python, điều phối mọi hoạt động.

4. Lưu trữ JSON (chat_history.json): Tệp vật lý trên ổ đĩa để lưu/tải lịch sử.

5. Gemini API: "Bộ não" AI, xử lý ngôn ngữ và quyết định hành động.

6. Bộ thực thi Tools (Tool Executor): Một phần của logic ứng dụng, có nhiệm vụ gọi các API bên ngoài.

7. Các API bên ngoài (External APIs): Google Places, Directions, OpenWeatherMap.


# Luồng hoạt động chi tiết (Flow Diagram)
Đây là luồng dữ liệu (Data Flow) khi người dùng gửi một tin nhắn:

1. [Người dùng] gõ câu hỏi (ví dụ: "thời tiết Đà Nẵng hôm nay") và nhấn "Gửi" trên [Giao diện Tkinter].

2. [Giao diện Tkinter] gọi hàm handle_send_message() trong [Bộ điều khiển ứng dụng].

3. [Bộ điều khiển ứng dụng] thực hiện:
- Hiển thị tin nhắn của người dùng lên màn hình chat (gọi add_message_to_ui()).

* Gọi hàm save_message():

    - Cập nhật tin nhắn "user" vào biến all_conversations_data (trong RAM).

    - Gọi commit_data_to_json() để ghi đè toàn bộ dữ liệu mới xuống tệp [Lưu trữ JSON].

* Lấy toàn bộ lịch sử hội thoại (history) từ biến all_conversations_data.

* Gọi hàm get_gemini_response(history).

4. [Bộ điều khiển ứng dụng] (bên trong hàm get_gemini_response) gửi history và danh sách tools đến [Gemini API].

5. [Gemini API] phân tích:

* Trường hợp A (Không cần Tool): Trả về câu trả lời dạng văn bản.

* Trường hợp B (Cần Tool): Nhận ra cần gọi get_weather_forecast. Nó trả về một yêu cầu FunctionCall (gọi hàm).

6. [Bộ điều khiển ứng dụng] nhận phản hồi từ Gemini:

* Nếu là Trường hợp A: Đi đến Bước 10.

* Nếu là Trường hợp B: Nó thấy có FunctionCall. Nó gọi [Bộ thực thi Tools].

7. [Bộ thực thi Tools] gọi API tương ứng, ví dụ: call_openweathermap_api("Đà Nẵng", "hôm nay").

8. [Các API bên ngoài] (ví dụ: OpenWeatherMap) trả về dữ liệu thời tiết thô (ví dụ: {"temp": 25, "rain": true}) cho [Bộ thực thi Tools].

9. [Bộ điều khiển ứng dụng] gửi yêu cầu lần 2 đến [Gemini API], đính kèm lịch sử cũ VÀ kết quả ({"temp": 25, "rain": true}) từ Tool.

10. [Gemini API] nhận dữ liệu thô, tổng hợp nó thành câu trả lời tự nhiên (ví dụ: "Thời tiết Đà Nẵng hôm nay 25°C, trời có mưa.") và trả về cho [Bộ điều khiển ứng dụng].

11. [Bộ điều khiển ứng dụng] (quay lại hàm handle_send_message) nhận được câu trả lời cuối cùng:

* Hiển thị tin nhắn của bot lên màn hình (gọi add_message_to_ui()).

* Gọi lại hàm save_message() để lưu tin nhắn "model" này vào [Lưu trữ JSON].

(Luồng tải "Recent Chats" và "Load Chat" là luồng riêng, chỉ đọc từ [Lưu trữ JSON] và hiển thị lên [Giao diện Tkinter]).

# Demo Json format
```json
{
  "convo_1729523000": {
    "title": "Lên lịch trình Phú Quốc",
    "created_at": "2025-10-21T10:00:00Z",
    "messages": [
      {
        "role": "user",
        "content": "Lên lịch trình 3 ngày ở Phú Quốc.",
        "timestamp": "2025-10-21T10:00:05Z"
      },
      {
        "role": "model",
        "content": "Ngày 1 VinWonders, Ngày 2 Hòn Thơm, Ngày 3 chợ Dương Đông.",
        "timestamp": "2025-10-21T10:02:15Z"
      },
      {
        "role": "user",
        "content": "Từ Hòn Thơm về chợ Dương Đông bao xa?",
        "timestamp": "2025-10-21T10:04:30Z"
      },
      {
        "role": "model",
        "content": "Khoảng 30km, mất 45 phút đi xe.",
        "timestamp": "2025-10-21T10:05:00Z"
      }
    ]
  }
}
```

# Demo tools which are declared for gemini
```python
tools = [
    {
        "function_declarations": [
            {
                "name": "find_places_of_interest",
                "description": "Tìm kiếm địa điểm (du lịch, ăn uống, khách sạn) tại một vị trí cụ thể.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "Nội dung tìm kiếm, ví dụ: 'điểm check-in đẹp', 'quán phở ngon', 'khách sạn giá rẻ'"
                        },
                        "location": {
                            "type": "STRING",
                            "description": "Địa danh hoặc thành phố, ví dụ: 'Ninh Bình', 'gần Hồ Gươm', 'Đà Lạt'"
                        }
                    },
                    "required": ["query", "location"]
                }
            },
            {
                "name": "get_directions_and_travel_time",
                "description": "Tính toán khoảng cách và thời gian di chuyển giữa hai địa điểm bằng một phương tiện cụ thể.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "origin": {
                            "type": "STRING",
                            "description": "Điểm bắt đầu, ví dụ: 'TP.HCM', 'Khách sạn Mường Thanh'"
                        },
                        "destination": {
                            "type": "STRING",
                            "description": "Điểm kết thúc, ví dụ: 'Phan Thiết', 'sân bay Cam Ranh'"
                        },
                        "mode": {
                            "type": "STRING",
                            "description": "Phương tiện di chuyển, ví dụ: 'driving' (ô tô), 'transit' (công cộng)"
                        }
                    },
                    "required": ["origin", "destination", "mode"]
                }
            },
            {
                "name": "get_weather_forecast",
                "description": "Lấy thông tin dự báo thời tiết cho một địa điểm vào một ngày cụ thể.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {
                            "type": "STRING",
                            "description": "Tên thành phố cần xem thời tiết, ví dụ: 'Sapa', 'Đà Nẵng'"
                        },
                        "date": {
                            "type": "STRING",
                            "description": "Ngày cần dự báo, ví dụ: 'hôm nay', 'ngày mai', 'tháng 10'"
                        }
                    },
                    "required": ["location", "date"]
                }
            },
            {
                "name": "general_knowledge_search",
                "description": "Tìm kiếm thông tin chung, sự kiện, văn hóa, hoặc giá vé không có trong các công cụ chuyên biệt.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "search_query": {
                            "type": "STRING",
                            "description": "Câu hỏi cần tìm kiếm, ví dụ: 'Lễ hội hoa Đà Lạt diễn ra khi nào?', 'Giá vé xe Phương Trang đi Phan Thiết', 'Do I need a visa for Vietnam?'"
                        }
                    },
                    "required": ["search_query"]
                }
            }
        ]
    }
]
```

# Demo pseudocode
```python
# --- BIẾN TOÀN CỤC ---
all_conversations_data = {}  # Dictionary lớn chứa toàn bộ lịch sử 
current_conversation_id = None # ID của chat đang mở
gemini_model = Khởi_tạo_Gemini_Model(với danh sách 'tools' ở trên) 
JSON_FILE_PATH = "chat_history.json"

# --- 1. KHỞI TẠO ỨNG DỤNG ---
FUNCTION main():
    # 1.1. Tải dữ liệu 
    all_conversations_data = load_history_from_json(JSON_FILE_PATH)

    # 1.2. Dựng giao diện Tkinter 
    root_window = Create_Tkinter_Window()
    sidebar = Create_Sidebar(root_window)
    chat_area = Create_Chat_Area(root_window)
    
    input_bar = Create_Input_Bar(chat_area)
    send_button = input_bar.send_button
    
    # 1.3. Gán sự kiện
    send_button.onClick = handle_send_message
    sidebar.new_chat_button.onClick = handle_new_chat
    
    # 1.4. Hiển thị
    update_recent_chats_list(sidebar)
    root_window.mainloop()

# --- 2. XỬ LÝ LƯU TRỮ JSON ---
FUNCTION load_history_from_json(file_path):
    IF file_path exists:
        data = Read_JSON_File(file_path)
        RETURN data
    ELSE:
        RETURN {} # Trả về dict rỗng nếu chưa có file

FUNCTION commit_data_to_json(file_path, data):
    Write_JSON_File(file_path, data) # Ghi đè toàn bộ 

FUNCTION save_message(convo_id, role, content):
    # Lấy ID mới nếu là tin nhắn đầu
    IF convo_id IS None:
        convo_id = "convo_" + generate_timestamp()
        all_conversations_data[convo_id] = {
            "title": content[:30] + "...", # Lấy 30 ký tự đầu làm tiêu đề 
            "created_at": get_current_iso_time(),
            "messages": []
        }
    
    # Thêm tin nhắn vào RAM 
    new_message = { "role": role, "content": content, "timestamp": get_current_iso_time() }
    all_conversations_data[convo_id]["messages"].append(new_message)
    all_conversations_data[convo_id]["last_updated"] = new_message["timestamp"] 
    
    # Lưu vào ổ đĩa 
    commit_data_to_json(JSON_FILE_PATH, all_conversations_data)
    
    RETURN convo_id # Trả về ID (có thể là ID mới)

# --- 3. LUỒNG XỬ LÝ CHÍNH KHI GỬI TIN NHẮN ---
FUNCTION handle_send_message():
    user_input = input_bar.getText()
    IF user_input IS empty:
        RETURN

    # Cập nhật UI và Lưu tin nhắn của user
    add_message_to_ui(user_input, "user") 
    input_bar.clearText()
    
    # Lưu tin nhắn user và cập nhật ID (nếu là chat mới) 
    global current_conversation_id
    current_conversation_id = save_message(current_conversation_id, "user", user_input)
    
    # Lấy lịch sử cho Gemini
    history = all_conversations_data[current_conversation_id]["messages"]
    
    # Hiển thị "Bot đang trả lời..."
    show_loading_indicator(chat_area)
    
    # 3.1. Gọi Gemini
    gemini_response = get_gemini_response(history)
    
    # 3.2. Lưu và hiển thị phản hồi của Bot
    hide_loading_indicator(chat_area)
    save_message(current_conversation_id, "model", gemini_response)
    add_message_to_ui(gemini_response, "model") 
    
    # Cập nhật danh sách "Recent Chats"
    update_recent_chats_list(sidebar)

# --- 4. LUỒNG GỌI GEMINI VÀ TOOL ---
FUNCTION get_gemini_response(history):
    # Bước 1: Gửi yêu cầu đầu tiên cho Gemini 
    response = gemini_model.generate_content(history, tools=tools)
    
    # Bước 2: Kiểm tra xem Gemini có yêu cầu gọi Tool không
    IF response.has_function_call:
        # Lấy tên hàm và tham số
        function_call = response.function_call
        function_name = function_call.name
        args = function_call.args
        
        # Bước 3: Thực thi Tool tương ứng
        IF function_name == "find_places_of_interest":
            tool_result = call_google_places_api(args.query, args.location) 
        ELSE IF function_name == "get_directions_and_travel_time":
            tool_result = call_google_directions_api(args.origin, args.destination, args.mode) 
        ELSE IF function_name == "get_weather_forecast":
            tool_result = call_openweathermap_api(args.location, args.date) 
        ELSE IF function_name == "general_knowledge_search":
            tool_result = call_google_search_api(args.search_query) # Giả định có hàm này
        
        # Bước 4: Gửi kết quả Tool ngược lại cho Gemini
        # Thêm lịch sử (gồm cả yêu cầu gọi tool và kết quả tool)
        history.append(response.raw_message) # Tin nhắn yêu cầu gọi tool
        history.append(Function_Result(tool_result)) # Tin nhắn chứa kết quả
        
        # Gọi Gemini lần 2 để nhận câu trả lời cuối cùng
        final_response = gemini_model.generate_content(history)
        RETURN final_response.text
        
    ELSE:
        # Nếu Gemini không cần Tool, trả lời trực tiếp
        RETURN response.text

# --- 5. HÀM GỌI API BÊN NGOÀI (Giả định) ---
FUNCTION call_google_places_api(query, location):
    # ... code gọi API Google Places ...
    RETURN json_result

FUNCTION call_google_directions_api(origin, dest, mode):
    # ... code gọi API Google Directions ...
    RETURN json_result

FUNCTION call_openweathermap_api(location, date):
    # ... code gọi API OpenWeatherMap ...
    RETURN json_result

FUNCTION call_google_search_api(search_query):
    # ... code gọi API tìm kiếm ...
    RETURN search_results

# --- 6. HÀM CẬP NHẬT GIAO DIỆN TKINTER ---
FUNCTION add_message_to_ui(message, role):
    # Tạo một bong bóng chat (Label hoặc Text)
    # Nếu role == 'user', căn lề phải, màu xanh
    # Nếu role == 'model', căn lề trái, màu xám
    # Thêm bong bóng chat vào chat_area 

FUNCTION update_recent_chats_list(sidebar):
    sidebar.clear_list()
    # Sắp xếp các cuộc hội thoại theo 'last_updated' (mới nhất trên cùng) 
    sorted_convos = sorted(all_conversations_data.items(), key=lambda item: item[1]['last_updated'], reverse=True)
    
    FOR convo_id, data IN sorted_convos:
        title = data['title']
        # Tạo nút bấm (Button) với 'title'
        # Gán sự kiện cho nút: button.onClick = lambda id=convo_id: handle_load_chat(id)
        sidebar.add_chat_button(title, convo_id)

FUNCTION handle_load_chat(convo_id):
    global current_conversation_id
    current_conversation_id = convo_id
    
    # Xóa màn hình chat hiện tại
    chat_area.clear_messages()
    
    # Tải và hiển thị lịch sử của chat đã chọn
    messages = all_conversations_data[convo_id]["messages"]
    FOR msg IN messages:
        add_message_to_ui(msg['content'], msg['role'])

FUNCTION handle_new_chat():
    global current_conversation_id
    current_conversation_id = None
    chat_area.clear_messages()
    # Hiển thị thông báo chào mừng
```
