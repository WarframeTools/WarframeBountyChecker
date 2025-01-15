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


class OverlayApp:
    def __init__(self):
        self.path = None
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("10x10")
        self.root.configure(bg="black")
        self.root.attributes("-alpha", 0.5)
        self.enable_overlay = True
        self.locked = False  # Add locked variable
        self.label1 = tk.Label(
            self.root, text="", fg="white", bg="black", font=("Times New Roman", 15, "")
        )
        self.label2 = tk.Label(
            self.root, text="", fg="white", bg="black", font=("Times New Roman", 15, "")
        )

        self.label1.pack(fill="both", expand=True)
        self.label2.pack(fill="both", expand=True)
        self.root.bind("<Control-l>", self.toggle_lock)
        self.stageselection = False
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
        wanted_bounties = requests.get(
            "https://gist.githubusercontent.com/ManInTheWallPog/d9cc2c83379a74ef57f0407b0d84d9b2/raw/"
        )
        wanted_bounties = wanted_bounties.content
        bounty_translation = requests.get(
            "https://gist.githubusercontent.com/ManInTheWallPog/02dfd3efdd62ed5b7061dd2e62324fa3/raw/"
        )
        bounty_translation = bounty_translation.content
        wanted_bounties_str = wanted_bounties.decode("utf-8")
        bounty_translation_str = bounty_translation.decode("utf-8")
        self.wanted_bounties = json.loads(wanted_bounties_str)
        self.bounty_translation = json.loads(bounty_translation_str)

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
        self.ignore_sp = False

        # Initialize counters
        self.completed_bounties = 0
        self.best_stage_counter = {}
        self.aya_count = 0
        self.ui_update_needed = False

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
        self.root.config(cursor="none")

    def update_overlay(self, text, text_color):
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
            print(e)

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
        ignore_sp_var = tk.BooleanVar(value=False)  # Default to unchecked
        ignore_sp_checkbox = ttk.Checkbutton(
            frame, text="Ignore SP", variable=ignore_sp_var
        )
        ignore_sp_checkbox.grid(
            row=len(self.bounty_translation) + 1, column=0, sticky=tk.W, pady=(10, 0)
        )  # Add gap above this checkbox

        def save_and_close():
            self.wanted_bounties = [key for key, var in var_dict.items() if var.get()]
            self.ignore_sp = (
                ignore_sp_var.get()
            )  # Store the Ignore SP state as an instance attribute
            popup.destroy()

        save_button = ttk.Button(frame, text="Save and Close", command=save_and_close)
        save_button.grid(
            row=len(self.bounty_translation) + 2, column=0, pady=10
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
        overlayselection = False
        print("To lock the overlay, click on the overlay and press CTRL + L")
        while not overlayselection:
            overlay_enabled = (
                input("Do you want to enable Overlay? (Y/N):").strip().lower()
            )
            if overlay_enabled == "y":
                overlayselection = True
            elif overlay_enabled == "n":
                overlayselection = True
                self.enable_overlay = False
                self.root.attributes("-alpha", 0.0)

        while not self.stageselection:
            stageselection_enabled = (
                input("Do you want to select your stages manually? (Y/N):")
                .strip()
                .lower()
            )
            if stageselection_enabled == "y":
                self.stageselection = True
                self.show_popup()
            elif stageselection_enabled == "n":
                self.stageselection = True
        print("Selected bounties:", self.wanted_bounties)
        threading.Thread(target=self.data_parser).start()
        threading.Thread(target=self.clock).start()
        self.update_overlay("starting", "white")
        self.root.mainloop()

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
            except ValueError as e:
                continue  # Skip to the next line if conversion fails
            message = " ".join(
                line_data_for_time[1:]
            )  # Reconstruct the message without the timestamp
            # Continue processing `message`
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
                    print(
                        "Mission aborted or player returned to hub. Resetting timers."
                    )
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
                    print("mission_started", message)
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
                    # print(message)
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
                    print("Stage Completed")
                    self.counts += 1
                    self.complete = self.bugged = False
                    self.ui_update_needed = True
                    if (
                        "Got Reward: /Lotus/StoreItems/Types/Items/MiscItems/SchismKey"
                        in message
                    ):
                        print("Aya")
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
                self.logger.error(f"Please Report this String5: {e} | Line: {i}")

    def data_parser(self):
        last_access = 0
        last_line_index = 0

        tts = pyttsx3.init()
        while True:
            try:
                checkaccesstime = os.path.getmtime(self.path)
                if checkaccesstime != last_access:
                    last_access = checkaccesstime
                    try:
                        data, current_last_index = self.read_ee(last_line_index)
                        if data == []:
                            continue
                    except Exception as e:
                        self.logger.info(f"Error reading EE.log {e}")
                        continue
                    if self.first_run:
                        self.first_run = False
                        text = "Waiting for bounty"
                        self.update_overlay(text, "white")
                        tts.say(text)
                        tts.runAndWait()

                        with open(self.path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            for line in lines:
                                last_line_index = f.tell()
                        continue
                    parse_success = self.parse_lines(data, tts)
                    self.time_lines(data)
                    last_line_index = current_last_index

                time.sleep(0.5)
            except Exception as e:
                self.logger.info(f"Error reading EE.log {e}")
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
        with open(self.path, "r", encoding="utf-8") as f:
            f.seek(current_last_index)
            lines = f.readlines()
            for line in lines:
                current_last_index = f.tell()
        return lines, current_last_index

    def parse_lines(self, data, tts):
        for i in range(len(data)):
            line_data = self.lstring(data[i], " ")

            try:

                if " ".join(line_data[1:6]) == "Net [Info]: Set squad mission:":
                    try:
                        data_string = " ".join(line_data[6:])
                        json_start_index = data_string.find("{")
                        json_end_index = data_string.rfind("}") + 1
                        json_data = data_string[json_start_index:json_end_index]
                        json_data = (
                            json_data.replace("null", "None")
                            .replace("true", "True")
                            .replace("false", "False")
                            .replace("True", '"True"')
                        )
                        try:
                            json_data = json.loads(json_data)
                        except Exception as e:
                            continue

                        if not all(
                            key in json_data for key in ["jobTier", "jobStages", "job"]
                        ):
                            continue
                        if json_data.get("isHardJob") == "True" and not self.ignore_sp:
                            self.update_overlay("Wrong Tier", "red")
                            text = f"Wrong tier, Bounty is Steel Path"
                            tts.say(text)
                            tts.runAndWait()
                            return True

                        if json_data["jobTier"] != 4:
                            if (
                                not json_data.get("isHardJob") == "True"
                                and not self.ignore_sp
                            ):
                                self.update_overlay("Wrong Tier", "red")
                                text = (
                                    f"Wrong tier, tier is {str(json_data['jobTier'])}"
                                )
                                tts.say(text)
                                tts.runAndWait()

                                return True

                        if not all(
                            stage in self.wanted_bounties
                            for stage in json_data["jobStages"]
                        ):
                            try:
                                stages = [
                                    self.bounty_translation[stage]
                                    for stage in json_data["jobStages"]
                                ]
                                stages_string = " -> ".join(stages)
                                self.logger.info(stages_string)
                                self.update_overlay(stages_string, "red")
                                self.logger.info("Bad Bounty")
                                tts.say("Bad Bounty")
                                tts.runAndWait()
                                return True
                            except Exception as e:
                                self.logger.error(f"Please Report this String: {e}")

                            return True
                    except Exception as e:
                        return False
                    stages = [
                        self.bounty_translation[stage]
                        for stage in json_data["jobStages"]
                    ]
                    stages_string = " -> ".join(stages)
                    self.update_overlay(stages_string, "green")
                    self.logger.info(stages_string)
                    self.logger.info("Good Bounty")
                    tts.say("Good Bounty")
                    tts.runAndWait()
                    return True

            except Exception as e:
                continue

    def parse_squad_mission_line(self, line_data):
        data_string = " ".join(line_data[6:])
        json_start_index = data_string.find("{")
        json_end_index = data_string.rfind("}") + 1
        json_data = data_string[json_start_index:json_end_index]
        json_data = (
            json_data.replace("null", "None")
            .replace("true", "True")
            .replace("false", "False")
            .replace("True", '"True"')
        )
        return json.loads(json_data)

    def update_state_with_completed_bounties(self, completed_bounties):
        self.state["completed_bounties"] = completed_bounties
        self.update_bounty_counter_ui(completed_bounties)

    def update_average_time_ui(self, average_time):
        try:
            self.ui.averageTimeLabel.setText(f"Average Time: {average_time:.2f} mins")
        except Exception as e:
            self.logger.error(f"Error updating average time UI: {e}")

    def update_bounties_completed(self, stage_number):
        if stage_number == 5:
            self.completed_bounties += 1
            self.ui.bountyCounterLabel.setText(
                f"Completed Bounties: {self.completed_bounties}"
            )

    def update_best_stage_counter(self, stage_name):
        if stage_name not in self.best_stage_counter:
            self.best_stage_counter[stage_name] = 0
        self.best_stage_counter[stage_name] += 1
        self.ui.bestStageCounterLabel.setText(
            f"Best {stage_name} Count: {self.best_stage_counter[stage_name]}"
        )

    def process_mission_stage(self, stage_number, stage_name):
        # Update counters
        if stage_number == 5:
            self.completed_bounties += 1
            self.ui_update_needed = True

        if stage_name not in self.best_stage_counter:
            self.best_stage_counter[stage_name] = 0
        self.best_stage_counter[stage_name] += 1
        self.ui_update_needed = True
        # Batch UI updates
        if self.ui_update_needed:
            self.update_ui()

    def update_ui(self):
        self.ui.bountyCounterLabel.setText(
            f"Completed Bounties: {self.completed_bounties} | Total Aya: {self.aya_count}"
        )
        self.ui.bestStageCounterLabel.setText(
            f"Best Stage Counts: {self.best_stage_counter}"
        )
        self.ui_update_needed = False


if __name__ == "__main__":

    app = OverlayApp()
    app.run()
