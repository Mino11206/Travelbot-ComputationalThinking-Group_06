import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
from collections import defaultdict
import json
import os
import threading
import urllib.request
import urllib.error
import calendar

class GObotApp(tk.Tk):
    """
    An AI-powered travel planner application using tkinter and the Gemini API.
    Name: GObot (Localized to Vietnamese)
    """

    def __init__(self):
        super().__init__()

        self.title("GObot - Trợ lý Du lịch AI")
        self.geometry("1200x700")
        self.minsize(700, 600)

        # --- Colors & Fonts ---
        self.colors = {
            "bg_primary": "#f3f4f6",
            "bg_secondary": "#ffffff",
            "bg_widget": "#e5e7eb",
            "fg_primary": "#1f2937",
            "fg_accent": "#3b82f6",
            "accent_primary": "#3b82f6",
            "accent_secondary": "#60a5fa",
            "accent_success": "#10b981",
            "accent_error": "#ef4444",
        }
        self.app_font = ("Segoe UI", 10)
        self.chat_font = ("Segoe UI", 12)
        self.chat_bold_font = ("Segoe UI", 12, "bold")
        self.title_font = ("Segoe UI", 18, "bold")
        self.h2_font = ("Segoe UI", 14, "bold")
        self.h3_font = ("Segoe UI", 12, "bold")
        self.code_font = ("Courier New", 10) # Font cho bảng

        self.api_key = "AIzaSyCK4R-jSQyVGEyhRfsUawChS-i4Rl3eRWk" 
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={self.api_key}"

        self.current_plan_json = None
        self.api_chat_history = []
        
        # --- StringVars for inputs ---
        self.budget_amount_var = tk.StringVar()
        self.budget_trace_id = None
        self.optional_destination = tk.StringVar()
        self.travelers_var = tk.StringVar(value="1")
        self.start_location_var = tk.StringVar()
        
        # To store the user's original criteria for regeneration
        self.last_criteria = {}
        
        # State tracking for finalizing plan
        self.accommodation_suggested = False
        self.transport_suggested = False

        self._configure_styles()
        self._create_menubar()

        # --- Main App Container ---
        self.container = ttk.Frame(self, style='TFrame')
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self._create_criteria_screen()
        self._create_planner_screen()

        self.show_frame("CriteriaScreen")

    def _configure_styles(self):
        s = ttk.Style(self)
        s.theme_use('clam') 
        
        c = self.colors
        s.configure('.', background=c["bg_primary"], foreground=c["fg_primary"], font=self.app_font, borderwidth=0)
        s.configure('TFrame', background=c["bg_primary"])
        s.configure('TLabel', background=c["bg_primary"], foreground=c["fg_primary"], font=self.app_font)
        s.configure('TButton', background=c["accent_primary"], foreground=c["bg_secondary"], font=(self.app_font[0], 12, "bold"), padding=10, borderwidth=0)
        s.map('TButton', background=[('active', c["accent_secondary"])])
        
        # Smaller button style for clear/dest buttons
        s.configure('Small.TButton', font=(self.app_font[0], 9), padding=5, background=c["bg_widget"], foreground=c["fg_primary"])
        s.map('Small.TButton', background=[('active', c["accent_secondary"])])
        
        s.configure('TEntry', fieldbackground=c["bg_widget"], foreground=c["fg_primary"], insertcolor=c["fg_primary"], borderwidth=1, relief='flat')
        s.configure('TCombobox', fieldbackground=c["bg_widget"], foreground=c["fg_primary"], borderwidth=1, relief='flat', arrowcolor=c["fg_primary"])
        s.configure('TLabelframe', background=c["bg_primary"], bordercolor=c["bg_widget"], padding=15)
        s.configure('TLabelfame.Label', background=c["bg_primary"], foreground=c["fg_accent"], font=(self.app_font[0], 12, "bold"))

    def _create_menubar(self):
        """Creates the main application menubar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        help_menu.add_command(label="Hướng dẫn", command=self.show_user_guide)
        help_menu.add_command(label="Giới thiệu...", command=self.show_about)

    def _create_date_dropdowns(self, parent_frame):
        """Helper to create Day, Month, Year dropdowns."""
        date_frame = ttk.Frame(parent_frame, style='TFrame')
        
        days = [str(i) for i in range(1, 32)]
        months = [f"Tháng {i}" for i in range(1, 13)]
        current_year = date.today().year
        years = [str(i) for i in range(current_year, current_year + 5)]
        
        day_var = tk.StringVar(value=str(date.today().day))
        month_var = tk.StringVar(value=f"Tháng {date.today().month}")
        year_var = tk.StringVar(value=str(current_year))
        
        day_combo = ttk.Combobox(date_frame, textvariable=day_var, values=days, state="readonly", width=5)
        day_combo.pack(side=tk.LEFT, padx=2, ipady=3)
        
        month_combo = ttk.Combobox(date_frame, textvariable=month_var, values=months, state="readonly", width=12)
        month_combo.pack(side=tk.LEFT, padx=2, ipady=3)
        
        year_combo = ttk.Combobox(date_frame, textvariable=year_var, values=years, state="readonly", width=7)
        year_combo.pack(side=tk.LEFT, padx=2, ipady=3)
        
        return date_frame, day_var, month_var, year_var

    def _get_date_from_dropdowns(self, day_var, month_var, year_var):
        """Converts date dropdowns to DD-MM-YYYY string."""
        try:
            day = int(day_var.get())
            month_num = int(month_var.get().split(" ")[1]) # "Tháng 1" -> 1
            month = f"{month_num:02d}"
            year = year_var.get()
            return f"{day:02d}-{month}-{year}"
        except (ValueError, IndexError):
            return ""

    def _on_budget_change(self, *args):
        """Formats the budget entry with commas."""
        self.budget_amount_var.trace_remove("write", self.budget_trace_id)
        current_val = self.budget_amount_var.get().replace(",", "")
        try:
            formatted_val = f"{int(current_val):,}"
        except ValueError:
            formatted_val = "".join(c for c in current_val if c.isdigit())
            if formatted_val:
                try: formatted_val = f"{int(formatted_val):,}"
                except ValueError: formatted_val = ""
            
        self.budget_amount_var.set(formatted_val)
        self.budget_trace_id = self.budget_amount_var.trace_add("write", self._on_budget_change)

    def _ask_for_destination(self):
        dest = simpledialog.askstring("Điểm đến tùy chọn", "Bạn muốn đi đâu?", parent=self)
        if dest:
            self.optional_destination.set(dest)
            self.destination_label.config(text=f"Điểm đến: {dest}")

    def _clear_destination(self):
        self.optional_destination.set("")
        self.destination_label.config(text="Điểm đến: AI sẽ gợi ý")

    def _create_criteria_screen(self):
        frame = ttk.Frame(self.container, style='TFrame', padding=20)
        frame.grid(row=0, column=0, sticky="nsew")
        self.frames["CriteriaScreen"] = frame

        content_frame = ttk.Frame(frame, style='TFrame')
        content_frame.place(relx=0.5, rely=0.5, anchor='center')

        title = ttk.Label(content_frame, text="GObot", font=("Segoe UI", 32, "bold"), foreground=self.colors["fg_accent"])
        title.pack(pady=(0, 10))
        subtitle = ttk.Label(content_frame, text="Trợ lý du lịch cá nhân của bạn.", font=("Segoe UI", 14))
        subtitle.pack(pady=(0, 25))

        form_frame = ttk.Frame(content_frame, style='TFrame', width=500)
        form_frame.pack(fill=tk.X)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Row 0: Travelers and Start Location
        ttk.Label(form_frame, text="Số lượng khách:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        travelers_entry = ttk.Entry(form_frame, font=self.app_font, width=10, textvariable=self.travelers_var)
        travelers_entry.grid(row=1, column=0, sticky="w", ipady=3, padx=5)
        
        ttk.Label(form_frame, text="Bạn bắt đầu từ đâu?").grid(row=0, column=1, sticky="w", pady=5, padx=5)
        start_location_entry = ttk.Entry(form_frame, font=self.app_font, textvariable=self.start_location_var)
        start_location_entry.grid(row=1, column=1, sticky="ew", ipady=3, padx=5)

        # Row 2 & 3: Dates
        ttk.Label(form_frame, text="Ngày bắt đầu").grid(row=2, column=0, sticky="w", pady=(15, 5), padx=5)
        ttk.Label(form_frame, text="Ngày kết thúc").grid(row=2, column=1, sticky="w", pady=(15, 5), padx=5)
        
        start_date_frame, self.start_day, self.start_month, self.start_year = self._create_date_dropdowns(form_frame)
        start_date_frame.grid(row=3, column=0, sticky="w", padx=5)
        
        end_date_frame, self.end_day, self.end_month, self.end_year = self._create_date_dropdowns(form_frame)
        end_date_frame.grid(row=3, column=1, sticky="w", padx=5)

        # Row 4: Budget
        ttk.Label(form_frame, text="Ngân sách (Tùy chọn)").grid(row=4, column=0, sticky="w", pady=(15, 5), padx=5)
        budget_frame = ttk.Frame(form_frame, style='TFrame')
        budget_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5)
        
        self.budget_amount_entry = ttk.Entry(budget_frame, font=self.app_font, justify='right', textvariable=self.budget_amount_var)
        self.budget_amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 5))
        self.budget_trace_id = self.budget_amount_var.trace_add("write", self._on_budget_change)
        
        self.budget_currency_combo = ttk.Combobox(budget_frame, values=["VND", "USD", "EUR", "GBP", "JPY", "CAD", "AUD"], state="readonly", width=8)
        self.budget_currency_combo.current(0)
        self.budget_currency_combo.pack(side=tk.LEFT, ipady=5)
        
        # Row 6: Travel Style
        ttk.Label(form_frame, text="Phong cách Du lịch").grid(row=6, column=0, sticky="w", pady=(15, 5), padx=5)
        styles = ["Thư giãn (Biển, Spa)", "Phiêu lưu (Leo núi, Thể thao)", "Văn hóa (Bảo tàng, Lịch sử)", "Ẩm thực (Nhà hàng, Tour)", "Lãng mạn (Cặp đôi, Cảnh đẹp)", "Gia đình (Công viên, Hoạt động)"]
        self.travel_style_combo = ttk.Combobox(form_frame, values=styles, state="readonly")
        self.travel_style_combo.current(0)
        self.travel_style_combo.grid(row=7, column=0, columnspan=2, sticky="ew", ipady=5, padx=5)
        
        # Row 8: Optional Destination
        dest_frame = ttk.Frame(form_frame, style='TFrame')
        dest_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(15, 0), padx=5)
        dest_btn = ttk.Button(dest_frame, text="Bạn đã có điểm đến?", command=self._ask_for_destination, style="Small.TButton")
        dest_btn.pack(side=tk.LEFT, padx=(0, 5))
        clear_btn = ttk.Button(dest_frame, text="Xóa", command=self._clear_destination, style="Small.TButton")
        clear_btn.pack(side=tk.LEFT, padx=5)
        self.destination_label = ttk.Label(dest_frame, text="Điểm đến: AI sẽ gợi ý", style='TLabel')
        self.destination_label.pack(side=tk.LEFT, padx=10)

        # Row 9: Generate Button
        self.generate_btn = ttk.Button(form_frame, text="Tạo chuyến đi", command=self.generate_trip)
        self.generate_btn.grid(row=9, column=0, columnspan=2, sticky="ew", ipady=10, pady=(25, 0), padx=5)

    def _create_planner_screen(self):
        frame = ttk.Frame(self.container, style='TFrame')
        frame.grid(row=0, column=0, sticky="nsew")
        self.frames["PlannerScreen"] = frame

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ttk.Frame(frame, style='TFrame', padding=(10, 10))
        header_frame.grid(row=0, column=0, sticky="ew")
        
        back_btn = ttk.Button(header_frame, text="< Quay lại", command=self.go_back_to_criteria)
        back_btn.pack(side=tk.LEFT)
        
        title = ttk.Label(header_frame, text="Kế hoạch du lịch GObot của bạn", font=self.title_font, foreground=self.colors["fg_accent"])
        title.pack(side=tk.LEFT, expand=True, padx=20)
        
        # Chat History
        chat_frame = ttk.Frame(frame, style='TFrame', padding=10)
        chat_frame.grid(row=1, column=0, sticky="nsew")
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_history_text = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, font=self.chat_font, bg=self.colors["bg_secondary"], fg=self.colors["fg_primary"], borderwidth=0, highlightthickness=0, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_history_text.yview)
        self.chat_history_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_history_text.grid(row=0, column=0, sticky="nsew")
        
        self._configure_chat_tags()

        # --- Button Bar ---
        button_bar = ttk.Frame(frame, style='TFrame', padding=(10, 0, 10, 10))
        button_bar.grid(row=2, column=0, sticky="ew")
        
        self.regenerate_btn = ttk.Button(button_bar, text="🔄 Tạo lại kế hoạch", command=self.regenerate_trip, state=tk.DISABLED)
        self.regenerate_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.diff_dest_btn = ttk.Button(button_bar, text="🔄 Đổi điểm đến", command=self.generate_different_destination, state=tk.DISABLED)
        self.diff_dest_btn.pack(side=tk.LEFT, padx=10)
        
        self.accommodation_btn = ttk.Button(button_bar, text="🏨 Gợi ý Chỗ ở", command=self.generate_accommodation, state=tk.DISABLED)
        self.accommodation_btn.pack(side=tk.LEFT, padx=10)
        
        self.transport_btn = ttk.Button(button_bar, text="✈️ Gợi ý Di chuyển", command=self.generate_transport, state=tk.DISABLED)
        self.transport_btn.pack(side=tk.LEFT, padx=10)

        self.finalize_btn = ttk.Button(button_bar, text="✅ Hoàn tất Kế hoạch", command=self.finalize_plan, state=tk.DISABLED)
        self.finalize_btn.pack(side=tk.RIGHT, padx=10)


        # --- Chat Input ---
        input_frame = ttk.Frame(frame, style='TFrame', padding=10)
        input_frame.grid(row=3, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_input_entry = ttk.Entry(input_frame, font=self.chat_font)
        self.chat_input_entry.grid(row=0, column=0, sticky="ew", ipady=8, padx=(0, 10))
        self.chat_send_btn = ttk.Button(input_frame, text="Gửi", command=self.send_chat_message)
        self.chat_send_btn.grid(row=0, column=1)
        self.chat_input_entry.bind("<Return>", lambda e: self.send_chat_message())

    def _configure_chat_tags(self):
        """Configure styles for the chat/plan Text widget."""
        self.chat_history_text.tag_configure("h1", font=self.title_font, foreground=self.colors["fg_accent"], spacing3=15)
        # SỬA LỖI: Đặt h2 thành màu fg_accent (xanh)
        self.chat_history_text.tag_configure("h2", font=self.h2_font, foreground=self.colors["fg_accent"], spacing3=10, spacing1=10)
        self.chat_history_text.tag_configure("h3", font=self.h3_font, foreground=self.colors["fg_accent"], spacing3=5, spacing1=5)
        self.chat_history_text.tag_configure("p", font=self.chat_font, lmargin1=10, lmargin2=10)
        self.chat_history_text.tag_configure("li", font=self.chat_font, lmargin1=20, lmargin2=35)
        self.chat_history_text.tag_configure("bold", font=self.chat_bold_font)
        self.chat_history_text.tag_configure("user_msg", font=self.chat_bold_font, foreground=self.colors["accent_secondary"])
        self.chat_history_text.tag_configure("bot_msg", font=self.chat_bold_font, foreground=self.colors["accent_success"])
        self.chat_history_text.tag_configure("error_msg", font=self.chat_bold_font, foreground=self.colors["accent_error"])
        self.chat_history_text.tag_configure("loading_msg", font=self.chat_font, foreground=self.colors["fg_primary"])
        self.chat_history_text.tag_configure("plan_activity_time", font=(self.app_font[0], 10, "bold"), lmargin1=10, lmargin2=10)
        self.chat_history_text.tag_configure("plan_activity_desc", font=self.app_font, lmargin1=10, lmargin2=40, spacing3=10)
        # Thẻ code (font đơn cách) vẫn hữu ích để căn chỉnh, ngay cả khi không phải là bảng
        self.chat_history_text.tag_configure("code", font=self.code_font, background=self.colors["bg_widget"], lmargin1=10, lmargin2=10)

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()
        
    def go_back_to_criteria(self):
        # Reset the planner when going back
        self.api_chat_history = []
        self.current_plan_json = None
        self.chat_history_text.config(state=tk.NORMAL)
        self.chat_history_text.delete("1.0", tk.END)
        self.chat_history_text.config(state=tk.DISABLED)
        
        # Reset buttons and destination
        self._clear_destination()
        self.set_action_buttons_state(tk.DISABLED)
        self.finalize_btn.config(state=tk.DISABLED)

        self.show_frame("CriteriaScreen")

    def add_message_to_chat(self, sender, message, tag_name="p"):
        self.chat_history_text.config(state=tk.NORMAL)
        if sender:
            self.chat_history_text.insert(tk.END, f"{sender}: ", f"{tag_name}_msg")
        self.chat_history_text.insert(tk.END, f"{message}\n\n", tag_name)
        self.chat_history_text.config(state=tk.DISABLED)
        self.chat_history_text.see(tk.END) # Auto-scroll
        
    def add_formatted_message_to_chat(self, sender, message, tag_name="bot"):
        self.chat_history_text.config(state=tk.NORMAL)
        sender_tag = f"{tag_name}_msg"
        self.chat_history_text.insert(tk.END, f"{sender}: \n", sender_tag)
        
        lines = message.split('\n')
        i = 0

        def apply_bold(line_content, base_tags):
            """Helper to apply bold tags within a line."""
            parts = line_content.split("**")
            for j, part in enumerate(parts):
                current_tags = base_tags + ("bold",) if j % 2 == 1 and part else base_tags
                if part:
                    self.chat_history_text.insert(tk.END, part, current_tags)

        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            
            # Giữ nguyên thụt lề của dòng gốc cho thẻ 'p' và 'li'
            leading_whitespace = " " * (len(line) - len(line.lstrip(' ')))

            # SỬA LỖI: Lọc bỏ các dòng phân cách của bảng
            if stripped_line.startswith("|") and "---" in stripped_line:
                i += 1
                continue
            
            if stripped_line.startswith("# "):
                self.chat_history_text.insert(tk.END, f"{stripped_line[2:]}\n", "h1")
            elif stripped_line.startswith("## "):
                self.chat_history_text.insert(tk.END, f"{stripped_line[3:]}\n", "h2")
            elif stripped_line.startswith("### "):
                self.chat_history_text.insert(tk.END, f"{stripped_line[4:]}\n", "h3")
            elif stripped_line.startswith("* "):
                self.chat_history_text.insert(tk.END, f"{leading_whitespace}  • ", "li")
                apply_bold(stripped_line[2:], ("li",))
                self.chat_history_text.insert(tk.END, "\n")
            elif stripped_line.startswith("|"):
                # Xử lý các dòng bảng còn lại (không phải dòng phân cách)
                # Chỉ cần chèn chúng dưới dạng văn bản thô, nhưng áp dụng bold
                self.chat_history_text.insert(tk.END, f"{leading_whitespace}", "p")
                apply_bold(stripped_line, ("p",))
                self.chat_history_text.insert(tk.END, "\n")
            elif stripped_line:
                # Dòng văn bản thông thường
                self.chat_history_text.insert(tk.END, leading_whitespace, "p")
                apply_bold(stripped_line, ("p",))
                self.chat_history_text.insert(tk.END, "\n")
            else:
                self.chat_history_text.insert(tk.END, "\n")
            
            i += 1
        
        self.chat_history_text.insert(tk.END, "\n") # Add spacing after the message
        self.chat_history_text.config(state=tk.DISABLED)
        self.chat_history_text.see(tk.END)
        
    def display_plan(self, plan):
        self.chat_history_text.config(state=tk.NORMAL)
        self.chat_history_text.delete("1.0", tk.END) # Clear loading message
        
        self.chat_history_text.insert(tk.END, f"{plan['tripTitle']}\n", "h1")
        if 'suggestedDestination' in plan:
            self.chat_history_text.insert(tk.END, f"Điểm đến gợi ý: {plan['suggestedDestination']}\n\n", "h2")
        
        for day in plan['itinerary']:
            self.chat_history_text.insert(tk.END, f"Ngày {day['day']} ({day['date']}) - {day['theme']}\n", "h3")
            for activity in day['activities']:
                self.chat_history_text.insert(tk.END, f"{activity['time']}: ", "plan_activity_time")
                self.chat_history_text.insert(tk.END, f"{activity['activity']}\n", "bold")
                self.chat_history_text.insert(tk.END, f"{activity['description']}\n", "plan_activity_desc")
        
        self.chat_history_text.insert(tk.END, "\n\n")
        self.chat_history_text.config(state=tk.DISABLED)
        self.chat_history_text.see("1.0")
        
        # Enable action buttons
        self.set_action_buttons_state(tk.NORMAL)
        self.finalize_btn.config(state=tk.DISABLED) # Keep finalize disabled
        self.accommodation_suggested = False
        self.transport_suggested = False

    def display_final_plan(self, plan):
        # This function is no longer used, as the final plan is now
        # simple markdown text handled by add_formatted_message_to_chat
        pass


    def _threaded_api_call(self, func, *args):
        """Helper to run any function in a separate thread."""
        thread = threading.Thread(target=func, args=args)
        thread.daemon = True
        thread.start()

    def generate_trip(self):
        start = self._get_date_from_dropdowns(self.start_day, self.start_month, self.start_year)
        end = self._get_date_from_dropdowns(self.end_day, self.end_month, self.end_year)
        if not start or not end:
            messagebox.showerror("Lỗi", "Vui lòng chọn Ngày bắt đầu và Ngày kết thúc hợp lệ.")
            return

        self.show_frame("PlannerScreen")
        self.add_message_to_chat("GObot", "Đang tạo chuyến đi, vui lòng chờ...", "loading")
        self.generate_btn.config(state=tk.DISABLED)
        self.set_action_buttons_state(tk.DISABLED)

        travelers = self.travelers_var.get()
        budget_amt = self.budget_amount_var.get().replace(",", "")
        budget_curr = self.budget_currency_combo.get()
        budget = f"{budget_amt} {budget_curr}" if budget_amt else "Không xác định"
        style = self.travel_style_combo.get()
        destination = self.optional_destination.get()
        start_location = self.start_location_var.get()
        
        # Store criteria for regeneration
        self.last_criteria = {"start": start, "end": end, "budget": budget, "style": style, "travelers": travelers, "destination": destination, "start_location": start_location, "budget_curr": budget_curr}
        
        self._threaded_api_call(self._get_initial_plan_task, start, end, budget, style, travelers, start_location, destination)

    def regenerate_trip(self):
        self.add_message_to_chat("GObot", "Đang tạo lại kế hoạch, vui lòng chờ...", "loading")
        self.set_action_buttons_state(tk.DISABLED, "🔄 Đang tạo lại...")
        crit = self.last_criteria
        self._threaded_api_call(self._get_initial_plan_task, crit['start'], crit['end'], crit['budget'], crit['style'], crit['travelers'], crit['start_location'], crit['destination'])
        
    def generate_different_destination(self):
        self.add_message_to_chat("GObot", "Đang tìm điểm đến mới, vui lòng chờ...", "loading")
        self.set_action_buttons_state(tk.DISABLED, "🔄 Đang tìm...")
        crit = self.last_criteria
        self._clear_destination()
        self.last_criteria["destination"] = ""
        self._threaded_api_call(self._get_initial_plan_task, crit['start'], crit['end'], crit['budget'], crit['style'], crit['travelers'], crit['start_location'], "", "Bạn PHẢI chọn một điểm đến và kế hoạch *khác* với kế hoạch trước đó.")
        
    def _get_initial_plan_task(self, start, end, budget, style, travelers, start_location, destination, prompt_injection=None):
        user_prompt = f"Lên kế hoạch chuyến đi cho tôi. Số lượng khách: {travelers}, Bắt đầu từ: {start_location}, Ngày bắt đầu: {start}, Ngày kết thúc: {end}, Ngân sách: {budget}, Phong cách du lịch: {style}."
        
        schema = {
            "type": "OBJECT",
            "properties": {
                "tripTitle": { "type": "STRING" },
                "itinerary": { "type": "ARRAY", "items": {
                    "type": "OBJECT", "properties": {
                        "day": { "type": "NUMBER" }, "date": { "type": "STRING" }, "theme": { "type": "STRING" },
                        "activities": { "type": "ARRAY", "items": {
                            "type": "OBJECT", "properties": {
                                "time": { "type": "STRING" }, "activity": { "type": "STRING" },
                                "description": { "type": "STRING" }, "location": { "type": "STRING" }
                            }, "required": ["time", "activity", "description"]
                        }}
                    }, "required": ["day", "date", "theme", "activities"]
                }}
            },
            "required": ["tripTitle", "itinerary"]
        }

        if destination:
            user_prompt += f"\nĐiểm đến: {destination}"
            system_prompt = "Bạn là một chuyên gia du lịch. Người dùng đã *cung cấp điểm đến*. Tạo một lịch trình du lịch JSON có cấu trúc cho điểm đến đó. JSON phải tuân theo schema đã cung cấp. LUÔN LUÔN trả lời bằng Tiếng Việt."
        else:
            system_prompt = "Bạn là một chuyên gia du lịch. Người dùng KHÔNG cung cấp điểm đến, vì vậy bạn phải CHỌN MỘT điểm đến cho họ dựa trên ngày, ngân sách và phong cách du lịch. Sau đó, tạo một lịch trình du lịch JSON có cấu trúc cho điểm đến đã chọn. JSON phải tuân theo schema đã cung cấp. LUÔN LUÔN trả lời bằng Tiếng Việt."
            schema["properties"]["suggestedDestination"] = { "type": "STRING" }
            schema["required"].append("suggestedDestination")

        if prompt_injection:
            user_prompt += f"\n\nQUAN TRỌNG: {prompt_injection}"

        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema}
        }
        
        response_text, error = self._make_api_request(payload)
        
        if error:
            self.after(0, self.add_message_to_chat, "GObot", error, "error")
        else:
            try:
                self.current_plan_json = json.loads(response_text)
                self.api_chat_history = [
                    {"role": "user", "parts": [{"text": user_prompt}]},
                    {"role": "model", "parts": [{"text": response_text}]}
                ]
                self.after(0, self.display_plan, self.current_plan_json)
            except json.JSONDecodeError:
                self.after(0, self.add_message_to_chat, "GObot", "Không thể phân tích kế hoạch từ AI.", "error")
        
        self.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
        self.after(0, lambda: self.set_action_buttons_state(tk.NORMAL))

    def send_chat_message(self, event=None):
        query = self.chat_input_entry.get().strip()
        if not query: return
        
        self.chat_input_entry.delete(0, tk.END)
        self.add_message_to_chat("Bạn", query, "user")
        self.add_message_to_chat("GObot", "Đang suy nghĩ...", "loading")
        
        self.api_chat_history.append({"role": "user", "parts": [{"text": query}]})
        
        self._threaded_api_call(self._get_chat_response_task)
        
    def _get_chat_response_task(self):
        payload = {
            "contents": self.api_chat_history,
            "systemInstruction": {"parts": [{"text": "Bạn là một chuyên gia du lịch. Kế hoạch ban đầu của người dùng nằm trong lịch sử. Trả lời các câu hỏi tiếp theo của họ một cách ngắn gọn. Định dạng câu trả lời của bạn bằng markdown đơn giản (sử dụng #, ##, ### cho tiêu đề, * cho gạch đầu dòng và ** cho chữ đậm). KHÔNG SỬ DỤNG BẢNG. LUÔN LUÔN trả lời bằng Tiếng Việt."}]}
        }
        
        response_text, error = self._make_api_request(payload)
        
        self.after(0, lambda: self.chat_history_text.config(state=tk.NORMAL))
        self.after(0, lambda: self.chat_history_text.delete("end-3l", "end-1l")) # Remove "Thinking..."
        
        if error:
            self.after(0, self.add_message_to_chat, "GObot", error, "error")
        else:
            self.api_chat_history.append({"role": "model", "parts": [{"text": response_text}]})
            self.after(0, self.add_formatted_message_to_chat, "GObot", response_text, "bot")
            
        self.after(0, lambda: self.chat_history_text.config(state=tk.DISABLED))
            
    def generate_accommodation(self):
        if not self.current_plan_json: return
        
        self.set_action_buttons_state(tk.DISABLED, "🏨 Đang tìm...")
        self.add_message_to_chat("GObot", "Đang tìm các lựa chọn chỗ ở...", "loading")

        plan = self.current_plan_json
        destination = plan.get('suggestedDestination', self.last_criteria.get('destination', 'the destination'))
        prompt = f"Dựa trên kế hoạch du lịch cho {self.last_criteria['travelers']} người:\n- Điểm đến: {destination}\n- Lịch trình: {plan['itinerary'][0]['theme']}...\n- Ngân sách: {self.last_criteria['budget']}\n- Phong cách: {self.last_criteria['style']}\n\nVui lòng gợi ý 2-3 lựa chọn chỗ ở (ví dụ: khách sạn, nhà nghỉ, homestay) phù hợp với ngân sách và phong cách. Bao gồm tên, khoảng giá ước tính và lý do ngắn gọn. LUÔN LUÔN trả lời bằng Tiếng Việt."

        accomo_api_history = self.api_chat_history + [{"role": "user", "parts": [{"text": prompt}]}]
        
        self._threaded_api_call(self._get_accommodation_task, accomo_api_history, prompt)

    def _get_accommodation_task(self, history, prompt):
        payload = {
            "contents": history,
            "systemInstruction": {"parts": [{"text": "Bạn là một trợ lý du lịch chuyên nghiệp. Người dùng muốn gợi ý chỗ ở. Cung cấp 2-3 lựa chọn. Định dạng câu trả lời bằng markdown đơn giản (sử dụng #, ##, * và **). KHÔNG SỬ DỤNG BẢNG. LUÔN LUÔN trả lời bằng Tiếng Việt."}]}
        }
        
        response_text, error = self._make_api_request(payload)

        self.after(0, lambda: self.chat_history_text.config(state=tk.NORMAL))
        self.after(0, lambda: self.chat_history_text.delete("end-3l", "end-1l")) # Remove "Searching..."

        if error:
            self.after(0, self.add_message_to_chat, "GObot", error, "error")
        else:
            self.api_chat_history.append({"role": "user", "parts": [{"text": prompt}]})
            self.api_chat_history.append({"role": "model", "parts": [{"text": response_text}]})
            self.after(0, self.add_formatted_message_to_chat, "GObot", response_text, "bot")
            self.accommodation_suggested = True
            
        self.after(0, lambda: self.set_action_buttons_state(tk.NORMAL))
        self.after(0, lambda: self.chat_history_text.config(state=tk.DISABLED))

    def generate_transport(self):
        if not self.current_plan_json: return
        
        self.set_action_buttons_state(tk.DISABLED, "✈️ Đang tìm...")
        self.add_message_to_chat("GObot", "Đang tìm các lựa chọn di chuyển...", "loading")

        plan = self.current_plan_json
        destination = plan.get('suggestedDestination', self.last_criteria.get('destination', 'the destination'))
        itinerary_summary = ", ".join([f"Ngày {d['day']}: {d['theme']}" for d in plan['itinerary']])
        prompt = f"Dựa trên kế hoạch du lịch cho {self.last_criteria['travelers']} người:\n- Điểm khởi hành: {self.last_criteria['start_location']}\n- Điểm đến: {destination}\n- Lịch trình: {itinerary_summary}\n- Ngân sách: {self.last_criteria['budget']}\n- Phong cách: {self.last_criteria['style']}\n\nVui lòng gợi ý phương tiện di chuyển tốt nhất (máy bay, tàu hỏa, v.v.) để đến đích và di chuyển trong thành phố. Giữ đúng ngân sách và phong cách. LUÔN LUÔN trả lời bằng Tiếng Việt."

        transport_api_history = self.api_chat_history + [{"role": "user", "parts": [{"text": prompt}]}]
        
        self._threaded_api_call(self._get_transport_task, transport_api_history, prompt)

    def _get_transport_task(self, history, prompt):
        payload = {
            "contents": history,
            "systemInstruction": {"parts": [{"text": "Bạn là một trợ lý du lịch chuyên nghiệp. Người dùng muốn gợi ý về phương tiện di chuyển. Cung cấp câu trả lời được định dạng markdown rõ ràng (sử dụng #, ##, * và **). KHÔNG SỬ DỤNG BẢNG. LUÔN LUÔN trả lời bằng Tiếng Việt."}]}
        }
        
        response_text, error = self._make_api_request(payload)

        self.after(0, lambda: self.chat_history_text.config(state=tk.NORMAL))
        self.after(0, lambda: self.chat_history_text.delete("end-3l", "end-1l")) # Remove "Searching..."

        if error:
            self.after(0, self.add_message_to_chat, "GObot", error, "error")
        else:
            self.api_chat_history.append({"role": "user", "parts": [{"text": prompt}]})
            self.api_chat_history.append({"role": "model", "parts": [{"text": response_text}]})
            self.after(0, self.add_formatted_message_to_chat, "GObot", response_text, "bot")
            self.transport_suggested = True
            
        self.after(0, lambda: self.set_action_buttons_state(tk.NORMAL))
        self.after(0, lambda: self.chat_history_text.config(state=tk.DISABLED))

    def _check_finalize_status(self):
        if self.accommodation_suggested and self.transport_suggested:
            self.finalize_btn.config(state=tk.NORMAL)

    def finalize_plan(self):
        self.add_message_to_chat("GObot", "Đang hoàn tất kế hoạch chuyến đi của bạn...", "loading")
        self.set_action_buttons_state(tk.DISABLED, "✅ Đang hoàn tất...")
        self.finalize_btn.config(text="✅ Đang hoàn tất...")
        
        self._threaded_api_call(self._get_final_plan_task)

    def _get_final_plan_task(self):
        # Yêu cầu AI trả về Markdown, không phải JSON
        prompt = f"Vui lòng tổng hợp toàn bộ kế hoạch du lịch từ lịch sử trò chuyện của chúng ta (lịch trình, gợi ý chỗ ở và gợi ý di chuyển) thành một bản tóm tắt cuối cùng. Đồng thời, cung cấp tổng chi phí ước tính cho chuyến đi bằng {self.last_criteria['budget_curr']} dựa trên ngân sách {self.last_criteria['budget']}, lịch trình và các gợi ý. Định dạng câu trả lời bằng markdown đơn giản (tiêu đề, gạch đầu dòng, in đậm)."
        
        final_history = self.api_chat_history + [{"role": "user", "parts": [{"text": prompt}]}]
        
        payload = {
            "contents": final_history,
            "systemInstruction": {"parts": [{"text": "Bạn là một chuyên gia du lịch. Người dùng đã xác nhận kế hoạch của họ. Tổng hợp tất cả thông tin (lịch trình, chỗ ở, di chuyển) từ lịch sử trò chuyện thành một bản tóm tắt CUỐI CÙNG. Cung cấp tổng chi phí ước tính. Định dạng câu trả lời bằng markdown đơn giản (sử dụng #, ##, ###, * và **). KHÔNG SỬ DỤNG BẢNG. LUÔN LUÔN trả lời bằng Tiếng Việt."}]},
        }
        
        response_text, error = self._make_api_request(payload)
        
        self.after(0, lambda: self.chat_history_text.config(state=tk.NORMAL))
        self.after(0, lambda: self.chat_history_text.delete("end-3l", "end-1l")) # Remove "Finalizing..."
        
        if error:
            self.after(0, self.add_message_to_chat, "GObot", error, "error")
            self.after(0, lambda: self.set_action_buttons_state(tk.NORMAL)) # Re-enable if error
        else:
            self.api_chat_history.append({"role": "user", "parts": [{"text": prompt}]})
            self.api_chat_history.append({"role": "model", "parts": [{"text": response_text}]})
            # Xóa kế hoạch cũ và hiển thị kế hoạch cuối cùng
            self.after(0, lambda: self.chat_history_text.delete("1.0", tk.END))
            self.after(0, self.add_formatted_message_to_chat, "GObot", response_text, "bot")
            self.after(0, lambda: self.set_action_buttons_state(tk.NORMAL))
            self.after(0, lambda: self.finalize_btn.config(text="✅ Đã hoàn tất!", state=tk.DISABLED))
            
        self.after(0, lambda: self.chat_history_text.config(state=tk.DISABLED))

    def set_action_buttons_state(self, state, loading_text=None):
        """Helper to enable/disable all action buttons."""
        self.regenerate_btn.config(state=state)
        self.diff_dest_btn.config(state=state)
        self.accommodation_btn.config(state=state)
        self.transport_btn.config(state=state)
        
        # Reset text
        self.regenerate_btn.config(text="🔄 Tạo lại kế hoạch")
        self.diff_dest_btn.config(text="🔄 Đổi điểm đến")
        self.accommodation_btn.config(text="🏨 Gợi ý Chỗ ở")
        self.transport_btn.config(text="✈️ Gợi ý Di chuyển")
        self.finalize_btn.config(text="✅ Hoàn tất Kế hoạch")
        
        # Set loading text
        if loading_text:
            if "Tạo lại" in loading_text: self.regenerate_btn.config(text=loading_text)
            elif "Đang tìm" in loading_text: self.diff_dest_btn.config(text=loading_text)
            elif "Chỗ ở" in loading_text: self.accommodation_btn.config(text=loading_text)
            elif "Di chuyển" in loading_text: self.transport_btn.config(text=loading_text)
            
        if state == tk.DISABLED:
            self.finalize_btn.config(state=tk.DISABLED)
        elif self.accommodation_suggested and self.transport_suggested:
             self.finalize_btn.config(state=tk.NORMAL)
        else:
            self.finalize_btn.config(state=tk.DISABLED)
            
        if self.last_criteria.get("destination"):
            self.diff_dest_btn.config(state=tk.DISABLED)

    def _make_api_request(self, payload):
        """Reusable function to make API calls."""
        if not self.api_key:
            return None, "Chưa có API Key. Vui lòng thêm Gemini API key của bạn vào đầu mã nguồn."
            
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.api_url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                
                if 'error' in result:
                    return None, result['error'].get('message', 'Lỗi API không xác định.')
                
                candidate = result.get('candidates', [{}])[0]
                content_part = candidate.get('content', {}).get('parts', [{}])[0]
                
                if 'text' in content_part:
                    return content_part['text'], None
                else:
                    return None, "Không có phản hồi văn bản từ API."
        
        except urllib.error.HTTPError as e:
            error_details = e.read().decode()
            return None, f"Lỗi API HTTP ({e.code}): {error_details}"
        except Exception as e:
            return None, f"Lỗi Mạng: {e}"

    def show_about(self):
        messagebox.showinfo("Về GObot", 
                            "GObot - Trợ lý Du lịch AI\n\n"
                            "Phiên bản: 1.2\n\n"
                            "Phát triển với Google Gemini.")
    
    def show_user_guide(self):
        UserGuideDialog(self)

class UserGuideDialog(tk.Toplevel):
    """A dialog window to display the user guide."""
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.title("GObot - Hướng dẫn sử dụng")
        self.geometry("700x550")
        self.transient(controller)
        self.grab_set()

        text_widget = tk.Text(self, wrap=tk.WORD, padx=15, pady=15, font=controller.app_font, bg=controller.colors["bg_secondary"], fg=controller.colors["fg_primary"])
        text_widget.pack(expand=True, fill=tk.BOTH)

        # Define styles for markdown
        text_widget.tag_configure("h1", font=("Segoe UI", 18, "bold"), spacing3=15)
        text_widget.tag_configure("h2", font=("Segoe UI", 14, "bold"), spacing3=10, spacing1=10)
        text_widget.tag_configure("bold", font=(controller.app_font[0], controller.app_font[1], "bold"))
        text_widget.tag_configure("p", font=controller.app_font, spacing3=5)
        text_widget.tag_configure("list", lmargin1=20, lmargin2=35, spacing3=2)
        text_widget.tag_configure("code", font=("Courier New", 10), background="#eee", lmargin1=10, lmargin2=10)

        # --- User Guide Content ---
        guide_content = [
            ("h1", "Chào mừng đến với GObot!"),
            ("p", "GObot là trợ lý du lịch cá nhân của bạn. Nó được thiết kế để tạo một lịch trình du lịch hoàn chỉnh, tùy chỉnh cho bạn dựa trên sở thích của bạn."),
            
            ("h2", "Cách sử dụng"),
            ("p", "Làm theo các bước đơn giản sau để lên kế hoạch:"),
            ("list", "Nhập số lượng khách và địa điểm bắt đầu của bạn."),
            ("list", "Chọn ngày bắt đầu và ngày kết thúc mong muốn."),
            ("list", "Nhập ngân sách gần đúng và chọn loại tiền tệ."),
            ("list", "Chọn 'Phong cách Du lịch' phù hợp nhất với kỳ nghỉ lý tưởng của bạn."),
            ("list", "Nếu bạn đã có điểm đến, hãy nhấp vào 'Bạn đã có điểm đến?' để nhập."),
            ("list", "Nhấp vào 'Tạo chuyến đi' và để AI xây dựng kế hoạch cho bạn!"),

            ("h2", "Màn hình Kế hoạch"),
            ("p", "Khi kế hoạch của bạn được tạo, bạn sẽ thấy màn hình lập kế hoạch. Tại đây bạn có thể:"),
            ("list", "Xem lại lịch trình của bạn: Xem điểm đến AI đã chọn cho bạn và kế hoạch hàng ngày."),
            ("list", "Nhận gợi ý: Nhấp vào '🏨 Gợi ý Chỗ ở' hoặc '✈️ Gợi ý Di chuyển' để được AI trợ giúp cụ thể hơn."),
            ("list", "Tạo lại kế hoạch: Không thích gợi ý đầu tiên? Nhấp vào '🔄 Tạo lại kế hoạch' để nhận một chuyến đi mới với các tiêu chí tương tự."),
            ("list", "Thay đổi điểm đến: Nhấp vào '🔄 Đổi điểm đến' để nhận một vị trí mới nhưng vẫn giữ ngày và ngân sách của bạn (chỉ hoạt động khi AI chọn điểm đến)."),
            ("list", "Trò chuyện với AI: Sử dụng hộp trò chuyện ở dưới cùng để đặt câu hỏi, yêu cầu thay đổi (ví dụ: 'Thời tiết ở đó thế nào?' hoặc 'Tìm hoạt động ít tốn kém hơn cho Ngày 2?')."),
            ("list", "Hoàn tất: Sau khi bạn nhận được gợi ý cho cả chỗ ở và phương tiện đi lại, hãy nhấp vào '✅ Hoàn tất Kế hoạch' để xem bản tóm tắt cuối cùng!"),
            
            ("h2", "Quay lại"),
            ("p", "Nếu bạn muốn bắt đầu lại, chỉ cần nhấp vào nút '< Quay lại'. Thao tác này sẽ xóa kế hoạch hiện tại của bạn và đưa bạn trở lại màn hình đầu tiên để nhập tiêu chí mới."),
            
            ("h2", "API Key"),
            ("p", "Ứng dụng này yêu cầu Google Gemini API key để hoạt động. Vui lòng đảm bảo bạn đã thêm key của mình vào biến 'api_key' ở đầu tệp 'gobot_planner.py'.")
        ]
        
        for tag, text in guide_content:
            text_widget.insert(tk.END, text + "\n", tag)
            if tag in ["h1", "h2", "p"]:
                text_widget.insert(tk.END, "\n") # Add extra spacing

        text_widget.config(state=tk.DISABLED)
        ttk.Button(self, text="Đóng", command=self.destroy).pack(pady=10)


if __name__ == "__main__":
    app = GObotApp()
    app.mainloop()

