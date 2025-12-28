import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from io import BytesIO

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color


class PDFWatermarkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RonsTechHub PDF Watermarker")
        self.root.geometry("500x500")
        self.root.minsize(450, 480)  # Minimum size to keep UI readable

        # Theme State
        self.dark_mode = False
        self.colors = {
            "light": {"bg": "#ffffff", "fg": "#000000", "btn": "#f0f0f0", "accent": "#2c3e50", "border": "#cccccc"},
            "dark": {"bg": "#1e1e1e", "fg": "#ffffff", "btn": "#333333", "accent": "#3498db", "border": "#444444"}
        }

        # Load Logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "RTH Logo.png")
            self.logo_img = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(False, self.logo_img)
            # Higher subsample = smaller image. 16x16 makes it very compact.
            self.header_logo = self.logo_img.subsample(16, 16)
        except:
            self.header_logo = None

        self.selected_paths = []
        self.is_cancelled = False
        self.setup_main_ui()
        self.apply_theme()

    def setup_main_ui(self):
        # Master container that allows resizing
        self.container = tk.Frame(self.root, padx=30, pady=20)
        self.container.pack(expand=True, fill="both")

        # Top Bar for Theme Toggle
        self.top_bar = tk.Frame(self.container)
        self.top_bar.pack(fill="x", pady=(0, 10))

        self.theme_btn = tk.Button(self.top_bar, text="🌙 Switch Theme", font=("Arial", 9, "bold"),
                                   command=self.toggle_theme, padx=10, pady=5)
        self.theme_btn.pack(side="right")

        # Header Section (Logo + Text Inline)
        self.header_frame = tk.Frame(self.container)
        self.header_frame.pack(pady=10)

        if self.header_logo:
            self.logo_label = tk.Label(self.header_frame, image=self.header_logo)
            self.logo_label.pack(side="left", padx=10)

        self.title_label = tk.Label(self.header_frame, text="RonsTechHub PDF Watermarker",
                                    font=("Helvetica", 15, "bold"))
        self.title_label.pack(side="left")

        # Selection Buttons
        self.btn_frame = tk.Frame(self.container)
        self.btn_frame.pack(expand=True, pady=20)

        self.btn_single = tk.Button(self.btn_frame, text="Watermark Single File", width=30, height=2,
                                    command=self.select_file, font=("Arial", 10))
        self.btn_single.pack(pady=8)

        self.btn_folder = tk.Button(self.btn_frame, text="Watermark Entire Folder", width=30, height=2,
                                    command=self.select_folder, font=("Arial", 10))
        self.btn_folder.pack(pady=8)

        # Status and Progress
        self.path_label = tk.Label(self.container, text="Please select a file to begin",
                                   wraplength=400, font=("Arial", 9, "italic"))
        self.path_label.pack(pady=10)

        self.progress_label = tk.Label(self.container, text="Ready", font=("Arial", 9))
        self.progress_label.pack()

        self.progress = ttk.Progressbar(self.container, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10, fill="x")

        # Cancel Operation (Visible on load, but disabled)
        self.cancel_btn = tk.Button(self.container, text="Cancel Operation",
                                    state="disabled", font=("Arial", 10, "bold"),
                                    command=self.cancel_task, pady=5)
        self.cancel_btn.pack(pady=10, fill="x")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        mode = "dark" if self.dark_mode else "light"
        c = self.colors[mode]

        self.root.config(bg=c["bg"])
        self.container.config(bg=c["bg"])
        self.top_bar.config(bg=c["bg"])
        self.header_frame.config(bg=c["bg"])
        self.btn_frame.config(bg=c["bg"])

        if hasattr(self, 'logo_label'): self.logo_label.config(bg=c["bg"])
        self.title_label.config(bg=c["bg"], fg=c["fg"])
        self.path_label.config(bg=c["bg"], fg=c["accent"] if not self.dark_mode else "#aaaaaa")
        self.progress_label.config(bg=c["bg"], fg=c["fg"])

        self.btn_single.config(bg=c["btn"], fg=c["fg"], highlightbackground=c["border"])
        self.btn_folder.config(bg=c["btn"], fg=c["fg"], highlightbackground=c["border"])

        # Theme Button Styling
        self.theme_btn.config(bg=c["accent"], fg="#ffffff", activebackground=c["fg"])

        # Cancel Button Styling
        if self.cancel_btn['state'] == 'normal':
            self.cancel_btn.config(bg="#e74c3c", fg="white")
        else:
            self.cancel_btn.config(bg=c["btn"], fg="#888888")

    def activate_controls(self):
        """Enable the cancel button once a selection is made."""
        self.cancel_btn.config(state="normal")
        self.apply_theme()  # Refresh colors for active state

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.selected_paths = [file_path]
            self.path_label.config(text=f"Selected: {os.path.basename(file_path)}")
            self.activate_controls()
            self.open_config_dialog()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                     if f.lower().endswith('.pdf')]
            if not files:
                messagebox.showwarning("No PDFs", "No PDF files found.")
                return
            self.selected_paths = files
            self.path_label.config(text=f"Folder: {folder_path}\n({len(files)} files found)")
            self.activate_controls()
            self.open_config_dialog()

    def open_config_dialog(self):
        config_win = tk.Toplevel(self.root)
        config_win.title("Watermark Config")
        config_win.geometry("350x420")
        config_win.grab_set()

        mode = "dark" if self.dark_mode else "light"
        c = self.colors[mode]
        config_win.config(bg=c["bg"])

        tk.Label(config_win, text="Watermark Text:", bg=c["bg"], fg=c["fg"], font=("Arial", 10, "bold")).pack(pady=10)
        text_entry = tk.Entry(config_win, width=25, font=("Arial", 12), justify="center",
                              bg=c["btn"], fg=c["fg"], insertbackground=c["fg"])
        text_entry.insert(0, "RonsTechHub")
        text_entry.pack(pady=5)

        tk.Label(config_win, text="Click a position to start:", bg=c["bg"], fg=c["fg"]).pack(pady=10)

        grid_frame = tk.Frame(config_win, bg=c["bg"])
        grid_frame.pack(pady=10)

        positions = [
            ("Top Left", 0, 0), ("Top Center", 0, 1), ("Top Right", 0, 2),
            ("Mid Left", 1, 0), ("Mid Center", 1, 1), ("Mid Right", 1, 2),
            ("Bot Left", 2, 0), ("Bot Center", 2, 1), ("Bot Right", 2, 2)
        ]

        for (name, r, c_idx) in positions:
            btn = tk.Button(grid_frame, text=name, width=10, height=2, bg=c["btn"], fg=c["fg"],
                            command=lambda p=name: self.start_processing(text_entry.get(), p, config_win))
            btn.grid(row=r, column=c_idx, padx=3, pady=3)

    def start_processing(self, text, position, dialog):
        dialog.destroy()
        self.is_cancelled = False
        thread = threading.Thread(target=self.process_files, args=(text, position))
        thread.daemon = True
        thread.start()

    def cancel_task(self):
        self.is_cancelled = True
        self.cancel_btn.config(state="disabled")
        self.apply_theme()

    def create_watermark_layer(self, text, position, page_width, page_height):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        can.setFont("Helvetica-Bold", 60)
        can.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.3))

        margin = 60
        x_map = {"Left": margin, "Center": float(page_width) / 2, "Right": float(page_width) - margin}
        y_map = {"Top": float(page_height) - margin, "Mid": float(page_height) / 2, "Bot": margin}

        parts = position.split()
        y_key, x_key = parts[0], parts[1]

        x = x_map.get(x_key, float(page_width) / 2)
        y = y_map.get(y_key, float(page_height) / 2)

        can.drawCentredString(x, y, text)
        can.save()
        packet.seek(0)
        return packet

    def process_files(self, watermark_text, position):
        total = len(self.selected_paths)
        self.root.after(0, lambda: self.progress.configure(maximum=total))

        for i, path in enumerate(self.selected_paths):
            if self.is_cancelled: break

            try:
                filename = os.path.basename(path)
                self.root.after(0, lambda v=i + 1, f=filename: self.update_status(v, total, f))

                reader = PdfReader(path)
                writer = PdfWriter()

                for page in reader.pages:
                    w_packet = self.create_watermark_layer(watermark_text, position,
                                                           page.mediabox.width, page.mediabox.height)
                    watermark_page = PdfReader(w_packet).pages[0]
                    page.merge_page(watermark_page)
                    writer.add_page(page)

                output_path = path.replace(".pdf", "_watermarked.pdf")
                with open(output_path, "wb") as f:
                    writer.write(f)

            except Exception as e:
                self.root.after(0, lambda m=str(e): messagebox.showerror("File Error", f"Error: {m}"))

        self.root.after(0, self.finish_processing)

    def update_status(self, val, total, filename):
        self.progress['value'] = val
        self.progress_label.config(text=f"Processing {val} of {total}: {filename}")

    def finish_processing(self):
        if not self.is_cancelled:
            self.progress_label.config(text="Status: Successfully Completed")
            messagebox.showinfo("Done", "All watermarked files have been created.")
        else:
            self.progress_label.config(text="Status: Process Cancelled")

        # Reset cancel button state for next run
        self.cancel_btn.config(state="disabled")
        self.apply_theme()


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFWatermarkerApp(root)
    root.mainloop()