## File Code.py
import tkinter as tk
from tkinter import scrolledtext
import json
import os
import datetime
import requests
from dotenv import load_dotenv

# ===== LOAD ENV =====
# Nếu file env của bạn tên "Hay.env", load nó — nếu dùng .env mặc định, sẽ vẫn ổn.
env_file = "Hay.env" if os.path.exists("Hay.env") else ".env"
print("Loading env file:", env_file)
load_dotenv(env_file)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_URL = os.getenv("AI_API_URL")

JSON_FILE_PATH = "chat_history.json"

print("GOOGLE_MAPS_API_KEY present?:", bool(GOOGLE_MAPS_API_KEY))
print("AI_API_KEY present?:", bool(AI_API_KEY))
print("AI_API_URL:", AI_API_URL)

# ===== TOOLS (tạm giữ nếu bạn muốn gửi) =====
tools = [
    {
        "function_declarations": [
            {
                "name": "find_places_of_interest",
                "description": "Tìm kiếm địa điểm tại vị trí cụ thể.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING"},
                        "location": {"type": "STRING"}
                    },
                    "required": ["query", "location"]
                }
            },
            {
                "name": "get_directions_and_travel_time",
                "description": "Tính khoảng cách và thời gian giữa hai địa điểm.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "origin": {"type": "STRING"},
                        "destination": {"type": "STRING"},
                        "mode": {"type": "STRING"}
                    },
                    "required": ["origin", "destination", "mode"]
                }
            },
            {
                "name": "get_weather_forecast",
                "description": "Dự báo thời tiết.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING"},
                        "date": {"type": "STRING"}
                    },
                    "required": ["location", "date"]
                }
            },
            {
                "name": "general_knowledge_search",
                "description": "Tìm kiếm thông tin chung.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "search_query": {"type": "STRING"}
                    },
                    "required": ["search_query"]
                }
            }
        ]
    }
]

# ===== GLOBALS =====
all_conversations_data = {}
current_conversation_id = None

def get_place(query, location):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query + " in " + location, "key": GOOGLE_MAPS_API_KEY}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if results:
        return results[0]["name"], results[0]["formatted_address"]
    return None, None

def get_directions(origin, destination, mode="driving"):
    url = f"https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "mode": mode, "key": GOOGLE_MAPS_API_KEY}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data["routes"]:
        leg = data["routes"][0]["legs"][0]
        return leg["distance"]["text"], leg["duration"]["text"]
    return None, None


# ===== GEMINI API CALL (với debug) =====
def call_gemini_api(user_message, history):
    if not AI_API_KEY or not AI_API_URL:
        print("Warning: AI_API_KEY hoặc AI_API_URL chưa được cấu hình.")
        return "(Chưa cài AI_API_KEY/AI_API_URL) Bạn nói: " + user_message

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ],
        "generationConfig": {"temperature": 0.7}
    }

    try:
        print("Gửi payload tới Gemini... (timeout 15s)")
        resp = requests.post(f"{AI_API_URL}?key={AI_API_KEY}", headers=headers, json=payload, timeout=15)
        print("HTTP status:", resp.status_code)
        print("Response text (debug):", resp.text[:1000])
        resp.raise_for_status()
        j = resp.json()
        if "candidates" in j and len(j["candidates"]) > 0:
            return j["candidates"][0]["content"]["parts"][0]["text"]
        return "(AI trả về rỗng)"
    except Exception as e:
        print("Lỗi khi gọi Gemini API:", e)
        return "Xin lỗi, có lỗi khi gọi Gemini API. (Xem console để biết chi tiết.)"

# ===== JSON STORAGE =====
def load_history():
    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Không thể đọc file lịch sử:", e)
            return {}
    return {}

def save_history():
    try:
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(all_conversations_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Lỗi khi lưu lịch sử:", e)

def save_message(convo_id, role, content):
    global all_conversations_data
    if convo_id is None:
        convo_id = "convo_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        all_conversations_data[convo_id] = {
            "title": content[:30]+"...",
            "created_at": datetime.datetime.now().isoformat(),
            "messages": [],
            "last_updated": datetime.datetime.now().isoformat()
        }
    msg = {"role": role, "content": content, "timestamp": datetime.datetime.now().isoformat()}
    all_conversations_data[convo_id]["messages"].append(msg)
    all_conversations_data[convo_id]["last_updated"] = msg["timestamp"]
    save_history()
    return convo_id

