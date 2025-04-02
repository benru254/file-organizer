import os
import shutil
import fnmatch
import logging
import threading
from tkinter import *
from tkinter import ttk, filedialog, messagebox, simpledialog

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class FileSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer Pro")
        self.root.geometry("800x600")
        self.setup_ui()
        
        # Initialize variables
        self.source_folder = ""
        self.dest_folder = ""
        self.keyword_groups = {}  # Format: {"Folder Name": ["keyword1", "keyword2"]}
        self.operation = "copy"
        self.min_size = 0  # in bytes
        self.max_size = 1024 * 1024 * 100  # 100 MB

    def setup_ui(self):
        # Configure theme colors
        self.root.configure(bg="#f0f0f0")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True)

        # Tab 1: Source & Destination
        self.tab1 = Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab1, text="Folders")
        self.setup_folder_ui()

        # Tab 2: Keywords & Settings
        self.tab2 = Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab2, text="Settings")
        self.setup_settings_ui()

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient=HORIZONTAL, mode='determinate')
        self.progress.pack(fill=X, padx=10, pady=5)

        # Log Window
        self.log_window = Text(self.root, height=10, width=100)
        self.log_window.pack(fill=BOTH, padx=10, pady=10)

    def setup_folder_ui(self):
        # Source Folder
        Label(self.tab1, text="Source Folder:", bg="#f0f0f0").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        self.source_label = Label(self.tab1, text="Not Selected", fg="blue", bg="#f0f0f0")
        self.source_label.grid(row=0, column=1, padx=10, pady=10)
        Button(self.tab1, text="Browse", command=self.select_source).grid(row=0, column=2, padx=10, pady=10)

        # Destination Folder
        Label(self.tab1, text="Destination Folder:", bg="#f0f0f0").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        self.dest_label = Label(self.tab1, text="Not Selected", fg="blue", bg="#f0f0f0")
        self.dest_label.grid(row=1, column=1, padx=10, pady=10)
        Button(self.tab1, text="Browse", command=self.select_dest).grid(row=1, column=2, padx=10, pady=10)

    def setup_settings_ui(self):
        # Keyword Groups
        Label(self.tab2, text="Keyword Groups (e.g., 'cash sale: cash, sale')", bg="#f0f0f0").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        self.keyword_text = Text(self.tab2, height=5, width=50)
        self.keyword_text.grid(row=0, column=1, padx=10, pady=10)
        self.keyword_text.insert(END, "cash sale: cash, cashsale\ninvoice: inv, invoice")

        # File Size Filter
        Label(self.tab2, text="File Size Filter (MB):", bg="#f0f0f0").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        self.size_slider = Scale(self.tab2, from_=0, to=100, orient=HORIZONTAL)
        self.size_slider.grid(row=1, column=1, padx=10, pady=10)

        # Operation Type
        Label(self.tab2, text="Operation:", bg="#f0f0f0").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        self.operation_var = StringVar(value="copy")
        Radiobutton(self.tab2, text="Copy", variable=self.operation_var, value="copy", bg="#f0f0f0").grid(row=2, column=1, sticky=W)
        Radiobutton(self.tab2, text="Move", variable=self.operation_var, value="move", bg="#f0f0f0").grid(row=2, column=1, sticky=E)

        # Run Button
        Button(self.tab2, text="Start Organizing", command=self.start_process).grid(row=3, column=1, pady=20)

    def select_source(self):
        self.source_folder = filedialog.askdirectory(title="Select Source Folder")
        self.source_label.config(text=self.source_folder)

    def select_dest(self):
        self.dest_folder = filedialog.askdirectory(title="Select Destination Folder")
        self.dest_label.config(text=self.dest_folder)

    def start_process(self):
        # Parse keyword groups
        self.keyword_groups = {}
        lines = self.keyword_text.get("1.0", END).split("\n")
        for line in lines:
            if ":" in line:
                folder, keywords = line.split(":", 1)
                self.keyword_groups[folder.strip()] = [kw.strip() for kw in keywords.split(",")]

        # Validate inputs
        if not self.source_folder or not self.dest_folder or not self.keyword_groups:
            messagebox.showerror("Error", "Please fill all fields!")
            return

        # Start processing in a new thread
        threading.Thread(target=self.process_files).start()

    def process_files(self):
        try:
            total_files = 0
            processed_files = 0

            # Count total files for progress bar
            for root, _, files in os.walk(self.source_folder):
                total_files += len(files)

            # Process files
            for root, _, files in os.walk(self.source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)

                    # Check file size
                    if file_size < self.min_size * 1024 * 1024 or file_size > self.max_size * 1024 * 1024:
                        continue

                    # Check keywords
                    for folder_name, keywords in self.keyword_groups.items():
                        if any(fnmatch.fnmatch(file.lower(), f"*{kw}*") for kw in keywords):
                            # Create subfolder
                            final_dest = os.path.join(self.dest_folder, folder_name)
                            os.makedirs(final_dest, exist_ok=True)

                            # Sort by file type
                            file_ext = os.path.splitext(file)[1][1:].upper()
                            file_type_folder = os.path.join(final_dest, file_ext if file_ext else "OTHERS")
                            os.makedirs(file_type_folder, exist_ok=True)

                            dest_path = os.path.join(file_type_folder, file)

                            # Copy/move file
                            if not os.path.exists(dest_path):
                                try:
                                    if self.operation_var.get() == "copy":
                                        shutil.copy2(file_path, dest_path)
                                        self.log(f"Copied: {file}")
                                    else:
                                        shutil.move(file_path, dest_path)
                                        self.log(f"Moved: {file}")
                                except Exception as e:
                                    self.log(f"Error: {file} → {str(e)}")

                    # Update progress
                    processed_files += 1
                    self.progress["value"] = (processed_files / total_files) * 100

            self.log("✅ All files processed!")
        except Exception as e:
            self.log(f"🚨 Critical Error: {str(e)}")

    def log(self, message):
        self.log_window.insert(END, message + "\n")
        self.log_window.see(END)

if __name__ == "__main__":
    root = Tk()
    app = FileSorterApp(root)
    root.mainloop()