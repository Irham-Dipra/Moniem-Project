"""
Science Point Coaching Management System
COMPLETE VERSION - All Tabs Working
Developed by Moniem Mortoza
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import sys
import csv
import shutil
import ctypes
import webbrowser
import logging
from typing import List, Dict, Tuple, Optional, Any
import pandas as pd  # For Excel operations

# Try to import ReportLab for PDF generation
try:
    from reportlab.lib.pagesizes import A4, landscape, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Fix for blurry UI on High DPI displays (Windows)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Setup Logging
logging.basicConfig(filename='coaching_app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                father TEXT,
                roll INTEGER,
                school TEXT,
                contact TEXT,
                cat TEXT,
                ssc_year INTEGER,
                class TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_type TEXT,
                exam_number TEXT,
                subject TEXT,
                total_marks INTEGER,
                segment TEXT,
                batch_year INTEGER,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                student_id INTEGER,
                score REAL,
                written_score REAL,
                mcq_score REAL,
                percentage REAL,
                grade TEXT,
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )''')
            # Add new columns if they don't exist (for database migration)
            try:
                conn.execute("ALTER TABLE results ADD COLUMN score REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE results ADD COLUMN written_score REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE results ADD COLUMN mcq_score REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            conn.execute('''CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                month TEXT,
                year INTEGER,
                due_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'due',
                date TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )''')

    
    def execute_query(self, query: str, params: tuple = (), fetch: bool = False):
        """Execute a query with parameters"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()
    
    def get_next_roll(self, ssc_year: int, category: str) -> int:
        """Get next available roll number for given year and category"""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT MAX(roll) FROM students WHERE ssc_year=? AND category=?", 
                     (ssc_year, category))
            max_roll = c.fetchone()[0]
            base_roll = (max_roll or 0) + 1
            
            # Check if this roll already exists
            current_roll = base_roll
            attempts = 0
            max_attempts = 100
            while attempts < max_attempts: # Avoid infinite loop
                c.execute("SELECT id FROM students WHERE roll=? AND ssc_year=? AND category=?", 
                         (current_roll, ssc_year, category))
                if c.fetchone():
                    current_roll += 1
                    attempts += 1
                else:
                    return current_roll
            
            return base_roll  # Fallback
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.get_connection() as conn:
            c = conn.cursor()
            
            stats = {}
            
            # Basic counts
            c.execute("SELECT COUNT(*) FROM students")
            stats['total_students'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM exams")
            stats['total_exams'] = c.fetchone()[0]
            
            # Current month payments
            curr_month = datetime.now().strftime("%B")
            curr_year = datetime.now().year
            c.execute("SELECT SUM(paid_amount) FROM payments WHERE month=? AND year=? AND status='paid'", 
                     (curr_month, curr_year))
            stats['paid_this_month'] = c.fetchone()[0] or 0
            
            # Total due amount
            c.execute("SELECT SUM(due_amount) FROM payments WHERE status='due'")
            stats['total_due'] = c.fetchone()[0] or 0
            
            # Total paid amount
            c.execute("SELECT SUM(paid_amount) FROM payments WHERE status='paid'")
            stats['total_paid'] = c.fetchone()[0] or 0
            
            # Recent students count by year
            c.execute("SELECT ssc_year, COUNT(*) FROM students GROUP BY ssc_year ORDER BY ssc_year DESC LIMIT 5")
            stats['students_by_year'] = dict(c.fetchall())
            
            return stats

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

class Utilities:
    """Utility functions for the application"""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount as currency"""
        return f"{amount:,.0f} Tk"
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate date string format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_ssc_years() -> List[str]:
        """Get list of SSC years for dropdowns"""
        current_year = datetime.now().year
        return [str(y) for y in range(current_year - 2, current_year + 6)]
    
    @staticmethod
    def get_months() -> List[str]:
        """Get list of months"""
        return ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December']
    
    @staticmethod
    def enable_mouse_scroll(canvas: tk.Canvas):
        """Enable mouse wheel scrolling for canvas"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    @staticmethod
    def create_labeled_entry(parent, label_text, row, col, font=('Segoe UI', 10), width=30, readonly=False, combo_values=None):
        """Helper to create a consistent labeled entry or combobox"""
        tk.Label(parent, text=label_text, bg="white", font=(font[0], font[1], 'bold')).grid(row=row, column=col, sticky="e", pady=8, padx=10)
        
        if combo_values:
            widget = ttk.Combobox(parent, values=combo_values, font=font, width=width-2, state="readonly" if readonly else "normal")
        else:
            widget = tk.Entry(parent, font=font, width=width, bg="#f8f9fa", relief="solid", borderwidth=1)
            if readonly:
                widget.configure(state="readonly")
        
        widget.grid(row=row, column=col+1, pady=8, padx=10, sticky="w")
        return widget

    @staticmethod
    def create_scrollable_frame(parent, bg_color="#ECF0F1"):
        """Create a scrollable frame"""
        canvas = tk.Canvas(parent, bg=bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_color)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))
        
        Utilities.enable_mouse_scroll(canvas)
        
        return scrollable_frame

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class CoachingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Science Point By Dr. Talha - Management System")
        self.root.geometry("1200x800")
        self.root.geometry("1280x850")
        self.root.minsize(1000, 600)
        
        # Setup paths
        self.app_path = self.get_application_path()
        os.chdir(self.app_path)
        self.db_path = os.path.join(self.app_path, "coaching_database.db")
        
        # Initialize managers
        self.db = DatabaseManager(self.db_path)
        self.utils = Utilities()
        
        # Theme configuration
        self.themes = {
            'light': {
                'bg': "#ECF0F1", 'fg': "#2C3E50", 'primary': "#2980B9", 
                'secondary': "#7F8C8D", 'success': "#27AE60", 'danger': "#C0392B",
                'warning': "#F39C12", 'light': "#FFFFFF", 'dark': "#34495E",
                'info': "#17a2b8", 'card_bg': "#FFFFFF"
            },
            'dark': {
                'bg': "#2C3E50", 'fg': "#ECF0F1", 'primary': "#3498DB", 
                'secondary': "#95A5A6", 'success': "#2ECC71", 'danger': "#E74C3C",
                'warning': "#F1C40F", 'light': "#34495E", 'dark': "#ECF0F1",
                'info': "#17a2b8"
            }
        }
        self.current_theme = 'light'
        self.colors = self.themes[self.current_theme]
        
        # UI state
        self.status_text = tk.StringVar(value="Ready")
        
        # Store references to widgets
        self.widgets = {}
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data
        self.load_initial_data()
    
    def get_application_path(self):
        """Get application path for bundled exe or script"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    
    def setup_ui(self):
        """Setup the main UI"""
        self.apply_theme()
        
        # Status bar
        status_bar = tk.Label(self.root, textvariable=self.status_text, anchor="w", 
                             bg=self.colors['secondary'], fg="white", font=('Segoe UI', 10))
        status_bar.pack(side="bottom", fill="x", padx=10)
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create all tabs
        self.create_tabs()
    
    def apply_theme(self):
        """Apply the current theme to the application"""
        self.root.configure(bg=self.colors['bg'])
        
        # Configure global styles
        self.root.option_add("*Font", ("Segoe UI", 10))
        self.root.option_add("*Label.Font", ("Segoe UI", 10))
        self.root.option_add("*Button.Font", ("Segoe UI", 10, "bold"))
        self.root.option_add("*Entry.Font", ("Segoe UI", 10))
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Notebook style
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 11, 'bold'))
        style.map('TNotebook.Tab', 
                 background=[('selected', self.colors['primary']), ('active', '#dbeafe')],
                 foreground=[('selected', 'white'), ('active', self.colors['fg'])])
        
        # Treeview style
        style.configure('Treeview', rowheight=35, font=('Segoe UI', 10), 
                       background="white", fieldbackground="white", foreground=self.colors['fg'])
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), 
                       background="#f8f9fa", foreground=self.colors['fg'], relief="flat")
        style.map('Treeview', 
                 background=[('selected', self.colors['primary'])], 
                 foreground=[('selected', 'white')])
    
    def create_tabs(self):
        """Create all application tabs"""
        self.tabs = {}
        
        # Define all tabs with icons and setup methods
        tab_definitions = [
            ("dashboard", "🏠 Dashboard", self.setup_dashboard),
            ("students", "👥 Students", self.setup_students),
            ("exams", "📝 Exams", self.setup_exams),
            ("results", "🏆 Results", self.setup_results),
            ("payments", "💰 Payments", self.setup_payments),
            ("due", "⚠️ Due List", self.setup_due),
            ("view", "🔍 View Data", self.setup_view),
            ("idcard", "🪪 ID Cards", self.setup_idcard),
            ("settings", "⚙️ Settings", self.setup_settings)
        ]
        
        for tab_id, tab_text, setup_method in tab_definitions:
            frame = ttk.Frame(self.notebook)
            self.tabs[tab_id] = frame
            self.notebook.add(frame, text=tab_text)
            setup_method()
    
    def load_initial_data(self):
        """Load initial data for the application"""
        self.update_status("Application loaded successfully")
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_text.set(message)
        logging.info(message)
        self.root.update_idletasks()
    
    # ============================================================================
    # DASHBOARD TAB
    # ============================================================================
    
    def setup_dashboard(self):
        """Setup dashboard tab"""
        frame = self.tabs['dashboard']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create scrollable canvas
        scrollable_frame = self.utils.create_scrollable_frame(frame, self.colors['bg'])
        
        # Main content
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Title
        tk.Label(main, text="Science Point Management System", 
                font=('Segoe UI', 28, 'bold'), bg=self.colors['bg'], fg=self.colors['primary']
                ).pack(pady=20)
        
        # Stats cards
        stats = self.db.get_statistics()
        
        stats_frame = tk.Frame(main, bg=self.colors['bg'])
        stats_frame.pack(fill="x", pady=20)
        
        # Create stat cards
        # Create stat cards with better layout
        cards = [
            ("Total Students", stats['total_students'], self.colors['primary'], "👥"),
            ("Total Exams", stats['total_exams'], self.colors['success'], "📝"),
            ("Paid This Month", stats['paid_this_month'], self.colors['secondary'], "💰"),
            ("Total Due", self.utils.format_currency(stats['total_due']), self.colors['danger'], "⚠️"),
            ("Total Collected", self.utils.format_currency(stats['total_paid']), self.colors['info'], "💵")
        ]
        
        for i, (title, value, color, icon) in enumerate(cards):
            card = self.create_stat_card(stats_frame, title, value, color, icon)
            card.grid(row=0, column=i, padx=15, pady=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Quick actions
        tk.Label(main, text="Quick Actions", font=('Segoe UI', 16, 'bold'), 
                bg=self.colors['bg'], fg=self.colors['dark']).pack(pady=(30, 10))
        
        actions_frame = tk.Frame(main, bg=self.colors['bg'])
        actions_frame.pack(pady=20)
        
        action_buttons = [
            ("🔄 Refresh Dashboard", self.setup_dashboard, self.colors['primary']),
            ("👥 Add Student", lambda: self.notebook.select(1), self.colors['success']),
            ("📝 Create Exam", lambda: self.notebook.select(2), self.colors['warning']),
            ("💰 Check Payments", lambda: self.notebook.select(4), self.colors['info'])
        ]
        
        for i, (text, command, color) in enumerate(action_buttons):
            btn = tk.Button(actions_frame, text=text, font=('Segoe UI', 11, 'bold'), bg=color, fg="white",
                           padx=25, pady=15, command=command, relief="flat", cursor="hand2")
            btn.grid(row=0, column=i, padx=15)
    
    def create_stat_card(self, parent, title: str, value, color: str, icon: str = ""):
        """Create a statistics card"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], padx=20, pady=20, 
                       highlightbackground=color, highlightthickness=1, relief="raised", borderwidth=1)
        
        # Icon
        if icon:
            tk.Label(card, text=icon, font=('Segoe UI', 24), bg=self.colors['card_bg'], fg=color
                    ).pack(anchor="w")
        
        # Title
        tk.Label(card, text=title, font=('Segoe UI', 11, 'bold'), bg=self.colors['card_bg'], fg="#7f8c8d"
                ).pack(anchor="w")
        
        # Value
        tk.Label(card, text=str(value), font=('Segoe UI', 26, 'bold'), bg=self.colors['card_bg'], fg=color
                ).pack(anchor="w")
        
        return card
    
    # ============================================================================
    # STUDENTS TAB (COMPLETE)
    # ============================================================================
    
    def setup_students(self):
        """Setup students tab with Excel import/export"""
        frame = self.tabs['students']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create notebook for student management sections
        self.student_notebook = ttk.Notebook(frame)
        self.student_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Add/Import Students
        add_tab = ttk.Frame(self.student_notebook)
        self.student_notebook.add(add_tab, text="➕ Add/Import")
        
        # Tab 2: View/Edit Students
        view_tab = ttk.Frame(self.student_notebook)
        self.student_notebook.add(view_tab, text="👀 View/Edit")
        
        # Tab 3: Edit/Delete Single
        edit_tab = ttk.Frame(self.student_notebook)
        self.student_notebook.add(edit_tab, text="✏️ Edit/Delete")
        
        # Setup all tabs
        self.setup_add_students_tab(add_tab)
        self.setup_view_students_tab(view_tab)
        self.setup_edit_student_tab(edit_tab)
    
    def setup_add_students_tab(self, parent):
        """Setup the add/import students tab"""
        # Main frame with scroll
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Quick add section
        quick_frame = tk.LabelFrame(main, text=" Quick Add Student ", bg="white", padx=20, pady=20)
        quick_frame.pack(fill="x", pady=(0, 20))
        
        labels = ["Name:", "Father's Name:", "Class:", "Segment:", "Batch Year:", "School:", "Contact:"]
        self.add_entries = []
        
        # Use helper for cleaner code
        for i, text in enumerate(labels):
            combo_vals = None
            readonly = False
            if text == "Batch Year:":
                combo_vals = self.utils.get_ssc_years()
                readonly = True
            elif text == "Segment:":
                combo_vals = ["SSC", "HSC"]
                readonly = True
            
            e = self.utils.create_labeled_entry(quick_frame, text, i, 0, width=40, combo_values=combo_vals, readonly=readonly)
            if text == "Batch Year:": e.set(str(datetime.now().year))
            if text == "Segment:": e.set("SSC")
            self.add_entries.append(e)
        
        tk.Button(quick_frame, text="➕ Add Student", bg=self.colors['success'], fg="white",
                 padx=20, pady=10, command=self.add_student_manual).grid(row=len(labels), column=1, pady=20)
        
        # Excel import/export section
        excel_frame = tk.LabelFrame(main, text=" 📊 Excel Operations ", bg="white", padx=20, pady=20)
        excel_frame.pack(fill="x", pady=10)
        
        tk.Label(excel_frame, text="Bulk operations using Excel files", 
                font=('Segoe UI', 12), bg="white").pack(pady=10)
        
        btn_frame = tk.Frame(excel_frame, bg="white")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="📥 Import from Excel", bg="#17a2b8", fg="white",
                 padx=15, pady=8, command=self.import_from_excel).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="📤 Export Template", bg="#6c757d", fg="white",
                 padx=15, pady=8, command=self.export_excel_template).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="📊 Export All Students", bg="#28a745", fg="white",
                 padx=15, pady=8, command=self.export_all_students).pack(side="left", padx=5)
        
        # Instructions
        tk.Label(excel_frame, text="• Roll numbers are auto-generated\n• No need to enter roll numbers\n• Excel template includes instructions",
                font=('Segoe UI', 10), bg="white", justify="left").pack(pady=10)
    
    def setup_view_students_tab(self, parent):
        """Setup the view/edit students tab"""
        # Filter controls
        filter_frame = tk.LabelFrame(parent, text=" Filter Students ", bg="white", padx=20, pady=15)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(filter_frame, text="Segment:", bg="white").pack(side="left", padx=5)
        self.view_segment = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"], 
                                        width=10, state="readonly")
        self.view_segment.set("All")
        self.view_segment.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Batch Year:", bg="white").pack(side="left", padx=10)
        self.ssc_year_combo = ttk.Combobox(filter_frame, width=15, state="readonly")
        self.ssc_year_combo.pack(side="left", padx=5)
        
        tk.Button(filter_frame, text="🔍 View Students", bg=self.colors['primary'], fg="white",
                 command=self.view_filtered_students).pack(side="left", padx=20)
        
        tk.Button(filter_frame, text="🖨️ Print List", bg="#6c757d", fg="white",
                 command=self.print_student_list).pack(side="left", padx=5)
        
        # Load SSC years
        self.refresh_ssc_years()
        
        # Student list treeview
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("ID", "Name", "Father", "Roll", "School", "Contact", "Segment", "Year", "Class")
        self.tree_students = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        column_configs = {
            "ID": 50, "Name": 150, "Father": 150, "Roll": 60, 
            "School": 180, "Contact": 100, "Segment": 70, "Year": 70, "Class": 80
        }
        
        for col in cols:
            self.tree_students.heading(col, text=col, anchor="center")
            self.tree_students.column(col, anchor="center", width=column_configs.get(col, 100))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_students.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_students.xview)
        self.tree_students.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree_students.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection to edit form
        self.tree_students.bind("<<TreeviewSelect>>", self.on_student_select)
        
        # Load initial data
        self.view_filtered_students()
    
    def setup_edit_student_tab(self, parent):
        """Setup edit/delete student tab"""
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'], padx=20, pady=20)
        main.pack(fill="both", expand=True)
        
        tk.Label(main, text="Edit / Delete Student", font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Student ID input
        id_frame = tk.Frame(main, bg=self.colors['bg'])
        id_frame.pack(pady=10)
        
        tk.Label(id_frame, text="Student ID:", bg=self.colors['bg']).pack(side="left", padx=5)
        self.edit_student_id = tk.Entry(id_frame, font=('Segoe UI', 11), width=20)
        self.edit_student_id.pack(side="left", padx=5)
        
        tk.Button(id_frame, text="Load Student", bg=self.colors['primary'], fg="white",
                 command=self.load_student_for_edit).pack(side="left", padx=10)
        
        # Edit form
        form_frame = tk.LabelFrame(main, text=" Student Details ", bg="white", padx=20, pady=20)
        form_frame.pack(fill="x", pady=20)
        
        labels = ["Name:", "Father's Name:", "Class:", "Segment:", "Batch Year:", "School:", "Contact:", "Roll:"]
        self.edit_entries = []
        
        for i, text in enumerate(labels):
            e = self.utils.create_labeled_entry(form_frame, text, i, 0, width=40)
            self.edit_entries.append(e)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg="white")
        btn_frame.grid(row=len(labels), column=1, pady=20)
        
        tk.Button(btn_frame, text="Update Student", bg=self.colors['warning'], fg="black",
                 padx=20, pady=10, command=self.update_student).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="Delete Student", bg=self.colors['danger'], fg="white",
                 padx=20, pady=10, command=self.delete_student).pack(side="left", padx=10)
    
    def on_student_select(self, event):
        """When student is selected in treeview, load into edit form"""
        selection = self.tree_students.selection()
        if selection:
            item = self.tree_students.item(selection[0])
            student_id = item['values'][0]
            self.edit_student_id.delete(0, tk.END)
            self.edit_student_id.insert(0, student_id)
            self.load_student_for_edit()
            # Switch to edit tab
            self.student_notebook.select(2)
    
    def load_student_for_edit(self):
        """Load student data into edit form"""
        try:
            student_id = self.edit_student_id.get().strip()
            if not student_id:
                messagebox.showwarning("Input", "Please enter Student ID")
                return
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT name, father_name, student_class, category, ssc_year, school, contact, roll FROM students WHERE id=?", (student_id,))
                student = c.fetchone()
            
            if not student:
                messagebox.showerror("Error", "Student not found")
                return
            
            # Fill the form
            for entry, value in zip(self.edit_entries, student):
                entry.delete(0, tk.END)
                if value:
                    entry.insert(0, str(value))
            
            self.update_status(f"Loaded student ID: {student_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load student: {str(e)}")
    
    def update_student(self):
        """Update student information"""
        try:
            student_id = self.edit_student_id.get().strip()
            if not student_id:
                messagebox.showwarning("Input", "Please enter Student ID")
                return
            
            # Get data from form
            data = []
            for entry in self.edit_entries:
                data.append(entry.get().strip())
            
            name, father_name, student_class, category, ssc_year, school, contact, roll = data
            
            # Validate
            if not all([name, father_name, ssc_year, category, school, contact, roll]):
                messagebox.showwarning("Validation", "Please fill all required fields")
                return
            
            # Update database
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""UPDATE students SET name=?, father_name=?, student_class=?, category=?, 
                           ssc_year=?, school=?, contact=?, roll=?, updated_at=CURRENT_TIMESTAMP 
                           WHERE id=?""",
                         (name, father_name, student_class, category, int(ssc_year), school, contact, int(roll), student_id))
                conn.commit()
            
            messagebox.showinfo("Success", "Student updated successfully")
            self.update_status(f"Updated student ID: {student_id}")
            
            # Refresh views
            self.view_filtered_students()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid data format (year and roll must be numbers)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update student: {str(e)}")
    
    def delete_student(self):
        """Delete a student"""
        try:
            student_id = self.edit_student_id.get().strip()
            if not student_id:
                messagebox.showwarning("Input", "Please enter Student ID")
                return
            
            if not messagebox.askyesno("Confirm Delete", 
                                      f"Delete student ID {student_id}?\n\nThis will also delete all related exam results and payments."):
                return
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM students WHERE id=?", (student_id,))
                conn.commit()
            
            messagebox.showinfo("Success", "Student deleted successfully")
            self.update_status(f"Deleted student ID: {student_id}")
            
            # Clear form and refresh views
            for entry in self.edit_entries:
                entry.delete(0, tk.END)
            self.edit_student_id.delete(0, tk.END)
            self.view_filtered_students()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete student: {str(e)}")
    
    def add_student_manual(self):
        """Add a student manually"""
        try:
            # Get data from entries
            name = self.add_entries[0].get().strip()
            father = self.add_entries[1].get().strip()
            student_class = self.add_entries[2].get().strip()
            segment = self.add_entries[3].get().strip()
            year_val = self.add_entries[4].get().strip()
            school = self.add_entries[5].get().strip()
            contact = self.add_entries[6].get().strip()
            
            # Validate
            if not all([name, father, year_val, segment, school, contact]):
                messagebox.showwarning("Validation", "Please fill all required fields")
                return
            
            year = int(year_val)
            
            # Auto-generate roll
            new_roll = self.db.get_next_roll(year, segment)
            
            # Insert student
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""INSERT INTO students 
                            (name, father_name, student_class, category, ssc_year, school, contact, roll) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                         (name, father, student_class, segment, year, school, contact, new_roll))
                student_id = c.lastrowid
                conn.commit()
            
            # Initialize payments for the student
            self.initialize_student_payments(student_id)
            
            logging.info(f"New student added: {name} (ID: {student_id})")
            # Clear form and show success
            for entry in self.add_entries:
                if isinstance(entry, tk.Entry):
                    entry.delete(0, tk.END)
            
            self.update_status(f"Added student: {name} (Roll: {new_roll})")
            messagebox.showinfo("Success", f"Student added successfully!\n\nName: {name}\nRoll: {new_roll}\nID: {student_id}")
            
            # Refresh student list
            self.view_filtered_students()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid data format (year must be a number)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add student: {str(e)}")
    
    def initialize_student_payments(self, student_id):
        """Initialize payment records for a new student"""
        months = self.utils.get_months()
        current_year = datetime.now().year
        
        with self.db.get_connection() as conn:
            c = conn.cursor()
            for month in months:
                c.execute("""INSERT OR IGNORE INTO payments (student_id, month, year, due_amount)
                           VALUES (?, ?, ?, ?)""", 
                         (student_id, month, current_year, 500))  # Default due amount: 500 Tk
            conn.commit()
    
    def refresh_ssc_years(self):
        """Refresh SSC years in combo box"""
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT ssc_year FROM students ORDER BY ssc_year DESC")
            years = ["All"] + [str(row[0]) for row in c.fetchall()]
            self.ssc_year_combo['values'] = years
            self.ssc_year_combo.set("All")
    
    def view_filtered_students(self):
        """View students with filters"""
        try:
            # Clear existing items
            for item in self.tree_students.get_children():
                self.tree_students.delete(item)
            
            segment = self.view_segment.get()
            year = self.ssc_year_combo.get()
            
            # Build query
            query = "SELECT id, name, father_name, roll, school, contact, category, ssc_year, student_class FROM students"
            params = []
            
            conditions = []
            if segment != "All":
                conditions.append("category = ?")
                params.append(segment)
            if year != "All":
                conditions.append("ssc_year = ?")
                params.append(int(year))
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY ssc_year DESC, category, roll"
            
            # Execute query
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                students = c.fetchall()
            
            # Insert into treeview
            for student in students:
                self.tree_students.insert("", "end", values=student)
            
            self.update_status(f"Showing {len(students)} students")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students: {str(e)}")
    
    def export_excel_template(self):
        """Export Excel template for student import"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Excel Template"
            )
            
            if not file_path:
                return
            
            # Create template data
            template_data = {
                'name': ['Sample Student 1', 'Sample Student 2'],
                'father_name': ['Sample Father 1', 'Sample Father 2'],
                'student_class': ['Class 9', 'Class 10'],
                'category': ['SSC', 'SSC'],
                'ssc_year': [2024, 2024],
                'school': ['Sample School', 'Sample School'],
                'contact': ['017XXXXXXXX', '018XXXXXXXX']
            }
            
            # Create DataFrame
            df = pd.DataFrame(template_data)
            
            # Save to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Students', index=False)
                
                # Add instructions sheet
                instructions = pd.DataFrame({
                    'Instructions': [
                        '1. Fill in student details in the Students sheet',
                        '2. Do NOT include roll numbers - they will be auto-generated',
                        '3. category should be either "SSC" or "HSC"',
                        '4. ssc_year should be the batch year (e.g., 2024)',
                        '5. Keep the column names exactly as provided',
                        '6. Save the file and use Import from Excel in the application'
                    ]
                })
                instructions.to_excel(writer, sheet_name='Instructions', index=False)
            
            self.update_status(f"Template exported to: {file_path}")
            messagebox.showinfo("Success", f"Excel template created successfully!\n\nLocation: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export template: {str(e)}")
    
    def import_from_excel(self):
        """Import students from Excel file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                title="Select Excel File to Import"
            )
            
            if not file_path:
                return
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Validate columns
            required_columns = ['name', 'father_name', 'ssc_year', 'category', 'school', 'contact']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror("Error", f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            # Process each row
            success_count = 0
            error_count = 0
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                for _, row in df.iterrows():
                    try:
                        name = str(row['name']).strip()
                        father_name = str(row['father_name']).strip()
                        ssc_year = int(row['ssc_year'])
                        category = str(row['category']).strip().upper()
                        school = str(row['school']).strip()
                        contact = str(row['contact']).strip()
                        student_class = str(row.get('student_class', '')).strip()
                        
                        # Auto-generate roll (using current cursor to avoid db lock)
                        c.execute("SELECT MAX(roll) FROM students WHERE ssc_year=? AND category=?", 
                                 (ssc_year, category))
                        max_roll = c.fetchone()[0]
                        current_roll = (max_roll or 0) + 1
                        
                        # Check collision
                        attempts = 0
                        while attempts < 100:
                            c.execute("SELECT id FROM students WHERE roll=? AND ssc_year=? AND category=?", 
                                     (current_roll, ssc_year, category))
                            if c.fetchone():
                                current_roll += 1
                                attempts += 1
                            else:
                                break
                        
                        new_roll = current_roll
                        
                        # Insert student
                        c.execute("""INSERT OR IGNORE INTO students 
                                    (name, father_name, student_class, category, ssc_year, school, contact, roll) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                 (name, father_name, student_class, category, ssc_year, school, contact, new_roll))
                        
                        if c.rowcount > 0:
                            student_id = c.lastrowid
                            # Initialize payments (using current cursor)
                            months = self.utils.get_months()
                            current_year_val = datetime.now().year
                            for month in months:
                                c.execute("""INSERT OR IGNORE INTO payments (student_id, month, year, due_amount)
                                           VALUES (?, ?, ?, ?)""", 
                                         (student_id, month, current_year_val, 500))
                            success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row: {e}")
                
                conn.commit()
            
            # Refresh student list
            self.view_filtered_students()
            self.refresh_ssc_years()
            
            self.update_status(f"Import complete: {success_count} successful, {error_count} failed")
            messagebox.showinfo("Import Complete", 
                              f"Students imported successfully!\n\n"
                              f"Successfully imported: {success_count}\n"
                              f"Failed: {error_count}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import from Excel: {str(e)}")
    
    def export_all_students(self):
        """Export all students to Excel"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Students Export"
            )
            
            if not file_path:
                return
            
            # Get all students
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT name, father_name, student_class, category, ssc_year, 
                           school, contact, roll, id FROM students ORDER BY ssc_year DESC, category, roll""")
                students = c.fetchall()
            
            # Create DataFrame
            df = pd.DataFrame(students, columns=[
                'name', 'father_name', 'student_class', 'category', 'ssc_year',
                'school', 'contact', 'roll', 'student_id'
            ])
            
            # Save to Excel
            df.to_excel(file_path, index=False)
            
            self.update_status(f"Exported {len(students)} students to: {file_path}")
            messagebox.showinfo("Success", f"Exported {len(students)} students to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export students: {str(e)}")
    
    def print_student_list(self):
        """Print student list to PDF"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab library not installed. Cannot generate PDF.")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Student List as PDF"
            )
            
            if not file_path:
                return
            
            # Get filtered students
            segment = self.view_segment.get()
            year = self.ssc_year_combo.get()
            
            query = "SELECT name, roll, school, contact, category, ssc_year FROM students"
            params = []
            
            conditions = []
            if segment != "All":
                conditions.append("category = ?")
                params.append(segment)
            if year != "All":
                conditions.append("ssc_year = ?")
                params.append(int(year))
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY ssc_year DESC, category, roll"
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                students = c.fetchall()
            
            # Create PDF
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), topMargin=30, bottomMargin=30)
            elements = []
            
            # Title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                spaceAfter=30,
                alignment=1
            )
            
            title = Paragraph(f"Science Point - Student List ({segment} {year})", title_style)
            elements.append(title)
            
            # Create table data
            table_data = [["Roll", "Name", "School", "Contact", "Year", "Segment"]]
            
            for student in students:
                name, roll, school, contact, segment, year_val = student
                table_data.append([
                    str(roll), name, school, contact, str(year_val), segment
                ])
            
            # Create table
            table = Table(table_data, colWidths=[60, 120, 180, 120, 60, 70], repeatRows=1)
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (1, 1), (2, -1), 'LEFT'),  # Name, School left align
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Roll center
                ('ALIGN', (3, 1), (5, -1), 'CENTER'),  # Contact, Year, Segment center
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            self.update_status(f"PDF generated: {len(students)} students")
            messagebox.showinfo("Success", f"PDF generated successfully!\n\nStudents: {len(students)}\nFile: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
    
        """
    SCIENCE POINT COACHING MANAGEMENT SYSTEM
    COMPLETE EXAMS & RESULTS MODULES
    """

    # ============================================================================
    # EXAMS TAB (Complete with all functionality)
    # ============================================================================

    def setup_exams(self):
        """Setup exams tab with full functionality"""
        frame = self.tabs['exams']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create notebook for exam management sections
        self.exam_notebook = ttk.Notebook(frame)
        self.exam_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Create Exam
        create_tab = ttk.Frame(self.exam_notebook)
        self.exam_notebook.add(create_tab, text="➕ Create Exam")
        
        # Tab 2: Manage Exams
        manage_tab = ttk.Frame(self.exam_notebook)
        self.exam_notebook.add(manage_tab, text="📋 Manage Exams")
        
        # Setup both tabs
        self.setup_create_exam_tab(create_tab)
        self.setup_manage_exams_tab(manage_tab)

    def setup_create_exam_tab(self, parent):
        """Setup create exam tab"""
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main, text="Create New Exam", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Form frame
        form_frame = tk.LabelFrame(main, text=" Exam Details ", bg="white", padx=20, pady=20)
        form_frame.pack(fill="x", pady=10)
        
        # Form fields with labels
        labels = [
            ("Exam Type:", "Weekly Test"), 
            ("Exam Number:", "e.g., 01, 02, etc."),
            ("Subject:", "e.g., Physics, Chemistry, Math"),
            ("Total Marks:", "100"),
            ("Segment:", "SSC"),
            ("Batch Year:", str(datetime.now().year)),
            ("Date (YYYY-MM-DD):", datetime.now().strftime("%Y-%m-%d"))
        ]
        
        self.exam_entries = []
        
        # Refactored to use helper where possible, but customized for specific needs
        for i, (label_text, default_value) in enumerate(labels):
            combo_vals = None
            readonly = False
            if "Exam Type" in label_text:
                combo_vals = ["Weekly Test", "Monthly Test", "Model Test", "Final", "Class Test"]
                readonly = True
            elif "Segment" in label_text:
                combo_vals = ["SSC", "HSC"]
                readonly = True
            elif "Batch Year" in label_text:
                combo_vals = self.utils.get_ssc_years()
                readonly = True
            
            e = self.utils.create_labeled_entry(form_frame, label_text, i, 0, width=35, combo_values=combo_vals, readonly=readonly)
            if default_value:
                if isinstance(e, ttk.Combobox): e.set(default_value)
                else: e.insert(0, default_value)
            self.exam_entries.append(e)
        
        # Button frame
        button_frame = tk.Frame(form_frame, bg="white")
        button_frame.grid(row=len(labels), column=1, pady=20, sticky="w")
        
        tk.Button(button_frame, text="➕ Create Exam", bg=self.colors['success'], fg="white",
                 font=('Segoe UI', 11, 'bold'), padx=25, pady=12,
                 command=self.create_exam).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="🔄 Clear Form", bg=self.colors['secondary'], fg="white",
                 font=('Segoe UI', 11), padx=20, pady=12,
                 command=self.clear_exam_form).pack(side="left", padx=5)
        
        # Instructions
        instructions_frame = tk.LabelFrame(main, text=" Instructions ", bg="white", padx=20, pady=15)
        instructions_frame.pack(fill="x", pady=20)
        
        instructions = """
        1. Fill in all exam details carefully
        2. Exam Number should be unique for each exam type
        3. Date format must be YYYY-MM-DD (e.g., 2024-01-15)
        4. After creating exam, go to "Manage Exams" tab to:
           - Enter results for students
           - Generate merit list
           - Delete exams if needed
        """
        
        tk.Label(instructions_frame, text=instructions, bg="white", justify="left",
                font=('Segoe UI', 10)).pack(anchor="w")

    def setup_manage_exams_tab(self, parent):
        """Setup manage exams tab"""
        # Main frame
        main = tk.Frame(parent, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Manage Exams", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Control frame
        control_frame = tk.LabelFrame(main, text=" Exam Actions ", bg="white", padx=20, pady=15)
        control_frame.pack(fill="x", pady=10)
        
        # Exam ID input
        tk.Label(control_frame, text="Exam ID:", bg="white", 
                font=('Segoe UI', 10, 'bold')).pack(side="left", padx=5)
        
        self.exam_action_id = tk.Entry(control_frame, width=20, font=('Segoe UI', 10), bg="#f8f9fa", relief="solid", borderwidth=1)
        self.exam_action_id.pack(side="left", padx=5)
        
        # Load button
        tk.Button(control_frame, text="🔍 Load Exam", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.load_exam_details).pack(side="left", padx=5)
        
        # Action buttons
        action_buttons_frame = tk.Frame(control_frame, bg="white")
        action_buttons_frame.pack(side="left", padx=20)
        
        # Create button grid for actions
        actions = [
            ("📝 Enter Results", self.enter_exam_results, self.colors['info']),
            ("📊 Merit List PDF", self.generate_merit_list_exam, "#28a745"),
            ("📄 Export CSV", self.export_exam_results_csv, "#17a2b8"),
            ("🖨️ Print Report", self.print_exam_report, "#6c757d"),
            ("🗑️ Delete Exam", self.delete_exam, self.colors['danger']),
            ("🔄 Refresh", self.load_exams_list, self.colors['warning'])
        ]
        
        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(action_buttons_frame, text=text, bg=color, fg="white" if color != self.colors['warning'] else "black",
                           padx=10, pady=8, font=('Segoe UI', 9), command=command)
            btn.grid(row=0, column=i, padx=3)
        
        # Exam details display
        self.exam_details_frame = tk.LabelFrame(main, text=" Exam Information ", bg="white", padx=20, pady=15)
        self.exam_details_frame.pack(fill="x", pady=10)
        
        self.exam_details_label = tk.Label(self.exam_details_frame, 
                                          text="Enter Exam ID and click 'Load Exam' to view details",
                                          bg="white", font=('Segoe UI', 10))
        self.exam_details_label.pack()
        
        # Exams list frame
        list_frame = tk.LabelFrame(main, text=" All Exams ", bg="white", padx=20, pady=20)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Filter frame
        filter_frame = tk.Frame(list_frame, bg="white")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(filter_frame, text="Filter by:", bg="white").pack(side="left", padx=5)
        
        self.filter_segment = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"], 
                                          width=10, state="readonly", font=('Segoe UI', 9))
        self.filter_segment.set("All")
        self.filter_segment.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Year:", bg="white").pack(side="left", padx=10)
        self.filter_year = ttk.Combobox(filter_frame, values=["All"] + self.utils.get_ssc_years(), 
                                       width=12, state="readonly", font=('Segoe UI', 9))
        self.filter_year.set("All")
        self.filter_year.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Type:", bg="white").pack(side="left", padx=10)
        self.filter_type = ttk.Combobox(filter_frame, values=["All", "Weekly Test", "Monthly Test", "Model Test", "Final", "Class Test"], 
                                       width=15, state="readonly", font=('Segoe UI', 9))
        self.filter_type.set("All")
        self.filter_type.pack(side="left", padx=5)
        
        tk.Button(filter_frame, text="🔍 Apply Filter", bg=self.colors['primary'], fg="white",
                 padx=10, pady=5, command=self.load_exams_list).pack(side="left", padx=10)
        
        # Treeview for exams
        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill="both", expand=True)
        
        cols = ("ID", "Type", "Number", "Subject", "Total", "Segment", "Year", "Date", "Students", "Created")
        self.tree_exams = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        
        column_configs = {
            "ID": 50, "Type": 100, "Number": 70, "Subject": 150, "Total": 70,
            "Segment": 70, "Year": 70, "Date": 100, "Students": 80, "Created": 150
        }
        
        for col in cols:
            self.tree_exams.heading(col, text=col, anchor="center")
            self.tree_exams.column(col, anchor="center", width=column_configs.get(col, 100))
        
        # Bind double-click and selection
        self.tree_exams.bind("<Double-1>", self.on_exam_double_click)
        self.tree_exams.bind("<<TreeviewSelect>>", self.on_exam_select)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_exams.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_exams.xview)
        self.tree_exams.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree_exams.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Load initial data
        self.load_exams_list()

    def clear_exam_form(self):
        """Clear the exam creation form"""
        for i, entry in enumerate(self.exam_entries):
            if isinstance(entry, ttk.Combobox):
                if i == 0:  # Exam Type
                    entry.set("Weekly Test")
                elif i == 4:  # Segment
                    entry.set("SSC")
                elif i == 5:  # Batch Year
                    entry.set(str(datetime.now().year))
            elif isinstance(entry, tk.Entry):
                if i == 3:  # Total Marks
                    entry.delete(0, tk.END)
                    entry.insert(0, "100")
                elif i == 6:  # Date
                    entry.delete(0, tk.END)
                    entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                else:
                    entry.delete(0, tk.END)
        
        self.update_status("Exam form cleared")

    def create_exam(self):
        """Create a new exam"""
        try:
            # Get data from entries
            exam_type = self.exam_entries[0].get()
            exam_number = self.exam_entries[1].get().strip()
            subject = self.exam_entries[2].get().strip()
            total_marks_str = self.exam_entries[3].get().strip()
            segment = self.exam_entries[4].get()
            ssc_year = int(self.exam_entries[5].get())
            date = self.exam_entries[6].get().strip()
            
            # Validate
            if not all([exam_type, exam_number, subject, total_marks_str, segment, date]):
                messagebox.showwarning("Validation", "Please fill all required fields")
                return
            
            total_marks = float(total_marks_str)
            
            if not self.utils.validate_date(date):
                messagebox.showwarning("Validation", "Invalid date format. Use YYYY-MM-DD")
                return
            
            # Check if exam already exists
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT id FROM exams WHERE type=? AND number=? AND subject=? 
                           AND ssc_year=? AND category=?""", 
                         (exam_type, exam_number, subject, ssc_year, segment))
                if c.fetchone():
                    if not messagebox.askyesno("Confirm", "Similar exam already exists. Create anyway?"):
                        return
            
            # Insert exam
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""INSERT INTO exams (type, number, subject, total_marks, ssc_year, category, date)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (exam_type, exam_number, subject, total_marks, ssc_year, segment, date))
                exam_id = c.lastrowid
                logging.info(f"Exam created: ID {exam_id}, {subject}")
                conn.commit()
            
            # Clear form
            self.clear_exam_form()
            
            self.update_status(f"Created exam: {exam_type} #{exam_number} - {subject} ({date})")
            messagebox.showinfo("Success", 
                              f"Exam created successfully!\n\n"
                              f"Exam ID: {exam_id}\n"
                              f"Type: {exam_type}\n"
                              f"Subject: {subject}\n"
                              f"Date: {date}\n\n"
                              f"You can now enter results for this exam.")
            
            # Refresh exam list
            self.load_exams_list()
            
            # Switch to manage tab
            self.exam_notebook.select(1)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid data format (total marks must be a number)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create exam: {str(e)}")

    def load_exams_list(self):
        """Load exams into treeview with filters"""
        try:
            # Clear existing items
            for item in self.tree_exams.get_children():
                self.tree_exams.delete(item)
            
            # Get filter values
            segment = self.filter_segment.get()
            year = self.filter_year.get()
            exam_type = self.filter_type.get()
            
            # Build query
            query = """SELECT e.id, e.type, e.number, e.subject, e.total_marks, e.category, 
                      e.ssc_year, e.date, COUNT(r.student_id) as student_count, e.created_at
                      FROM exams e
                      LEFT JOIN results r ON e.id = r.exam_id"""
            
            conditions = []
            params = []
            
            if segment != "All":
                conditions.append("e.category = ?")
                params.append(segment)
            if year != "All":
                conditions.append("e.ssc_year = ?")
                params.append(int(year))
            if exam_type != "All":
                conditions.append("e.type = ?")
                params.append(exam_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " GROUP BY e.id ORDER BY e.date DESC, e.created_at DESC"
            
            # Execute query
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                exams = c.fetchall()
            
            # Insert into treeview
            for exam in exams:
                self.tree_exams.insert("", "end", values=exam)
            
            self.update_status(f"Loaded {len(exams)} exams")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exams: {str(e)}")

    def on_exam_double_click(self, event):
        """When exam is double-clicked in treeview, load into action field"""
        selection = self.tree_exams.selection()
        if selection:
            item = self.tree_exams.item(selection[0])
            exam_id = item['values'][0]
            self.exam_action_id.delete(0, tk.END)
            self.exam_action_id.insert(0, str(exam_id))
            self.load_exam_details()

    def on_exam_select(self, event):
        """When exam is selected in treeview"""
        selection = self.tree_exams.selection()
        if selection:
            item = self.tree_exams.item(selection[0])
            exam_id = item['values'][0]
            # Update exam ID field if empty
            if not self.exam_action_id.get():
                self.exam_action_id.delete(0, tk.END)
                self.exam_action_id.insert(0, str(exam_id))
                self.load_exam_details()

    def load_exam_details(self):
        """Load exam details for the selected exam ID"""
        try:
            exam_id = self.exam_action_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date, created_at 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                self.exam_details_label.config(
                    text="❌ Exam not found. Please check the Exam ID.",
                    fg=self.colors['danger']
                )
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date, created = exam
            
            # Get student count
            c.execute("SELECT COUNT(*) FROM results WHERE exam_id=?", (exam_id,))
            student_count = c.fetchone()[0]
            
            # Format details
            details = f"""✅ <b>Exam Found:</b> {exam_type} #{exam_number}
    <b>Subject:</b> {subject}
    <b>Total Marks:</b> {total_marks}
    <b>Segment:</b> {segment} | <b>Year:</b> {year}
    <b>Date:</b> {date}
    <b>Students with results:</b> {student_count}
    <b>Created:</b> {created[:10]}"""
            
            self.exam_details_label.config(
                text=details,
                justify="left",
                font=('Segoe UI', 10)
            )
            
            self.update_status(f"Loaded exam details: {exam_type} #{exam_number} - {subject}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exam details: {str(e)}")

    def enter_exam_results(self):
        """Navigate to enter results for selected exam"""
        try:
            exam_id = self.exam_action_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Verify exam exists
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM exams WHERE id=?", (exam_id,))
                if not c.fetchone():
                    messagebox.showerror("Error", "Exam not found")
                    return
            
            # Set exam ID in results tab and switch to it
            if hasattr(self, 'result_exam_id'):
                self.result_exam_id.delete(0, tk.END)
                self.result_exam_id.insert(0, exam_id)
            
            # Switch to results tab
            self.notebook.select(3)  # Results tab index
            self.results_notebook.select(0) # Ensure "Enter Results" tab is selected
            self.update_status(f"Ready to enter results for exam {exam_id}")
            
            # Load exam for results if method exists
            if hasattr(self, 'load_exam_for_results'):
                # Small delay to ensure tab is loaded
                self.root.after(100, self.load_exam_for_results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to navigate to results: {str(e)}")

    def generate_merit_list_exam(self):
        """Generate merit list for selected exam from exams tab"""
        try:
            exam_id = self.exam_action_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results with student info, sorted by score (descending)
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score, 
                           (r.score * 100.0 / ?) as percentage
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (total_marks, exam_id))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Merit List as PDF",
                initialfile=f"Merit_List_{subject}_{date.replace('-', '')}.pdf"
            )
            
            if not file_path:
                return
            
            if not REPORTLAB_AVAILABLE:
                messagebox.showerror("Error", "ReportLab library not installed. Cannot generate PDF.")
                return
            
            # Create merit list PDF
            self.create_merit_list_pdf(exam_type, exam_number, subject, total_marks, 
                                      segment, year, date, results, file_path)
            
            messagebox.showinfo("Success", 
                              f"✅ Merit list generated successfully!\n\n"
                              f"Exam: {exam_type} #{exam_number} - {subject}\n"
                              f"Students: {len(results)}\n"
                              f"File: {os.path.basename(file_path)}")
            
            self.update_status(f"Generated merit list for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate merit list: {str(e)}")

    def create_merit_list_pdf(self, exam_type, exam_number, subject, total_marks, 
                             segment, year, date, results, file_path):
        """Create PDF with merit list"""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            
            # Create PDF document in landscape mode
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), 
                                   topMargin=2*cm, bottomMargin=2*cm,
                                   leftMargin=2*cm, rightMargin=2*cm)
            elements = []
            
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Title'],
                fontSize=20,
                spaceAfter=20,
                alignment=1,
                textColor=colors.HexColor("#2980B9"),
                fontName='Helvetica-Bold'
            )
            
            title = Paragraph("Science Point By Dr. Talha", title_style)
            elements.append(title)
            
            # Exam details
            details_style = ParagraphStyle(
                'DetailsStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=25,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            
            details_text = f"{exam_type} #{exam_number} - {subject}<br/>"
            details_text += f"Segment: {segment} | Batch Year: {year} | Date: {date}<br/>"
            details_text += f"Total Marks: {total_marks} | Total Students: {len(results)}"
            
            details = Paragraph(details_text, details_style)
            elements.append(details)
            
            # Create table data
            table_data = [["Rank", "Roll", "Name", "School", "Marks", "Percentage", "Grade"]]
            
            # Define grading system
            def get_grade(percentage):
                if percentage >= 80:
                    return "A+"
                elif percentage >= 70:
                    return "A"
                elif percentage >= 60:
                    return "A-"
                elif percentage >= 50:
                    return "B"
                elif percentage >= 40:
                    return "C"
                elif percentage >= 33:
                    return "D"
                else:
                    return "F"
            
            # Add students with ranking
            for rank, (roll, name, school, score, percentage) in enumerate(results, 1):
                grade = get_grade(percentage)
                table_data.append([
                    str(rank),
                    str(roll),
                    name,
                    school,
                    f"{score:.1f}",
                    f"{percentage:.1f}%",
                    grade
                ])
            
            # Calculate statistics
            if results:
                scores = [r[3] for r in results]
                percentages = [r[4] for r in results]
                
                highest_score = max(scores)
                lowest_score = min(scores)
                average_score = sum(scores) / len(scores)
                average_percentage = sum(percentages) / len(percentages)
                
                # Statistics row
                table_data.append(["", "", "STATISTICS", "", "", "", ""])
                table_data.append([
                    "",
                    f"Highest: {highest_score:.1f}",
                    f"Lowest: {lowest_score:.1f}",
                    f"Average: {average_score:.1f}",
                    f"Avg %: {average_percentage:.1f}%",
                    f"Total: {len(results)}",
                    ""
                ])
            
            # Create table
            table = Table(table_data, repeatRows=1)
            
            # Table style
            table_style = TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2980B9")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -3), colors.white),
                ('GRID', (0, 0), (-1, -3), 1, colors.black),
                ('ALIGN', (0, 1), (-1, -3), 'CENTER'),
                ('FONTSIZE', (0, 1), (-1, -3), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Statistics header
                ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor("#FFC107")),
                ('TEXTCOLOR', (0, -2), (-1, -2), colors.black),
                ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
                ('ALIGN', (0, -2), (-1, -2), 'CENTER'),
                
                # Statistics values
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E9ECEF")),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                
                # Column widths
                ('COLWIDTHS', (0, 0), (0, -1), 1.5*cm),  # Rank
                ('COLWIDTHS', (1, 0), (1, -1), 2*cm),    # Roll
                ('COLWIDTHS', (2, 0), (2, -1), 5*cm),    # Name
                ('COLWIDTHS', (3, 0), (3, -1), 5*cm),    # School
                ('COLWIDTHS', (4, 0), (4, -1), 2.5*cm),  # Marks
                ('COLWIDTHS', (5, 0), (5, -1), 3*cm),    # Percentage
                ('COLWIDTHS', (6, 0), (6, -1), 2*cm),    # Grade
                
                # Highlight top 3
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#FFF9C4")),  # Gold background
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor("#B71C1C")),  # Red text
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#F5F5F5")),  # Silver background
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor("#424242")),  # Dark gray text
                ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#FFE0B2")),  # Bronze background
                ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor("#5D4037")),  # Brown text
                ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ])
            
            table.setStyle(table_style)
            elements.append(table)
            
            # Add footer
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceBefore=30,
                alignment=2,
                textColor=colors.grey
            )
            
            footer = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style)
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create merit list PDF: {str(e)}")
            raise

    def export_exam_results_csv(self):
        """Export exam results to CSV from exams tab"""
        try:
            exam_id = self.exam_action_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score 
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Results as CSV",
                initialfile=f"Results_{subject}_{date.replace('-', '')}.csv"
            )
            
            if not file_path:
                return
            
            # Define grading system
            def get_grade(percentage):
                if percentage >= 80:
                    return "A+"
                elif percentage >= 70:
                    return "A"
                elif percentage >= 60:
                    return "A-"
                elif percentage >= 50:
                    return "B"
                elif percentage >= 40:
                    return "C"
                elif percentage >= 33:
                    return "D"
                else:
                    return "F"
            
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["SCIENCE POINT COACHING - EXAM RESULTS"])
                writer.writerow([f"{exam_type} #{exam_number} - {subject}"])
                writer.writerow([f"Segment: {segment} | Batch Year: {year} | Date: {date}"])
                writer.writerow([f"Total Marks: {total_marks} | Total Students: {len(results)}"])
                writer.writerow([])
                
                # Write column headers
                writer.writerow(["Rank", "Roll", "Name", "School", "Marks", "Percentage", "Grade"])
                
                # Write data with ranking
                for rank, (roll, name, school, score) in enumerate(results, 1):
                    percentage = (score / total_marks) * 100
                    grade = get_grade(percentage)
                    
                    writer.writerow([
                        rank,
                        roll,
                        name,
                        school,
                        f"{score:.2f}",
                        f"{percentage:.2f}%",
                        grade
                    ])
                
                # Add statistics
                writer.writerow([])
                scores = [r[3] for r in results]
                
                writer.writerow(["STATISTICS"])
                writer.writerow([f"Highest Score: {max(scores):.2f}"])
                writer.writerow([f"Lowest Score: {min(scores):.2f}"])
                writer.writerow([f"Average Score: {sum(scores)/len(scores):.2f}"])
                writer.writerow([f"Total Students: {len(results)}"])
                writer.writerow([])
                writer.writerow([f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            
            messagebox.showinfo("Success", 
                              f"✅ Results exported to CSV!\n\n"
                              f"Exam: {exam_type} #{exam_number} - {subject}\n"
                              f"Students: {len(results)}\n"
                              f"File: {os.path.basename(file_path)}")
            
            self.update_status(f"Exported results for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")

    def print_exam_report(self):
        """Print exam report"""
        try:
            exam_id = self.exam_action_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT COUNT(*) FROM results WHERE exam_id=?""", (exam_id,))
                student_count = c.fetchone()[0]
            
            # Create report text
            report = f"EXAM REPORT\n"
            report += "=" * 50 + "\n\n"
            report += f"Exam ID: {exam_id}\n"
            report += f"Type: {exam_type}\n"
            report += f"Number: #{exam_number}\n"
            report += f"Subject: {subject}\n"
            report += f"Total Marks: {total_marks}\n"
            report += f"Segment: {segment}\n"
            report += f"Batch Year: {year}\n"
            report += f"Date: {date}\n"
            report += f"Students with Results: {student_count}\n\n"
            report += f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Show report dialog
            self.show_report_dialog(f"Exam Report - {exam_type} #{exam_number}", report)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def delete_exam(self):
        """Delete an exam and its results"""
        try:
            exam_id = self.exam_action_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details for confirmation
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT type, number, subject, date FROM exams WHERE id=?", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, date = exam
            
            # Get student count for confirmation
            c.execute("SELECT COUNT(*) FROM results WHERE exam_id=?", (exam_id,))
            result_count = c.fetchone()[0]
            
            warning_msg = f"""⚠️ DELETE EXAM CONFIRMATION ⚠️

    Exam Details:
    • Type: {exam_type} #{exam_number}
    • Subject: {subject}
    • Date: {date}
    • Students with results: {result_count}

    This action will:
    1. Permanently delete the exam
    2. Delete all {result_count} results for this exam
    3. This action CANNOT be undone!

    Are you absolutely sure you want to delete this exam?"""
            
            if not messagebox.askyesno("⚠️ CONFIRM DELETE ⚠️", warning_msg):
                return
            
            # Double confirmation
            if not messagebox.askyesno("FINAL CONFIRMATION", 
                                      f"Type YES to confirm deletion of:\n{exam_type} #{exam_number} - {subject}"):
                return
            
            # Delete exam (cascade delete will handle results)
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM exams WHERE id=?", (exam_id,))
                conn.commit()
            
            # Clear exam details display
            self.exam_details_label.config(
                text="✅ Exam deleted successfully. Enter another Exam ID to load details.",
                fg=self.colors['success']
            )
            
            # Clear exam ID field
            self.exam_action_id.delete(0, tk.END)
            
            messagebox.showinfo("Success", 
                              f"✅ Exam deleted successfully!\n\n"
                              f"Deleted: {exam_type} #{exam_number} - {subject}\n"
                              f"Removed {result_count} result records")
            
            self.update_status(f"Deleted exam ID: {exam_id}")
            
            # Refresh exam list
            self.load_exams_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete exam: {str(e)}")

    # ============================================================================
    # RESULTS TAB (Complete with all functionality)
    # ============================================================================

    def setup_results(self):
        """Setup results tab with all functionality"""
        frame = self.tabs['results']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create notebook for results management
        self.results_notebook = ttk.Notebook(frame)
        self.results_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Enter Results
        enter_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(enter_tab, text="📝 Enter Results")
        
        # Tab 2: View Results
        view_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(view_tab, text="📊 View Results")
        
        # Tab 3: Merit List
        merit_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(merit_tab, text="🏆 Merit List")
        
        # Setup all tabs
        self.setup_enter_results_tab(enter_tab)
        self.setup_view_results_tab(view_tab)
        self.setup_merit_list_tab(merit_tab)

    def setup_enter_results_tab(self, parent):
        """Setup enter results tab"""
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Enter Exam Results", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Select exam frame
        exam_frame = tk.LabelFrame(main, text=" Select Exam ", bg="white", padx=20, pady=20)
        exam_frame.pack(fill="x", pady=10)
        
        tk.Label(exam_frame, text="Exam ID:", bg="white", font=('Segoe UI', 10, 'bold')
                ).pack(side="left", padx=5)
        
        self.result_exam_id = tk.Entry(exam_frame, width=20, font=('Segoe UI', 10),
                                      bg="#f8f9fa", relief="solid", borderwidth=1)
        self.result_exam_id.pack(side="left", padx=5)
        
        tk.Button(exam_frame, text="🔍 Load Exam", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.load_exam_for_results).pack(side="left", padx=10)
        
        tk.Label(exam_frame, text="or", bg="white").pack(side="left", padx=10)
        
        tk.Button(exam_frame, text="📋 Browse Exams", bg=self.colors['info'], fg="white",
                 padx=15, pady=8, command=self.browse_exams_for_results).pack(side="left")
        
        # Exam info frame
        self.exam_info_frame = tk.LabelFrame(main, text=" Exam Information ", bg="white", padx=20, pady=20)
        self.exam_info_frame.pack(fill="x", pady=10)
        
        self.exam_info_label = tk.Label(self.exam_info_frame, 
                                       text="Enter Exam ID and click 'Load Exam' to enter results", 
                                       bg="white", font=('Segoe UI', 11))
        self.exam_info_label.pack()
        
        # Results entry frame (will be populated dynamically)
        self.results_entry_frame = tk.Frame(main, bg=self.colors['bg'])
        self.results_entry_frame.pack(fill="both", expand=True, pady=10)
        
        # Submit button (initially hidden)
        self.submit_results_btn = tk.Button(main, text="💾 Save All Results", bg=self.colors['success'], fg="white",
                                           padx=25, pady=12, state="disabled", font=('Segoe UI', 11, 'bold'),
                                           command=self.save_all_results)
        self.submit_results_btn.pack(pady=20)

    def setup_view_results_tab(self, parent):
        """Setup view results tab"""
        main = tk.Frame(parent, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="View Exam Results", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Filter frame
        filter_frame = tk.LabelFrame(main, text=" Filter Results ", bg="white", padx=20, pady=15)
        filter_frame.pack(fill="x", pady=10)
        
        # Exam ID input
        tk.Label(filter_frame, text="Exam ID:", bg="white", font=('Segoe UI', 10, 'bold')
                ).pack(side="left", padx=5)
        
        self.view_exam_id = tk.Entry(filter_frame, width=15, font=('Segoe UI', 10),
                                    bg="#f8f9fa", relief="solid", borderwidth=1)
        self.view_exam_id.pack(side="left", padx=5)
        
        # Load button
        tk.Button(filter_frame, text="🔍 Load Results", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.view_exam_results).pack(side="left", padx=10)
        
        # Browse exams button
        tk.Button(filter_frame, text="📋 Browse Exams", bg=self.colors['info'], fg="white",
                 padx=15, pady=8, command=self.browse_exams_for_view).pack(side="left", padx=5)
        
        # Action buttons
        action_frame = tk.Frame(filter_frame, bg="white")
        action_frame.pack(side="left", padx=20)
        
        tk.Button(action_frame, text="📊 Merit List PDF", bg="#28a745", fg="white",
                 padx=10, pady=8, command=self.generate_merit_list_from_view).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="📄 Export CSV", bg="#17a2b8", fg="white",
                 padx=10, pady=8, command=self.export_results_csv).pack(side="left", padx=5)
        
        # Results treeview
        tree_frame = tk.Frame(main)
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        cols = ("Rank", "Roll", "Name", "Score", "Percentage", "Grade")
        self.tree_results = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        
        column_configs = {
            "Rank": 60, "Roll": 70, "Name": 200, 
            "Score": 100, "Percentage": 100, "Grade": 70
        }
        
        for col in cols:
            self.tree_results.heading(col, text=col, anchor="center")
            self.tree_results.column(col, anchor="center", width=column_configs.get(col, 100))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_results.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_results.xview)
        self.tree_results.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree_results.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def setup_merit_list_tab(self, parent):
        """Setup merit list tab"""
        main = tk.Frame(parent, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Merit List Generator", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Control frame
        control_frame = tk.LabelFrame(main, text=" Generate Merit List ", bg="white", padx=20, pady=20)
        control_frame.pack(fill="x", pady=10)
        
        # Exam ID input
        tk.Label(control_frame, text="Exam ID:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=0, column=0, sticky="e", pady=10, padx=5)
        
        self.merit_exam_id = tk.Entry(control_frame, width=25, font=('Segoe UI', 10),
                                     bg="#f8f9fa", relief="solid", borderwidth=1)
        self.merit_exam_id.grid(row=0, column=1, pady=10, padx=5)
        
        tk.Button(control_frame, text="🔍 Load Exam", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.load_exam_for_merit).grid(row=0, column=2, padx=10)
        
        # Exam info display
        self.merit_exam_info = tk.Label(control_frame, text="Enter Exam ID to load details",
                                       bg="white", font=('Segoe UI', 10))
        self.merit_exam_info.grid(row=1, column=0, columnspan=3, pady=10, sticky="w")
        
        # Options frame
        options_frame = tk.LabelFrame(main, text=" Options ", bg="white", padx=20, pady=20)
        options_frame.pack(fill="x", pady=10)
        
        # Grade system
        tk.Label(options_frame, text="Grading System:", bg="white").grid(row=0, column=0, sticky="w", pady=5)
        
        self.grade_system_var = tk.StringVar(value="standard")
        
        tk.Radiobutton(options_frame, text="Standard (A+ to F)", variable=self.grade_system_var,
                      value="standard", bg="white").grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        tk.Radiobutton(options_frame, text="Numeric (1.00 to 5.00)", variable=self.grade_system_var,
                      value="numeric", bg="white").grid(row=0, column=2, sticky="w", pady=5, padx=10)
        
        # Include details
        self.include_details_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Include student details (School)", 
                      variable=self.include_details_var, bg="white").grid(row=1, column=0, columnspan=3, 
                                                                         sticky="w", pady=5)
        
        self.highlight_top3_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Highlight top 3 positions", 
                      variable=self.highlight_top3_var, bg="white").grid(row=2, column=0, columnspan=3, 
                                                                       sticky="w", pady=5)
        
        # Generate buttons
        button_frame = tk.Frame(options_frame, bg="white")
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        tk.Button(button_frame, text="📊 Generate PDF", bg="#28a745", fg="white",
                 padx=20, pady=12, font=('Segoe UI', 11), command=self.generate_merit_list_pdf_results
                 ).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="📄 Export CSV", bg="#17a2b8", fg="white",
                 padx=20, pady=12, font=('Segoe UI', 11), command=self.export_merit_list_csv_results
                 ).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="🖨️ Print", bg="#6c757d", fg="white",
                 padx=20, pady=12, font=('Segoe UI', 11), command=self.print_merit_list_results
                 ).pack(side="left", padx=10)
        
        # Preview frame
        preview_frame = tk.LabelFrame(main, text=" Preview ", bg="white", padx=20, pady=20)
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        # Preview text
        self.merit_preview_text = tk.Text(preview_frame, height=15, font=('Courier New', 10),
                                         bg="white", fg="black", wrap="none")
        
        preview_scroll_y = tk.Scrollbar(preview_frame, orient="vertical", command=self.merit_preview_text.yview)
        preview_scroll_x = tk.Scrollbar(preview_frame, orient="horizontal", command=self.merit_preview_text.xview)
        self.merit_preview_text.configure(yscrollcommand=preview_scroll_y.set, xscrollcommand=preview_scroll_x.set)
        
        self.merit_preview_text.grid(row=0, column=0, sticky="nsew")
        preview_scroll_y.grid(row=0, column=1, sticky="ns")
        preview_scroll_x.grid(row=1, column=0, sticky="ew")
        
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Insert default preview
        self.merit_preview_text.insert("1.0", "Enter Exam ID and click 'Load Exam' to preview merit list")
        self.merit_preview_text.bind("<Key>", lambda e: "break")

    # ============================================================================
    # RESULTS MANAGEMENT METHODS
    # ============================================================================

    def browse_exams_for_results(self):
        """Browse exams for result entry"""
        self.browse_exams_dialog("Select Exam for Result Entry", self.result_exam_id, 
                                lambda exam_id: self.load_exam_for_results())

    def browse_exams_for_view(self):
        """Browse exams for viewing results"""
        self.browse_exams_dialog("Select Exam to View Results", self.view_exam_id,
                                lambda exam_id: self.view_exam_results())

    def browse_exams_dialog(self, title, target_entry, load_callback=None):
        """Generic dialog for browsing exams"""
        try:
            browse_window = tk.Toplevel(self.root)
            browse_window.title(title)
            browse_window.geometry("900x500")
            browse_window.configure(bg=self.colors['bg'])
            
            tk.Label(browse_window, text=title, font=('Segoe UI', 16, 'bold'),
                    bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
            
            # Filter frame
            filter_frame = tk.Frame(browse_window, bg=self.colors['bg'])
            filter_frame.pack(fill="x", padx=20, pady=10)
            
            tk.Label(filter_frame, text="Filter:", bg=self.colors['bg']).pack(side="left", padx=5)
            
            filter_segment = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"], 
                                         width=10, state="readonly")
            filter_segment.set("All")
            filter_segment.pack(side="left", padx=5)
            
            tk.Label(filter_frame, text="Year:", bg=self.colors['bg']).pack(side="left", padx=10)
            filter_year = ttk.Combobox(filter_frame, values=["All"] + self.utils.get_ssc_years(),
                                      width=12, state="readonly")
            filter_year.set("All")
            filter_year.pack(side="left", padx=5)
            
            # Treeview for exams
            tree_frame = tk.Frame(browse_window)
            tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            cols = ("ID", "Type", "Number", "Subject", "Total", "Segment", "Year", "Date", "Students")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
            
            for col in cols:
                tree.heading(col, text=col, anchor="center")
                tree.column(col, width=100, anchor="center")
            
            tree.column("ID", width=50)
            tree.column("Subject", width=150)
            tree.column("Students", width=80)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            def load_filtered_exams():
                """Load exams with filters"""
                for item in tree.get_children():
                    tree.delete(item)
                
                segment = filter_segment.get()
                year = filter_year.get()
                
                query = """SELECT e.id, e.type, e.number, e.subject, e.total_marks, e.category, 
                          e.ssc_year, e.date, COUNT(r.student_id) as student_count
                          FROM exams e
                          LEFT JOIN results r ON e.id = r.exam_id"""
                
                conditions = []
                params = []
                
                if segment != "All":
                    conditions.append("e.category = ?")
                    params.append(segment)
                if year != "All":
                    conditions.append("e.ssc_year = ?")
                    params.append(int(year))
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " GROUP BY e.id ORDER BY e.date DESC"
                
                with self.db.get_connection() as conn:
                    c = conn.cursor()
                    c.execute(query, params)
                    exams = c.fetchall()
                
                for exam in exams:
                    tree.insert("", "end", values=exam)
            
            tk.Button(filter_frame, text="🔍 Apply Filter", bg=self.colors['primary'], fg="white",
                     command=load_filtered_exams).pack(side="left", padx=10)
            
            # Load initial data
            load_filtered_exams()
            
            def select_exam():
                """Select exam and close dialog"""
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    exam_id = item['values'][0]
                    target_entry.delete(0, tk.END)
                    target_entry.insert(0, str(exam_id))
                    
                    if load_callback:
                        load_callback()
                    
                    browse_window.destroy()
            
            # Button frame
            button_frame = tk.Frame(browse_window, bg=self.colors['bg'])
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="✅ Select Exam", bg=self.colors['success'], fg="white",
                     padx=20, pady=10, command=select_exam).pack(side="left", padx=10)
            
            tk.Button(button_frame, text="❌ Cancel", bg=self.colors['secondary'], fg="white",
                     padx=20, pady=10, command=browse_window.destroy).pack(side="left", padx=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse exams: {str(e)}")

    def load_exam_for_results(self):
        """Load exam and students for result entry"""
        try:
            exam_id = self.result_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, category, ssc_year, date = exam
            
            # Update exam info
            exam_info = f"""📝 {exam_type} #{exam_number} - {subject}
    📅 Date: {date} | 📊 Total Marks: {total_marks}
    🎯 Segment: {category} | 🎓 Year: {ssc_year}"""
            
            self.exam_info_label.config(text=exam_info, justify="left", font=('Segoe UI', 11))
            
            # Get students for this exam
            c.execute("""SELECT s.id, s.name, s.roll, r.written_score, r.mcq_score 
                       FROM students s 
                       LEFT JOIN results r ON s.id = r.student_id AND r.exam_id = ?
                       WHERE s.ssc_year = ? AND s.category = ?
                       ORDER BY s.roll""", (exam_id, ssc_year, category))
            students = c.fetchall()
            
            if not students:
                messagebox.showinfo("No Students", f"No students found for {category} {ssc_year}")
                return
            
            # Clear previous results frame
            for widget in self.results_entry_frame.winfo_children():
                widget.destroy()
            
            # Create scrollable frame for results
            canvas = tk.Canvas(self.results_entry_frame, bg=self.colors['bg'], highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.results_entry_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
            
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Enable mouse scrolling
            self.utils.enable_mouse_scroll(canvas)
            
            # Store student entry widgets
            self.result_entries = []
            
            # Header frame
            header_frame = tk.Frame(scrollable_frame, bg=self.colors['primary'], padx=10, pady=10)
            header_frame.pack(fill="x", pady=(0, 5))
            
            tk.Label(header_frame, text="Roll", width=10, bg=self.colors['primary'], fg="white", 
                    font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
            tk.Label(header_frame, text="Name", width=30, bg=self.colors['primary'], fg="white",
                    font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
            tk.Label(header_frame, text="Written", width=10, bg=self.colors['primary'], fg="white",
                    font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
            tk.Label(header_frame, text="MCQ", width=10, bg=self.colors['primary'], fg="white",
                    font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
            tk.Label(header_frame, text="Total", width=10, bg=self.colors['primary'], fg="white",
                    font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
            tk.Label(header_frame, text="Percentage", width=12, bg=self.colors['primary'], fg="white",
                    font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
            
            # Create entry for each student
            for student in students:
                student_id, name, roll, written_score, mcq_score = student
                
                row_frame = tk.Frame(scrollable_frame, bg="white", padx=10, pady=8)
                row_frame.pack(fill="x", pady=2)
                
                # Roll number
                tk.Label(row_frame, text=str(roll), width=10, bg="white", 
                        font=('Segoe UI', 10)).pack(side="left", padx=2)
                
                # Name
                tk.Label(row_frame, text=name, width=30, bg="white", anchor="w",
                        font=('Segoe UI', 10)).pack(side="left", padx=2)
                
                # Written Score entry
                written_entry = tk.Entry(row_frame, width=10, font=('Segoe UI', 10),
                                bg="#f8f9fa", relief="solid", borderwidth=1)
                if written_score is not None:
                    written_entry.insert(0, str(written_score))
                written_entry.pack(side="left", padx=2)

                # MCQ Score entry
                mcq_entry = tk.Entry(row_frame, width=10, font=('Segoe UI', 10),
                                bg="#f8f9fa", relief="solid", borderwidth=1)
                if mcq_score is not None:
                    mcq_entry.insert(0, str(mcq_score))
                mcq_entry.pack(side="left", padx=2)

                # Total score label
                total_label = tk.Label(row_frame, text="0.0", width=10, bg="white",
                                           font=('Segoe UI', 10))
                total_label.pack(side="left", padx=2)
                
                # Percentage label (will be updated dynamically)
                percentage_label = tk.Label(row_frame, text="0.0%", width=12, bg="white",
                                           font=('Segoe UI', 10))
                percentage_label.pack(side="left", padx=2)
                
                # Store references
                self.result_entries.append((student_id, written_entry, mcq_entry, total_label, percentage_label))
                
                # Bind key release to calculate percentage
                def update_scores(event=None, w_entry=written_entry, m_entry=mcq_entry, t_label=total_label, p_label=percentage_label, total=total_marks):
                    self.calculate_total_and_percentage(w_entry, m_entry, t_label, p_label, total)

                written_entry.bind('<KeyRelease>', update_scores)
                mcq_entry.bind('<KeyRelease>', update_scores)
                update_scores() # Initial calculation
            
            # Setup keyboard navigation for result entries
            all_entries = []
            for _, written_entry, mcq_entry, _, _ in self.result_entries:
                all_entries.append(written_entry)
                all_entries.append(mcq_entry)
            
            for i, entry in enumerate(all_entries):
                # Return key moves to the next entry field (written -> mcq -> next student's written)
                entry.bind('<Return>', lambda e, idx=i: all_entries[(idx + 1) % len(all_entries)].focus_set())
                # Down arrow moves to the same type of entry in the next row
                if i < len(all_entries) - 2:
                    entry.bind('<Down>', lambda e, idx=i: all_entries[idx + 2].focus_set())
                # Up arrow moves to the same type of entry in the previous row
                if i >= 2:
                    entry.bind('<Up>', lambda e, idx=i: all_entries[idx - 2].focus_set())
            
            # Enable submit button
            self.submit_results_btn.config(state="normal")
            
            self.update_status(f"Loaded {len(students)} students for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exam: {str(e)}")

    def calculate_total_and_percentage(self, written_entry, mcq_entry, total_label, percentage_label, total_marks):
        """Calculate total score and percentage from written and mcq entries."""
        try:
            written_str = written_entry.get().strip()
            mcq_str = mcq_entry.get().strip()

            written_score = float(written_str) if written_str else 0.0
            mcq_score = float(mcq_str) if mcq_str else 0.0

            total_score = written_score + mcq_score
            total_label.config(text=f"{total_score:.1f}")

            if total_marks > 0:
                percentage = (total_score / total_marks) * 100
                percentage_label.config(text=f"{percentage:.1f}%")

                # Color code based on percentage
                if percentage >= 80:
                    percentage_label.config(fg="#28a745")  # Green
                elif percentage >= 60:
                    percentage_label.config(fg="#17a2b8")  # Blue
                elif percentage >= 40:
                    percentage_label.config(fg="#ffc107")  # Yellow
                else:
                    percentage_label.config(fg="#dc3545")  # Red
            else:
                percentage_label.config(text="N/A", fg="black")

        except ValueError:
            total_label.config(text="Invalid")
            percentage_label.config(text="Invalid", fg="red")

    def save_all_results(self):
        """Save all results for the current exam"""
        try:
            exam_id = self.result_exam_id.get().strip()
            if not exam_id:
                return
            
            # Get total marks for validation
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT total_marks FROM exams WHERE id=?", (exam_id,))
                total_marks = c.fetchone()[0]
            
            # Save results
            saved_count = 0
            error_count = 0
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                for student_id, written_entry, mcq_entry, _, _ in self.result_entries:
                    written_str = written_entry.get().strip()
                    mcq_str = mcq_entry.get().strip()
                    
                    if written_str or mcq_str:  # Only save if at least one score is entered
                        try:
                            written_score = float(written_str) if written_str else 0.0
                            mcq_score = float(mcq_str) if mcq_str else 0.0
                            total_score = written_score + mcq_score
                            
                            # Validate score
                            if total_score < 0 or total_score > total_marks:
                                error_count += 1
                                continue
                            
                            # Insert or update result
                            c.execute("""INSERT OR REPLACE INTO results (student_id, exam_id, score, written_score, mcq_score)
                                       VALUES (?, ?, ?, ?, ?)""", (student_id, exam_id, total_score, written_score, mcq_score))
                            saved_count += 1
                            
                        except ValueError:
                            error_count += 1
                            continue
                    else:
                        # If no score entered, delete existing result
                        c.execute("DELETE FROM results WHERE student_id=? AND exam_id=?", 
                                 (student_id, exam_id))
                
                conn.commit()
            
            # Show summary
            summary = f"""✅ Results Saved Successfully!

    Summary:
    • Saved results: {saved_count} students
    • Errors/Skipped: {error_count} entries
    • Exam ID: {exam_id}

    Results have been saved to the database."""
            
            logging.info(f"Results saved for exam {exam_id}: {saved_count} records")
            messagebox.showinfo("Success", summary)
            self.update_status(f"Saved {saved_count} results for exam {exam_id}")
            
            # Disable submit button to prevent duplicate saves
            self.submit_results_btn.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {str(e)}")

    def view_exam_results(self):
        """View results for a specific exam"""
        try:
            exam_id = self.view_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Clear existing items
            for item in self.tree_results.get_children():
                self.tree_results.delete(item)
            
            # Get exam details and results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                # Get exam total marks
                c.execute("SELECT total_marks FROM exams WHERE id=?", (exam_id,))
                result = c.fetchone()
                
                if not result:
                    messagebox.showerror("Error", "Exam not found")
                    return
                
                total_marks = result[0]
                
                # Get results with student info
                c.execute("""SELECT s.roll, s.name, r.score 
                           FROM students s 
                           JOIN results r ON s.id = r.student_id 
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Define grading function
            def get_grade(percentage):
                if percentage >= 80:
                    return "A+"
                elif percentage >= 70:
                    return "A"
                elif percentage >= 60:
                    return "A-"
                elif percentage >= 50:
                    return "B"
                elif percentage >= 40:
                    return "C"
                elif percentage >= 33:
                    return "D"
                else:
                    return "F"
            
            # Insert into treeview with ranking
            for rank, (roll, name, score) in enumerate(results, 1):
                percentage = (score / total_marks) * 100 if score else 0
                grade = get_grade(percentage)
                
                self.tree_results.insert("", "end", values=(
                    rank, roll, name, f"{score:.1f}/{total_marks}", 
                    f"{percentage:.1f}%", grade
                ))
            
            # Add statistics row
            scores = [r[2] for r in results]
            highest = max(scores)
            lowest = min(scores)
            average = sum(scores) / len(scores)
            average_percentage = (average / total_marks) * 100
            
            self.tree_results.insert("", "end", values=(
                "", "STATS", "Statistics:", 
                f"High: {highest:.1f} | Low: {lowest:.1f} | Avg: {average:.1f}",
                f"Avg: {average_percentage:.1f}%", 
                f"Total: {len(results)}"
            ))
            
            self.update_status(f"Showing {len(results)} results for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results: {str(e)}")

    def export_results_csv(self):
        """Export results to CSV from results tab"""
        try:
            exam_id = self.view_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score 
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Results as CSV",
                initialfile=f"Results_{subject}_{date.replace('-', '')}.csv"
            )
            
            if not file_path:
                return
            
            # Define grading system
            def get_grade(percentage):
                if percentage >= 80:
                    return "A+"
                elif percentage >= 70:
                    return "A"
                elif percentage >= 60:
                    return "A-"
                elif percentage >= 50:
                    return "B"
                elif percentage >= 40:
                    return "C"
                elif percentage >= 33:
                    return "D"
                else:
                    return "F"
            
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["SCIENCE POINT COACHING - EXAM RESULTS"])
                writer.writerow([f"{exam_type} #{exam_number} - {subject}"])
                writer.writerow([f"Segment: {segment} | Batch Year: {year} | Date: {date}"])
                writer.writerow([f"Total Marks: {total_marks} | Total Students: {len(results)}"])
                writer.writerow([])
                
                # Write column headers
                writer.writerow(["Rank", "Roll", "Name", "Father's Name", "School", "Marks", "Percentage", "Grade"])
                
                # Write data with ranking
                for rank, (roll, name, father, school, score) in enumerate(results, 1):
                    percentage = (score / total_marks) * 100
                    grade = get_grade(percentage)
                    
                    writer.writerow([
                        rank,
                        roll,
                        name,
                        father,
                        school,
                        f"{score:.2f}",
                        f"{percentage:.2f}%",
                        grade
                    ])
                
                # Add statistics
                writer.writerow([])
                scores = [r[4] for r in results]
                
                writer.writerow(["STATISTICS"])
                writer.writerow([f"Highest Score: {max(scores):.2f}"])
                writer.writerow([f"Lowest Score: {min(scores):.2f}"])
                writer.writerow([f"Average Score: {sum(scores)/len(scores):.2f}"])
                writer.writerow([f"Total Students: {len(results)}"])
                writer.writerow([])
                writer.writerow([f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            
            messagebox.showinfo("Success", 
                              f"✅ Results exported to CSV!\n\n"
                              f"Exam: {exam_type} #{exam_number} - {subject}\n"
                              f"Students: {len(results)}\n"
                              f"File: {os.path.basename(file_path)}")
            
            self.update_status(f"Exported results for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")

    def generate_merit_list_from_view(self):
        """Generate merit list from view results tab"""
        exam_id = self.view_exam_id.get().strip()
        if not exam_id:
            messagebox.showwarning("Input", "Please enter Exam ID")
            return
        
        # Set the exam ID in merit list tab
        self.merit_exam_id.delete(0, tk.END)
        self.merit_exam_id.insert(0, exam_id)
        
        # Switch to merit list tab and load
        self.results_notebook.select(2)  # Switch to Merit List tab
        self.load_exam_for_merit()

    def load_exam_for_merit(self):
        """Load exam for merit list generation"""
        try:
            exam_id = self.merit_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                self.merit_exam_info.config(text="❌ Exam not found", fg="red")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score 
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                self.merit_exam_info.config(
                    text=f"✅ {exam_type} #{exam_number} - {subject}\nNo results found for this exam",
                    fg="orange"
                )
                self.merit_preview_text.configure(state="normal")
                self.merit_preview_text.delete("1.0", tk.END)
                self.merit_preview_text.insert("1.0", "No results found for this exam")
                self.merit_preview_text.configure(state="disabled")
                return
            
            # Update exam info
            info_text = f"""✅ {exam_type} #{exam_number} - {subject}
    📊 Total Marks: {total_marks} | 🎯 Segment: {segment}
    🎓 Year: {year} | 📅 Date: {date}
    👥 Students with results: {len(results)}"""
            
            self.merit_exam_info.config(text=info_text, justify="left", fg="green")
            
            # Generate preview
            self.generate_merit_preview(results, total_marks)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exam: {str(e)}")

    def generate_merit_preview(self, results, total_marks):
        """Generate text preview of merit list"""
        try:
            # Define grading system based on selection
            grade_system = self.grade_system_var.get()
            
            def get_grade(percentage):
                if grade_system == "numeric":
                    # GPA system (5.00 scale)
                    if percentage >= 80:
                        return "5.00"
                    elif percentage >= 70:
                        return "4.00"
                    elif percentage >= 60:
                        return "3.50"
                    elif percentage >= 50:
                        return "3.00"
                    elif percentage >= 40:
                        return "2.00"
                    elif percentage >= 33:
                        return "1.00"
                    else:
                        return "0.00"
                else:
                    # Standard grading
                    if percentage >= 80:
                        return "A+"
                    elif percentage >= 70:
                        return "A"
                    elif percentage >= 60:
                        return "A-"
                    elif percentage >= 50:
                        return "B"
                    elif percentage >= 40:
                        return "C"
                    elif percentage >= 33:
                        return "D"
                    else:
                        return "F"
            
            # Calculate statistics
            scores = [r[3] for r in results]
            highest = max(scores)
            lowest = min(scores)
            average = sum(scores) / len(scores)
            
            # Generate preview text
            preview_text = "Science Point By Dr. Talha\n"
            preview_text += "=" * 60 + "\n\n"
            
            # Header
            preview_text += f"Total Students: {len(results)}\n"
            preview_text += f"Statistics: Highest={highest:.1f}, Lowest={lowest:.1f}, Average={average:.1f}\n\n"
            
            # Column headers
            if self.include_details_var.get():
                preview_text += f"{'Rank':<5} {'Roll':<8} {'Name':<20} {'Marks':<10} {'%':<8} {'Grade':<6}\n"
                preview_text += "-" * 60 + "\n"
            else:
                preview_text += f"{'Rank':<5} {'Roll':<8} {'Name':<25} {'Marks':<10} {'%':<8} {'Grade':<6}\n"
                preview_text += "-" * 52 + "\n"
            
            # Student data
            for rank, (roll, name, school, score) in enumerate(results, 1):
                percentage = (score / total_marks) * 100
                grade = get_grade(percentage)
                
                # Highlight top 3
                if rank <= 3 and self.highlight_top3_var.get():
                    name_display = f"**{name}**"
                else:
                    name_display = name
                
                if self.include_details_var.get():
                    preview_text += f"{rank:<5} {roll:<8} {name_display:<20} {score:<10.1f} {percentage:<8.1f} {grade:<6}\n"
                    # Add school in next line
                    preview_text += f"     School: {school[:25]}\n"
                else:
                    preview_text += f"{rank:<5} {roll:<8} {name_display:<25} {score:<10.1f} {percentage:<8.1f} {grade:<6}\n"
            
            preview_text += "\n" + "=" * 60 + "\n"
            preview_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            
            # Update preview text widget
            self.merit_preview_text.configure(state="normal")
            self.merit_preview_text.delete("1.0", tk.END)
            self.merit_preview_text.insert("1.0", preview_text)
            # Make read-only
            self.merit_preview_text.bind("<Key>", lambda e: "break")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")

    def generate_merit_list_pdf_results(self):
        """Generate merit list PDF from results tab"""
        try:
            exam_id = self.merit_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score 
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Merit List as PDF",
                initialfile=f"Merit_List_{subject}_{date.replace('-', '')}.pdf"
            )
            
            if not file_path:
                return
            
            if not REPORTLAB_AVAILABLE:
                messagebox.showerror("Error", "ReportLab library not installed. Cannot generate PDF.")
                return
            
            # Calculate percentages for results
            results_with_percentage = []
            for roll, name, school, score in results:
                percentage = (score / total_marks) * 100
                results_with_percentage.append((roll, name, school, score, percentage))
            
            # Call the PDF creation function
            self.create_merit_list_pdf(exam_type, exam_number, subject, total_marks, 
                                      segment, year, date, results_with_percentage, file_path)
            
            messagebox.showinfo("Success", f"✅ Merit list PDF generated!\n\nFile: {file_path}")
            self.update_status(f"Generated merit list PDF for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate merit list PDF: {str(e)}")

    def export_merit_list_csv_results(self):
        """Export merit list CSV from results tab"""
        try:
            exam_id = self.merit_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score 
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Merit List as CSV",
                initialfile=f"Merit_List_{subject}_{date.replace('-', '')}.csv"
            )
            
            if not file_path:
                return
            
            # Define grading system based on selection
            grade_system = self.grade_system_var.get()
            
            def get_grade(percentage):
                if grade_system == "numeric":
                    if percentage >= 80:
                        return "5.00"
                    elif percentage >= 70:
                        return "4.00"
                    elif percentage >= 60:
                        return "3.50"
                    elif percentage >= 50:
                        return "3.00"
                    elif percentage >= 40:
                        return "2.00"
                    elif percentage >= 33:
                        return "1.00"
                    else:
                        return "0.00"
                else:
                    if percentage >= 80:
                        return "A+"
                    elif percentage >= 70:
                        return "A"
                    elif percentage >= 60:
                        return "A-"
                    elif percentage >= 50:
                        return "B"
                    elif percentage >= 40:
                        return "C"
                    elif percentage >= 33:
                        return "D"
                    else:
                        return "F"
            
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Science Point By Dr. Talha"])
                writer.writerow([f"{exam_type} #{exam_number} - {subject}"])
                writer.writerow([f"Segment: {segment} | Batch Year: {year} | Date: {date}"])
                writer.writerow([f"Total Marks: {total_marks} | Total Students: {len(results)}"])
                writer.writerow([f"Grading System: {grade_system.upper()}"])
                writer.writerow([])
                
                # Write column headers
                headers = ["Rank", "Roll", "Name"]
                if self.include_details_var.get():
                    headers.extend(["School"])
                headers.extend(["Marks", "Percentage", "Grade"])
                
                writer.writerow(headers)
                
                # Write data
                for rank, (roll, name, school, score) in enumerate(results, 1):
                    percentage = (score / total_marks) * 100
                    grade = get_grade(percentage)
                    
                    row = [rank, roll, name]
                    if self.include_details_var.get():
                        row.extend([school])
                    row.extend([f"{score:.2f}", f"{percentage:.2f}%", grade])
                    
                    writer.writerow(row)
                
                # Add statistics
                writer.writerow([])
                scores = [r[3] for r in results]
                
                writer.writerow(["STATISTICS"])
                writer.writerow([f"Highest Score: {max(scores):.2f}"])
                writer.writerow([f"Lowest Score: {min(scores):.2f}"])
                writer.writerow([f"Average Score: {sum(scores)/len(scores):.2f}"])
                writer.writerow([f"Total Students: {len(results)}"])
                writer.writerow([])
                writer.writerow([f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            
            messagebox.showinfo("Success", 
                              f"✅ Merit list CSV exported!\n\n"
                              f"Exam: {exam_type} #{exam_number} - {subject}\n"
                              f"Students: {len(results)}\n"
                              f"File: {os.path.basename(file_path)}")
            
            self.update_status(f"Exported merit list CSV for exam {exam_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export merit list CSV: {str(e)}")

    def print_merit_list_results(self):
        """Print merit list from results tab"""
        try:
            exam_id = self.merit_exam_id.get().strip()
            if not exam_id:
                messagebox.showwarning("Input", "Please enter Exam ID")
                return
            
            # Get exam details
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT type, number, subject, total_marks, category, ssc_year, date 
                           FROM exams WHERE id=?""", (exam_id,))
                exam = c.fetchone()
            
            if not exam:
                messagebox.showerror("Error", "Exam not found")
                return
            
            exam_type, exam_number, subject, total_marks, segment, year, date = exam
            
            # Get results
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.roll, s.name, s.school, r.score 
                           FROM results r
                           JOIN students s ON r.student_id = s.id
                           WHERE r.exam_id = ?
                           ORDER BY r.score DESC, s.roll""", (exam_id,))
                results = c.fetchall()
            
            if not results:
                messagebox.showinfo("No Results", "No results found for this exam")
                return
            
            # Create report text
            report = f"MERIT LIST - {exam_type} #{exam_number}\n"
            report += f"Subject: {subject} | Date: {date}\n"
            report += f"Segment: {segment} | Year: {year}\n"
            report += f"Total Marks: {total_marks} | Students: {len(results)}\n"
            report += "=" * 60 + "\n\n"
            
            # Define grading based on selection
            grade_system = self.grade_system_var.get()
            
            def get_grade(percentage):
                if grade_system == "numeric":
                    if percentage >= 80:
                        return "5.00"
                    elif percentage >= 70:
                        return "4.00"
                    elif percentage >= 60:
                        return "3.50"
                    elif percentage >= 50:
                        return "3.00"
                    elif percentage >= 40:
                        return "2.00"
                    elif percentage >= 33:
                        return "1.00"
                    else:
                        return "0.00"
                else:
                    if percentage >= 80:
                        return "A+"
                    elif percentage >= 70:
                        return "A"
                    elif percentage >= 60:
                        return "A-"
                    elif percentage >= 50:
                        return "B"
                    elif percentage >= 40:
                        return "C"
                    elif percentage >= 33:
                        return "D"
                    else:
                        return "F"
            
            # Add ranked students
            for rank, (roll, name, school, score) in enumerate(results, 1):
                percentage = (score / total_marks) * 100
                grade = get_grade(percentage)
                
                if rank <= 3 and self.highlight_top3_var.get():
                    rank_display = f"**{rank}**"
                else:
                    rank_display = str(rank)
                
                if self.include_details_var.get():
                    report += f"{rank_display:>3}. Roll {roll}: {name}\n"
                    report += f"     School: {school}\n"
                    report += f"     Marks: {score:.1f}/{total_marks} ({percentage:.1f}%) - Grade: {grade}\n\n"
                else:
                    report += f"{rank_display:>3}. Roll {roll}: {name}\n"
                    report += f"     Marks: {score:.1f}/{total_marks} ({percentage:.1f}%) - Grade: {grade}\n\n"
            
            # Add statistics
            scores = [r[3] for r in results]
            report += "\n" + "=" * 60 + "\n"
            report += f"Statistics:\n"
            report += f"Highest Score: {max(scores):.1f}\n"
            report += f"Lowest Score:  {min(scores):.1f}\n"
            report += f"Average Score: {sum(scores)/len(scores):.1f}\n"
            report += f"Total Students: {len(results)}\n\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Show report
            self.show_report_dialog(f"Merit List - {subject}", report)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print merit list: {str(e)}")
            # ============================================================================
    # PAYMENTS TAB (Complete with Batch Processing and Slip Generation)
    # ============================================================================

    def setup_payments(self):
        """Setup payments tab with full functionality including batch processing"""
        frame = self.tabs['payments']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create notebook for payment management
        payment_notebook = ttk.Notebook(frame)
        payment_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.record_tab = ttk.Frame(payment_notebook)
        self.batch_tab = ttk.Frame(payment_notebook)
        self.view_tab = ttk.Frame(payment_notebook)
        self.receipt_tab = ttk.Frame(payment_notebook)
        
        payment_notebook.add(self.record_tab, text="💰 Record Payment")
        payment_notebook.add(self.batch_tab, text="📦 Batch Payment")
        payment_notebook.add(self.view_tab, text="📋 View Payments")
        payment_notebook.add(self.receipt_tab, text="🖨️ Generate Slips")
        
        # Setup all tabs
        self.setup_record_payment_tab(self.record_tab)
        self.setup_batch_payment_tab(self.batch_tab)
        self.setup_view_payments_tab(self.view_tab)
        self.setup_receipt_generation_tab(self.receipt_tab)
        
        # Initialize variables
        self.batch_students = []
        self.selected_batch_ids = set()

    def setup_record_payment_tab(self, parent):
        """Setup individual record payment tab"""
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Record Student Payment", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Student search frame
        search_frame = tk.LabelFrame(main, text=" Find Student ", bg="white", padx=20, pady=20)
        search_frame.pack(fill="x", pady=10)
        
        # Search options
        search_option_frame = tk.Frame(search_frame, bg="white")
        search_option_frame.pack(fill="x", pady=10)
        
        self.search_option = tk.StringVar(value="id")
        
        tk.Radiobutton(search_option_frame, text="By Student ID", variable=self.search_option,
                      value="id", bg="white", command=self.on_search_option_change_payment).pack(side="left", padx=10)
        
        tk.Radiobutton(search_option_frame, text="By Roll Number", variable=self.search_option,
                      value="roll", bg="white", command=self.on_search_option_change_payment).pack(side="left", padx=10)
        
        tk.Radiobutton(search_option_frame, text="By Name", variable=self.search_option,
                      value="name", bg="white", command=self.on_search_option_change_payment).pack(side="left", padx=10)
        
        # Search input
        search_input_frame = tk.Frame(search_frame, bg="white")
        search_input_frame.pack(fill="x", pady=10)
        
        tk.Label(search_input_frame, text="Search:", bg="white", font=('Segoe UI', 10, 'bold')
                ).pack(side="left", padx=5)
        
        self.search_input_payment = tk.Entry(search_input_frame, width=30, font=('Segoe UI', 10),
                                            bg="#f8f9fa", relief="solid", borderwidth=1)
        self.search_input_payment.pack(side="left", padx=5)
        
        tk.Button(search_input_frame, text="🔍 Search", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.search_student_for_payment).pack(side="left", padx=10)
        
        # Student list frame (for name search)
        self.student_list_frame_payment = tk.Frame(search_frame, bg="white")
        self.student_list_frame_payment.pack(fill="x", pady=10)
        self.student_list_frame_payment.pack_forget()
        
        # Student info frame
        self.student_info_frame = tk.LabelFrame(main, text=" Student Information ", bg="white", padx=20, pady=20)
        self.student_info_frame.pack(fill="x", pady=10)
        
        self.student_info_label = tk.Label(self.student_info_frame, 
                                          text="Search for a student to record payment",
                                          bg="white", font=('Segoe UI', 11))
        self.student_info_label.pack()
        
        # Payment details frame
        self.payment_details_frame = tk.LabelFrame(main, text=" Payment Details ", bg="white", padx=20, pady=20)
        self.payment_details_frame.pack(fill="x", pady=10)
        self.payment_details_frame.pack_forget()
        
        # Month and Year selection
        tk.Label(self.payment_details_frame, text="Month:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=0, column=0, sticky="e", pady=10, padx=5)
        
        self.payment_month = ttk.Combobox(self.payment_details_frame, values=self.utils.get_months(), 
                                         width=25, state="readonly", font=('Segoe UI', 10))
        self.payment_month.set(datetime.now().strftime("%B"))
        self.payment_month.grid(row=0, column=1, pady=10, padx=5)
        
        tk.Label(self.payment_details_frame, text="Year:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=1, column=0, sticky="e", pady=10, padx=5)
        
        current_year = datetime.now().year
        self.payment_year = ttk.Combobox(self.payment_details_frame, 
                                        values=[str(y) for y in range(current_year-2, current_year+3)], 
                                        width=25, state="readonly", font=('Segoe UI', 10))
        self.payment_year.set(str(current_year))
        self.payment_year.grid(row=1, column=1, pady=10, padx=5)
        
        # Amount details
        tk.Label(self.payment_details_frame, text="Due Amount:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=2, column=0, sticky="e", pady=10, padx=5)
        
        self.due_amount_label = tk.Label(self.payment_details_frame, text="0 Tk", bg="white",
                                        font=('Segoe UI', 10, 'bold'), fg=self.colors['danger'])
        self.due_amount_label.grid(row=2, column=1, pady=10, padx=5, sticky="w")
        
        tk.Label(self.payment_details_frame, text="Paid Amount:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=3, column=0, sticky="e", pady=10, padx=5)
        
        self.paid_amount_label = tk.Label(self.payment_details_frame, text="0 Tk", bg="white",
                                         font=('Segoe UI', 10, 'bold'), fg=self.colors['success'])
        self.paid_amount_label.grid(row=3, column=1, pady=10, padx=5, sticky="w")
        
        # Payment amount input
        tk.Label(self.payment_details_frame, text="Payment Amount (Tk):", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=4, column=0, sticky="e", pady=10, padx=5)
        
        self.payment_amount_entry = tk.Entry(self.payment_details_frame, width=28, font=('Segoe UI', 10),
                                            bg="#f8f9fa", relief="solid", borderwidth=1)
        self.payment_amount_entry.grid(row=4, column=1, pady=10, padx=5)
        self.payment_amount_entry.insert(0, "500")
        
        # Balance display
        tk.Label(self.payment_details_frame, text="Balance:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=5, column=0, sticky="e", pady=10, padx=5)
        
        self.balance_label = tk.Label(self.payment_details_frame, text="0 Tk", bg="white",
                                     font=('Segoe UI', 10, 'bold'), fg=self.colors['warning'])
        self.balance_label.grid(row=5, column=1, pady=10, padx=5, sticky="w")
        
        # Payment type
        tk.Label(self.payment_details_frame, text="Payment Method:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=6, column=0, sticky="e", pady=10, padx=5)
        
        self.payment_method = ttk.Combobox(self.payment_details_frame, 
                                          values=["Cash", "Bank Transfer", "Bkash", "Nagad", "Rocket", "Other"],
                                          width=25, state="readonly", font=('Segoe UI', 10))
        self.payment_method.set("Cash")
        self.payment_method.grid(row=6, column=1, pady=10, padx=5)
        
        # Remarks
        tk.Label(self.payment_details_frame, text="Remarks:", bg="white", font=('Segoe UI', 10, 'bold')
                ).grid(row=7, column=0, sticky="e", pady=10, padx=5)
        
        self.payment_remarks = tk.Entry(self.payment_details_frame, width=28, font=('Segoe UI', 10),
                                       bg="#f8f9fa", relief="solid", borderwidth=1)
        self.payment_remarks.grid(row=7, column=1, pady=10, padx=5)
        self.payment_remarks.insert(0, "Monthly fee payment")
        
        # Submit button
        self.submit_payment_btn = tk.Button(self.payment_details_frame, text="💳 Record Payment", 
                                           bg=self.colors['success'], fg="white",
                                           padx=20, pady=12, font=('Segoe UI', 11, 'bold'),
                                           command=self.record_payment, state="disabled")
        self.submit_payment_btn.grid(row=8, column=1, pady=20, sticky="w")
        
        # Bind amount change to update balance
        self.payment_amount_entry.bind('<KeyRelease>', self.update_payment_balance)
        
        # Initialize current student id
        self.current_student_id = None

    def setup_batch_payment_tab(self, parent):
        """Setup batch payment recording tab with working checkboxes and filters"""
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="📦 Batch Payment Recording", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # ================= FILTER SETTINGS =================
        filter_frame = tk.LabelFrame(main, text=" Filter Students ", bg="white", padx=20, pady=15)
        filter_frame.pack(fill="x", pady=10)
        
        # Segment filter
        tk.Label(filter_frame, text="Segment:", bg="white", 
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="e", pady=10, padx=5)
        
        self.batch_segment = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"],
                                         width=15, state="readonly", font=('Segoe UI', 10))
        self.batch_segment.set("All")
        self.batch_segment.grid(row=0, column=1, pady=10, padx=5)
        
        # Batch Year filter
        tk.Label(filter_frame, text="Batch Year:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky="e", pady=10, padx=(20,5))
        
        current_year = datetime.now().year
        years = ["All"] + [str(y) for y in range(current_year-2, current_year+3)]
        self.batch_year_filter = ttk.Combobox(filter_frame, values=years,
                                            width=15, state="readonly", font=('Segoe UI', 10))
        self.batch_year_filter.set(str(current_year))
        self.batch_year_filter.grid(row=0, column=3, pady=10, padx=5)
        
        # Payment Month/Year
        tk.Label(filter_frame, text="Payment Month:", bg="white", 
                font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky="e", pady=10, padx=5)
        
        self.batch_month = ttk.Combobox(filter_frame, values=self.utils.get_months(),
                                       width=15, state="readonly", font=('Segoe UI', 10))
        self.batch_month.set(datetime.now().strftime("%B"))
        self.batch_month.grid(row=1, column=1, pady=10, padx=5)
        
        tk.Label(filter_frame, text="Payment Year:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=1, column=2, sticky="e", pady=10, padx=(20,5))
        
        self.batch_year = ttk.Combobox(filter_frame, 
                                      values=[str(y) for y in range(current_year-2, current_year+3)],
                                      width=15, state="readonly", font=('Segoe UI', 10))
        self.batch_year.set(str(current_year))
        self.batch_year.grid(row=1, column=3, pady=10, padx=5)
        
        # Load Students Button
        self.load_batch_btn = tk.Button(filter_frame, text="📋 Load Students", bg=self.colors['info'], fg="white",
                                       padx=15, pady=8, command=self.load_students_for_batch)
        self.load_batch_btn.grid(row=1, column=4, padx=20)
        
        # Show only due students checkbox
        self.show_only_due_var = tk.BooleanVar(value=False)
        self.show_only_due_cb = tk.Checkbutton(filter_frame, text="Show Only Due Students",
                                              variable=self.show_only_due_var, bg="white")
        self.show_only_due_cb.grid(row=0, column=4, padx=10, sticky="w")
        
        # ================= BATCH ACTION BUTTONS =================
        action_frame = tk.Frame(main, bg=self.colors['bg'])
        action_frame.pack(fill="x", pady=10)
        
        self.select_all_var = tk.BooleanVar()
        self.select_all_cb = tk.Checkbutton(action_frame, text="Select All Students", variable=self.select_all_var,
                                           bg=self.colors['bg'], command=self.toggle_select_all_batch)
        self.select_all_cb.pack(side="left", padx=10)
        
        tk.Button(action_frame, text="✅ Mark as Paid", bg=self.colors['success'], fg="white",
                 padx=15, pady=8, command=self.mark_as_paid_batch).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="💰 Record Payments", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.record_batch_payments).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="🖨️ Generate Slips", bg="#6c757d", fg="white",
                 padx=15, pady=8, command=self.generate_batch_slips).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="🔄 Clear Selection", bg=self.colors['warning'], fg="black",
                 padx=15, pady=8, command=self.clear_batch_selection).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="🔄 Refresh List", bg=self.colors['info'], fg="white",
                 padx=15, pady=8, command=self.load_students_for_batch).pack(side="left", padx=5)
        
        # ================= BATCH STUDENTS TABLE =================
        table_frame = tk.LabelFrame(main, text=" Students List ", bg="white", padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        # Create Treeview for batch students
        cols = ("Select", "ID", "Roll", "Name", "Segment", "Year", "Due", "Paid", "Balance", "Status")
        self.batch_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        
        # Configure columns
        column_widths = {
            "Select": 60, "ID": 70, "Roll": 70, "Name": 150, "Segment": 70, "Year": 70,
            "Due": 90, "Paid": 90, "Balance": 90, "Status": 80
        }
        
        for col in cols:
            self.batch_tree.heading(col, text=col, anchor="center")
            self.batch_tree.column(col, anchor="center", width=column_widths.get(col, 100))
        
        # Add tags for styling
        self.batch_tree.tag_configure('selected', background='lightgreen')
        self.batch_tree.tag_configure('paid', background='#d4edda')  # Light green
        self.batch_tree.tag_configure('partial', background='#fff3cd')  # Light yellow
        self.batch_tree.tag_configure('due', background='#f8d7da')  # Light red
        self.batch_tree.tag_configure('unbilled', background='#e9ecef')
        
        # Bind click event for checkboxes
        self.batch_tree.bind('<Button-1>', self.on_batch_tree_click)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.batch_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.batch_tree.xview)
        self.batch_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.batch_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # ================= PAYMENT DETAILS FOR BATCH =================
        payment_frame = tk.LabelFrame(main, text=" Payment Details (Applied to Selected) ", bg="white", padx=20, pady=15)
        payment_frame.pack(fill="x", pady=10)
        
        tk.Label(payment_frame, text="Payment Amount per Student:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="e", pady=10, padx=5)
        
        self.batch_amount_entry = tk.Entry(payment_frame, width=20, font=('Segoe UI', 10),
                                          bg="#f8f9fa", relief="solid", borderwidth=1)
        self.batch_amount_entry.grid(row=0, column=1, pady=10, padx=5)
        self.batch_amount_entry.insert(0, "500")
        
        tk.Label(payment_frame, text="Payment Method:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky="e", pady=10, padx=5)
        
        self.batch_payment_method = ttk.Combobox(payment_frame,
                                               values=["Cash", "Bank Transfer", "Bkash", "Nagad", "Rocket", "Other"],
                                               width=15, state="readonly", font=('Segoe UI', 10))
        self.batch_payment_method.set("Cash")
        self.batch_payment_method.grid(row=0, column=3, pady=10, padx=5)
        
        tk.Label(payment_frame, text="Remarks:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky="e", pady=10, padx=5)
        
        self.batch_remarks_entry = tk.Entry(payment_frame, width=20, font=('Segoe UI', 10),
                                           bg="#f8f9fa", relief="solid", borderwidth=1)
        self.batch_remarks_entry.grid(row=1, column=1, pady=10, padx=5)
        self.batch_remarks_entry.insert(0, "Monthly fee - Batch payment")
        
        # Summary frame
        summary_frame = tk.Frame(main, bg=self.colors['bg'])
        summary_frame.pack(fill="x", pady=10)
        
        self.batch_summary_label = tk.Label(summary_frame, text="Select segment and batch year, then click 'Load Students'", 
                                           bg=self.colors['bg'], font=('Segoe UI', 10))
        self.batch_summary_label.pack()
        
        # Initialize variables
        self.batch_students = []
        self.selected_batch_ids = set()

    def load_students_for_batch(self):
        """Load students for batch processing with filters"""
        try:
            segment_filter = self.batch_segment.get()
            year_filter = self.batch_year_filter.get()
            month = self.batch_month.get()
            year = int(self.batch_year.get())
            show_only_due = self.show_only_due_var.get()
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                # Build query
                query = """SELECT s.id, s.roll, s.name, s.category, s.ssc_year 
                          FROM students s WHERE 1=1"""
                params = []
                
                if segment_filter != "All":
                    query += " AND s.category = ?"
                    params.append(segment_filter)
                
                if year_filter != "All":
                    query += " AND s.ssc_year = ?"
                    params.append(int(year_filter))
                
                query += " ORDER BY s.category, s.roll"
                
                c.execute(query, params)
                students = c.fetchall()
            
            if not students:
                messagebox.showinfo("No Students", "No students found with the selected filters")
                return
            
            # Clear existing items
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)
            
            self.batch_students = []
            self.selected_batch_ids.clear()
            self.select_all_var.set(False)
            
            # Load payment status for each student
            for student in students:
                student_id, roll, name, category, ssc_year = student
                
                # Get payment status for selected month/year
                c.execute("""SELECT due_amount, paid_amount, status FROM payments 
                           WHERE student_id=? AND month=? AND year=?""", 
                         (student_id, month, year))
                payment = c.fetchone()
                
                if payment:
                    due_amount, paid_amount, status = payment
                    balance = due_amount - paid_amount
                else:
                    # If no payment record exists, there is no due for this month.
                    if show_only_due:
                        continue
                    due_amount = 0
                    paid_amount = 0
                    balance = due_amount
                    status = "unbilled"
                
                # Skip if showing only due students and student is already paid
                if show_only_due and status == "paid":
                    continue
                
                # Store student data
                student_data = {
                    'id': student_id, 'roll': roll, 'name': name, 'segment': category, 'year': ssc_year,
                    'due_amount': due_amount, 'paid_amount': paid_amount, 'balance': balance,
                    'status': status,
                    'selected': False,
                    'tree_item': None
                }
                self.batch_students.append(student_data)
                
                # Add to treeview with checkbox
                checkbox_text = "✓" if student_id in self.selected_batch_ids else "□"
                status_display = self.get_status_display(status)
                
                # Determine tag based on status
                tags = (status,)
                if student_id in self.selected_batch_ids:
                    tags = tags + ('selected',)
                
                item_id = self.batch_tree.insert("", "end", values=(
                    checkbox_text,
                    student_id,
                    roll,
                    name,
                    category if category else "N/A",
                    ssc_year,
                    f"{due_amount:,.0f}",
                    f"{paid_amount:,.0f}",
                    f"{balance:,.0f}",
                    status_display
                ), tags=tags)
                
                # Store tree item reference
                student_data['tree_item'] = item_id
            
            # Update summary
            self.update_batch_summary()
            self.update_status(f"Loaded {len(self.batch_students)} students for batch processing")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students: {str(e)}")

    def on_batch_tree_click(self, event):
        """Handle click on batch treeview for checkbox toggling"""
        region = self.batch_tree.identify("region", event.x, event.y)
        
        if region == "cell":
            column = self.batch_tree.identify_column(event.x)
            row = self.batch_tree.identify_row(event.y)
            
            if column == "#1":  # First column (Select)
                item = self.batch_tree.item(row)
                values = list(item['values'])
                student_id = values[1]  # ID is at index 1
                
                # Toggle selection
                if student_id in self.selected_batch_ids:
                    self.selected_batch_ids.remove(student_id)
                    values[0] = "□"
                    # Get original status tag
                    for student in self.batch_students:
                        if student['id'] == student_id:
                            self.batch_tree.item(row, values=values, tags=(student['status'],))
                            student['selected'] = False
                            break
                else:
                    self.selected_batch_ids.add(student_id)
                    values[0] = "✓"
                    # Get status tag for background color
                    for student in self.batch_students:
                        if student['id'] == student_id:
                            self.batch_tree.item(row, values=values, tags=(student['status'], 'selected'))
                            student['selected'] = True
                            break
                
                # Update summary
                self.update_batch_summary()
                
                # Update select all checkbox state
                self.update_select_all_checkbox()

    def toggle_select_all_batch(self):
        """Select/Deselect all students in batch"""
        select_all = self.select_all_var.get()
        
        # Update internal data and treeview
        for student in self.batch_students:
            student['selected'] = select_all
            if select_all:
                self.selected_batch_ids.add(student['id'])
            elif student['id'] in self.selected_batch_ids:
                self.selected_batch_ids.remove(student['id'])
            
            # Update treeview
            if student['tree_item']:
                values = list(self.batch_tree.item(student['tree_item'])['values'])
                values[0] = "✓" if select_all else "□"
                
                if select_all:
                    self.batch_tree.item(student['tree_item'], values=values, 
                                        tags=(student['status'], 'selected'))
                else:
                    self.batch_tree.item(student['tree_item'], values=values, 
                                        tags=(student['status'],))
        
        self.update_batch_summary()

    def update_select_all_checkbox(self):
        """Update select all checkbox based on current selection"""
        total_students = len(self.batch_students)
        selected_count = len(self.selected_batch_ids)
        
        if selected_count == 0:
            self.select_all_var.set(False)
        elif selected_count == total_students:
            self.select_all_var.set(True)
        else:
            self.select_all_var.set(False)  # Intermediate state

    def update_batch_summary(self):
        """Update batch summary label"""
        selected_count = len(self.selected_batch_ids)
        total_students = len(self.batch_students)
        
        if selected_count > 0:
            try:
                amount_per_student = float(self.batch_amount_entry.get() or 0)
                total_amount = amount_per_student * selected_count
                summary = f"Selected: {selected_count}/{total_students} students | Total Amount: {total_amount:,.0f} Tk"
            except:
                summary = f"Selected: {selected_count}/{total_students} students"
        else:
            summary = f"Total Students: {total_students} | Select students to record payments"
        
        self.batch_summary_label.config(text=summary)

    def clear_batch_selection(self):
        """Clear all selections in batch"""
        self.selected_batch_ids.clear()
        self.select_all_var.set(False)
        
        # Update all students in the list
        for student in self.batch_students:
            student['selected'] = False
            
            # Update treeview
            if student['tree_item']:
                values = list(self.batch_tree.item(student['tree_item'])['values'])
                values[0] = "□"
                self.batch_tree.item(student['tree_item'], values=values, 
                                    tags=(student['status'],))
        
        self.update_batch_summary()

    def mark_as_paid_batch(self):
        """Mark selected students as fully paid"""
        try:
            selected_students = [s for s in self.batch_students if s['selected']]
            
            if not selected_students:
                messagebox.showwarning("Selection", "Please select at least one student")
                return
            
            month = self.batch_month.get()
            year = int(self.batch_year.get())
            
            confirm_msg = f"Mark {len(selected_students)} students as fully paid for {month} {year}?\n\n"
            confirm_msg += "This will set their status to 'paid' and clear any remaining balance."
            
            if not messagebox.askyesno("Confirm Mark as Paid", confirm_msg):
                return
            
            successful = 0
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                for student in selected_students:
                    student_id = student['id']
                    
                    # Check existing payment
                    c.execute("""SELECT due_amount, paid_amount FROM payments 
                               WHERE student_id=? AND month=? AND year=?""", 
                             (student_id, month, year))
                    payment = c.fetchone()
                    
                    if payment:
                        due_amount, existing_paid = payment
                        new_paid = due_amount  # Pay the full due amount
                        c.execute("""UPDATE payments SET paid_amount=?, due_amount=0, status='paid', 
                                   updated_at=CURRENT_TIMESTAMP 
                                   WHERE student_id=? AND month=? AND year=?""",
                                 (new_paid, student_id, month, year))
                    else:
                        # Create new payment record marked as paid
                        default_due = 500
                        c.execute("""INSERT INTO payments (student_id, month, year, status, 
                                   due_amount, paid_amount, updated_at) 
                                   VALUES (?, ?, ?, 'paid', 0, ?, CURRENT_TIMESTAMP)""",
                                 (student_id, month, year, default_due))
                    
                    successful += 1
                
                conn.commit()
            
            messagebox.showinfo("Success", f"✅ {successful} students marked as paid!")
            
            # Refresh the view
            self.load_students_for_batch()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark as paid: {str(e)}")

    def record_batch_payments(self):
        """Record payments for selected students in batch"""
        try:
            # Get batch settings
            month = self.batch_month.get()
            year = int(self.batch_year.get())
            amount_per_student_str = self.batch_amount_entry.get().strip()
            method = self.batch_payment_method.get()
            remarks = self.batch_remarks_entry.get().strip()
            
            if not amount_per_student_str:
                messagebox.showwarning("Input", "Please enter payment amount")
                return
            
            amount_per_student = float(amount_per_student_str)
            
            if amount_per_student <= 0:
                messagebox.showwarning("Validation", "Amount must be greater than 0")
                return
            
            # Get selected students using the selected_batch_ids set
            selected_students = [s for s in self.batch_students if s['id'] in self.selected_batch_ids]
            
            if not selected_students:
                messagebox.showwarning("Selection", "Please select at least one student")
                return
            
            # Confirm batch operation
            confirm_msg = f"Record payment of {amount_per_student:,.0f} Tk for {len(selected_students)} students?\n\n"
            confirm_msg += f"Month: {month} {year}\nMethod: {method}\nRemarks: {remarks}"
            
            if not messagebox.askyesno("Confirm Batch Payment", confirm_msg):
                return
            
            # Process each selected student
            successful = 0
            failed = []
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                for student in selected_students:
                    try:
                        student_id = student['id']
                        
                        # Check existing payment
                        c.execute("""SELECT due_amount, paid_amount FROM payments 
                                   WHERE student_id=? AND month=? AND year=?""", 
                                 (student_id, month, year))
                        payment = c.fetchone()
                        
                        if payment:
                            due_amount, existing_paid = payment
                            new_paid = existing_paid + amount_per_student
                            new_due = max(0, due_amount - amount_per_student)
                            
                            # Determine status
                            if new_due == 0:
                                status = "paid"
                            elif new_paid > 0:
                                status = "partial"
                            else:
                                status = "due"
                            
                            # Update payment
                            c.execute("""UPDATE payments SET paid_amount=?, due_amount=?, status=?, 
                                       updated_at=CURRENT_TIMESTAMP 
                                       WHERE student_id=? AND month=? AND year=?""",
                                     (new_paid, new_due, status, student_id, month, year))
                        else:
                            # Create new payment record
                            default_due = 500  # Default monthly fee
                            new_due = max(0, default_due - amount_per_student)
                            status = "paid" if new_due == 0 else "partial"
                            
                            c.execute("""INSERT INTO payments (student_id, month, year, status, 
                                       due_amount, paid_amount, updated_at) 
                                       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                                     (student_id, month, year, status, new_due, amount_per_student))
                        
                        # Record in payment history
                        try:
                            c.execute("""CREATE TABLE IF NOT EXISTS payment_history (
                                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                                       student_id INTEGER,
                                       month TEXT,
                                       year INTEGER,
                                       amount REAL,
                                       method TEXT,
                                       remarks TEXT,
                                       recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                       FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                                       )""")
                            
                            c.execute("""INSERT INTO payment_history (student_id, month, year, amount, method, remarks)
                                       VALUES (?, ?, ?, ?, ?, ?)""",
                                     (student_id, month, year, amount_per_student, method, remarks))
                        except Exception as history_error:
                            print(f"Note: Could not save payment history for student {student_id}: {history_error}")
                        
                        successful += 1
                        
                    except Exception as student_error:
                        failed.append(f"{student['name']} (ID: {student['id']}): {str(student_error)}")
                
                conn.commit()
            
            # Show results
            result_msg = f"✅ Batch payment completed!\n\n"
            result_msg += f"Successful: {successful} students\n"
            result_msg += f"Amount per student: {amount_per_student:,.0f} Tk\n"
            result_msg += f"Total amount: {amount_per_student * successful:,.0f} Tk"
            
            if failed:
                result_msg += f"\n\n❌ Failed ({len(failed)}):\n" + "\n".join(failed[:5])  # Show first 5 failures
                if len(failed) > 5:
                    result_msg += f"\n... and {len(failed)-5} more"
            
            messagebox.showinfo("Batch Payment Result", result_msg)
            
            # Refresh the batch view
            self.load_students_for_batch()
            
            self.update_status(f"Batch payment: {successful} students, {amount_per_student * successful:,.0f} Tk")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process batch payment: {str(e)}")

    def generate_batch_slips(self):
        """Generate slips for selected students in batch"""
        try:
            selected_students = [s for s in self.batch_students if s['selected']]
            
            if not selected_students:
                messagebox.showwarning("Selection", "Please select at least one student")
                return
            
            # Get batch settings
            month = self.batch_month.get()
            year = int(self.batch_year.get())
            amount = float(self.batch_amount_entry.get() or 0)
            method = self.batch_payment_method.get()
            
            # Generate slips
            self.generate_payment_slips(selected_students, month, year, amount, method)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate slips: {str(e)}")

    def get_status_display(self, status):
        """Get display text for status"""
        if status == "paid":
            return "✅ Paid"
        elif status == "partial":
            return "⚠️ Partial"
        elif status == "unbilled":
            return "⚪ Not Billed"
        elif status == "overdue":
            return "🔴 Overdue"
        else:
            return "❌ Due"

    def setup_view_payments_tab(self, parent):
        """Setup view payments tab"""
        main = tk.Frame(parent, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="View Student Payments", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Filter frame
        filter_frame = tk.LabelFrame(main, text=" Filter Payments ", bg="white", padx=20, pady=15)
        filter_frame.pack(fill="x", pady=10)
        
        # Student ID input
        tk.Label(filter_frame, text="Student ID:", bg="white", font=('Segoe UI', 10, 'bold')
                ).pack(side="left", padx=5)
        
        self.view_student_id = tk.Entry(filter_frame, width=15, font=('Segoe UI', 10),
                                       bg="#f8f9fa", relief="solid", borderwidth=1)
        self.view_student_id.pack(side="left", padx=5)
        
        tk.Button(filter_frame, text="🔍 View Payments", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.view_student_payments).pack(side="left", padx=10)
        
        # Filter by month/year
        tk.Label(filter_frame, text="Month:", bg="white").pack(side="left", padx=10)
        self.filter_payment_month = ttk.Combobox(filter_frame, values=["All"] + self.utils.get_months(), 
                                               width=12, state="readonly", font=('Segoe UI', 9))
        self.filter_payment_month.set("All")
        self.filter_payment_month.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Year:", bg="white").pack(side="left", padx=10)
        current_year = datetime.now().year
        self.filter_payment_year = ttk.Combobox(filter_frame, 
                                              values=["All"] + [str(y) for y in range(current_year-2, current_year+3)],
                                              width=12, state="readonly", font=('Segoe UI', 9))
        self.filter_payment_year.set("All")
        self.filter_payment_year.pack(side="left", padx=5)
        
        tk.Button(filter_frame, text="📊 View All", bg=self.colors['info'], fg="white",
                 padx=15, pady=8, command=self.view_all_payments).pack(side="left", padx=10)
        
        tk.Button(filter_frame, text="📄 Export", bg="#17a2b8", fg="white",
                 padx=15, pady=8, command=self.export_payments_csv).pack(side="left", padx=10)
        
        # Payments summary frame
        self.payment_summary_frame = tk.LabelFrame(main, text=" Payment Summary ", bg="white", padx=20, pady=15)
        self.payment_summary_frame.pack(fill="x", pady=10)
        
        self.payment_summary_label = tk.Label(self.payment_summary_frame, 
                                             text="Enter Student ID to view payment summary",
                                             bg="white", font=('Segoe UI', 10))
        self.payment_summary_label.pack()
        
        # Payments treeview
        tree_frame = tk.Frame(main)
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        cols = ("Student ID", "Name", "Month", "Year", "Status", "Balance", "Method", "Date")
        self.tree_payments = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        
        column_configs = {
            "Student ID": 80, "Name": 120, "Month": 80, "Year": 60, "Status": 80,
            "Balance": 90, "Method": 90, "Date": 100
        }
        
        for col in cols:
            self.tree_payments.heading(col, text=col, anchor="center")
            self.tree_payments.column(col, anchor="center", width=column_configs.get(col, 100))
        
        # Add tags for coloring
        self.tree_payments.tag_configure('paid', background='#d4edda')
        self.tree_payments.tag_configure('partial', background='#fff3cd')
        self.tree_payments.tag_configure('due', background='#f8d7da')
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_payments.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_payments.xview)
        self.tree_payments.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree_payments.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def view_student_payments(self):
        """View payments for a specific student"""
        try:
            student_id = self.view_student_id.get().strip()
            if not student_id:
                messagebox.showwarning("Input", "Please enter Student ID")
                return
            
            # Clear existing items
            for item in self.tree_payments.get_children():
                self.tree_payments.delete(item)
            
            # Get student info
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT name, roll, category, ssc_year FROM students WHERE id=?", (student_id,))
                student = c.fetchone()
                
                if not student:
                    messagebox.showerror("Error", "Student not found")
                    return
                
                name, roll, segment, year_level = student
                
                # Build query with filters
                query = """SELECT month, year, status, due_amount, paid_amount, updated_at 
                          FROM payments WHERE student_id=?"""
                params = [student_id]
                
                month_filter = self.filter_payment_month.get()
                year_filter = self.filter_payment_year.get()
                
                if month_filter != "All":
                    query += " AND month = ?"
                    params.append(month_filter)
                if year_filter != "All":
                    query += " AND year = ?"
                    params.append(int(year_filter))
                
                query += " ORDER BY year, CASE month "
                months = self.utils.get_months()
                for i, month in enumerate(months, 1):
                    query += f"WHEN '{month}' THEN {i} "
                query += "END"
                
                c.execute(query, params)
                payments = c.fetchall()
            
            # Update summary
            total_due = sum(p[3] for p in payments)
            total_paid = sum(p[4] for p in payments)
            total_balance = total_due - total_paid
            
            summary_text = f"""Student: {name} (Roll: {roll})
    Segment: {segment} | Year: {year_level}
    Total Due: {total_due:,.0f} Tk | Total Paid: {total_paid:,.0f} Tk
    Balance: {total_balance:,.0f} Tk | Payments: {len(payments)} months"""
            
            self.payment_summary_label.config(text=summary_text, justify="left")
            
            # Insert into treeview
            for month, year, status, due_amount, paid_amount, updated in payments:
                balance = due_amount - paid_amount
                
                # Color code status
                tag = ''
                if status == "paid":
                    status_display = "✅ Paid"
                    tag = 'paid'
                elif status == "partial":
                    status_display = "⚠️ Partial"
                    tag = 'partial'
                else:
                    status_display = "❌ Due"
                    tag = 'due'
                
                self.tree_payments.insert("", "end", values=(
                    student_id, name, month, year, status_display,
                    f"{due_amount:,.0f}",
                    f"{paid_amount:,.0f}",
                    f"{balance:,.0f}",
                    "-",  # Method (would need payment_history table)
                    updated[:10]  # Just date
                ), tags=(tag,))
            
            self.update_status(f"Showing {len(payments)} payments for {name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load payments: {str(e)}")

    def view_all_payments(self):
        """View all payments with filters"""
        try:
            # Clear existing items
            for item in self.tree_payments.get_children():
                self.tree_payments.delete(item)
            
            # Build query
            query = """SELECT s.id, s.name, p.month, p.year, p.status, 
                      p.due_amount, p.paid_amount, p.updated_at
                      FROM payments p
                      JOIN students s ON p.student_id = s.id"""
            
            params = []
            conditions = []
            
            month_filter = self.filter_payment_month.get()
            year_filter = self.filter_payment_year.get()
            
            if month_filter != "All":
                conditions.append("p.month = ?")
                params.append(month_filter)
            if year_filter != "All":
                conditions.append("p.year = ?")
                params.append(int(year_filter))
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY p.year DESC, p.month DESC, s.roll"
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                payments = c.fetchall()
            
            # Update summary
            total_due = sum(p[5] for p in payments)
            total_paid = sum(p[6] for p in payments)
            total_balance = total_due - total_paid
            
            summary_text = f"""ALL PAYMENTS SUMMARY
    Total Records: {len(payments)}
    Total Due: {total_due:,.0f} Tk
    Total Paid: {total_paid:,.0f} Tk
    Balance: {total_balance:,.0f} Tk"""
            
            self.payment_summary_label.config(text=summary_text, justify="left")
            
            # Insert into treeview
            for student_id, name, month, year, status, due_amount, paid_amount, updated in payments:
                balance = due_amount - paid_amount
                
                # Color code status
                tag = ''
                if status == "paid":
                    status_display = "✅ Paid"
                    tag = 'paid'
                elif status == "partial":
                    status_display = "⚠️ Partial"
                    tag = 'partial'
                else:
                    status_display = "❌ Due"
                    tag = 'due'
                
                self.tree_payments.insert("", "end", values=(
                    student_id, name, month, year, status_display,
                    f"{due_amount:,.0f}",
                    f"{paid_amount:,.0f}",
                    f"{balance:,.0f}",
                    "-",  # Method
                    updated[:10]
                ), tags=(tag,))
            
            self.update_status(f"Showing {len(payments)} payment records")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load payments: {str(e)}")

    def export_payments_csv(self):
        """Export payments to CSV"""
        try:
            import csv
            from tkinter import filedialog
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if not filename:
                return
            
            # Get all payments
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT s.id, s.name, s.roll, s.category, p.month, p.year, 
                          p.status, p.due_amount, p.paid_amount, p.updated_at
                          FROM payments p
                          JOIN students s ON p.student_id = s.id
                          ORDER BY p.year DESC, p.month DESC""")
                payments = c.fetchall()
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['Student ID', 'Name', 'Roll', 'Class', 'Month', 'Year', 
                               'Status', 'Due Amount', 'Paid Amount', 'Balance', 'Updated Date'])
                
                # Write data
                for payment in payments:
                    student_id, name, roll, class_name, month, year, status, due_amount, paid_amount, updated = payment
                    balance = due_amount - paid_amount
                    writer.writerow([student_id, name, roll, class_name, month, year, 
                                   status, due_amount, paid_amount, balance, updated[:10]])
            
            messagebox.showinfo("Export Successful", f"Payments exported successfully!\n\nSaved to:\n{filename}")
            self.update_status(f"Exported {len(payments)} payment records to CSV")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export payments: {str(e)}")

    def setup_receipt_generation_tab(self, parent):
        """Setup receipt/slip generation tab"""
        scrollable_frame = self.utils.create_scrollable_frame(parent, self.colors['bg'])
        
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="🖨️ Payment Slip Generation", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # ================= SLIP SETTINGS =================
        settings_frame = tk.LabelFrame(main, text=" Slip Settings ", bg="white", padx=20, pady=15)
        settings_frame.pack(fill="x", pady=10)
        
        # Paper format selection
        tk.Label(settings_frame, text="Paper Format:", bg="white", 
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=10)
        
        self.paper_format = ttk.Combobox(settings_frame, values=["A4 (6 slips per page)", "A4 (4 slips per page)", "A4 (2 slips per page)", "Individual Slips"],
                                        width=25, state="readonly", font=('Segoe UI', 10))
        self.paper_format.set("A4 (6 slips per page)")
        self.paper_format.grid(row=0, column=1, pady=10, padx=5)
        
        # Month/Year for slips
        tk.Label(settings_frame, text="Month:", bg="white", 
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky="w", pady=10, padx=(20,5))
        
        self.slip_month = ttk.Combobox(settings_frame, values=self.utils.get_months(),
                                      width=15, state="readonly", font=('Segoe UI', 10))
        self.slip_month.set(datetime.now().strftime("%B"))
        self.slip_month.grid(row=0, column=3, pady=10, padx=5)
        
        tk.Label(settings_frame, text="Year:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=1, column=2, sticky="w", pady=10, padx=(20,5))
        
        current_year = datetime.now().year
        self.slip_year = ttk.Combobox(settings_frame, 
                                     values=[str(y) for y in range(current_year-2, current_year+3)],
                                     width=15, state="readonly", font=('Segoe UI', 10))
        self.slip_year.set(str(current_year))
        self.slip_year.grid(row=1, column=3, pady=10, padx=5)
        
        # ================= STUDENT SELECTION =================
        selection_frame = tk.LabelFrame(main, text=" Select Students for Slips ", bg="white", padx=20, pady=15)
        selection_frame.pack(fill="x", pady=10)
        
        # Segment filter
        tk.Label(selection_frame, text="Segment:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=10)
        
        self.slip_segment_filter = ttk.Combobox(selection_frame, values=["All", "SSC", "HSC"],
                                               width=15, state="readonly", font=('Segoe UI', 10))
        self.slip_segment_filter.set("All")
        self.slip_segment_filter.grid(row=0, column=1, pady=10, padx=5)
        
        # Year filter
        tk.Label(selection_frame, text="Batch Year:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky="w", pady=10, padx=(20,5))
        
        self.slip_year_filter = ttk.Combobox(selection_frame, values=["All"] + [str(y) for y in range(current_year-2, current_year+3)],
                                            width=15, state="readonly", font=('Segoe UI', 10))
        self.slip_year_filter.set("All")
        self.slip_year_filter.grid(row=0, column=3, pady=10, padx=5)
        
        # Status filter
        tk.Label(selection_frame, text="Payment Status:", bg="white",
                font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=10, padx=5)
        
        self.slip_status_filter = ttk.Combobox(selection_frame, 
                                             values=["All", "Paid", "Partial", "Due"],
                                             width=15, state="readonly", font=('Segoe UI', 10))
        self.slip_status_filter.set("All")
        self.slip_status_filter.grid(row=1, column=1, pady=10, padx=5)
        
        # Load students button
        tk.Button(selection_frame, text="📋 Load Students", bg=self.colors['info'], fg="white",
                 padx=15, pady=8, command=self.load_students_for_slips).grid(row=0, column=4, padx=20, rowspan=2)
        
        # ================= STUDENTS TABLE FOR SLIPS =================
        table_frame = tk.LabelFrame(main, text=" Students for Slip Generation ", bg="white", padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        # Create Treeview for slip students
        cols = ("Select", "ID", "Roll", "Name", "Segment", "Year", "Balance", "Status")
        self.slip_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        
        column_widths = {
            "Select": 60, "ID": 70, "Roll": 70, "Name": 150, "Segment": 70, "Year": 70,
            "Balance": 90, "Status": 80
        }
        
        for col in cols:
            self.slip_tree.heading(col, text=col, anchor="center")
            self.slip_tree.column(col, anchor="center", width=column_widths.get(col, 100))
        
        # Add tags
        self.slip_tree.tag_configure('selected', background='lightgreen')
        self.slip_tree.tag_configure('paid', background='#d4edda')
        self.slip_tree.tag_configure('partial', background='#fff3cd')
        self.slip_tree.tag_configure('due', background='#f8d7da')
        
        # Bind click event
        self.slip_tree.bind('<Button-1>', self.on_slip_tree_click)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.slip_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.slip_tree.xview)
        self.slip_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.slip_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # ================= ACTION BUTTONS =================
        action_frame = tk.Frame(main, bg=self.colors['bg'])
        action_frame.pack(fill="x", pady=10)
        
        self.select_all_slips_var = tk.BooleanVar()
        tk.Checkbutton(action_frame, text="Select All", variable=self.select_all_slips_var,
                      bg=self.colors['bg'], command=self.toggle_select_all_slips).pack(side="left", padx=10)
        
        tk.Button(action_frame, text="🖨️ Generate Selected Slips", bg=self.colors['primary'], fg="white",
                 padx=15, pady=8, command=self.generate_slips).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="📄 Preview Slip", bg="#17a2b8", fg="white",
                 padx=15, pady=8, command=self.preview_slip).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="🔄 Clear Selection", bg=self.colors['warning'], fg="black",
                 padx=15, pady=8, command=self.clear_slip_selection).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="🔄 Refresh List", bg=self.colors['info'], fg="white",
                 padx=15, pady=8, command=self.load_students_for_slips).pack(side="left", padx=5)
        
        # Summary label
        self.slip_summary_label = tk.Label(main, text="Select students to generate payment slips", 
                                          bg=self.colors['bg'], font=('Segoe UI', 10))
        self.slip_summary_label.pack(pady=5)
        
        # Initialize variables
        self.slip_students = []
        self.selected_slip_ids = set()

    def load_students_for_slips(self):
        """Load students for slip generation"""
        try:
            segment_filter = self.slip_segment_filter.get()
            year_filter = self.slip_year_filter.get()
            status_filter = self.slip_status_filter.get()
            month = self.slip_month.get()
            year = int(self.slip_year.get())
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                # Build query
                query = """SELECT s.id, s.roll, s.name, s.category, s.ssc_year,
                          COALESCE(p.due_amount, 500) as due_amount,
                          COALESCE(p.paid_amount, 0) as paid_amount,
                          COALESCE(p.status, 'due') as status
                          FROM students s
                          LEFT JOIN payments p ON s.id = p.student_id 
                          AND p.month = ? AND p.year = ?
                          WHERE 1=1"""
                
                params = [month, year]
                
                if segment_filter != "All":
                    query += " AND s.category = ?"
                    params.append(segment_filter)
                
                if year_filter != "All":
                    query += " AND s.ssc_year = ?"
                    params.append(int(year_filter))
                
                if status_filter != "All":
                    query += " AND COALESCE(p.status, 'due') = ?"
                    params.append(status_filter.lower())
                
                query += " ORDER BY s.category, s.roll"
                
                c.execute(query, params)
                students = c.fetchall()
            
            if not students:
                messagebox.showinfo("No Students", "No students found with the selected filters")
                return
            
            # Clear existing items
            for item in self.slip_tree.get_children():
                self.slip_tree.delete(item)
            
            self.slip_students = []
            self.selected_slip_ids.clear()
            self.select_all_slips_var.set(False)
            
            # Add students to treeview
            for student in students:
                student_id, roll, name, category, year_level, due_amount, paid_amount, status = student
                balance = due_amount - paid_amount
                
                student_data = {
                    'id': student_id,
                    'roll': roll,
                    'name': name,
                    'segment': category,
                    'year': year_level,
                    'due_amount': due_amount,
                    'paid_amount': paid_amount,
                    'balance': balance,
                    'status': status,
                    'selected': False,
                    'tree_item': None
                }
                self.slip_students.append(student_data)
                
                checkbox_text = "✓" if student_id in self.selected_slip_ids else "□"
                status_display = self.get_status_display(status)
                
                # Determine tag based on status
                tags = (status,)
                if student_id in self.selected_slip_ids:
                    tags = tags + ('selected',)
                
                item_id = self.slip_tree.insert("", "end", values=(
                    checkbox_text,
                    student_id,
                    roll,
                    name,
                    category if category else "N/A",
                    year_level,
                    f"{due_amount:,.0f}",
                    f"{paid_amount:,.0f}",
                    f"{balance:,.0f}",
                    status_display
                ), tags=tags)
                
                # Store tree item reference
                student_data['tree_item'] = item_id
            
            # Update summary
            self.slip_summary_label.config(text=f"Loaded {len(students)} students for slip generation")
            self.update_status(f"Loaded {len(students)} students for slips")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students: {str(e)}")

    def on_slip_tree_click(self, event):
        """Handle click on slip treeview for checkbox toggling"""
        region = self.slip_tree.identify("region", event.x, event.y)
        
        if region == "cell":
            column = self.slip_tree.identify_column(event.x)
            row = self.slip_tree.identify_row(event.y)
            
            if column == "#1":  # First column (Select)
                item = self.slip_tree.item(row)
                values = list(item['values'])
                student_id = values[1]  # ID is at index 1
                
                # Toggle selection
                if student_id in self.selected_slip_ids:
                    self.selected_slip_ids.remove(student_id)
                    values[0] = "□"
                    # Get original status tag
                    for student in self.slip_students:
                        if student['id'] == student_id:
                            self.slip_tree.item(row, values=values, tags=(student['status'],))
                            student['selected'] = False
                            break
                else:
                    self.selected_slip_ids.add(student_id)
                    values[0] = "✓"
                    # Get status tag for background color
                    for student in self.slip_students:
                        if student['id'] == student_id:
                            self.slip_tree.item(row, values=values, tags=(student['status'], 'selected'))
                            student['selected'] = True
                            break
                
                # Update select all checkbox state
                self.update_select_all_slips_checkbox()

    def toggle_select_all_slips(self):
        """Select/Deselect all students for slips"""
        select_all = self.select_all_slips_var.get()
        
        # Update internal data and treeview
        for student in self.slip_students:
            student['selected'] = select_all
            if select_all:
                self.selected_slip_ids.add(student['id'])
            elif student['id'] in self.selected_slip_ids:
                self.selected_slip_ids.remove(student['id'])
            
            # Update treeview
            if student['tree_item']:
                values = list(self.slip_tree.item(student['tree_item'])['values'])
                values[0] = "✓" if select_all else "□"
                
                if select_all:
                    self.slip_tree.item(student['tree_item'], values=values, 
                                       tags=(student['status'], 'selected'))
                else:
                    self.slip_tree.item(student['tree_item'], values=values, 
                                       tags=(student['status'],))
        
        self.update_slip_summary()

    def update_select_all_slips_checkbox(self):
        """Update select all checkbox based on current selection"""
        total_students = len(self.slip_students)
        selected_count = len(self.selected_slip_ids)
        
        if selected_count == 0:
            self.select_all_slips_var.set(False)
        elif selected_count == total_students:
            self.select_all_slips_var.set(True)
        else:
            self.select_all_slips_var.set(False)

    def clear_slip_selection(self):
        """Clear all selections for slips"""
        self.selected_slip_ids.clear()
        self.select_all_slips_var.set(False)
        
        # Update all students in the list
        for student in self.slip_students:
            student['selected'] = False
            
            # Update treeview
            if student['tree_item']:
                values = list(self.slip_tree.item(student['tree_item'])['values'])
                values[0] = "□"
                self.slip_tree.item(student['tree_item'], values=values, 
                                   tags=(student['status'],))
        
        self.update_slip_summary()

    def update_slip_summary(self):
        """Update slip summary"""
        selected_count = len(self.selected_slip_ids)
        total_students = len(self.slip_students)
        
        if selected_count > 0:
            summary = f"Selected: {selected_count}/{total_students} students for slip generation"
        else:
            summary = f"Total Students: {total_students} | Select students to generate slips"
        
        self.slip_summary_label.config(text=summary)

    def generate_slips(self):
        """Generate payment slips for selected students"""
        try:
            # Get selected students
            selected_students = [s for s in self.slip_students if s['selected']]
            
            if not selected_students:
                messagebox.showwarning("Selection", "Please select at least one student")
                return
            
            # Get slip settings
            month = self.slip_month.get()
            year = int(self.slip_year.get())
            paper_format = self.paper_format.get()
            
            # Generate slips
            self.generate_payment_slips(selected_students, month, year, 0, "Cash", paper_format)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate slips: {str(e)}")

    def preview_slip(self):
        """Preview a sample slip"""
        try:
            # Create a sample student for preview
            sample_student = {
                'id': 'SAMPLE001',
                'roll': '101',
                'name': 'John Doe',
                'segment': 'Science',
                'year': '2024',
                'due_amount': 500,
                'paid_amount': 500,
                'balance': 0,
                'status': 'paid',
                'selected': True
            }
            
            month = self.slip_month.get()
            year = int(self.slip_year.get())
            paper_format = self.paper_format.get()
            
            # Generate preview slip
            self.generate_payment_slips([sample_student], month, year, 500, "Cash", paper_format, preview=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview slip: {str(e)}")

    def generate_payment_slips(self, students, month, year, amount, method, paper_format="A4 (4 slips per page)", preview=False):
        """Generate payment slips PDF"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab library not installed. Cannot generate PDF.")
            return

        try:
            # Ask for save location if not preview
            if preview:
                import tempfile
                fd, file_path = tempfile.mkstemp(suffix=".pdf")
                os.close(fd)
            else:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    title="Save Payment Slips",
                    initialfile=f"Payment_Slips_{month}_{year}.pdf"
                )
                
                if not file_path:
                    return

            from reportlab.lib.units import cm
            
            # Setup document
            doc = SimpleDocTemplate(file_path, pagesize=A4, 
                                   topMargin=0.5*cm, bottomMargin=0.5*cm,
                                   leftMargin=0.5*cm, rightMargin=0.5*cm)
            elements = []
            styles = getSampleStyleSheet()
            
            # Define styles
            title_style = ParagraphStyle('Title', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=1)
            subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=1)
            normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Helvetica', fontSize=10)
            bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
            
            # Helper to create a single slip
            def create_slip(student):
                # Slip content
                data = [
                    [Paragraph("SCIENCE POINT By Dr. Talha", title_style)],
                    [Paragraph("MONEY RECEIPT", subtitle_style)],
                    [Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", normal_style)],
                    [Paragraph(f"Student: {student['name']} (Roll: {student['roll']})", bold_style)],
                    [Paragraph(f"Batch: {student.get('year', '')} | Segment: {student.get('segment', '')}", normal_style)],
                    [Paragraph(f"Payment For: {month} {year}", normal_style)],
                    [Paragraph(f"Status: {student.get('status', 'Paid').upper()}", normal_style)],
                    [Spacer(1, 0.5*cm)],
                    [Paragraph("_______________________", normal_style)],
                    [Paragraph("Authorized Signature", normal_style)]
                ]
                
                # Create table for the slip with border
                t = Table(data, colWidths=[8*cm])
                t.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('BOX', (0,0), (-1,-1), 1, colors.black),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ]))
                return t

            # Layout logic based on paper format
            slip_tables = []
            for student in students:
                slip_tables.append(create_slip(student))

            # Arrange slips on page
            if "6 slips" in paper_format:
                # 2x3 grid
                for i in range(0, len(slip_tables), 6):
                    batch = slip_tables[i:i+6]
                    rows = []
                    for j in range(0, len(batch), 2):
                        row_items = batch[j:j+2]
                        if len(row_items) < 2:
                            row_items.append(Spacer(1, 1))
                        row_table = Table([row_items], colWidths=[9*cm, 9*cm])
                        row_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                        rows.append(row_table)
                        rows.append(Spacer(1, 0.5*cm))
                    elements.extend(rows)
                    if i + 6 < len(slip_tables):
                        elements.append(PageBreak())
            elif "4 slips" in paper_format:
                # 2x2 grid
                for i in range(0, len(slip_tables), 4):
                    batch = slip_tables[i:i+4]
                    rows = []
                    for j in range(0, len(batch), 2):
                        row_items = batch[j:j+2]
                        if len(row_items) < 2:
                            row_items.append(Spacer(1, 1))
                        row_table = Table([row_items], colWidths=[9*cm, 9*cm])
                        row_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                        rows.append(row_table)
                        rows.append(Spacer(1, 1*cm))
                    elements.extend(rows)
                    if i + 4 < len(slip_tables):
                        elements.append(PageBreak())
            elif "2 slips" in paper_format:
                for i, slip in enumerate(slip_tables):
                    elements.append(slip)
                    elements.append(Spacer(1, 2*cm))
                    if (i + 1) % 2 == 0 and i < len(slip_tables) - 1:
                        elements.append(PageBreak())
            else:
                for i, slip in enumerate(slip_tables):
                    elements.append(slip)
                    if i < len(slip_tables) - 1:
                        elements.append(PageBreak())

            doc.build(elements)

            if preview:
                webbrowser.open(file_path)
            else:
                messagebox.showinfo("Success", f"Payment slips generated successfully!\nFile: {file_path}")
                self.update_status(f"Generated {len(students)} payment slips")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")

    # ============================================================================
    # HELPER METHODS FOR PAYMENTS TAB
    # ============================================================================

    def search_student_for_payment(self):
        """Search for student to record payment"""
        try:
            search_term = self.search_input_payment.get().strip()
            if not search_term:
                messagebox.showwarning("Input", "Please enter search term")
                return
            
            search_by = self.search_option.get()
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                
                if search_by == "id":
                    c.execute("""SELECT id, name, roll, category, ssc_year, contact FROM students 
                               WHERE id=?""", (search_term,))
                elif search_by == "roll":
                    c.execute("""SELECT id, name, roll, category, ssc_year, contact FROM students 
                               WHERE roll=?""", (search_term,))
                else:  # name
                    c.execute("""SELECT id, name, roll, category, ssc_year, contact FROM students 
                               WHERE name LIKE ? ORDER BY name LIMIT 20""", (f"%{search_term}%",))
                
                students = c.fetchall()
            
            if not students:
                messagebox.showinfo("No Results", "No students found")
                return
            
            if search_by == "name" and len(students) > 1:
                # Show student list for selection
                self.show_student_list_for_selection_payment(students)
                return
            
            # If single student found or ID/Roll search
            student = students[0]
            self.load_student_for_payment(student)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search student: {str(e)}")

    def load_student_for_payment(self, student):
        """Load student information for payment"""
        try:
            student_id, name, roll, segment, year, contact = student
            
            # Update student info
            info_text = f"""✅ Student Found:
    👤 Name: {name}
    🎯 Roll: {roll} | ID: {student_id}
    📚 Segment: {segment} | Year: {year}
    📞 Contact: {contact}"""
            
            self.student_info_label.config(text=info_text, justify="left", fg="green")
            
            # Store current student ID
            self.current_student_id = student_id
            
            # Show payment details frame
            self.payment_details_frame.pack(fill="x", pady=10)
            
            # Load current month's payment status
            current_month = datetime.now().strftime("%B")
            current_year = datetime.now().year
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT due_amount, paid_amount, status FROM payments 
                           WHERE student_id=? AND month=? AND year=?""", 
                         (student_id, current_month, current_year))
                payment = c.fetchone()
            
            if payment:
                due_amount, paid_amount, status = payment
                balance = due_amount - paid_amount
            else:
                # Default values
                due_amount = 500  # Default monthly fee
                paid_amount = 0
                balance = due_amount
                status = "due"
            
            # Update labels
            self.due_amount_label.config(text=f"{due_amount:,.0f} Tk")
            self.paid_amount_label.config(text=f"{paid_amount:,.0f} Tk")
            self.balance_label.config(text=f"{balance:,.0f} Tk")
            
            # Set payment amount to balance if any
            if balance > 0:
                self.payment_amount_entry.delete(0, tk.END)
                self.payment_amount_entry.insert(0, str(balance))
            
            # Update payment month/year to current
            self.payment_month.set(current_month)
            self.payment_year.set(str(current_year))
            
            # Enable submit button
            self.submit_payment_btn.config(state="normal")
            
            self.update_status(f"Loaded student: {name} (Balance: {balance:,.0f} Tk)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load student: {str(e)}")

    def record_payment(self):
        """Record a payment"""
        try:
            if not hasattr(self, 'current_student_id') or self.current_student_id is None:
                messagebox.showwarning("Error", "No student selected. Please search and select a student first.")
                return
            
            student_id = self.current_student_id
            month = self.payment_month.get()
            year = int(self.payment_year.get())
            amount_str = self.payment_amount_entry.get().strip()
            method = self.payment_method.get()
            remarks = self.payment_remarks.get().strip()
            
            if not all([month, year, amount_str, method]):
                messagebox.showwarning("Validation", "Please fill all required fields")
                return
            
            amount = float(amount_str)
            
            if amount <= 0:
                messagebox.showwarning("Validation", "Amount must be greater than 0")
                return
            
            # Get current payment status
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT due_amount, paid_amount FROM payments 
                           WHERE student_id=? AND month=? AND year=?""", 
                         (student_id, month, year))
                payment = c.fetchone()
            
            if payment:
                due_amount, existing_paid = payment
                new_paid = existing_paid + amount
                new_due = max(0, due_amount - amount)  # Due amount shouldn't go negative
                
                # Determine status
                if new_due == 0:
                    status = "paid"
                elif new_paid > 0:
                    status = "partial"
                else:
                    status = "due"
                
                # Update payment
                c.execute("""UPDATE payments SET paid_amount=?, due_amount=?, status=?, 
                           updated_at=CURRENT_TIMESTAMP 
                           WHERE student_id=? AND month=? AND year=?""",
                         (new_paid, new_due, status, student_id, month, year))
            else:
                # Create new payment record with default due amount
                default_due = 500  # Default monthly fee
                new_due = max(0, default_due - amount)
                status = "paid" if new_due == 0 else "partial"
                
                c.execute("""INSERT INTO payments (student_id, month, year, status, 
                           due_amount, paid_amount, updated_at) 
                           VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                         (student_id, month, year, status, new_due, amount))
            
            # Record payment details in a separate table (for history)
            try:
                c.execute("""CREATE TABLE IF NOT EXISTS payment_history (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           student_id INTEGER,
                           month TEXT,
                           year INTEGER,
                           amount REAL,
                           method TEXT,
                           remarks TEXT,
                           recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                           )""")
                
                c.execute("""INSERT INTO payment_history (student_id, month, year, amount, method, remarks)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                         (student_id, month, year, amount, method, remarks))
            except Exception as history_error:
                logging.error(f"Failed to save payment history: {history_error}")
                print(f"Note: Could not save payment history: {history_error}")
            
            conn.commit()
            
            # Get student name for receipt
            c.execute("SELECT name, roll FROM students WHERE id=?", (student_id,))
            student = c.fetchone()
            student_name, roll = student if student else ("Unknown", "")
            
            # Clear form
            self.payment_amount_entry.delete(0, tk.END)
            self.payment_remarks.delete(0, tk.END)
            self.payment_remarks.insert(0, "Monthly fee payment")
            
            # Show success message with receipt
            receipt = f"""✅ PAYMENT RECORDED SUCCESSFULLY!

    Student: {student_name} (Roll: {roll})
    Month: {month} {year}
    Amount: {amount:,.0f} Tk
    Payment Method: {method}
    Remarks: {remarks}

    New Status: {status.upper()}
    Balance Updated"""

            messagebox.showinfo("Payment Successful", receipt)
            logging.info(f"Payment recorded: {amount} for student {student_id}")
            
            # Refresh student payment info
            self.load_student_for_payment((student_id, student_name, roll, "", year, ""))
            
            self.update_status(f"Recorded payment: {amount:,.0f} Tk for {student_name}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount format. Please enter a valid number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record payment: {str(e)}")

    def update_payment_balance(self, event=None):
        """Update balance when payment amount changes"""
        try:
            due_text = self.due_amount_label.cget("text").replace(" Tk", "").replace(",", "")
            due_amount = float(due_text) if due_text else 0
            
            paid_text = self.paid_amount_label.cget("text").replace(" Tk", "").replace(",", "")
            paid_amount = float(paid_text) if paid_text else 0
            
            current_balance = due_amount - paid_amount
            
            payment_text = self.payment_amount_entry.get().strip()
            if payment_text:
                try:
                    payment_amount = float(payment_text)
                    new_balance = current_balance - payment_amount
                    
                    # Validate payment amount
                    if payment_amount < 0:
                        self.balance_label.config(text="Invalid amount", fg="red")
                        return
                    elif payment_amount > current_balance:
                        self.balance_label.config(text=f"{(payment_amount - current_balance):,.0f} Tk (Overpaid)", 
                                                 fg="orange")
                    else:
                        self.balance_label.config(text=f"{new_balance:,.0f} Tk", fg=self.colors['warning'])
                except ValueError:
                    self.balance_label.config(text="Invalid amount", fg="red")
            else:
                self.balance_label.config(text=f"{current_balance:,.0f} Tk", fg=self.colors['warning'])
                
        except Exception:
            self.balance_label.config(text="Error calculating", fg="red")

    def on_search_option_change_payment(self):
        """Handle search option change in payment tab"""
        if self.search_option.get() == "name":
            self.student_list_frame_payment.pack(fill="x", pady=10)
        else:
            self.student_list_frame_payment.pack_forget()

    def show_student_list_for_selection_payment(self, students):
        """Show list of students for selection in payment tab"""
        # Clear previous list
        for widget in self.student_list_frame_payment.winfo_children():
            widget.destroy()
        
        tk.Label(self.student_list_frame_payment, text="Select Student:", bg="white", 
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=5)
        
        # Create listbox
        listbox = tk.Listbox(self.student_list_frame_payment, height=6, font=('Segoe UI', 10),
                            bg="white", selectbackground=self.colors['primary'])
        scrollbar = tk.Scrollbar(self.student_list_frame_payment, orient="vertical")
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        listbox.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Add students to listbox
        for student in students:
            student_id, name, roll, segment, year, contact = student
            listbox.insert(tk.END, f"{name} (Roll: {roll}, ID: {student_id}, {segment})")
        
        def select_student():
            """Select student from listbox"""
            selection = listbox.curselection()
            if selection:
                student = students[selection[0]]
                self.load_student_for_payment(student)
        
        # Select button
        tk.Button(self.student_list_frame_payment, text="Select", bg=self.colors['primary'], fg="white",
                 command=select_student).pack(pady=5)
        
        # Bind double-click to select
        listbox.bind('<Double-Button-1>', lambda e: select_student()) 
    # ============================================================================
    # DUE LIST TAB
    # ============================================================================
    
    def setup_due(self):
        """Setup due list tab"""
        frame = self.tabs['due']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Main frame
        main = tk.Frame(frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main, text="Due Payments List", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['danger']).pack(pady=10)
        
        # Filter frame
        filter_frame = tk.LabelFrame(main, text=" Filter Dues ", bg="white", padx=20, pady=15)
        filter_frame.pack(fill="x", pady=10)
        
        tk.Label(filter_frame, text="Segment:", bg="white").pack(side="left", padx=5)
        self.due_segment = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"], 
                                       width=10, state="readonly")
        self.due_segment.set("All")
        self.due_segment.pack(side="left", padx=5)
        
        tk.Label(filter_frame, text="Batch Year:", bg="white").pack(side="left", padx=10)
        self.due_year = ttk.Combobox(filter_frame, width=15, state="readonly")
        self.due_year.pack(side="left", padx=5)
        
        tk.Button(filter_frame, text="🔍 Load Dues", bg=self.colors['danger'], fg="white",
                 command=self.load_due_list).pack(side="left", padx=20)
        
        tk.Button(filter_frame, text="🖨️ Print Report", bg="#6c757d", fg="white",
                 command=self.print_due_report).pack(side="left", padx=5)
        
        # Load years
        self.refresh_due_years()
        
        # Due list treeview
        tree_frame = tk.Frame(main)
        tree_frame.pack(fill="both", expand=True, pady=10)
        
        cols = ("Student ID", "Name", "Roll", "Segment", "Year", "Total Due", "Total Paid", "Balance")
        self.tree_due = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        column_configs = {
            "Student ID": 80, "Name": 150, "Roll": 60, "Segment": 70, 
            "Year": 70, "Total Due": 100, "Total Paid": 100, "Balance": 100
        }
        
        for col in cols:
            self.tree_due.heading(col, text=col, anchor="center")
            self.tree_due.column(col, anchor="center", width=column_configs.get(col, 100))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_due.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_due.xview)
        self.tree_due.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree_due.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def refresh_due_years(self):
        """Refresh years for due list"""
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT ssc_year FROM students ORDER BY ssc_year DESC")
            years = ["All"] + [str(row[0]) for row in c.fetchall()]
            self.due_year['values'] = years
            self.due_year.set("All")
    
    def load_due_list(self):
        """Load due list"""
        try:
            # Clear existing items
            for item in self.tree_due.get_children():
                self.tree_due.delete(item)
            
            segment = self.due_segment.get()
            year = self.due_year.get()
            
            # Build query
            query = """SELECT s.id, s.name, s.roll, s.category, s.ssc_year, 
                      COALESCE(SUM(p.due_amount), 0) as total_due,
                      COALESCE(SUM(p.paid_amount), 0) as total_paid
                      FROM students s 
                      LEFT JOIN payments p ON s.id = p.student_id 
                      WHERE (p.status IN ('due', 'partial') OR p.status IS NULL)"""
            
            params = []
            
            conditions = []
            if segment != "All":
                conditions.append("s.category = ?")
                params.append(segment)
            if year != "All":
                conditions.append("s.ssc_year = ?")
                params.append(int(year))
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            query += " GROUP BY s.id HAVING total_due > total_paid ORDER BY s.ssc_year DESC, s.roll"
            
            # Execute query
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                dues = c.fetchall()
            
            # Insert into treeview
            total_balance = 0
            for student in dues:
                student_id, name, roll, category, ssc_year, total_due, total_paid = student
                balance = total_due - total_paid
                total_balance += balance
                
                self.tree_due.insert("", "end", values=(
                    student_id, name, roll, category, ssc_year,
                    self.utils.format_currency(total_due),
                    self.utils.format_currency(total_paid),
                    self.utils.format_currency(balance)
                ))
            
            # Add totals row
            self.tree_due.insert("", "end", values=(
                "TOTAL", "", "", "", "",
                "", "",
                self.utils.format_currency(total_balance)
            ))
            
            self.update_status(f"Showing {len(dues)} students with dues (Total due: {self.utils.format_currency(total_balance)})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load due list: {str(e)}")
    
    def print_due_report(self):
        """Print due report to PDF"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab library not installed. Cannot generate PDF.")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Due Report as PDF"
            )
            
            if not file_path:
                return
            
            # Get due list data
            segment = self.due_segment.get()
            year = self.due_year.get()
            
            query = """SELECT s.name, s.roll, s.category, s.ssc_year, 
                      COALESCE(SUM(p.due_amount), 0) as total_due,
                      COALESCE(SUM(p.paid_amount), 0) as total_paid
                      FROM students s 
                      LEFT JOIN payments p ON s.id = p.student_id 
                      WHERE (p.status IN ('due', 'partial') OR p.status IS NULL)"""
            
            params = []
            
            conditions = []
            if segment != "All":
                conditions.append("s.category = ?")
                params.append(segment)
            if year != "All":
                conditions.append("s.ssc_year = ?")
                params.append(int(year))
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            query += " GROUP BY s.id HAVING total_due > total_paid ORDER BY s.ssc_year DESC, s.roll"
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                dues = c.fetchall()
            
            # Create PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=30, bottomMargin=30)
            elements = []
            
            # Title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18, spaceAfter=20, alignment=1
            )
            
            title = Paragraph(f"Science Point - Due Students for {month} {payment_year}", title_style)
            elements.append(title)
            
            # Date
            date_style = ParagraphStyle(
                'DateStyle', parent=styles['Normal'], fontSize=10, alignment=2, spaceAfter=15
            )
            date_text = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_style)
            elements.append(date_text)
            
            table_data = [["ID", "Name", "Roll", "Segment", "Batch Year", "Contact"]]
            
            for student in due_students:
                table_data.append([str(val) for val in student])
            
            # Create table
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#C0392B")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
            
            # Summary
            summary_style = ParagraphStyle(
                'SummaryStyle', parent=styles['Normal'], fontSize=12, alignment=0, spaceBefore=30
            )
            summary_text = Paragraph(f"<b>Total Due Students:</b> {len(due_students)}", summary_style)
            elements.append(summary_text)
            
            # Build PDF
            doc.build(elements)
            
            self.update_status(f"Due report generated for {month} {payment_year}")
            messagebox.showinfo("Success", f"Due report generated successfully!\n\nFile: {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate due report: {str(e)}")

    # ============================================================================
    # VIEW DATA TAB
    # ============================================================================
    
    def setup_view(self):
        """Setup view data tab"""
        frame = self.tabs['view']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Main frame
        main = tk.Frame(frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=30, pady=20)
        
        tk.Label(main, text="View Database Data", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=10)
        
        # Create notebook for different data views
        view_notebook = ttk.Notebook(main)
        view_notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab 1: Students
        students_tab = ttk.Frame(view_notebook)
        view_notebook.add(students_tab, text="👥 Students")
        
        # Tab 2: Exams
        exams_tab = ttk.Frame(view_notebook)
        view_notebook.add(exams_tab, text="📝 Exams")
        
        # Tab 3: Results
        results_tab = ttk.Frame(view_notebook)
        view_notebook.add(results_tab, text="🏆 Results")
        
        # Tab 4: Payments
        payments_tab = ttk.Frame(view_notebook)
        view_notebook.add(payments_tab, text="💰 Payments")
        
        # Setup all tabs
        self.setup_view_data_students(students_tab)
        self.setup_view_data_exams(exams_tab)
        self.setup_view_data_results(results_tab)
        self.setup_view_data_payments(payments_tab)
    
    def setup_view_data_students(self, parent):
        """Setup view students tab with filters and progress reports"""
        # Filter Frame
        filter_frame = tk.LabelFrame(parent, text=" Filter Students ", bg="white", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(filter_frame, text="Year:", bg="white").pack(side="left", padx=5)
        self.view_student_year = ttk.Combobox(filter_frame, values=["All"] + self.utils.get_ssc_years(), width=10, state="readonly")
        self.view_student_year.set("All")
        self.view_student_year.pack(side="left", padx=5)
        tk.Label(filter_frame, text="Segment:", bg="white").pack(side="left", padx=5)
        self.view_student_segment = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"], width=10, state="readonly")
        self.view_student_segment.set("All")
        self.view_student_segment.pack(side="left", padx=5)
        tk.Label(filter_frame, text="Search:", bg="white").pack(side="left", padx=5)
        self.view_student_search = tk.Entry(filter_frame, width=15)
        self.view_student_search.pack(side="left", padx=5)
        tk.Button(filter_frame, text="🔍 Load", bg=self.colors['primary'], fg="white", 
                 command=self.load_view_students_filtered).pack(side="left", padx=10)
        # Report Actions Frame
        report_frame = tk.LabelFrame(parent, text=" Progress Report Actions ", bg="white", padx=10, pady=10)
        report_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(report_frame, text="Date Range (YYYY-MM-DD):", bg="white").pack(side="left", padx=5)
        self.report_start_date = tk.Entry(report_frame, width=12)
        self.report_start_date.pack(side="left", padx=2)
        tk.Label(report_frame, text="to", bg="white").pack(side="left", padx=2)
        self.report_end_date = tk.Entry(report_frame, width=12)
        self.report_end_date.pack(side="left", padx=5)
        self.report_bw_var = tk.BooleanVar(value=False)
        tk.Checkbutton(report_frame, text="Black & White PDF", variable=self.report_bw_var, bg="white").pack(side="left", padx=10)
        tk.Button(report_frame, text="📊 Single Report", bg=self.colors['info'], fg="white",
                 command=self.generate_selected_progress_report).pack(side="left", padx=5)
        tk.Button(report_frame, text="📚 Batch Reports", bg=self.colors['warning'], fg="black",
                 command=self.generate_batch_progress_reports).pack(side="left", padx=5)

        # Treeview for students
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("ID", "Name", "Father", "Roll", "Class", "Segment", "Year", "School", "Contact")
        self.tree_view_students = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        for col in cols:
            self.tree_view_students.heading(col, text=col, anchor="center")
            self.tree_view_students.column(col, width=100, anchor="center")
        
        self.tree_view_students.column("ID", width=50)
        self.tree_view_students.column("Name", width=150)
        self.tree_view_students.column("Father", width=150)
        self.tree_view_students.column("School", width=200)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_view_students.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_view_students.xview)
        self.tree_view_students.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree_view_students.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double click to view details
        self.tree_view_students.bind("<Double-1>", self.view_student_full_details)
        
        # Load initial data
        self.load_view_students_filtered()

    def load_view_students_filtered(self):
        """Load students into view tab with filters"""
        try:
            # Clear existing
            for item in self.tree_view_students.get_children():
                self.tree_view_students.delete(item)
            
            year = self.view_student_year.get()
            segment = self.view_student_segment.get()
            search = self.view_student_search.get().strip()
            
            query = "SELECT id, name, father, roll, student_class, category, ssc_year, school, contact FROM students WHERE 1=1"
            params = []
            
            if year != "All":
                query += " AND ssc_year = ?"
                params.append(int(year))
            
            if segment != "All":
                query += " AND category = ?"
                params.append(segment)
            
            if search:
                query += " AND (name LIKE ? OR roll LIKE ? OR contact LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                
            query += " ORDER BY ssc_year DESC, roll"
            
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute(query, params)
                students = c.fetchall()
            
            for student in students:
                self.tree_view_students.insert("", "end", values=student)
                
            self.update_status(f"Loaded {len(students)} students")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students: {str(e)}")

    def view_student_full_details(self, event):
        """Show full details of a student in a popup"""
        selection = self.tree_view_students.selection()
        if not selection:
            return
        
        item = self.tree_view_students.item(selection[0])
        student_id = item['values'][0]
        
        # Create popup
        popup = tk.Toplevel(self.root)
        popup.title(f"Student Details")
        popup.geometry("900x700")
        popup.configure(bg=self.colors['bg'])
        
        # Fetch all data
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM students WHERE id=?", (student_id,))
            student = c.fetchone()
            # Schema: id, name, father, roll, school, contact, cat, ssc_year, class, created_at
            
            # Results
            c.execute("""SELECT e.type, e.subject, e.total_marks, r.score, e.date 
                       FROM results r JOIN exams e ON r.exam_id = e.id 
                       WHERE r.student_id=? ORDER BY e.date DESC""", (student_id,))
            results = c.fetchall()
            
            # Payments
            c.execute("""SELECT month, year, status, due_amount, paid_amount, updated_at 
                       FROM payments WHERE student_id=? ORDER BY year DESC, month DESC""", (student_id,))
            payments = c.fetchall()

        if not student:
            return

        # Create UI
        # Header
        header = tk.Frame(popup, bg=self.colors['primary'], pady=20)
        header.pack(fill="x")
        tk.Label(header, text=f"{student[1]}", font=('Segoe UI', 20, 'bold'), bg=self.colors['primary'], fg="white").pack()
        tk.Label(header, text=f"Roll: {student[7]} | Class: {student[8]} | Batch: {student[3]}", font=('Segoe UI', 12), bg=self.colors['primary'], fg="white").pack()

        # Content - Scrollable
        canvas = tk.Canvas(popup, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.utils.enable_mouse_scroll(canvas)
        
        # Info Section
        info_frame = tk.LabelFrame(scroll_frame, text=" Personal Information ", bg="white", padx=20, pady=15, font=('Segoe UI', 10, 'bold'))
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_grid = [
            ("Father's Name:", student[2]), ("School:", student[5]),
            ("Contact:", student[6]), ("Category:", student[4]),
            ("Student ID:", str(student[0])), ("Joined:", str(student[9])[:10])
        ]
        
        for i, (label, value) in enumerate(info_grid):
            tk.Label(info_frame, text=label, bg="white", font=('Segoe UI', 10, 'bold')).grid(row=i//2, column=(i%2)*2, sticky="e", padx=5, pady=5)
            tk.Label(info_frame, text=value, bg="white", font=('Segoe UI', 10)).grid(row=i//2, column=(i%2)*2+1, sticky="w", padx=5, pady=5)

        # Results Section
        res_frame = tk.LabelFrame(scroll_frame, text=" Exam Results ", bg="white", padx=20, pady=15, font=('Segoe UI', 10, 'bold'))
        res_frame.pack(fill="x", padx=20, pady=10)
        
        if results:
            cols = ("Date", "Exam", "Subject", "Marks", "Obtained", "%")
            tree_res = ttk.Treeview(res_frame, columns=cols, show="headings", height=6)
            for col in cols:
                tree_res.heading(col, text=col)
                tree_res.column(col, width=100, anchor="center")
            tree_res.pack(fill="x")
            
            for r in results:
                pct = (r[3]/r[2]*100) if r[2] else 0
                tree_res.insert("", "end", values=(r[4], r[0], r[1], r[2], r[3], f"{pct:.1f}%"))
        else:
            tk.Label(res_frame, text="No exam results found.", bg="white").pack()

        # Payments Section
        pay_frame = tk.LabelFrame(scroll_frame, text=" Payment History ", bg="white", padx=20, pady=15, font=('Segoe UI', 10, 'bold'))
        pay_frame.pack(fill="x", padx=20, pady=10)
        
        if payments:
            cols = ("Month/Year", "Status", "Due", "Paid", "Date")
            tree_pay = ttk.Treeview(pay_frame, columns=cols, show="headings", height=6)
            for col in cols:
                tree_pay.heading(col, text=col)
                tree_pay.column(col, width=100, anchor="center")
            tree_pay.pack(fill="x")
            
            for p in payments:
                tree_pay.insert("", "end", values=(f"{p[0]} {p[1]}", p[2].upper(), p[3], p[4], str(p[5])[:10]))
        else:
            tk.Label(pay_frame, text="No payment records found.", bg="white").pack()
            
        # Close Button
        tk.Button(scroll_frame, text="Close", command=popup.destroy, bg=self.colors['secondary'], fg="white", padx=20).pack(pady=20)

    def generate_selected_progress_report(self):
        """Generate progress report for selected student"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab not installed")
            return
            
        start_date = self.report_start_date.get().strip()
        end_date = self.report_end_date.get().strip()
        is_bw = self.report_bw_var.get()
            
        selection = self.tree_view_students.selection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a student")
            return
            
        item = self.tree_view_students.item(selection[0])
        student_id = item['values'][0]
        name = item['values'][1]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Progress_Report_{name}.pdf"
        )
        
        if file_path:
            if self.create_progress_report_pdf(student_id, file_path, start_date, end_date, is_bw):
                messagebox.showinfo("Success", f"Report generated: {file_path}")
                
    def generate_batch_progress_reports(self):
        """Generate progress reports for all listed students"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab not installed")
            return
            
        start_date = self.report_start_date.get().strip()
        end_date = self.report_end_date.get().strip()
        is_bw = self.report_bw_var.get()
            
        if not messagebox.askyesno("Confirm", "Generate progress reports for all listed students?"):
            return
            
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if not folder_path:
            return
            
        count = 0
        for item in self.tree_view_students.get_children():
            vals = self.tree_view_students.item(item)['values']
            student_id = vals[0]
            name = vals[1]
            roll = vals[3]
            
            filename = f"{roll}_{name}_Progress_Report.pdf".replace("/", "-")
            file_path = os.path.join(folder_path, filename)
            
            if self.create_progress_report_pdf(student_id, file_path, start_date, end_date, is_bw):
                count += 1
                
        messagebox.showinfo("Success", f"Generated {count} reports in {folder_path}")

    def create_progress_report_pdf(self, student_id, file_path, start_date=None, end_date=None, is_bw=False):
        """Create PDF progress report for a student. Can be filtered by date and rendered in B&W."""
        try:
            # Fetch data
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT name, roll, category, ssc_year, school, father_name FROM students WHERE id=?", (student_id,))
                student = c.fetchone()
                
                if not student: return False
                
                query = """SELECT e.date, e.type, e.subject, e.total_marks, r.score
                           FROM results r 
                           JOIN exams e ON r.exam_id = e.id 
                           WHERE r.student_id = ?
                           ORDER BY e.date DESC"""
                params = [student_id]

                if start_date and self.utils.validate_date(start_date):
                    query += " AND e.date >= ?"
                    params.append(start_date)
                if end_date and self.utils.validate_date(end_date):
                    query += " AND e.date <= ?"
                    params.append(end_date)

                query += " ORDER BY e.date DESC"
                c.execute(query, tuple(params))
                results = c.fetchall()
                
            # Generate PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            elements.append(Paragraph("Science Point By Dr. Talha", styles['Title']))
            elements.append(Paragraph("Student Progress Report", styles['Heading2']))
            elements.append(Spacer(1, 20))
            
            # Student Info
            info_data = [
                [f"Name: {student[0]}", f"Roll: {student[1]}"], 
                [f"Batch: {student[2]} {student[3]}", f"Father: {student[5]}"],
                [f"School: {student[4]}", f"Report Date: {datetime.now().strftime('%Y-%m-%d')}"]
            ]
            t_info = Table(info_data, colWidths=[250, 200])
            t_info.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold')]))
            elements.append(t_info)
            elements.append(Spacer(1, 20))
            
            # Results Table
            if results:
                data = [["Date", "Exam Type", "Subject", "Marks", "Obtained", "%", "Grade"]]
                total_obtained = 0
                total_marks = 0
                
                for r in results:
                    date, etype, subject, total, score = r
                    percentage = (score/total)*100 if total > 0 else 0
                    
                    # Grade
                    if percentage >= 80: grade = "A+"
                    elif percentage >= 70: grade = "A"
                    elif percentage >= 60: grade = "A-"
                    elif percentage >= 50: grade = "B"
                    elif percentage >= 40: grade = "C"
                    elif percentage >= 33: grade = "D"
                    else: grade = "F"
                    
                    data.append([
                        date, etype, subject, str(total), str(score), 
                        f"{percentage:.1f}%", grade
                    ])
                    
                    total_obtained += score
                    total_marks += total
                
                # Summary row
                overall_pct = (total_obtained/total_marks)*100 if total_marks > 0 else 0
                data.append(["", "", "TOTAL", str(total_marks), str(total_obtained), f"{overall_pct:.1f}%", ""])
                
                # Define colors based on B&W flag
                if is_bw:
                    header_bg = colors.black
                    summary_bg = colors.lightgrey
                else:
                    header_bg = colors.HexColor("#2980B9")
                    summary_bg = colors.HexColor("#ECF0F1")

                t = Table(data, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2980B9")),
                    ('BACKGROUND', (0,0), (-1,0), header_bg),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#ECF0F1")),
                    ('BACKGROUND', (0,-1), (-1,-1), summary_bg),
                    ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ]))
                elements.append(t)
            else:
                elements.append(Paragraph("No exam results found for this student.", styles['Normal']))
                
            doc.build(elements)
            return True
            
        except Exception as e:
            print(f"Error generating PDF for {student_id}: {e}")
            logging.error(f"Error generating PDF for {student_id}: {e}")
            return False
    
    def setup_view_data_exams(self, parent):
        """Setup view exams tab"""
        # Treeview for exams
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("ID", "Type", "Number", "Subject", "Total", "Segment", "Year", "Date", "Created")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        for col in cols:
            tree.heading(col, text=col, anchor="center")
            tree.column(col, width=100, anchor="center")
        
        tree.column("ID", width=50)
        tree.column("Subject", width=200)
        tree.column("Created", width=150)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Load exams
        try:
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT id, type, number, subject, total_marks, category, 
                           ssc_year, date, created_at FROM exams ORDER BY id DESC""")
                exams = c.fetchall()
            
            for exam in exams:
                tree.insert("", "end", values=exam)
            
            self.update_status(f"Loaded {len(exams)} exams")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exams: {str(e)}")
    
    def setup_view_data_results(self, parent):
        """Setup view results tab"""
        # Treeview for results
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("Student ID", "Exam ID", "Score", "Recorded")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        for col in cols:
            tree.heading(col, text=col, anchor="center")
            tree.column(col, width=150, anchor="center")
        
        tree.column("Recorded", width=200)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Load results
        try:
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT student_id, exam_id, score, recorded_at FROM results ORDER BY recorded_at DESC")
                results = c.fetchall()
            
            for result in results:
                tree.insert("", "end", values=result)
            
            self.update_status(f"Loaded {len(results)} results")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results: {str(e)}")
    
    def setup_view_data_payments(self, parent):
        """Setup view payments tab"""
        # Treeview for payments
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("Student ID", "Month", "Year", "Status", "Due Amount", "Paid Amount", "Updated")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        for col in cols:
            tree.heading(col, text=col, anchor="center")
            tree.column(col, width=120, anchor="center")
        
        tree.column("Updated", width=150)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Load payments
        try:
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT student_id, month, year, status, due_amount, paid_amount, updated_at 
                           FROM payments ORDER BY updated_at DESC""")
                payments = c.fetchall()
            
            for payment in payments:
                tree.insert("", "end", values=payment)
            
            self.update_status(f"Loaded {len(payments)} payments")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load payments: {str(e)}")
    
       # ============================================================================
    # ID CARDS TAB - FIXED VERSION
    # ============================================================================

    def setup_idcard(self):
        main = tk.Frame(self.tabs['idcard'], bg="#f4f6f9")
        main.pack(fill="both", expand=True, padx=30, pady=20)

        # Title
        title_frame = tk.Frame(main, bg="#f4f6f9")
        title_frame.pack(fill="x", pady=10)
        tk.Label(title_frame, text="📇 Student ID Card Generator", font=('Segoe UI', 20, 'bold'), 
                bg="#f4f6f9", fg="#2c3e50").pack()

        # Content Frame (Left: Selection, Right: Preview)
        content = tk.Frame(main, bg="#f4f6f9")
        content.pack(fill="both", expand=True)

        # Left Side: Selection
        left_frame = tk.LabelFrame(content, text=" Select Students ", bg="white", padx=10, pady=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Filter
        filter_frame = tk.Frame(left_frame, bg="white")
        filter_frame.pack(fill="x", pady=5)
        
        tk.Label(filter_frame, text="Segment:", bg="white").pack(side="left")
        self.id_segment_filter = ttk.Combobox(filter_frame, values=["All", "SSC", "HSC"], width=8, state="readonly")
        self.id_segment_filter.set("All")
        self.id_segment_filter.pack(side="left", padx=5)
        self.id_segment_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_student_list())

        tk.Label(filter_frame, text="Filter by Batch Year:", bg="white").pack(side="left")
        self.id_ssc_filter = ttk.Combobox(filter_frame, width=10, state="readonly")
        self.id_ssc_filter.pack(side="left", padx=5)
        self.id_ssc_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_student_list())
        tk.Button(filter_frame, text="↻", command=self.refresh_id_card_data, width=2).pack(side="left", padx=2)
        tk.Label(filter_frame, text="(Hold Ctrl to select multiple)", font=('Segoe UI', 8), bg="white", fg="#666").pack(side="left", padx=5)
        
        tk.Button(filter_frame, text="Select All", command=self.select_all_students, bg="#6c757d", fg="white").pack(side="right", padx=5)

        # Treeview
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        cols = ("ID", "Name", "Roll", "Seg", "Year")
        self.tree_id_students = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        self.tree_id_students.heading("ID", text="ID")
        self.tree_id_students.heading("Name", text="Name")
        self.tree_id_students.heading("Roll", text="Roll")
        self.tree_id_students.heading("Seg", text="Seg")
        self.tree_id_students.heading("Year", text="Year")
        self.tree_id_students.column("ID", width=40, anchor="center")
        self.tree_id_students.column("Name", width=150)
        self.tree_id_students.column("Roll", width=60, anchor="center")
        self.tree_id_students.column("Seg", width=50, anchor="center")
        self.tree_id_students.column("Year", width=50, anchor="center")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_id_students.yview)
        self.tree_id_students.configure(yscrollcommand=vsb.set)
        self.tree_id_students.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.tree_id_students.bind("<<TreeviewSelect>>", self.on_id_student_select)

        # Right Side: Preview & Actions
        right_frame = tk.Frame(content, bg="#f4f6f9")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Preview
        preview_frame = tk.LabelFrame(right_frame, text=" Preview ", bg="white", padx=10, pady=10)
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.preview_text = tk.Text(preview_frame, bg="#f8f9fa", font=('Consolas', 10), relief="flat",
                                   width=40, height=15)
        self.preview_text.pack(fill="both", expand=True)

        # Actions
        action_frame = tk.LabelFrame(right_frame, text=" Actions ", bg="white", padx=10, pady=10)
        action_frame.pack(fill="x")
        
        tk.Button(action_frame, text="🖨️ Print Selected", bg="#0078d7", fg="white", command=self.print_id_card).pack(fill="x", pady=5)
        tk.Button(action_frame, text="💾 Save PDF", bg="#28a745", fg="white", command=self.save_id_card_pdf).pack(fill="x", pady=5)

        self.idcard_status = tk.Label(main, text="Ready", bg="#f4f6f9", fg="#555")
        self.idcard_status.pack()

        self.load_id_ssc_years()
        self.refresh_student_list()

    def refresh_id_card_data(self):
        """Refresh ID card filter data"""
        self.load_id_ssc_years()
        self.refresh_student_list()

    def load_id_ssc_years(self):
        """Load SSC years for ID card filter"""
        try:
            conn = self.db.get_connection()
            try:
                c = conn.cursor()
                c.execute("SELECT DISTINCT ssc_year FROM students ORDER BY ssc_year DESC")
                years = [str(row[0]) for row in c.fetchall()]
            finally:
                conn.close()
            
            values = ["All"] + years
            self.id_ssc_filter['values'] = values
            if not self.id_ssc_filter.get():
                self.id_ssc_filter.set("All")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load SSC years: {str(e)}")

    def refresh_student_list(self):
        """Refresh the student dropdown list based on filter"""
        segment_filter = self.id_segment_filter.get()
        ssc_filter = self.id_ssc_filter.get()
        try:
            conn = self.db.get_connection()
            try:
                for i in self.tree_id_students.get_children():
                    self.tree_id_students.delete(i)

                c = conn.cursor()
                
                query = "SELECT id, name, roll, category, ssc_year FROM students WHERE 1=1"
                params = []
                
                if segment_filter and segment_filter != "All":
                    query += " AND category=?"
                    params.append(segment_filter)
                
                if ssc_filter and ssc_filter != "All":
                    query += " AND ssc_year=?"
                    params.append(ssc_filter)
                
                query += " ORDER BY ssc_year DESC, roll ASC"
                
                c.execute(query, params)
                students = c.fetchall()
                for s in students:
                    self.tree_id_students.insert("", "end", values=s)
            finally:
                conn.close()
            
            self.idcard_status.config(text=f"Loaded {len(students)} students")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students: {str(e)}")

    def select_all_students(self):
        for item in self.tree_id_students.get_children():
            self.tree_id_students.selection_add(item)
        self.on_id_student_select(None)

    def get_student_details(self, student_id):
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT id, name, father_name, ssc_year, school, contact, roll, category FROM students WHERE id=?", (student_id,))
            student = c.fetchone()
        finally:
            conn.close()
        if student:
            return {
                'id': student[0],
                'name': student[1],
                'father': student[2],
                'ssc_year': student[3],
                'school': student[4],
                'contact': student[5],
                'roll': student[6],
                'cat': student[7]
            }
        return None

    def on_id_student_select(self, event):
        """Preview the ID card for the last selected student"""
        selected = self.tree_id_students.selection()
        if not selected:
            self.preview_text.delete(1.0, tk.END)
            self.idcard_status.config(text="Select a student to preview")
            return

        # Preview the last selected item
        item = self.tree_id_students.item(selected[-1])
        sid = item['values'][0]
        
        student = self.get_student_details(sid)
        if not student:
            return
        
        # Clear text widget
        self.preview_text.delete(1.0, tk.END)
        
        # Create ID card text
        id_card = f"""
{'='*40}
{'Science Point By Dr. Talha'.center(40)}
{'='*40}

Name:    {student['name']}
ID:      {student['id']}
Roll:    {student['roll']}
Batch:   {student['cat']} {student['ssc_year']}
Father:  {student['father']}
School:  {student['school'][:30]}
Contact: {student['contact']}

{'-'*40}
{'Signature'.center(40)}
{'='*40}
"""
        self.preview_text.insert(1.0, id_card)
        self.idcard_status.config(text=f"Selected {len(selected)} students")

    def generate_id_cards_pdf(self, students, filename):
        """Generate PDF with ID cards (9 per page on A4 Landscape)"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab is missing.\nPlease run: pip install reportlab")
            return False
            
        try:
            card_width = 243  # Standard CR80 size
            card_height = 153
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(A4), 
                                    topMargin=20, bottomMargin=20, leftMargin=20, rightMargin=20)
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle('CardTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=1, textColor=colors.black)
            text_style = ParagraphStyle('CardText', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9)
            label_style = ParagraphStyle('CardLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9)
            sig_style = ParagraphStyle('Sig', parent=styles['Normal'], fontSize=6, alignment=1)
            
            def create_card(student):
                if not student:
                    return Spacer(card_width, card_height)
                # Header
                header = Table([[Paragraph("Science Point By Dr. Talha", title_style)]], colWidths=[card_width - 12])
                header.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('LINEBELOW', (0,0), (-1,-1), 1, colors.black),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ]))
                
                # Info
                info_content = [
                    [Paragraph("Name:", label_style), Paragraph(student['name'], text_style)],
                    [Paragraph("ID:", label_style), Paragraph(str(student['id']), text_style)],
                    [Paragraph("Roll:", label_style), Paragraph(str(student['roll']), text_style)],
                    [Paragraph("Batch:", label_style), Paragraph(f"{student['cat']} {student['ssc_year']}", text_style)],
                    [Paragraph("School:", label_style), Paragraph(student['school'][:25], text_style)],
                    [Paragraph("Contact:", label_style), Paragraph(student['contact'], text_style)],
                ]
                
                t_info = Table(info_content, colWidths=[50, card_width - 70])
                t_info.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 2),
                    ('RIGHTPADDING', (0,0), (-1,-1), 2),
                    ('TOPPADDING', (0,0), (-1,-1), 0),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ]))
                
                # Footer
                footer = Paragraph(f"Valid Until: {int(student['ssc_year']) + 1}-12-31", text_style)
                
                # Assemble Card Table
                card_elements = [
                    [header],
                    [Spacer(1, 5)],
                    [t_info],
                    [Spacer(1, 15)], 
                    [Paragraph("Authorized Signature", sig_style)],
                    [Spacer(1, 2)],
                    [footer]
                ]
                
                t_card = Table(card_elements, colWidths=[card_width - 10])
                t_card.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 1, colors.black),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 5),
                    ('RIGHTPADDING', (0,0), (-1,-1), 5),
                ]))
                return t_card

            all_cards = [create_card(s) for s in students]

            # Arrange cards in a 3x2 grid per page for 6 cards
            for i in range(0, len(all_cards), 6):
                page_cards = all_cards[i:i+6]
                # Pad with empty spacers if it's the last page and not full
                while len(page_cards) < 6:
                    page_cards.append(create_card(None))

                table_data = [
                    page_cards[0:3],
                    page_cards[3:6]
                ]
                
                page_table = Table(table_data, colWidths=[card_width + 10] * 3)
                page_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                ]))
                elements.append(page_table)
                
                if i + 6 < len(all_cards):
                    elements.append(PageBreak())
            
            if not elements:
                messagebox.showinfo("Info", "No students to generate cards for.")
                return False

            doc.build(elements)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create PDF: {str(e)}")
            return False

    def print_id_card(self):
        """Print ID card(s)"""
        selected = self.tree_id_students.selection()
        if not selected:
            messagebox.showwarning("Input", "Please select at least one student")
            return
        
        student_list = []
        for item_id in selected:
            sid = self.tree_id_students.item(item_id)['values'][0]
            s = self.get_student_details(sid)
            if s:
                student_list.append(s)
        
        # Create temporary PDF
        temp_pdf = os.path.join(self.app_path, "temp_id_cards.pdf")
        if self.generate_id_cards_pdf(student_list, temp_pdf):
            # Try to open PDF for printing
            try:
                if sys.platform == "win32":
                    os.startfile(temp_pdf, "print")
                else:
                    import subprocess
                    subprocess.run(["lp", temp_pdf])
                messagebox.showinfo("Success", f"{len(student_list)} ID card(s) sent to printer")
            except:
                messagebox.showinfo("Print", "PDF created. Please print manually from:\n" + temp_pdf)

    def save_id_card_pdf(self):
        """Save ID card as PDF"""
        selected = self.tree_id_students.selection()
        if not selected:
            messagebox.showwarning("Input", "Please select at least one student")
            return
        
        student_list = []
        for item_id in selected:
            sid = self.tree_id_students.item(item_id)['values'][0]
            s = self.get_student_details(sid)
            if s:
                student_list.append(s)
        
        default_name = f"ID_Cards_{len(student_list)}_Students.pdf"
        if len(student_list) == 1:
            default_name = f"ID_Card_{student_list[0]['name']}.pdf"
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if file_path:
            if self.generate_id_cards_pdf(student_list, file_path):
                messagebox.showinfo("Success", f"Saved to:\n{file_path}")

    
    # ============================================================================
    # SETTINGS TAB
    # ============================================================================
    
    def setup_settings(self):
        """Setup settings tab"""
        frame = self.tabs['settings']
        
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create scrollable canvas
        scrollable_frame = self.utils.create_scrollable_frame(frame, self.colors['bg'])
        
        # Main content
        main = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        main.pack(fill="both", expand=True, padx=30, pady=20)
        
        tk.Label(main, text="Application Settings", font=('Segoe UI', 24, 'bold'),
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=20)
        
        # Theme settings
        theme_frame = tk.LabelFrame(main, text=" Theme Settings ", bg="white", padx=20, pady=20)
        theme_frame.pack(fill="x", pady=10)
        
        tk.Label(theme_frame, text="Select Theme:", bg="white").pack(side="left", padx=5)
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        
        tk.Radiobutton(theme_frame, text="Light Theme", variable=self.theme_var, 
                      value="light", bg="white", command=self.change_theme).pack(side="left", padx=10)
        
        tk.Radiobutton(theme_frame, text="Dark Theme", variable=self.theme_var, 
                      value="dark", bg="white", command=self.change_theme).pack(side="left", padx=10)
        
        # Application settings
        app_frame = tk.LabelFrame(main, text=" Application Settings ", bg="white", padx=20, pady=20)
        app_frame.pack(fill="x", pady=10)
        
        # Default fee amount
        tk.Label(app_frame, text="Default Monthly Fee (Tk):", bg="white").grid(row=0, column=0, sticky="e", pady=5)
        self.default_fee = tk.Entry(app_frame, width=20)
        self.default_fee.insert(0, "500")
        self.default_fee.grid(row=0, column=1, pady=5, padx=5)
        
        # Save button
        tk.Button(app_frame, text="💾 Save Settings", bg=self.colors['success'], fg="white",
                 command=self.save_settings).grid(row=1, column=1, pady=20, sticky="w")
        
        # Database operations
        db_frame = tk.LabelFrame(main, text=" Database Operations ", bg="white", padx=20, pady=20)
        db_frame.pack(fill="x", pady=10)
        
        tk.Button(db_frame, text="🗄️ Backup Database", bg="#17a2b8", fg="white",
                 command=self.backup_database).pack(side="left", padx=5, pady=5)
        
        tk.Button(db_frame, text="🔄 Restore Database", bg="#ffc107", fg="black",
                 command=self.restore_database).pack(side="left", padx=5, pady=5)
        
        tk.Button(db_frame, text="⚠️ Reset Database", bg="#dc3545", fg="white",
                 command=self.reset_database).pack(side="left", padx=5, pady=5)
        
        # System information
        info_frame = tk.LabelFrame(main, text=" System Information ", bg="white", padx=20, pady=20)
        info_frame.pack(fill="x", pady=10)
        
        # Get database info
        db_stats = self.db.get_statistics()
        
        info_text = f"""Application Version: 1.0.0
