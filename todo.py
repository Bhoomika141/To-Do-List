import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
from datetime import date
import random
from PIL import Image, ImageTk
import os

quotes = [
    "Believe you can and you're halfway there.",
    "Progress, not perfection.",
    "Success is not for the lazy.",
    "Each step forward is toward success."
]

FONT_SIZES = {
    "Small": {'LARGE': 13, 'TASK': 10, 'NOTE': 9},
    "Medium": {'LARGE': 16, 'TASK': 12, 'NOTE': 11},
    "Large": {'LARGE': 20, 'TASK': 15, 'NOTE': 14},
}
THEMES = {
    "Light": {
        "BG": "#F7F6E7", "BTN": "#407BFF", "BTN_TEXT": "#FFFFFF", "FRAME": "#FFFFFF", "ENTRY": "#FFFFFF", "TEXT": "#111111"
    },
    "Dark": {
        "BG": "#222939", "BTN": "#50A7FF", "BTN_TEXT": "#F3F3F3", "FRAME": "#31394D", "ENTRY": "#31394D", "TEXT": "#F3F3F3"
    },
    "High Contrast": {
        "BG": "#000000", "BTN": "#FFFF00", "BTN_TEXT": "#000000", "FRAME": "#000000", "ENTRY": "#000000", "TEXT": "#FFFFFF"
    }
}
PRIORITY_LOOKUP = {
    'High': ('#e74c3c', 'HIGH'),
    'Medium': ('#f39c12', 'MEDIUM'),
    'Low': ('#27ae60', 'LOW'),
}

class Task:
    def __init__(self, description, quote, deadline=None, completed=False, notes="", subtasks=None, priority="Medium"):
        self.description = description
        self.quote = quote
        self.deadline = deadline
        self.completed = completed
        self.notes = notes
        self.subtasks = subtasks if subtasks is not None else []
        self.priority = priority

