import logging
import os
import time
import tkinter as tk
import pyttsx3
import json
import threading
import requests
import json
from tkinter import ttk
import datetime


def setup_custom_logger(name):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    )

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


class ConfigPopup:
    def __init__(self, parent=None):
        self.result = {
            "overlay_enabled": True,
            "tts_enabled": True,
            "ignore_sp": False,
            "ignore_tier": False,
            "manual_stages": False
        }
        
        # Create popup window
        self.popup = tk.Tk() if parent is None else tk.Toplevel(parent)
        self.popup.title("Bounty Checker Configuration")
        self.popup.attributes("-topmost", True)
        self.popup.resizable(False, False)
        
        # Center the window
        window_width = 400
        window_height = 420  # Increased height to ensure all elements fit
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create main frame
        frame = ttk.Frame(self.popup, padding="20")
        frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Bounty Checker Settings", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Checkboxes frame
        check_frame = ttk.Frame(frame)
        check_frame.pack(fill="x", pady=5)
        
        # Checkboxes
        self.overlay_var = tk.BooleanVar(value=True)
        overlay_cb = ttk.Checkbutton(
            check_frame, text="Enable Overlay", variable=self.overlay_var
        )
        overlay_cb.pack(anchor="w", pady=2)
        
        self.tts_var = tk.BooleanVar(value=True)
        tts_cb = ttk.Checkbutton(
            check_frame, text="Enable Text-to-Speech", variable=self.tts_var
        )
        tts_cb.pack(anchor="w", pady=2)
        
        self.ignore_sp_var = tk.BooleanVar(value=False)
        ignore_sp_cb = ttk.Checkbutton(
            check_frame, text="Ignore Steel Path", variable=self.ignore_sp_var
        )
        ignore_sp_cb.pack(anchor="w", pady=2)
        
        self.ignore_tier_var = tk.BooleanVar(value=False)
        ignore_tier_cb = ttk.Checkbutton(
            check_frame, text="Ignore Tier", variable=self.ignore_tier_var
        )
        ignore_tier_cb.pack(anchor="w", pady=2)
        
        self.manual_stages_var = tk.BooleanVar(value=False)
        manual_stages_cb = ttk.Checkbutton(
            check_frame, text="Select Stages Manually", variable=self.manual_stages_var
        )
        manual_stages_cb.pack(anchor="w", pady=2)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(frame, text="Instructions", padding=10)
        instructions_frame.pack(fill="x", pady=10, padx=5)
        
        instructions_text = (
            "• To move the overlay: Click and drag it\n"
            "• To lock the overlay: Click on it and press CTRL+L\n"
            "• To unlock: Press CTRL+L again\n"
            "• Select the stages manually to choose which bounties to track\n"
            "• Right-click the overlay for more options"
        )
        
        instructions_label = ttk.Label(
            instructions_frame, 
            text=instructions_text,
            justify="left",
            wraplength=330
        )
        instructions_label.pack(fill="x")
        
        # Explicit Start button at the bottom with more visibility
        start_button = ttk.Button(
            frame, 
            text="Start",
            command=self.save_and_close,
            width=20
        )
        # Ensure the button is positioned at the bottom of the dialog
        start_button.pack(pady=20, padx=20)
        
        # Make window modal
        self.popup.transient(parent)
        self.popup.grab_set()
        
    def save_and_close(self):
        self.result = {
            "overlay_enabled": self.overlay_var.get(),
            "tts_enabled": self.tts_var.get(),
            "ignore_sp": self.ignore_sp_var.get(),
            "ignore_tier": self.ignore_tier_var.get(),
            "manual_stages": self.manual_stages_var.get()
        }
        self.popup.destroy()
        
    def get_config(self):
        self.popup.wait_window()
        return self.result