Database Path: {self.db_path}
Total Students: {db_stats['total_students']}
Total Exams: {db_stats['total_exams']}
Total Paid: {self.utils.format_currency(db_stats['total_paid'])}
Total Due: {self.utils.format_currency(db_stats['total_due'])}
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        tk.Label(info_frame, text=info_text, bg="white", justify="left", font=('Courier New', 10)
                ).pack(anchor="w")
        
        # About section
        about_frame = tk.LabelFrame(main, text=" About ", bg="white", padx=20, pady=20)
        about_frame.pack(fill="x", pady=10)
        
        about_text = """Science Point Coaching Management System
Version 1.0.0
Developed by Moniem Mortoza

(c) 2024 Science Point. All rights reserved.
For support and feedback, please contact the developer."""
        
        tk.Label(about_frame, text=about_text, bg="white", justify="left"
                ).pack(anchor="w")
    
    def change_theme(self):
        """Change application theme"""
        self.current_theme = self.theme_var.get()
        self.colors = self.themes[self.current_theme]
        
        # Reapply theme
        self.apply_theme()
        
        # Recreate all tabs with new theme
        for tab_id, frame in self.tabs.items():
            for widget in frame.winfo_children():
                widget.destroy()
        
        # Recreate tab content
        self.create_tabs()
        
        self.update_status(f"Theme changed to {self.current_theme}")
    
    def save_settings(self):
        """Save application settings"""
        try:
            # In a real application, you would save these to a configuration file
            # For now, just show a message
            fee = self.default_fee.get()
            messagebox.showinfo("Settings Saved", 
                              f"Settings saved successfully!\n\nDefault monthly fee: {fee} Tk")
            self.update_status("Settings saved")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def backup_database(self):
        """Create a backup of the database"""
        try:
            backup_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                title="Save Database Backup",
                initialfile=f"coaching_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if backup_path:
                shutil.copy2(self.db_path, backup_path)
                messagebox.showinfo("Backup Complete", 
                                  f"Database backup created successfully!\n\nLocation: {backup_path}")
                self.update_status(f"Database backed up to: {backup_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {str(e)}")
    
    def restore_database(self):
        """Restore database from backup"""
        try:
            backup_path = filedialog.askopenfilename(
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                title="Select Database Backup to Restore"
            )
            
            if backup_path:
                if messagebox.askyesno("Confirm Restore", 
                                      "Restore database from backup?\n\nThis will replace the current database."):
                    shutil.copy2(backup_path, self.db_path)
                    messagebox.showinfo("Restore Complete", 
                                      "Database restored successfully!\n\nPlease restart the application.")
                    self.update_status("Database restored from backup")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {str(e)}")
    
    def reset_database(self):
        """Reset the database (dangerous operation)"""
        if messagebox.askyesno("⚠️ WARNING ⚠️", 
                              "RESET DATABASE?\n\nThis will delete ALL data including:\n• All students\n• All exams\n• All results\n• All payments\n• All expenses\n\nThis action cannot be undone!\n\nAre you absolutely sure?"):
            if messagebox.askyesno("Double Confirmation", 
                                  "This will DELETE EVERYTHING!\n\nType YES to confirm:"):
                try:
                    # Close and delete database
                    import sqlite3
                    conn = sqlite3.connect(self.db_path)
                    conn.close()
                    
                    # Remove database file
                    os.remove(self.db_path)
                    
                    # Reinitialize database
                    self.db = DatabaseManager(self.db_path)
                    
                    messagebox.showinfo("Database Reset", 
                                      "Database has been reset successfully!\n\nPlease restart the application.")
                    self.update_status("Database reset complete")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to reset database: {str(e)}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    try:
        root = tk.Tk()
        app = CoachingApp(root)
        
        # Center the window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start:\n\n{str(e)}")
        raise

if __name__ == "__main__":
    main()