tasks = []

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.theme = "Light"
        self.font_size = "Medium"
        self.colors = THEMES[self.theme]
        self.root.title("Motivational To-Do List")
        self.root.config(bg=self.colors["BG"])
        self.avatar_images = []
        self.avatar_idx = 0
        self.username = "User"
        self.load_avatars()
        self.deleted_task = None
        self.deleted_index = None
        self.filter_var = tk.StringVar(value="All")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda a,b,c: self.refresh_tasks())
        self.achievements_var = tk.StringVar(value="")
        self.font_var = tk.StringVar(value=self.font_size)
        self.high_contrast_on = False

        # Header
        topbar = tk.Frame(root, bg=self.colors["BG"])
        topbar.pack(fill="x", pady=(2,2))
        self.avatar_label = tk.Label(topbar, bg=self.colors["BG"])
        self.avatar_label.pack(side="left", padx=5)
        self.avatar_label.bind("<Button-1>", self.change_avatar)
        self.username_label = tk.Label(topbar, text=self.username, font=self.get_font('TASK', bold=True), bg=self.colors["BG"], fg=self.colors["TEXT"], cursor="hand2")
        self.username_label.pack(side="left", padx=(3,10))
        self.username_label.bind("<Button-1>", self.change_username)
        self.theme_btn = tk.Button(topbar, text="Theme", font=self.get_font('NOTE'),
                                  command=self.switch_theme, bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"])
        self.theme_btn.pack(side="right", padx=12)
        self.font_btn = tk.Menubutton(topbar, text="Font Size", font=self.get_font('NOTE'), bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"])
        font_menu = tk.Menu(self.font_btn, tearoff=False)
        for label in FONT_SIZES.keys():
            font_menu.add_radiobutton(label=label, variable=self.font_var, command=self.change_fontsize)
        self.font_btn["menu"] = font_menu
        self.font_btn.pack(side="right", padx=5)
        self.highcont_btn = tk.Checkbutton(topbar, text="High Contrast", variable=tk.BooleanVar(value=False),
                                          command=self.toggle_contrast, font=self.get_font('NOTE'), bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.highcont_btn.pack(side="right", padx=5)
        self.show_avatar_and_username()

        self.achievements_lbl = tk.Label(root, textvariable=self.achievements_var, font=self.get_font('TASK', bold=True), bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.achievements_lbl.pack(pady=(1,0))

        self.daily_quote = random.choice(quotes)
        self.motivation_lbl = tk.Label(
            root, text=f"💡 {self.daily_quote}", font=self.get_font('NOTE', italic=True),
            fg='#8888AA', bg=self.colors["BG"], pady=2
        )
        self.motivation_lbl.pack()

        self.title = tk.Label(root, text="Motivational To-Do List", font=self.get_font('LARGE', bold=True), bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.title.pack(pady=4)

        # Search/Filters
        search_frame = tk.Frame(root, bg=self.colors["BG"])
        search_frame.pack(pady=(2,4))
        tk.Label(search_frame, text="Search:", font=self.get_font('NOTE'), bg=self.colors["BG"], fg=self.colors["TEXT"]).pack(side="left", padx=(0,2))
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=22, font=self.get_font('TASK'), bg=self.colors["ENTRY"], fg=self.colors["TEXT"])
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda e: self.refresh_tasks())
        for status in ("All", "Pending", "Completed"):
            b = tk.Radiobutton(
                search_frame, text=status, value=status,
                variable=self.filter_var, font=self.get_font('NOTE'),
                bg=self.colors["BG"], fg=self.colors["TEXT"], command=self.refresh_tasks,
                selectcolor=self.colors["FRAME"], activebackground=self.colors["BG"]
            )
            b.pack(side="left", padx=(6,0))

        # New Task Entry
        entry_frame = tk.Frame(root, bg=self.colors["BG"])
        entry_frame.pack(pady=2)
        self.task_entry = tk.Entry(entry_frame, font=self.get_font('TASK'), width=20, bg=self.colors["ENTRY"], fg=self.colors["TEXT"])
        self.task_entry.pack(side="left", padx=2)
        self.task_entry.bind('<Return>', lambda e: self.add_task())
        self.priority_var = tk.StringVar(value="Medium")
        priority_menu = ttk.Combobox(entry_frame, textvariable=self.priority_var, values=list(PRIORITY_LOOKUP.keys()), width=7, font=self.get_font('NOTE'), state='readonly')
        priority_menu.pack(side="left", padx=(5,2))
        self.deadline_entry = DateEntry(entry_frame, width=12, background='darkblue', foreground='white', borderwidth=2, font=self.get_font('NOTE'))
        self.deadline_entry.set_date(date.today())
        self.deadline_entry.pack(side="left", padx=2)
        self.add_btn = tk.Button(entry_frame, text="Add Task", font=self.get_font('TASK'), bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"], command=self.add_task)
        self.add_btn.pack(side="left", padx=(5,2))
        self.add_btn.bind("<Return>", lambda e: self.add_task())

        # Progress and chart
        self.progress_label = tk.Label(root, text="", bg=self.colors["BG"], fg=self.colors["TEXT"], font=self.get_font('NOTE'))
        self.progress_label.pack(pady=2)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=280, mode="determinate")
        self.progress.pack(pady=1, padx=5)
        self.chart_frame = tk.Frame(root, bg=self.colors["BG"])
        self.chart_frame.pack(pady=1)
        self.tasks_frame = tk.Frame(root, bg=self.colors["BG"])
        self.tasks_frame.pack(pady=6)

        # Undo
        self.undo_frame = tk.Frame(root, bg=self.colors["BG"])
        self.undo_frame.pack()
        self.setup_shortcuts()
        self.apply_fonts()
        self.refresh_tasks()

    def get_font(self, which, bold=False, italic=False):
        sz = FONT_SIZES[self.font_var.get()][which]
        family = 'Helvetica'
        weight = 'bold' if bold else 'normal'
        slant = 'italic' if italic else 'roman'
        return (family, sz, weight, slant)

    def load_avatars(self):
        self.avatar_images.clear()
        self.avatar_files = []
        avatar_folder = os.path.join(os.path.dirname(__file__), "avatars")
        if not os.path.exists(avatar_folder):
            os.makedirs(avatar_folder)
        for i in range(1, 7):
            fn_png = os.path.join(avatar_folder, f"avatar{i}.png")
            if os.path.isfile(fn_png):
                img = Image.open(fn_png).resize((46, 46))
                self.avatar_images.append(ImageTk.PhotoImage(img))
                self.avatar_files.append(fn_png)
        if not self.avatar_images:
            empty_img = Image.new("RGB", (46,46), "#949494")
            self.avatar_images = [ImageTk.PhotoImage(empty_img)]
            self.avatar_files = [None]
        self.avatar_idx = 0

    def show_avatar_and_username(self):
        img = self.avatar_images[self.avatar_idx]
        self.avatar_label.config(image=img, bg=self.colors["BG"])
        self.avatar_label.image = img
        self.username_label.config(text=self.username, fg=self.colors["TEXT"], bg=self.colors["BG"])

    def change_avatar(self, event=None):
        self.avatar_idx = (self.avatar_idx + 1) % len(self.avatar_images)
        self.show_avatar_and_username()

    def change_username(self, event=None):
        def set_username():
            n = user_entry.get().strip()
            if n:
                self.username = n
                self.show_avatar_and_username()
                dlg.destroy()
        dlg = tk.Toplevel(self.root)
        dlg.title("Change Username")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.config(bg=self.colors["BG"])
        tk.Label(dlg, text="Enter your name:", bg=self.colors["BG"], fg=self.colors["TEXT"], font=('Helvetica', 11)).pack(pady=(8,3), padx=10)
        user_entry = tk.Entry(dlg, font=('Helvetica', 12), width=20)
        user_entry.insert(0, self.username)
        user_entry.pack(padx=10, pady=4)
        tk.Button(dlg, text="Set Name", bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"], font=('Helvetica', 10), command=set_username).pack(pady=6)
        user_entry.focus_set()
        dlg.bind('<Return>', lambda e: set_username())

    def switch_theme(self):
        order = ["Light", "Dark", "High Contrast"]
        idx = (order.index(self.theme) + 1) % len(order)
        self.theme = order[idx]
        self.colors = THEMES[self.theme]
        self.root.config(bg=self.colors["BG"])
        self.motivation_lbl.config(bg=self.colors["BG"], fg='#FFFF00' if self.theme=="High Contrast" else '#bbbbcc' if self.theme=="Dark" else '#8888AA')
        self.title.config(bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.progress_label.config(bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.undo_frame.config(bg=self.colors["BG"])
        self.avatar_label.config(bg=self.colors["BG"])
        self.username_label.config(bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.theme_btn.config(bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"])
        self.font_btn.config(bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"])
        self.highcont_btn.config(bg=self.colors["BG"], fg=self.colors["TEXT"], selectcolor=self.colors["FRAME"])
        self.achievements_lbl.config(bg=self.colors["BG"], fg=self.colors["TEXT"])
        self.chart_frame.config(bg=self.colors["BG"])
        self.tasks_frame.config(bg=self.colors["BG"])
        self.apply_fonts()
        self.refresh_tasks()
    
    def change_fontsize(self):
        self.apply_fonts()
        self.refresh_tasks()

    def apply_fonts(self):
        self.title.config(font=self.get_font('LARGE', bold=True))
        self.username_label.config(font=self.get_font('TASK', bold=True))
        self.achievements_lbl.config(font=self.get_font('TASK', bold=True))
        self.motivation_lbl.config(font=self.get_font('NOTE', italic=True))
        self.search_entry.config(font=self.get_font('TASK'))
        self.task_entry.config(font=self.get_font('TASK'))
        self.progress_label.config(font=self.get_font('NOTE'))
        self.theme_btn.config(font=self.get_font('NOTE'))
        self.font_btn.config(font=self.get_font('NOTE'))
        # Add more static widgets here as needed

    def toggle_contrast(self):
        self.theme = "High Contrast" if self.theme != "High Contrast" else "Light"
        self.colors = THEMES[self.theme]
        self.font_btn["fg"] = self.colors["BTN_TEXT"]
        self.switch_theme()

    def setup_shortcuts(self):
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus_set())
        self.root.bind('<Control-n>', lambda e: self.task_entry.focus_set())
        self.root.bind('<Control-t>', lambda e: self.switch_theme())
        self.root.bind('<Alt-a>', lambda e: self.add_task())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def add_task(self):
        desc = self.task_entry.get().strip()
        deadline = self.deadline_entry.get_date()
        priority = self.priority_var.get()
        if not desc:
            messagebox.showwarning("Input Error", "Please enter a task description.")
            return
        quote = random.choice(quotes)
        tasks.append(Task(desc, quote, deadline=deadline, priority=priority))
        self.task_entry.delete(0, tk.END)
        self.refresh_tasks()

    def toggle_task(self, idx):
        tasks[idx].completed = not tasks[idx].completed
        self.refresh_tasks()

    def toggle_subtask(self, task_idx, sub_idx):
        task = tasks[task_idx]
        task.subtasks[sub_idx]['completed'] = not task.subtasks[sub_idx]['completed']
        self.refresh_tasks()

    def delete_subtask(self, task_idx, sub_idx):
        del tasks[task_idx].subtasks[sub_idx]
        self.refresh_tasks()

    def edit_task(self, idx):
        task = tasks[idx]
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Task")
        edit_win.config(bg=self.colors["BG"])
        tk.Label(edit_win, text="Edit description:", bg=self.colors["BG"], font=self.get_font('TASK')).pack(pady=4)
        desc_entry = tk.Entry(edit_win, font=self.get_font('TASK'), width=32, bg=self.colors["ENTRY"], fg=self.colors["TEXT"])
        desc_entry.insert(0, task.description)
        desc_entry.pack(pady=4)
        tk.Label(edit_win, text="Edit deadline:", bg=self.colors["BG"], font=self.get_font('TASK')).pack(pady=4)
        deadline_entry = DateEntry(edit_win, width=15, background='darkblue', foreground='white', borderwidth=2, font=self.get_font('NOTE'))
        deadline_entry.set_date(task.deadline if task.deadline else date.today())
        deadline_entry.pack(pady=4)
        tk.Label(edit_win, text="Priority:", bg=self.colors["BG"], font=self.get_font('TASK')).pack(pady=4)
        priority_var = tk.StringVar(value=task.priority)
        priority_menu = ttk.Combobox(edit_win, textvariable=priority_var, values=list(PRIORITY_LOOKUP.keys()), width=8, font=self.get_font('NOTE'), state='readonly')
        priority_menu.pack(pady=3)
        tk.Label(edit_win, text="Notes:", bg=self.colors["BG"], font=self.get_font('TASK')).pack(pady=4)
        notes_text = tk.Text(edit_win, width=35, height=4, font=self.get_font('NOTE'), bg=self.colors["ENTRY"], fg=self.colors["TEXT"])
        notes_text.insert('1.0', task.notes)
        notes_text.pack(pady=4)
        subtasks_frame = tk.LabelFrame(edit_win, text="Subtasks", bg=self.colors["BG"], font=self.get_font('NOTE', bold=True))
        subtasks_frame.pack(pady=8, padx=4, fill="both")
        def refresh_subtasks():
            for w in subtasks_frame.winfo_children():
                w.destroy()
            for i, sub in enumerate(task.subtasks):
                var = tk.BooleanVar(value=sub['completed'])
                cb = tk.Checkbutton(
                    subtasks_frame, text=sub['desc'], variable=var, font=self.get_font('NOTE'),
                    bg=self.colors["BG"], fg=self.colors["TEXT"], command=lambda si=i: toggle_and_update(si))
                if sub['completed']:
                    cb.select()
                cb.grid(row=i, column=0, sticky="w")
                del_btn = tk.Button(subtasks_frame, text="Delete", bg="#FF4444", fg="white",
                                    font=self.get_font('NOTE'), command=lambda si=i: delete_subtask(si))
                del_btn.grid(row=i, column=1, padx=5, pady=1)
        def toggle_and_update(si):
            task.subtasks[si]['completed'] = not task.subtasks[si]['completed']
            refresh_subtasks()
        def delete_subtask(si):
            del task.subtasks[si]
            refresh_subtasks()
        refresh_subtasks()
        tk.Label(edit_win, text="Add subtask:", bg=self.colors["BG"], font=self.get_font('NOTE')).pack(pady=(7,0))
        new_sub_entry = tk.Entry(edit_win, font=self.get_font('NOTE'), width=25, bg=self.colors["ENTRY"], fg=self.colors["TEXT"])
        new_sub_entry.pack(pady=(0,3))
        def add_subtask():
            desc = new_sub_entry.get().strip()
            if desc:
                task.subtasks.append({'desc': desc, 'completed': False})
                new_sub_entry.delete(0, tk.END)
                refresh_subtasks()
        add_sub_btn = tk.Button(edit_win, text="Add", font=self.get_font('NOTE'), bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"], command=add_subtask)
        add_sub_btn.pack(pady=(0,5))
        def save_changes():
            new_desc = desc_entry.get().strip()
            new_deadline = deadline_entry.get_date()
            new_notes = notes_text.get("1.0", tk.END).strip()
            new_priority = priority_var.get()
            if not new_desc:
                messagebox.showwarning("Input Error", "Description cannot be empty.")
                return
            task.description = new_desc
            task.deadline = new_deadline
            task.notes = new_notes
            task.priority = new_priority
            edit_win.destroy()
            self.refresh_tasks()
        save_btn = tk.Button(edit_win, text="Save", font=self.get_font('TASK'), bg=self.colors["BTN"], fg=self.colors["BTN_TEXT"], command=save_changes)
        save_btn.pack(pady=6)

    def delete_task(self, idx):
        confirmed = messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?")
        if confirmed:
            self.deleted_task = tasks[idx]
            self.deleted_index = idx
            del tasks[idx]
            self.refresh_tasks()
            self.show_undo()

    def show_undo(self):
        for widget in self.undo_frame.winfo_children():
            widget.destroy()
        undo_label = tk.Label(self.undo_frame, text="Task deleted.", font=self.get_font('TASK'), bg=self.colors["BG"], fg="#FF4444")
        undo_label.pack(side="left")
        undo_btn = tk.Button(
            self.undo_frame, text="Undo", font=self.get_font('NOTE', bold=True), bg="#22BB33", fg="#fff",
            command=self.undelete_task)
        undo_btn.pack(side="left", padx=5)
        self.root.after(6000, self.hide_undo)

    def undelete_task(self):
        if self.deleted_task is not None and self.deleted_index is not None:
            tasks.insert(self.deleted_index, self.deleted_task)
            self.deleted_task = None
            self.deleted_index = None
            self.refresh_tasks()
        self.hide_undo()

    def hide_undo(self):
        for widget in self.undo_frame.winfo_children():
            widget.destroy()
        self.deleted_task = None
        self.deleted_index = None

    def get_filtered_tasks(self):
        filter_status = self.filter_var.get()
        search = self.search_var.get().strip().lower()
        result = []
        for t in tasks:
            match_status = (
                filter_status == "All" or
                (filter_status == "Completed" and t.completed) or
                (filter_status == "Pending" and not t.completed)
            )
            match_search = (
                not search or
                search in t.description.lower() or
                search in t.notes.lower() or
                any(search in sub['desc'].lower() for sub in t.subtasks)
            )
            if match_status and match_search:
                result.append(t)
        return result

    def show_achievements(self, completed, total):
        badge = ""
        if completed >= 20:
            badge = "🏆 Master Doer! 20+ tasks done!"
        elif completed >= 10:
            badge = "🌟 Achiever! 10+ tasks!"
        elif completed >= 5:
            badge = "✨ Go-Getter! 5+ completed!"
        elif completed >= 1:
            badge = "👍 First steps! Keep going!"
        else:
            badge = ""
        self.achievements_var.set(badge)

    def show_pie_chart(self, completed, pending):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        fig, ax = plt.subplots(figsize=(2.4,2), dpi=100)
        values = [completed, pending]
        labels = ["Completed", "Pending"]
        colors = ["#81C784", "#FFF176"]
        if sum(values)>0:
            ax.pie(values, labels=labels, autopct="%1.0f%%",colors=colors,startangle=90)
        ax.axis('equal')
        fig.tight_layout(pad=0)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        chart_widget = canvas.get_tk_widget()
        chart_widget.pack()
        fig.patch.set_alpha(0)

    def refresh_tasks(self):
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        tasklist = self.get_filtered_tasks()
        total = len(tasklist)
        completed = sum(1 for t in tasklist if t.completed)
        percent = int((completed / total) * 100) if total else 0
        self.progress["value"] = percent
        self.progress_label.config(text=f"Displayed: {completed}/{total} completed ({percent}%)")
        self.show_achievements(completed, total)
        pending = total - completed
        self.show_pie_chart(completed, pending)
        for i, task in enumerate(tasklist):
            idx = tasks.index(task)
            color, label = PRIORITY_LOOKUP[task.priority]
            frame = tk.Frame(self.tasks_frame, bg=self.colors["BG"], pady=2)
            frame.pack(fill="x", expand=True)
            canvas = tk.Canvas(frame, width=5, height=26, bg=self.colors["BG"], highlightthickness=0)
            canvas.pack(side="left", padx=0)
            canvas.create_rectangle(0,0,8,28,fill=color,outline=color)
            today = date.today()
            overdue = not task.completed and task.deadline and (task.deadline < today)
            var = tk.BooleanVar(value=task.completed)
            cb = tk.Checkbutton(
                frame,
                text=task.description,
                font=self.get_font('TASK', bold=task.completed),
                bg=self.colors["BG"],
                fg='#FFFF00' if self.theme == "High Contrast" and overdue else ('#aa0000' if overdue else self.colors["TEXT"] if not task.completed else '#999'),
                variable=var,
                command=lambda idx=idx: self.toggle_task(idx),
                activebackground=self.colors["BG"],
                selectcolor=self.colors["BG"]
            )
            if task.completed:
                cb.select()
            cb.pack(side="left")
            pri_label = tk.Label(frame, text=f"[{label}]", font=self.get_font('NOTE', bold=True), bg=self.colors["BG"], fg=color, padx=3)
            pri_label.pack(side="left")
            deadline_text = f" (Due: {task.deadline.strftime('%Y-%m-%d')})" if task.deadline else ""
            deadline_lbl = tk.Label(frame, text=deadline_text, font=self.get_font('NOTE'), fg='#FFFF00' if self.theme=="High Contrast" and overdue else '#cc3333' if overdue else '#888888', bg=self.colors["BG"])
            deadline_lbl.pack(side="left", padx=2)
            quote_lbl = tk.Label(
                frame, text=f"“{task.quote}”",
                font=self.get_font('NOTE', italic=True), fg='#FFFF00' if self.theme=="High Contrast" else '#737373', bg=self.colors["BG"])
            quote_lbl.pack(side="left", padx=6)
            if task.notes.strip():
                notes_preview = task.notes.replace("\n", " ").strip()[:24]
                if len(task.notes) > 24:
                    notes_preview += "…"
                note_lbl = tk.Label(frame, text=f"🗒 {notes_preview}", font=self.get_font('NOTE'), fg='#FFFF00' if self.theme=="High Contrast" else '#555577', bg=self.colors["BG"])
                note_lbl.pack(side="left", padx=7)
            edit_btn = tk.Button(
                frame, text="Edit", bg='#FFA500', fg='white', font=self.get_font('NOTE'),
                command=lambda idx=idx: self.edit_task(idx))
            edit_btn.pack(side="right", padx=1)
            del_btn = tk.Button(
                frame, text="Delete", bg='#FF4444', fg='white', font=self.get_font('NOTE'),
                command=lambda idx=idx: self.delete_task(idx))
            del_btn.pack(side="right", padx=1)
            if task.subtasks:
                for j, sub in enumerate(task.subtasks):
                    sub_frame = tk.Frame(self.tasks_frame, bg=self.colors["BG"])
                    sub_frame.pack(fill="x", padx=30)
                    sub_var = tk.BooleanVar(value=sub['completed'])
                    sub_cb = tk.Checkbutton(
                        sub_frame,
                        text=sub['desc'],
                        font=self.get_font('NOTE', italic=True),
                        bg=self.colors["BG"],
                        fg='#FFFF00' if self.theme=="High Contrast" and sub['completed'] else '#25a625' if sub['completed'] else self.colors["TEXT"],
                        variable=sub_var,
                        command=lambda tidx=idx, sidx=j: self.toggle_subtask(tidx, sidx),
                        activebackground=self.colors["BG"],
                        selectcolor=self.colors["BG"]
                    )
                    if sub['completed']:
                        sub_cb.select()
                    sub_cb.pack(side="left", anchor="w")
                    sub_del_btn = tk.Button(
                        sub_frame, text="Delete", bg='#DD3333', fg='white', font=self.get_font('NOTE'),
                        command=lambda t=idx, s=j: self.delete_subtask(t, s))
                    sub_del_btn.pack(side="left", padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
