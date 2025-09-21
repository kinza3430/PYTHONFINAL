import os
import shutil
import logging
import schedule
import time
import threading
import json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

class FileOrganizer:
    def __init__(self):
        # Define file categories and their extensions
        self.categories = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
            'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
            'Documents': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.pptx', '.csv', '.rtf', '.odt'],
            'Music': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.json', '.xml'],
            'Executables': ['.exe', '.msi', '.bat', '.sh', '.deb', '.rpm'],
            'Others': []  # For any other file types
        }
        
        # Create the main application window
        self.root = tk.Tk()
        self.root.title("Advanced File Organizer")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.configure(bg='#f5f5f5')
        
        # Variables
        self.source_path = tk.StringVar()
        self.schedule_minutes = tk.IntVar(value=5)
        self.organizing = False
        self.scheduler_running = False
        self.scheduler_thread = None
        self.move_history = []
        
        # Load previous state if available
        self.load_state()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Organizer Tab
        organizer_frame = ttk.Frame(notebook, padding=10)
        notebook.add(organizer_frame, text='File Organizer')
        
        # Settings Tab
        settings_frame = ttk.Frame(notebook, padding=10)
        notebook.add(settings_frame, text='Settings')
        
        # Log Tab
        log_frame = ttk.Frame(notebook, padding=10)
        notebook.add(log_frame, text='Logs')
        
        # Build each tab
        self.build_organizer_tab(organizer_frame)
        self.build_settings_tab(settings_frame)
        self.build_log_tab(log_frame)
        
    def build_organizer_tab(self, parent):
        # Header
        header = tk.Label(
            parent, 
            text="File Organizer", 
            font=("Arial", 18, "bold"),
            bg='#f5f5f5',
            fg='#2c3e50'
        )
        header.pack(pady=10)
        
        # Description
        desc = tk.Label(
            parent,
            text="Automatically organize your files into categories",
            font=("Arial", 10),
            bg='#f5f5f5',
            fg='#7f8c8d'
        )
        desc.pack(pady=5)
        
        # Folder selection frame
        folder_frame = tk.Frame(parent, bg='#f5f5f5')
        folder_frame.pack(pady=15, padx=10, fill='x')
        
        tk.Label(
            folder_frame,
            text="Source Folder:",
            font=("Arial", 10, "bold"),
            bg='#f5f5f5',
            fg='#34495e'
        ).pack(anchor='w')
        
        path_frame = tk.Frame(folder_frame, bg='#f5f5f5')
        path_frame.pack(fill='x', pady=5)
        
        tk.Entry(
            path_frame,
            textvariable=self.source_path,
            font=("Arial", 10),
        ).pack(side='left', fill='x', expand=True, ipady=3)
        
        tk.Button(
            path_frame,
            text="Browse",
            command=self.browse_folder,
            bg='#3498db',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15
        ).pack(side='right', padx=(5, 0))
        
        # Categories frame
        cat_frame = tk.LabelFrame(
            parent,
            text="File Categories",
            font=("Arial", 11, "bold"),
            bg='#f5f5f5',
            fg='#34495e'
        )
        cat_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Create a canvas and scrollbar for the categories
        canvas = tk.Canvas(cat_frame, bg='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(cat_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f5')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add category labels
        row = 0
        for category, extensions in self.categories.items():
            if category == 'Others':
                continue
                
            tk.Label(
                scrollable_frame,
                text=f"{category}:",
                font=("Arial", 9, "bold"),
                bg='#f5f5f5',
                fg='#2c3e50',
                width=12,
                anchor='w'
            ).grid(row=row, column=0, sticky='w', padx=5, pady=2)
            
            ext_text = ", ".join(extensions)
            tk.Label(
                scrollable_frame,
                text=ext_text,
                font=("Arial", 9),
                bg='#f5f5f5',
                fg='#7f8c8d',
                wraplength=500,
                justify='left'
            ).grid(row=row, column=1, sticky='w', padx=5, pady=2)
            
            row += 1
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = tk.Frame(parent, bg='#f5f5f5')
        button_frame.pack(pady=15, fill='x')
        
        # Organize button
        self.organize_btn = tk.Button(
            button_frame,
            text="Organize Files",
            command=self.organize_files,
            bg='#2ecc71',
            fg='white',
            font=("Arial", 12, "bold"),
            relief='flat',
            padx=20,
            pady=10
        )
        self.organize_btn.pack(side='left', padx=5)
        
        # Undo button
        self.undo_btn = tk.Button(
            button_frame,
            text="Undo Last Organization",
            command=self.undo_last_organization,
            bg='#e74c3c',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15,
            pady=8,
            state='disabled'
        )
        self.undo_btn.pack(side='left', padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            parent,
            orient='horizontal',
            length=500,
            mode='determinate'
        )
        self.progress.pack(pady=10, fill='x', padx=10)
        
        # Status label
        self.status = tk.Label(
            parent,
            text="Select a folder to organize",
            font=("Arial", 9),
            bg='#f5f5f5',
            fg='#7f8c8d'
        )
        self.status.pack(pady=5)
        
    def build_settings_tab(self, parent):
        # Header
        header = tk.Label(
            parent, 
            text="Scheduler Settings", 
            font=("Arial", 18, "bold"),
            bg='#f5f5f5',
            fg='#2c3e50'
        )
        header.pack(pady=10)
        
        # Scheduler frame
        scheduler_frame = tk.Frame(parent, bg='#f5f5f5')
        scheduler_frame.pack(pady=15, padx=10, fill='x')
        
        tk.Label(
            scheduler_frame,
            text="Run automatically every:",
            font=("Arial", 10, "bold"),
            bg='#f5f5f5',
            fg='#34495e'
        ).pack(anchor='w', pady=5)
        
        # Minutes selection
        minutes_frame = tk.Frame(scheduler_frame, bg='#f5f5f5')
        minutes_frame.pack(fill='x', pady=5)
        
        tk.Entry(
            minutes_frame,
            textvariable=self.schedule_minutes,
            font=("Arial", 10),
            width=5
        ).pack(side='left')
        
        tk.Label(
            minutes_frame,
            text="minutes",
            font=("Arial", 10),
            bg='#f5f5f5',
            fg='#34495e'
        ).pack(side='left', padx=5)
        
        # Scheduler buttons frame
        scheduler_btn_frame = tk.Frame(scheduler_frame, bg='#f5f5f5')
        scheduler_btn_frame.pack(pady=10, fill='x')
        
        self.start_scheduler_btn = tk.Button(
            scheduler_btn_frame,
            text="Start Scheduler",
            command=self.start_scheduler,
            bg='#3498db',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15,
            pady=5
        )
        self.start_scheduler_btn.pack(side='left', padx=5)
        
        self.stop_scheduler_btn = tk.Button(
            scheduler_btn_frame,
            text="Stop Scheduler",
            command=self.stop_scheduler,
            bg='#e74c3c',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            state='disabled'
        )
        self.stop_scheduler_btn.pack(side='left', padx=5)
        
        # Scheduler status
        self.scheduler_status = tk.Label(
            scheduler_frame,
            text="Scheduler is not running",
            font=("Arial", 9),
            bg='#f5f5f5',
            fg='#e74c3c'
        )
        self.scheduler_status.pack(anchor='w', pady=5)
        
        # History frame
        history_frame = tk.LabelFrame(
            parent,
            text="Organization History",
            font=("Arial", 11, "bold"),
            bg='#f5f5f5',
            fg='#34495e'
        )
        history_frame.pack(pady=15, padx=10, fill='both', expand=True)
        
        # History listbox
        self.history_listbox = tk.Listbox(
            history_frame,
            height=8,
            font=("Arial", 9)
        )
        self.history_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Populate history
        self.update_history_listbox()
        
    def build_log_tab(self, parent):
        # Header
        header = tk.Label(
            parent, 
            text="Organization Log", 
            font=("Arial", 18, "bold"),
            bg='#f5f5f5',
            fg='#2c3e50'
        )
        header.pack(pady=10)
        
        # Log text area
        log_text_frame = tk.Frame(parent, bg='#f5f5f5')
        log_text_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_text_frame,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill='both', expand=True)
        self.log_text.config(state='disabled')
        
        # Log buttons frame
        log_btn_frame = tk.Frame(parent, bg='#f5f5f5')
        log_btn_frame.pack(pady=10, fill='x')
        
        tk.Button(
            log_btn_frame,
            text="Refresh Log",
            command=self.refresh_log_display,
            bg='#3498db',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)
        
        tk.Button(
            log_btn_frame,
            text="Clear Log",
            command=self.clear_log,
            bg='#e74c3c',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)
        
        tk.Button(
            log_btn_frame,
            text="Open Log File",
            command=self.view_log_file,
            bg='#2ecc71',
            fg='white',
            font=("Arial", 10, "bold"),
            relief='flat',
            padx=15,
            pady=5
        ).pack(side='left', padx=5)
        
        # Refresh log display initially
        self.refresh_log_display()
        
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_path.set(folder_selected)
            self.status.config(text="Ready to organize files")
            
    def organize_files(self):
        if self.organizing:
            return
            
        source = self.source_path.get()
        if not source:
            messagebox.showerror("Error", "Please select a folder first")
            return
            
        self.organizing = True
        self.organize_btn.config(state='disabled', text="Organizing...")
        self.status.config(text="Organizing files...")
        self.root.update()
        
        try:
            # Get all files in the source directory
            files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
            total_files = len(files)
            
            if total_files == 0:
                messagebox.showinfo("Info", "No files found to organize")
                self.organizing = False
                self.organize_btn.config(state='normal', text="Organize Files")
                self.status.config(text="No files found to organize")
                return
                
            self.progress['maximum'] = total_files
            moved_count = 0
            move_operations = []
            
            for i, filename in enumerate(files):
                file_path = os.path.join(source, filename)
                
                # Skip if it's a directory
                if os.path.isdir(file_path):
                    continue
                    
                # Get file extension
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                # Find the category for this file
                category = 'Others'
                for cat, exts in self.categories.items():
                    if ext in exts:
                        category = cat
                        break
                
                # Create category directory if it doesn't exist
                category_dir = os.path.join(source, category)
                if not os.path.exists(category_dir):
                    os.makedirs(category_dir)
                
                # Move the file
                try:
                    dest_path = os.path.join(category_dir, filename)
                    shutil.move(file_path, dest_path)
                    moved_count += 1
                    
                    # Record the move operation for undo
                    move_operations.append({
                        'filename': filename,
                        'source': source,
                        'destination': category_dir,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Log the action
                    logging.info(f"Moved: {filename} -> {category}")
                    
                except Exception as e:
                    logging.error(f"Error moving {filename}: {str(e)}")
                
                # Update progress
                self.progress['value'] = i + 1
                self.status.config(text=f"Processed {i+1} of {total_files} files")
                self.root.update()
            
            # Add to history if files were moved
            if move_operations:
                self.move_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'source': source,
                    'operations': move_operations,
                    'total_moved': moved_count,
                    'total_files': total_files
                })
                self.save_state()
                self.update_history_listbox()
                self.undo_btn.config(state='normal')
            
            # Show completion message
            messagebox.showinfo("Complete", f"Organized {moved_count} of {total_files} files")
            self.status.config(text=f"Organized {moved_count} of {total_files} files")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            logging.error(f"Organization error: {str(e)}")
            self.status.config(text="Error occurred during organization")
            
        finally:
            self.organizing = False
            self.organize_btn.config(state='normal', text="Organize Files")
            self.progress['value'] = 0
            self.refresh_log_display()
            
    def undo_last_organization(self):
        if not self.move_history:
            messagebox.showinfo("Info", "No organization history to undo")
            return
            
        last_organization = self.move_history.pop()
        operations = last_organization['operations']
        total_operations = len(operations)
        
        self.progress['maximum'] = total_operations
        self.progress['value'] = 0
        self.status.config(text="Undoing last organization...")
        self.root.update()
        
        restored_count = 0
        
        for i, operation in enumerate(operations):
            try:
                source_file = os.path.join(operation['destination'], operation['filename'])
                dest_path = os.path.join(operation['source'], operation['filename'])
                
                if os.path.exists(source_file):
                    shutil.move(source_file, dest_path)
                    restored_count += 1
                    logging.info(f"Undo: Moved {operation['filename']} back to original location")
                
            except Exception as e:
                logging.error(f"Error during undo for {operation['filename']}: {str(e)}")
            
            self.progress['value'] = i + 1
            self.root.update()
        
        # Update UI
        self.save_state()
        self.update_history_listbox()
        self.refresh_log_display()
        
        if not self.move_history:
            self.undo_btn.config(state='disabled')
            
        messagebox.showinfo("Undo Complete", f"Restored {restored_count} of {total_operations} files")
        self.status.config(text=f"Undo complete: {restored_count} files restored")
        self.progress['value'] = 0
        
    def start_scheduler(self):
        minutes = self.schedule_minutes.get()
        if minutes <= 0:
            messagebox.showerror("Error", "Please enter a valid number of minutes")
            return
            
        if not self.source_path.get():
            messagebox.showerror("Error", "Please select a folder first")
            return
            
        self.scheduler_running = True
        self.start_scheduler_btn.config(state='disabled')
        self.stop_scheduler_btn.config(state='normal')
        self.scheduler_status.config(text=f"Scheduler running every {minutes} minutes", fg='#2ecc71')
        
        # Clear any existing schedule
        schedule.clear()
        
        # Schedule the task
        schedule.every(minutes).minutes.do(self.scheduled_organization)
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logging.info(f"Scheduler started. Will run every {minutes} minutes.")
        self.refresh_log_display()
        
    def stop_scheduler(self):
        self.scheduler_running = False
        self.start_scheduler_btn.config(state='normal')
        self.stop_scheduler_btn.config(state='disabled')
        self.scheduler_status.config(text="Scheduler is not running", fg='#e74c3c')
        
        logging.info("Scheduler stopped.")
        self.refresh_log_display()
        
    def scheduler_loop(self):
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)
            
    def scheduled_organization(self):
        # This method runs on the scheduler thread
        logging.info("Scheduled organization started")
        
        # Use after() to schedule UI updates on the main thread
        self.root.after(0, lambda: self.status.config(text="Running scheduled organization..."))
        self.root.after(0, lambda: self.organize_btn.config(state='disabled', text="Organizing..."))
        
        try:
            source = self.source_path.get()
            files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
            total_files = len(files)
            
            if total_files == 0:
                logging.info("Scheduled organization: No files to organize")
                return
                
            moved_count = 0
            move_operations = []
            
            for filename in files:
                file_path = os.path.join(source, filename)
                
                if os.path.isdir(file_path):
                    continue
                    
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                category = 'Others'
                for cat, exts in self.categories.items():
                    if ext in exts:
                        category = cat
                        break
                
                category_dir = os.path.join(source, category)
                if not os.path.exists(category_dir):
                    os.makedirs(category_dir)
                
                try:
                    dest_path = os.path.join(category_dir, filename)
                    shutil.move(file_path, dest_path)
                    moved_count += 1
                    
                    move_operations.append({
                        'filename': filename,
                        'source': source,
                        'destination': category_dir,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logging.info(f"Scheduled move: {filename} -> {category}")
                    
                except Exception as e:
                    logging.error(f"Error in scheduled move for {filename}: {str(e)}")
            
            if move_operations:
                self.move_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'source': source,
                    'operations': move_operations,
                    'total_moved': moved_count,
                    'total_files': total_files
                })
                self.save_state()
                
                # Update UI on main thread
                self.root.after(0, self.update_history_listbox)
                self.root.after(0, lambda: self.undo_btn.config(state='normal'))
                
            logging.info(f"Scheduled organization complete: {moved_count} files moved")
            
        except Exception as e:
            logging.error(f"Error in scheduled organization: {str(e)}")
            
        finally:
            # Update UI on main thread
            self.root.after(0, lambda: self.organize_btn.config(state='normal', text="Organize Files"))
            self.root.after(0, lambda: self.status.config(
                text=f"Scheduled organization complete: {moved_count} files moved"
            ))
            self.root.after(0, self.refresh_log_display)
            
    def update_history_listbox(self):
        self.history_listbox.delete(0, tk.END)
        
        for i, history in enumerate(reversed(self.move_history)):
            timestamp = datetime.fromisoformat(history['timestamp']).strftime("%Y-%m-%d %H:%M")
            self.history_listbox.insert(0, f"{timestamp}: {history['total_moved']} files moved in {history['source']}")
            
    def refresh_log_display(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        
        if os.path.exists('organizer_log.txt'):
            with open('organizer_log.txt', 'r') as f:
                log_content = f.read()
                self.log_text.insert(tk.END, log_content)
        
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)
        
    def clear_log(self):
        try:
            with open('organizer_log.txt', 'w') as f:
                f.write("")
            self.refresh_log_display()
            logging.info("Log file cleared by user")
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear log file: {str(e)}")
            
    def view_log_file(self):
        if os.path.exists('organizer_log.txt'):
            os.startfile('organizer_log.txt')
        else:
            messagebox.showinfo("Info", "No log file found yet.")
            
    def save_state(self):
        state = {
            'source_path': self.source_path.get(),
            'move_history': self.move_history,
            'schedule_minutes': self.schedule_minutes.get()
        }
        
        with open('organizer_state.json', 'w') as f:
            json.dump(state, f)
            
    def load_state(self):
        try:
            if os.path.exists('organizer_state.json'):
                with open('organizer_state.json', 'r') as f:
                    state = json.load(f)
                    
                self.source_path.set(state.get('source_path', ''))
                self.move_history = state.get('move_history', [])
                self.schedule_minutes.set(state.get('schedule_minutes', 5))
                
        except Exception as e:
            print(f"Error loading state: {str(e)}")
            
    def run(self):
        # Set up logging
        logging.basicConfig(
            filename='organizer_log.txt',
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        logging.info("File Organizer started")
        
        # Start the application
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        self.stop_scheduler()
        self.save_state()
        self.root.destroy()

# Run the application
if __name__ == "__main__":
    app = FileOrganizer()
    app.run()