# ===== GUI HELPERS =====
def add_message_to_ui(message, role):
    chat_area.config(state='normal')
    if role == "user":
        chat_area.insert(tk.END, f"Bạn: {message}\n", "user_tag")
    else:
        # mọi role khác coi là AI
        chat_area.insert(tk.END, f"AI: {message}\n", "ai_tag")
    chat_area.insert(tk.END, "\n")
    chat_area.config(state='disabled')
    chat_area.yview(tk.END)

def update_recent_chats_list():
    sidebar_frame.delete(0, tk.END)
    sorted_convos = sorted(all_conversations_data.items(), key=lambda x: x[1]["last_updated"], reverse=True)
    for convo_id, data in sorted_convos:
        sidebar_frame.insert(tk.END, data["title"])

def handle_load_chat(event=None):
    global current_conversation_id
    sel = sidebar_frame.curselection()
    if sel:
        idx = sel[0]
        convo_ids = list(all_conversations_data.keys())
        if idx < len(convo_ids):
            current_conversation_id = convo_ids[idx]
            chat_area.config(state='normal')
            chat_area.delete(1.0, tk.END)
            for msg in all_conversations_data[current_conversation_id]["messages"]:
                add_message_to_ui(msg["content"], msg["role"])
            chat_area.config(state='disabled')

def handle_new_chat():
    global current_conversation_id
    current_conversation_id = None
    chat_area.config(state='normal')
    chat_area.delete(1.0, tk.END)
    chat_area.config(state='disabled')

def handle_send_message(event=None):
    global current_conversation_id
    user_input = input_entry.get()
    if not user_input.strip():
        return
    add_message_to_ui(user_input, "user")
    input_entry.delete(0, tk.END)

    # Kiểm tra từ khóa map
    if "địa điểm" in user_input or "hướng đi" in user_input:
        place, address = get_place("coffee shop", "Hanoi")  # ví dụ tạm
        ai_text = f"Đây là kết quả Map: {place}, {address}"
    else:
        ai_text = call_gemini_api(user_input, all_conversations_data.get(current_conversation_id, {}).get("messages", []))

    current_conversation_id = save_message(current_conversation_id, "user", user_input)
    add_message_to_ui(ai_text, "model")
    save_message(current_conversation_id, "model", ai_text)
    update_recent_chats_list()

# ===== TKINTER GUI =====
root = tk.Tk()
root.title("Chat GUI AI + Gemini")
root.geometry("800x500")

sidebar_frame = tk.Listbox(root, width=30)
sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
sidebar_frame.bind("<<ListboxSelect>>", handle_load_chat)

chat_area = scrolledtext.ScrolledText(root, state='disabled', wrap=tk.WORD)
chat_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
chat_area.tag_config("user_tag", foreground="blue")
chat_area.tag_config("ai_tag", foreground="gray")

input_frame = tk.Frame(root)
input_frame.pack(side=tk.BOTTOM, fill=tk.X)
input_entry = tk.Entry(input_frame)
input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
input_entry.bind("<Return>", handle_send_message)
send_btn = tk.Button(input_frame, text="Gửi", command=handle_send_message)
send_btn.pack(side=tk.LEFT)

new_chat_btn = tk.Button(root, text="New Chat", command=handle_new_chat)
new_chat_btn.pack(side=tk.BOTTOM, fill=tk.X)

# Load history
all_conversations_data = load_history()
update_recent_chats_list()

root.mainloop()  




# File Hay.env
# GOOGLE_MAPS_API_KEY=AIzaSyCyrTbLvXwdrSuQWNK9h1vJupbWHLVjLck
# AI_API_KEY=AIzaSyAYEKutzmBEvLMlTvimTcMxsiEfj8-iFAA
# AI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