class OverlayApp:
    def __init__(self):
        # Get configuration
        config_popup = ConfigPopup()
        self.config = config_popup.get_config()
        
        self.path = None
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("10x10")
        self.root.configure(bg="black")
        self.root.attributes("-alpha", 0.5 if self.config["overlay_enabled"] else 0.0)
        self.enable_overlay = self.config["overlay_enabled"]
        self.enable_tts = self.config["tts_enabled"]
        self.ignore_sp = self.config["ignore_sp"]
        self.ignore_tier = self.config["ignore_tier"]
        self.locked = False  # Add locked variable
        self.label1 = tk.Label(
            self.root, text="", fg="white", bg="black", font=("Times New Roman", 15, "")
        )
        self.label2 = tk.Label(
            self.root, text="", fg="white", bg="black", font=("Times New Roman", 15, "")
        )

        self.label1.pack(fill="both", expand=True)
        self.label2.pack(fill="both", expand=True)
        # Keyboard shortcuts
        self.root.bind("<Control-l>", self.toggle_lock)
        self.root.bind("<Control-s>", lambda e: self.show_popup())
        self.root.bind("<Control-o>", lambda e: self.toggle_overlay())
        
        self.stageselection = self.config["manual_stages"]  # Set based on config
        self.label1.bind("<Button-1>", self.start_drag)
        self.label1.bind("<ButtonRelease-1>", self.stop_drag)
        self.label1.bind("<B1-Motion>", self.on_drag)
        self.label2.bind("<Button-1>", self.start_drag)
        self.label2.bind("<ButtonRelease-1>", self.stop_drag)
        self.label2.bind("<B1-Motion>", self.on_drag)
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

        self.width = (
            max(self.label1.winfo_reqwidth(), self.label2.winfo_reqwidth()) + 2
        )  # Add padding
        height = 50  # Fixed height
        self.screen_width = self.root.winfo_screenwidth()
        self.x = (self.screen_width / 2) - (self.width / 2)
        self.y = 0
        self.center = self.x + (self.width / 2)
        self.root.geometry(f"{self.width}x{height}+{int(self.x)}+{int(self.y)}")
        # settings
        self.logger = setup_custom_logger("Aya Bounty Tracker")

        self.path = os.getenv("LOCALAPPDATA") + "/Warframe/EE.log"
        self.first_run = True
        
        # Encoding detection
        self.file_encoding = self.detect_file_encoding()
        print(self.file_encoding)
        self.logger.info(f"Detected file encoding: {self.file_encoding}")
        
        # Delayed initialization of TTS
        self.tts = pyttsx3.init() if self.enable_tts else None
        
        # Initialize bounty data
        self.initialize_bounty_data()

        # Timer Settings
        self.last_line_index = self.last_access = self.bountycycles = 0
        self.start = self.end = self.elapsed = self.best_elapsed = 0
        self.start_bool = self.stage_bool = self.parse_success = self.good_bounty = (
            False
        )
        self.start_time = self.counts = 0
        self.stages_int = 5
        self.stage_time = self.stage_start = self.stage_end = self.stage_elapse = (
            self.elapsed_prev
        ) = 0
        self.stages_start = [
            "ResIntro",
            "AssIntro",
            "CapIntro",
            "CacheIntro",
            "HijackIntro",
            "FinalIntro",
        ]
        self.stages_translate_start = {
            "ResIntro": "Rescue",
            "AssIntro": "Assassinate",
            "CapIntro": "Capture",
            "CacheIntro": "Cache",
            "HijackIntro": "Drone",
            "FinalIntro": "Capture",
        }
        self.stages_translate_end = {
            "ResWin": "Rescue",
            "AssWin": "Assassinate",
            "CapWin": "Capture",
            "CacheWin": "Cache",
            "HijackWin": "Drone",
            "FinalWin": "Capture",
        }
        self.stages_end = [
            "ResWin",
            "AssWin",
            "CapWin",
            "CacheWin",
            "HijackWin",
            "FinalWin",
        ]
        self.tent_mapping = {
            "TentA": "Tent A: ",
            "TentB": "Tent B: ",
            "TentC": "Tent C: ",
        }
        self.stage_to_index = {
            "Rescue": 0,
            "Assassinate": 1,
            "Capture": 2,
            "Cache": 3,
            "Drone": 4,
        }
        self.dataset = []  # Store inliers
        self.mean = 0  # Running average
        self.stage = ""
        self.best_stage_elapses = [0, 0, 0, 0, 0]
        self.complete = self.bugged = False
        self.host = False
        self.line_num = 0

        # Initialize counters
        self.completed_bounties = 0
        self.best_stage_counter = {}
        self.aya_count = 0
        self.ui_update_needed = False
        
        # Add a flag to track the last seen bounty
        self.last_seen_bounty = None
        self.last_bounty_stages = []

    def detect_file_encoding(self):
        """Detect the encoding of the EE.log file using a more robust approach"""
        if not os.path.exists(self.path):
            self.logger.warning(f"Log file not found: {self.path}")
            return 'utf-8'  # Default to UTF-8 if file doesn't exist
            
        # Always try UTF-8 first as requested
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                # Try to read a small part of the file
                f.read(1024)
                self.logger.info("Successfully using UTF-8 encoding")
                return 'utf-8'
        except UnicodeDecodeError:
            self.logger.info("UTF-8 encoding failed, trying other encodings")
            
        # Try more robust detection by reading in binary mode
        try:
            # Read the file in binary mode to analyze the bytes
            with open(self.path, 'rb') as f:
                raw_data = f.read(4096)  # Read a larger chunk for better detection
                
            # Check for BOM (Byte Order Mark)
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            elif raw_data.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            elif raw_data.startswith(b'\xfe\xff'):
                return 'utf-16-be'
                
            # Try a series of common encodings
            encodings = [
                'cp1252', 'latin-1', 'iso-8859-1', 
                'windows-1250', 'windows-1252', 'ascii'
            ]
            
            for encoding in encodings:
                try:
                    raw_data.decode(encoding)
                    self.logger.info(f"Successfully detected encoding: {encoding}")
                    return encoding
                except UnicodeDecodeError:
                    continue
                    
            # If all else fails, use a very permissive encoding
            self.logger.warning("Could not detect specific encoding, using latin-1 which handles all byte values")
            return 'latin-1'  # latin-1 can decode any byte value
            
        except Exception as e:
            self.logger.error(f"Error during encoding detection: {e}")
            self.logger.warning("Falling back to latin-1 encoding which handles all byte values")
            return 'latin-1'  # Fallback to a very permissive encoding
            
    def initialize_bounty_data(self):
        try:
            wanted_bounties = requests.get(
                "https://gist.githubusercontent.com/ManInTheWallPog/d9cc2c83379a74ef57f0407b0d84d9b2/raw/"
            )
            wanted_bounties = wanted_bounties.content
            bounty_translation = requests.get(
                "https://gist.githubusercontent.com/ManInTheWallPog/02dfd3efdd62ed5b7061dd2e62324fa3/raw/"
            )
            bounty_translation = bounty_translation.content
            
            # Use utf-8 for API responses as they're typically in UTF-8
            wanted_bounties_str = wanted_bounties.decode('utf-8', errors='replace')
            bounty_translation_str = bounty_translation.decode('utf-8', errors='replace')
            
            self.wanted_bounties = json.loads(wanted_bounties_str)
            self.bounty_translation = json.loads(bounty_translation_str)
        except Exception as e:
            self.logger.error(f"Failed to initialize bounty data: {e}")
            # Fallback to empty datasets
            self.wanted_bounties = []
            self.bounty_translation = {}

    def start_drag(self, event):
        # Only start dragging if not locked
        if not self.locked:
            self.dragging = True
            self.offset_x = event.x
            self.offset_y = event.y

    def stop_drag(self, _):
        self.dragging = False

    def on_drag(self, event):
        if self.dragging:
            x = self.root.winfo_pointerx() - self.offset_x
            y = self.root.winfo_pointery() - self.offset_y
            self.root.geometry(f"+{x}+{y}")

    def toggle_lock(self, event=None):
        # Toggle lock state
        self.locked = not self.locked
        lock_status = "Locked" if self.locked else "Unlocked"
        
        # Provide visual feedback
        self.root.config(cursor="no" if self.locked else "")
        
        # Change label color to indicate locked state
        border_color = "#FF6666" if self.locked else "black"  # Light red border when locked
        self.root.configure(bg=border_color)
        
        # Provide audible feedback
        if self.enable_tts:
            self.speak_text(f"Overlay {lock_status}")
            
        # Flash effect for visual feedback
        original_fg = self.label1.cget("fg")
        flash_color = "#FF6666" if self.locked else "#66FF66"  # Red for locked, green for unlocked
        
        def flash():
            self.label1.config(fg=flash_color)
            self.label2.config(fg=flash_color)
            self.root.after(200, lambda: self.label1.config(fg=original_fg))
            self.root.after(200, lambda: self.label2.config(fg=original_fg))
            
        flash()

    def toggle_overlay(self):
        """Toggle overlay visibility"""
        self.enable_overlay = not self.enable_overlay
        self.root.attributes("-alpha", 0.5 if self.enable_overlay else 0.0)
        if self.enable_tts:
            self.speak_text("Overlay " + ("shown" if self.enable_overlay else "hidden"))

    def update_overlay(self, text, text_color):
        if not self.enable_overlay:
            return
            
        try:
            # Update label if necessary
            if text != "same" and text_color != "same":
                self.label1.config(text=text, fg=text_color)

            if self.bugged or (
                self.host == True
                and self.bountycycles % 42 == 0
                and self.bountycycles != 0
            ):
                self.label1.config(fg="red")

            best_stages = ""
            if self.stage in self.stage_to_index:
                index = self.stage_to_index[self.stage]
                best_stages = str(
                    datetime.timedelta(seconds=self.best_stage_elapses[index])
                )

            # Convert the times to a readable format
            finish = str(
                datetime.timedelta(
                    seconds=self.start_time if self.start_bool else self.elapsed
                )
            )
            best = str(datetime.timedelta(seconds=self.best_elapsed))
            stage = str(
                datetime.timedelta(
                    seconds=self.stage_time if self.stage_bool else self.stage_elapse
                )
            )
            mean = str(datetime.timedelta(seconds=self.mean))

            # Ensure millisecond precision
            def append_milliseconds(time_str):
                return time_str[:11] if "." in time_str else time_str + ".000"

            # Directly process each variable
            finish, best, mean, stage, best_stages = (
                append_milliseconds(var)
                for var in [finish, best, mean, stage, best_stages]
            )

            # Update label with formatted string
            if best_stages == ".000":
                text = f" Bounties Completed: {self.bountycycles} | Aya Farmed: {self.aya_count} | Timer: {finish} | Best Time: {best} | Avg. Time: {mean}"
            else:
                text = f" Bounties Completed: {self.bountycycles} | Aya Farmed: {self.aya_count} | Timer: {finish} | Best Time: {best} | Avg. Time: {mean} | Stage Timer: {stage} | Best {self.stage}: {best_stages}"
            self.label2.config(text=text)

            # Update window size
            self.root.update_idletasks()
            self.width = (
                max(self.label1.winfo_reqwidth(), self.label2.winfo_reqwidth()) + 2
            )  # Add padding
            height = 50  # Fixed height

            # Calculate coordinates for the window
            self.x = self.center - (self.width / 2)

            self.root.geometry(f"{self.width}x{height}+{int(self.x)}+{int(self.y)}")
        except Exception as e:
            self.logger.error(f"Error in update_overlay: {e}")

    def show_popup(self):
        popup = tk.Toplevel()
        popup.title("Bounty Tasks")
        popup.attributes("-topmost", True)
        popup.focus_force()
        frame = ttk.Frame(popup, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        var_dict = {}

        # Create checkboxes for each bounty
        for idx, (key, value) in enumerate(self.bounty_translation.items()):
            var_dict[key] = tk.BooleanVar(value=(key in self.wanted_bounties))
            cb = ttk.Checkbutton(frame, text=value, variable=var_dict[key])
            cb.grid(row=idx, column=0, sticky=tk.W)

        # Add some padding for the gap before "Ignore SP" checkbox
        ignore_sp_var = tk.BooleanVar(value=self.ignore_sp)  # Default to current setting
        ignore_sp_checkbox = ttk.Checkbutton(
            frame, text="Ignore SP", variable=ignore_sp_var
        )
        ignore_sp_checkbox.grid(
            row=len(self.bounty_translation) + 1, column=0, sticky=tk.W, pady=(10, 0)
        )  # Add gap above this checkbox
        
        ignore_tier_var = tk.BooleanVar(value=self.ignore_tier)  # Default to current setting
        ignore_tier_checkbox = ttk.Checkbutton(
            frame, text="Ignore Tier", variable=ignore_tier_var
        )
        ignore_tier_checkbox.grid(
            row=len(self.bounty_translation) + 2, column=0, sticky=tk.W, pady=(5, 0)
        )

        def save_and_close():
            self.wanted_bounties = [key for key, var in var_dict.items() if var.get()]
            self.ignore_sp = ignore_sp_var.get()
            self.ignore_tier = ignore_tier_var.get()
            popup.destroy()

        save_button = ttk.Button(frame, text="Save and Close", command=save_and_close)
        save_button.grid(
            row=len(self.bounty_translation) + 3, column=0, pady=10
        )  # No gap above this button

        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

    def calculate_running_average(self, value):
        # Add new value to the data
        self.dataset.append(value)

        if len(self.dataset) < 2:  # Need at least 4 values to reliably compute IQR
            self.mean = sum(self.dataset) / len(self.dataset) if self.dataset else 0
            return

        sorted_data = sorted(self.dataset)
        n = len(sorted_data)

        Q1 = sorted_data[n // 4]  # 25th percentile
        Q3 = sorted_data[3 * n // 4]  # 75th percentile
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Filter data points that are not outliers
        filtered_data = [x for x in self.dataset if lower_bound <= x <= upper_bound]

        # Update mean
        if filtered_data:
            self.mean = sum(filtered_data) / len(filtered_data)
        else:
            self.mean = 0  # No valid data points to average

    def clock(self):
        while True:
            if self.start_bool:
                self.update_overlay("same", "same")
                time.sleep(1)
                self.start_time += 1
                if self.stage_bool:
                    self.stage_time += 1
            else:
                time.sleep(0.5)

    def run(self):
        # If manual stage selection is enabled, show the popup
        if self.stageselection:
            self.show_popup()
            
        print("To lock the overlay, click on the overlay and press CTRL + L")
        print("Selected bounties:", self.wanted_bounties)
        threading.Thread(target=self.data_parser, daemon=True).start()
        threading.Thread(target=self.clock, daemon=True).start()
        self.update_overlay("Waiting for bounty", "white")
        
        # Add a right-click menu to the labels for quick access to stage selection
        self.create_context_menu()
        
        self.root.mainloop()
        
    def create_context_menu(self):
        """Create a right-click context menu for quick access to features"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Select Stages", command=self.show_popup)
        self.context_menu.add_command(label="Toggle Lock (Ctrl+L)", command=self.toggle_lock)
        self.context_menu.add_command(label="Toggle Overlay (Ctrl+O)", command=self.toggle_overlay)
        
        # Add a submenu for common settings
        settings_menu = tk.Menu(self.context_menu, tearoff=0)
        
        # Create variable for checkboxes
        self.menu_tts_var = tk.BooleanVar(value=self.enable_tts)
        self.menu_ignore_sp_var = tk.BooleanVar(value=self.ignore_sp)
        self.menu_ignore_tier_var = tk.BooleanVar(value=self.ignore_tier)
        
        def toggle_tts():
            self.enable_tts = self.menu_tts_var.get()
            if not self.enable_tts and self.tts:
                try:
                    self.tts.stop()
                except:
                    pass
        
        def toggle_ignore_sp():
            self.ignore_sp = self.menu_ignore_sp_var.get()
            
        def toggle_ignore_tier():
            self.ignore_tier = self.menu_ignore_tier_var.get()
        
        settings_menu.add_checkbutton(label="Text-to-Speech", 
                                     variable=self.menu_tts_var,
                                     command=toggle_tts)
        settings_menu.add_checkbutton(label="Ignore Steel Path", 
                                     variable=self.menu_ignore_sp_var,
                                     command=toggle_ignore_sp)
        settings_menu.add_checkbutton(label="Ignore Tier", 
                                     variable=self.menu_ignore_tier_var,
                                     command=toggle_ignore_tier)
        
        self.context_menu.add_cascade(label="Settings", menu=settings_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit", command=self.root.destroy)
        
        def show_menu(event):
            # Update checkbox states
            self.menu_tts_var.set(self.enable_tts)
            self.menu_ignore_sp_var.set(self.ignore_sp)
            self.menu_ignore_tier_var.set(self.ignore_tier)
            self.context_menu.post(event.x_root, event.y_root)
            
        self.label1.bind("<Button-3>", show_menu)
        self.label2.bind("<Button-3>", show_menu)

    def time_lines(self, data):
        for i in range(len(data)):
            line_data_for_time = self.lstring(data[i], " ")

            # Check if line is empty after splitting
            if not line_data_for_time:
                continue  # Skip empty lines

            # Attempt to convert the first part of the line to a timestamp
            try:
                timestamp = float(
                    line_data_for_time[0]
                )  # Extract the timestamp (first element)
            except ValueError:
                continue  # Skip to the next line if conversion fails
            
            message = " ".join(
                line_data_for_time[1:]
            )  # Reconstruct the message without the timestamp
            
            try:
                # Resets timers if aborted
                if any(
                    substring in message
                    for substring in [
                        "Script [Info]: EidolonMP.lua: EIDOLONMP: Going back to hub",
                        "Script [Info]: TopMenu.lua: Abort:",
                    ]
                ):
                    # Reset timers if mission aborted or player returns to hub
                    self.logger.info("Mission aborted or player returned to hub. Resetting timers.")
                    self.start_time = self.elapsed = self.stage_time = (
                        self.stage_elapse
                    ) = 0
                    self.start_bool = self.stage_bool = False
                    self.counts = 0
                    self.parse_success = True
                    self.complete = self.bugged = False

                elif (
                    "Net [Info]: MISSION_READY message: 1" in message
                    or "Net [Info]: SetSquadMissionReady(1)" in message
                ):
                    self.logger.info(f"Mission started: {message}")
                    self.start = timestamp
                    self.start_time = 0
                    self.start_bool = True
                    self.counts = 0
                    self.parse_success = True
                    self.complete = self.bugged = False

                # Checks Transmissions
                elif (
                    "Sys [Info]: GiveItem Queuing resource load for Transmission:"
                    in message
                ):
                    # Resets if bounty fails
                    if "BountyFail" in message:
                        self.start_time = self.elapsed = self.stage_time = (
                            self.stage_elapse
                        ) = 0
                        self.start_bool = self.stage_bool = False
                        self.counts = 0
                        self.complete = self.bugged = False

                    # Stage Start
                    elif any(stage in message for stage in self.stages_start):
                        self.stage_start = timestamp
                        self.stage_time = 0
                        self.stage_bool = True
                        stage = next(
                            (stage for stage in self.stages_start if stage in message),
                            "",
                        )
                        self.stage = self.stages_translate_start[stage]

                    # Stage End
                    elif any(stage in message for stage in self.stages_end):
                        self.stage_end = timestamp
                        if self.stage_start != 0:
                            self.stage_elapse = self.stage_end - self.stage_start
                        stage = next(
                            (stage for stage in self.stages_end if stage in message), ""
                        )
                        self.stage = self.stages_translate_end[stage]
                        if self.stage in self.stage_to_index:
                            index = self.stage_to_index[self.stage]
                            # Check the conditions for updating the best_stage_elapses
                            if (self.best_stage_elapses[index] == 0) or (
                                self.stage_elapse <= self.best_stage_elapses[index]
                            ):
                                if self.stage_elapse >= 0:
                                    self.best_stage_elapses[index] = round(
                                        self.stage_elapse, 3
                                    )
                        self.stage_start = 0
                        self.stage_bool = False
                    self.parse_success = True

                if self.complete == True:
                    self.line_num += 1
                    if self.line_num == 5:
                        self.complete = False
                        self.line_num = 0
                        self.bugged = True

                # Checks if stage is completed
                if "Created /Lotus/Interface/EidolonMissionComplete.swf" in message:
                    self.complete = True
                    self.parse_success = True
                    self.line_num = 0
                    self.bugged = False

                # Increments after each reward
                if (
                    "EidolonMissionComplete.lua: EidolonMissionComplete:: Got Reward:"
                    in message
                ):
                    self.logger.info("Stage Completed")
                    self.counts += 1
                    self.complete = self.bugged = False
                    self.ui_update_needed = True
                    if (
                        "Got Reward: /Lotus/StoreItems/Types/Items/MiscItems/SchismKey"
                        in message
                    ):
                        self.logger.info("Aya found!")
                        self.aya_count += 1
                    if self.counts == 5:
                        self.end = timestamp
                        self.start_bool = False
                        self.bountycycles += 1
                        # Calculate elapsed time if conditions are met
                        if self.end > self.start:
                            self.elapsed = self.end - self.start
                        if (self.best_elapsed == 0) or (
                            self.elapsed <= self.best_elapsed
                        ):
                            self.best_elapsed = round(self.elapsed, 3)
                        if self.elapsed != self.elapsed_prev and self.elapsed != 0:
                            self.calculate_running_average(self.elapsed)
                            self.elapsed_prev = self.elapsed

                    self.parse_success = True
            except Exception as e:
                self.logger.error(f"Error processing line: {e} | Line: {i}")

    def data_parser(self):
        last_access = 0
        last_line_index = 0

        while True:
            try:
                checkaccesstime = os.path.getmtime(self.path)
                if checkaccesstime != last_access:
                    last_access = checkaccesstime
                    try:
                        data, current_last_index = self.read_ee(last_line_index)
                        if not data:
                            time.sleep(0.5)
                            continue
                    except Exception as e:
                        self.logger.error(f"Error reading EE.log: {e}")
                        time.sleep(0.5)
                        continue
                        
                    if self.first_run:
                        self.first_run = False
                        text = "Waiting for bounty"
                        self.update_overlay(text, "white")
                        if self.enable_tts:
                            self.tts.say(text)
                            self.tts.runAndWait()

                        with open(self.path, "r", encoding=self.file_encoding, errors='replace') as f:
                            f.readlines()  # Read all lines to get to the end
                            last_line_index = f.tell()
                        continue
                        
                    parse_success = self.parse_lines(data)
                    self.time_lines(data)
                    last_line_index = current_last_index

                time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error in data_parser: {e}")
                time.sleep(0.5)

    def lstring(self, data, seperators):
        output = []
        var = ""
        for char in data:
            Outputting = True
            if char in seperators:
                Outputting = False
            if Outputting:
                var = var + char
            else:
                output.append(var)
                var = ""
        output.append(var)

        return output

    def read_ee(self, last_line_index):
        current_last_index = last_line_index
        lines = []
        
        try:
            # First attempt with detected encoding
            with open(self.path, "r", encoding=self.file_encoding, errors='replace') as f:
                f.seek(current_last_index)
                lines = f.readlines()
                for line in lines:
                    current_last_index = f.tell()
                    
        except UnicodeDecodeError as e:
            self.logger.warning(f"Unicode decode error with {self.file_encoding}: {e}")
            
            try:
                # If specific encoding fails, try latin-1 which can handle any byte
                self.logger.info("Falling back to latin-1 encoding for this read")
                with open(self.path, "r", encoding='latin-1', errors='replace') as f:
                    f.seek(current_last_index)
                    lines = f.readlines()
                    for line in lines:
                        current_last_index = f.tell()
            except Exception as e2:
                self.logger.error(f"Error reading file with fallback encoding: {e2}")
                # Final attempt with binary reading
                try:
                    with open(self.path, "rb") as f:
                        f.seek(current_last_index)
                        binary_data = f.read()
                        # Decode with replacing errors
                        text = binary_data.decode('latin-1', errors='replace')
                        lines = text.splitlines(True)  # Keep line endings
                        current_last_index = f.tell()
                except Exception as e3:
                    self.logger.error(f"Error reading file in binary mode: {e3}")
                    return [], last_line_index
                    
        except Exception as e:
            self.logger.error(f"Error reading EE.log file: {e}")
            return [], last_line_index
            
        return lines, current_last_index

    def speak_text(self, text):
        if self.enable_tts and self.tts:
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception as e:
                self.logger.error(f"TTS Error: {e}")

    def parse_lines(self, data):
        for i in range(len(data)):
            line_data = self.lstring(data[i], " ")
            
            if len(line_data) < 6:
                continue

            try:
                # Only proceed if this is a bounty-related line
                if " ".join(line_data[1:6]) == "Net [Info]: Set squad mission:":
                    try:
                        # Check if the line contains bounty-related keywords before attempting to parse
                        if not any(keyword in " ".join(line_data) for keyword in ["/Lotus/Types/Gameplay/Eidolon/Jobs/", "jobStages", "jobTier"]):
                            continue
                            
                        json_data = self.parse_squad_mission_line(line_data)
                        
                        # Store this bounty info as the last seen bounty
                        bounty_hash = str(json_data.get('job', '')) + str(json_data.get('jobStages', []))
                        
                        # Skip processing if we've already seen this exact bounty recently
                        if bounty_hash == self.last_seen_bounty:
                            # Only continue if the UI needs updating
                            if not self.ui_update_needed:
                                continue
                                
                        # Update last seen bounty
                        self.last_seen_bounty = bounty_hash
                        
                        if not all(
                            key in json_data for key in ["jobTier", "jobStages", "job"]
                        ):
                            continue
                            
                        # Check Steel Path condition
                        is_steel_path = json_data.get("isHardJob") == "True"
                        if is_steel_path and not self.ignore_sp:
                            self.update_overlay("Wrong Tier - Steel Path Bounty", "red")
                            self.speak_text("Wrong tier, Bounty is Steel Path")
                            return True

                        # Check tier condition if configured
                        if not self.ignore_tier and json_data["jobTier"] != 4:
                            if not json_data.get("isHardJob") == "True":
                                self.update_overlay(f"Wrong Tier: {json_data['jobTier']}", "red")
                                self.speak_text(f"Wrong tier, tier is {str(json_data['jobTier'])}")
                                return True

                        # Check if all stages are wanted
                        if not all(
                            stage in self.wanted_bounties
                            for stage in json_data["jobStages"]
                        ):
                            try:
                                stages = [
                                    self.bounty_translation[stage]
                                    for stage in json_data["jobStages"]
                                ]
                                self.last_bounty_stages = stages  # Save stages for display
                                stages_string = " -> ".join(stages)
                                self.logger.info(stages_string)
                                self.update_overlay(stages_string, "red")
                                self.logger.info("Bad Bounty")
                                self.speak_text("Bad Bounty")
                                return True
                            except Exception as e:
                                self.logger.error(f"Error processing bad bounty: {e}")
                            return True
                            
                        # This is a good bounty
                        stages = [
                            self.bounty_translation[stage]
                            for stage in json_data["jobStages"]
                        ]
                        self.last_bounty_stages = stages  # Save stages for display
                        stages_string = " -> ".join(stages)
                        self.update_overlay(stages_string, "green")
                        self.logger.info(stages_string)
                        self.logger.info("Good Bounty")
                        self.speak_text("Good Bounty")
                        return True
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing squad mission: {e}")
                        return False

            except Exception as e:
                self.logger.error(f"Error in parse_lines: {e}")
                continue
                
        return False

    def parse_squad_mission_line(self, line_data):
        try:
            # Join the line data and find the JSON portion
            data_string = " ".join(line_data[6:])
            
            # First try to find JSON-like content
            json_start_index = data_string.find("{")
            json_end_index = data_string.rfind("}")
            
            # If we can't find proper JSON brackets, try to extract information directly
            if json_start_index == -1 or json_end_index == -1:
                # Only log if we actually found bounty-related content
                if any(keyword in data_string for keyword in ["/Lotus/Types/Gameplay/Eidolon/Jobs/", "jobStages", "jobTier"]):
                    self.logger.debug("No valid JSON found in squad mission line, attempting direct extraction")
                else:
                    return {}
                    
                # Try to extract job information directly from the string
                job_info = {}
                
                # Look for job path pattern
                job_path_pattern = "/Lotus/Types/Gameplay/Eidolon/Jobs/"
                job_start = data_string.find(job_path_pattern)
                if job_start != -1:
                    # Extract job identifier
                    job_end = data_string.find(" ", job_start)
                    if job_end == -1:
                        job_end = len(data_string)
                    job = data_string[job_start:job_end]
                    job_info["job"] = job
                
                # Look for jobStages array
                stages_start = data_string.find("jobStages")
                if stages_start != -1:
                    stages_start = data_string.find("[", stages_start)
                    if stages_start != -1:
                        stages_end = data_string.find("]", stages_start)
                        if stages_end != -1:
                            stages_str = data_string[stages_start + 1:stages_end]
                            stages = [s.strip().strip('"') for s in stages_str.split(",")]
                            job_info["jobStages"] = stages
                
                # Look for jobTier
                tier_start = data_string.find("jobTier")
                if tier_start != -1:
                    tier_start = data_string.find(":", tier_start)
                    if tier_start != -1:
                        tier_end = data_string.find(",", tier_start)
                        if tier_end == -1:
                            tier_end = data_string.find("}", tier_start)
                        if tier_end != -1:
                            tier = data_string[tier_start + 1:tier_end].strip()
                            try:
                                job_info["jobTier"] = int(tier)
                            except ValueError:
                                job_info["jobTier"] = 0
                
                # Look for isHardJob
                hard_start = data_string.find("isHardJob")
                if hard_start != -1:
                    hard_start = data_string.find(":", hard_start)
                    if hard_start != -1:
                        hard_end = data_string.find(",", hard_start)
                        if hard_end == -1:
                            hard_end = data_string.find("}", hard_start)
                        if hard_end != -1:
                            is_hard = data_string[hard_start + 1:hard_end].strip().lower()
                            job_info["isHardJob"] = is_hard == "true"
                
                if job_info:
                    self.logger.debug(f"Successfully extracted job info: {job_info}")
                    return job_info
                
                self.update_overlay("Select Different Tier Bounty -> Reselect this Bounty", "yellow")
                if self.enable_tts:
                    self.speak_text("Reselect Bounty")
                return {}
            
            # If we found JSON brackets, try to parse the JSON
            json_data = data_string[json_start_index:json_end_index + 1]
            
            # Clean up the JSON string for parsing
            json_data = (
                json_data.replace("null", "None")
                .replace("true", "True")
                .replace("false", "False")
                .replace("True", '"True"')
                .replace("False", '"False"')
            )
            
            try:
                parsed_data = json.loads(json_data)
                if isinstance(parsed_data, dict):
                    return parsed_data
                else:
                    self.logger.debug("Parsed JSON is not a dictionary")
                    return {}
            except json.JSONDecodeError as e:
                self.logger.debug(f"Failed to parse JSON: {e}")
                # Try to extract information directly as fallback
                return self.parse_squad_mission_line(line_data)  # Recursive call to use direct extraction
                
        except Exception as e:
            self.logger.error(f"Error in parse_squad_mission_line: {e}")
            self.update_overlay("Select Different Tier Bounty -> Reselect this Bounty", "yellow")
            if self.enable_tts:
                self.speak_text("Reselect Bounty")
            return {}

    def update_state_with_completed_bounties(self, completed_bounties):
        self.completed_bounties = completed_bounties
        self.ui_update_needed = True
        
    def update_ui(self):
        self.ui_update_needed = False
        # If we have stages from the last seen bounty, display them
        if self.last_bounty_stages:
            stages_string = " -> ".join(self.last_bounty_stages)
            color = "green" if all(stage in self.wanted_bounties for stage in self.last_bounty_stages) else "red"
            self.update_overlay(stages_string, color)


if __name__ == "__main__":
    app = OverlayApp()
    app.run()