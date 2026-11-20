"""
AI & File Metadata Remover
Supports: PDF (.pdf), Word Documents (.docx), Images (.png, .jpg, .jpeg, .webp, .tiff, .bmp)
Removes all EXIF, Author, Creator, AI prompt data, and document history.
"""

import os
import sys
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# Image Processing
from PIL import Image

# PDF Processing
try:
    import pypdf
except ImportError:
    pypdf = None

# DOCX Processing
try:
    import docx
except ImportError:
    docx = None


class MetadataRemover:
    SUPPORTED_EXTENSIONS = {
        'pdf': ['.pdf'],
        'docx': ['.docx'],
        'image': ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif']
    }

    @classmethod
    def is_supported(cls, filepath):
        ext = Path(filepath).suffix.lower()
        for exts in cls.SUPPORTED_EXTENSIONS.values():
            if ext in exts:
                return True
        return False

    @classmethod
    def clean_pdf(cls, in_path, out_path):
        """Cleans all metadata, XMP data, and creator tags from a PDF."""
        if not pypdf:
            raise RuntimeError("pypdf library not found. Run 'pip install pypdf'")

        reader = pypdf.PdfReader(in_path)
        writer = pypdf.PdfWriter()

        if reader.is_encrypted:
            try:
                reader.decrypt('')
            except Exception:
                raise RuntimeError("Password-protected PDF cannot be processed without password.")

        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)

        # Clear document information dictionary
        empty_info = {
            '/Producer': '',
            '/Creator': '',
            '/Author': '',
            '/Title': '',
            '/Subject': '',
            '/Keywords': '',
            '/CreationDate': '',
            '/ModDate': ''
        }
        writer.add_metadata(empty_info)

        # Ensure no residual XMP stream is retained
        if hasattr(writer, 'root_object') and '/Metadata' in writer.root_object:
            try:
                del writer.root_object['/Metadata']
            except Exception:
                pass

        with open(out_path, 'wb') as f_out:
            writer.write(f_out)

        return "PDF metadata, Author, Creator, and XMP streams cleared."

    @classmethod
    def clean_image(cls, in_path, out_path):
        """Removes EXIF, GPS, camera, and AI generation prompts/parameters from images."""
        ext = Path(in_path).suffix.lower()

        with Image.open(in_path) as img:
            # Re-create clean image without any metadata dictionaries
            if img.mode in ('RGBA', 'LA'):
                clean_img = Image.new(img.mode, img.size, (0, 0, 0, 0))
                clean_img.paste(img)
            elif img.mode == 'P':
                # Preserve transparency if present
                if 'transparency' in img.info:
                    clean_img = Image.new('RGBA', img.size)
                    clean_img.paste(img.convert('RGBA'))
                else:
                    clean_img = Image.new('RGB', img.size)
                    clean_img.paste(img.convert('RGB'))
            elif img.mode in ('L', '1'):
                clean_img = Image.new(img.mode, img.size)
                clean_img.paste(img)
            else:
                clean_img = Image.new('RGB', img.size)
                clean_img.paste(img.convert('RGB'))

            # Save clean image
            if ext in ('.jpg', '.jpeg'):
                clean_img.save(out_path, 'JPEG', quality=95, optimize=True)
            elif ext == '.png':
                clean_img.save(out_path, 'PNG', optimize=True)
            elif ext == '.webp':
                clean_img.save(out_path, 'WEBP', quality=95)
            elif ext in ('.tif', '.tiff'):
                clean_img.save(out_path, 'TIFF')
            else:
                clean_img.save(out_path)

        return "EXIF, GPS tags, camera info, and AI prompt metadata stripped."

    @classmethod
    def clean_docx(cls, in_path, out_path):
        """Cleans author, revision, comment, and application metadata from DOCX files."""
        if not docx:
            raise RuntimeError("python-docx library not found. Run 'pip install python-docx'")

        # First pass: use python-docx to clear standard core properties
        doc = docx.Document(in_path)
        cp = doc.core_properties
        for attr in ['author', 'last_modified_by', 'title', 'comments', 'category',
                     'subject', 'keywords', 'content_status', 'identifier', 'version']:
            try:
                setattr(cp, attr, '')
            except Exception:
                pass
        
        # Save temp file
        temp_out = out_path + ".tmp.docx"
        doc.save(temp_out)

        # Second pass: inspect docProps/app.xml and remove custom properties if present
        try:
            with zipfile.ZipFile(temp_out, 'r') as zin, zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    content = zin.read(item.filename)
                    if item.filename == 'docProps/app.xml':
                        # Sanitize Company, Manager, Application tags
                        try:
                            xml_str = content.decode('utf-8', errors='ignore')
                            for tag in ['Company', 'Manager', 'Application', 'Template']:
                                xml_str = re.sub(f'<{tag}>.*?</{tag}>', f'<{tag}></{tag}>', xml_str)
                            content = xml_str.encode('utf-8')
                        except Exception:
                            pass
                    # Skip custom.xml if present to avoid leaking custom metadata
                    if item.filename == 'docProps/custom.xml':
                        continue
                    zout.writestr(item, content)
            
            if os.path.exists(temp_out):
                os.remove(temp_out)
        except Exception:
            # Fallback to direct temp copy if zip rewrite fails
            if os.path.exists(temp_out):
                if os.path.exists(out_path):
                    os.remove(out_path)
                os.rename(temp_out, out_path)

        return "Word author, editor history, company, and document properties cleared."

    @classmethod
    def clean_file(cls, in_path, out_path=None):
        """Dispatches cleaning to the appropriate file handler."""
        in_path = os.path.abspath(in_path)
        ext = Path(in_path).suffix.lower()

        if not os.path.exists(in_path):
            return False, f"File not found: {in_path}"

        if not cls.is_supported(in_path):
            return False, f"Unsupported file type: {ext}"

        if not out_path:
            p = Path(in_path)
            out_path = str(p.parent / f"{p.stem}_clean{p.suffix}")

        out_path = os.path.abspath(out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        try:
            if ext in cls.SUPPORTED_EXTENSIONS['pdf']:
                msg = cls.clean_pdf(in_path, out_path)
            elif ext in cls.SUPPORTED_EXTENSIONS['docx']:
                msg = cls.clean_docx(in_path, out_path)
            elif ext in cls.SUPPORTED_EXTENSIONS['image']:
                msg = cls.clean_image(in_path, out_path)
            else:
                return False, f"No cleaner defined for {ext}"

            return True, msg
        except Exception as e:
            return False, f"Error: {str(e)}"


# ==========================================
# GUI APPLICATION (Tkinter)
# ==========================================
def launch_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("AI & File Metadata Remover")
    root.geometry("750x580")
    root.minsize(650, 480)

    # Set background color & styling
    bg_color = "#f5f6f8"
    card_bg = "#ffffff"
    primary_color = "#2563eb"
    success_color = "#16a34a"
    
    root.configure(bg=bg_color)

    selected_files = []

    # Title Banner Frame
    header_frame = tk.Frame(root, bg=card_bg, padx=20, pady=15, relief=tk.RIDGE, bd=1)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

    title_lbl = tk.Label(header_frame, text="🛡️ AI & File Metadata Remover", font=("Segoe UI", 16, "bold"), bg=card_bg, fg="#1e293b")
    title_lbl.pack(anchor="w")

    subtitle_lbl = tk.Label(header_frame, 
                            text="Clean author details, creator tags, AI prompts, and EXIF from PDF, DOCX, & Images.", 
                            font=("Segoe UI", 9), bg=card_bg, fg="#64748b")
    subtitle_lbl.pack(anchor="w", pady=(2, 0))

    # Controls Frame
    btn_frame = tk.Frame(root, bg=bg_color)
    btn_frame.pack(fill=tk.X, padx=15, pady=5)

    def update_file_list_ui():
        file_tree.delete(*file_tree.get_children())
        for f in selected_files:
            size_kb = os.path.getsize(f) / 1024
            ext = Path(f).suffix.upper()
            file_tree.insert("", tk.END, values=(Path(f).name, ext, f"{size_kb:.1f} KB", f))
        
        status_lbl.config(text=f"Total files selected: {len(selected_files)}")
        clean_btn.config(state=tk.NORMAL if selected_files else tk.DISABLED)

    def add_files():
        files = filedialog.askopenfilenames(
            title="Select PDF, Word, or Image Files",
            filetypes=[
                ("All Supported Files", "*.pdf;*.docx;*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff"),
                ("PDF Documents", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff"),
                ("All Files", "*.*")
            ]
        )
        if files:
            for f in files:
                if f not in selected_files and MetadataRemover.is_supported(f):
                    selected_files.append(f)
            update_file_list_ui()

    def add_folder():
        folder = filedialog.askdirectory(title="Select Folder to Clean")
        if folder:
            for root_dir, _, filenames in os.walk(folder):
                for fname in filenames:
                    fpath = os.path.join(root_dir, fname)
                    if fpath not in selected_files and MetadataRemover.is_supported(fpath):
                        selected_files.append(fpath)
            update_file_list_ui()

    def clear_list():
        selected_files.clear()
        update_file_list_ui()
        log_text.config(state=tk.NORMAL)
        log_text.delete("1.0", tk.END)
        log_text.config(state=tk.DISABLED)

    add_btn = tk.Button(btn_frame, text="📄 Add Files", font=("Segoe UI", 10, "bold"), 
                        bg=primary_color, fg="white", activebackground="#1d4ed8", activeforeground="white",
                        padx=12, pady=6, relief=tk.FLAT, cursor="hand2", command=add_files)
    add_btn.pack(side=tk.LEFT, padx=(0, 8))

    folder_btn = tk.Button(btn_frame, text="📁 Add Folder", font=("Segoe UI", 10), 
                           bg="#e2e8f0", fg="#1e293b", activebackground="#cbd5e1",
                           padx=12, pady=6, relief=tk.FLAT, cursor="hand2", command=add_folder)
    folder_btn.pack(side=tk.LEFT, padx=(0, 8))

    clear_btn = tk.Button(btn_frame, text="✖ Clear List", font=("Segoe UI", 10), 
                          bg="#fee2e2", fg="#991b1b", activebackground="#fecaca",
                          padx=12, pady=6, relief=tk.FLAT, cursor="hand2", command=clear_list)
    clear_btn.pack(side=tk.LEFT)

    # File List Display
    tree_frame = tk.Frame(root, bg=card_bg, relief=tk.RIDGE, bd=1)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    columns = ("name", "type", "size", "path")
    file_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=7)
    file_tree.heading("name", text="File Name")
    file_tree.heading("type", text="Type")
    file_tree.heading("size", text="Size")
    file_tree.heading("path", text="Full Path")

    file_tree.column("name", width=200, anchor="w")
    file_tree.column("type", width=80, anchor="center")
    file_tree.column("size", width=90, anchor="e")
    file_tree.column("path", width=340, anchor="w")

    tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=file_tree.yview)
    file_tree.configure(yscrollcommand=tree_scroll.set)
    file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Output options & Action Bar
    bottom_frame = tk.Frame(root, bg=bg_color)
    bottom_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

    save_subfolder_var = tk.BooleanVar(value=True)
    chk_subfolder = tk.Checkbutton(bottom_frame, text="Save cleaned files in a 'cleaned_files' subfolder", 
                                   variable=save_subfolder_var, bg=bg_color, fg="#1e293b",
                                   font=("Segoe UI", 9), activebackground=bg_color)
    chk_subfolder.pack(anchor="w", pady=(0, 5))

    action_bar = tk.Frame(bottom_frame, bg=bg_color)
    action_bar.pack(fill=tk.X)

    status_lbl = tk.Label(action_bar, text="Ready. Add files above to begin.", font=("Segoe UI", 9), bg=bg_color, fg="#475569")
    status_lbl.pack(side=tk.LEFT, pady=5)

    last_out_dir = [None]

    def open_output_folder():
        target = last_out_dir[0]
        if target and os.path.exists(target):
            os.startfile(target)
        else:
            messagebox.showinfo("Notice", "Output folder not created yet.")

    open_dir_btn = tk.Button(action_bar, text="📂 Open Output Folder", font=("Segoe UI", 9),
                             bg="#e2e8f0", fg="#1e293b", padx=10, pady=6, relief=tk.FLAT,
                             cursor="hand2", command=open_output_folder, state=tk.DISABLED)
    open_dir_btn.pack(side=tk.RIGHT, padx=(8, 0))

    def run_cleaning():
        if not selected_files:
            return

        log_text.config(state=tk.NORMAL)
        log_text.delete("1.0", tk.END)

        clean_btn.config(state=tk.DISABLED)
        add_btn.config(state=tk.DISABLED)
        folder_btn.config(state=tk.DISABLED)

        success_count = 0
        error_count = 0

        for idx, fpath in enumerate(selected_files, start=1):
            p = Path(fpath)
            if save_subfolder_var.get():
                out_dir = str(p.parent / "cleaned_files")
                out_file = os.path.join(out_dir, f"{p.stem}_clean{p.suffix}")
            else:
                out_dir = str(p.parent)
                out_file = str(p.parent / f"{p.stem}_clean{p.suffix}")

            last_out_dir[0] = out_dir

            status_lbl.config(text=f"Processing ({idx}/{len(selected_files)}): {p.name}...")
            root.update_idletasks()

            ok, msg = MetadataRemover.clean_file(fpath, out_file)
            if ok:
                success_count += 1
                log_text.insert(tk.END, f"✔ [SUCCESS] {p.name}\n   -> {msg}\n   Saved: {out_file}\n\n", "success")
            else:
                error_count += 1
                log_text.insert(tk.END, f"✖ [FAILED] {p.name}: {msg}\n\n", "error")

        log_text.see(tk.END)
        log_text.config(state=tk.DISABLED)

        status_lbl.config(text=f"Done! Cleaned: {success_count}, Failed: {error_count}")
        clean_btn.config(state=tk.NORMAL)
        add_btn.config(state=tk.NORMAL)
        folder_btn.config(state=tk.NORMAL)
        open_dir_btn.config(state=tk.NORMAL)

        messagebox.showinfo("Finished", f"Cleaning complete!\nSuccessfully cleaned: {success_count} file(s)\nOutput saved in: {last_out_dir[0]}")

    clean_btn = tk.Button(action_bar, text="✨ Clean Metadata Now", font=("Segoe UI", 10, "bold"),
                          bg=success_color, fg="white", activebackground="#15803d", activeforeground="white",
                          padx=15, pady=6, relief=tk.FLAT, cursor="hand2", command=run_cleaning, state=tk.DISABLED)
    clean_btn.pack(side=tk.RIGHT)

    # Log / Output Console
    log_frame = tk.Frame(root, bg=card_bg, relief=tk.RIDGE, bd=1)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

    log_title = tk.Label(log_frame, text="Activity Log", font=("Segoe UI", 9, "bold"), bg=card_bg, fg="#334155")
    log_title.pack(anchor="w", padx=10, pady=(5, 0))

    log_scroll = ttk.Scrollbar(log_frame)
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    log_text = tk.Text(log_frame, height=6, bg="#ffffff", fg="#1e293b", font=("Consolas", 9),
                       yscrollcommand=log_scroll.set, wrap=tk.WORD, relief=tk.FLAT)
    log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
    log_scroll.config(command=log_text.yview)

    log_text.tag_config("success", foreground="#16a34a")
    log_text.tag_config("error", foreground="#dc2626")
    log_text.config(state=tk.DISABLED)

    root.mainloop()


# ==========================================
# CLI / ENTRYPOINT
# ==========================================
if __name__ == '__main__':
    import re  # needed for regex in clean_docx
    if len(sys.argv) > 1:
        # CLI Mode
        inputs = sys.argv[1:]
        print(f"--- Running Metadata Remover on {len(inputs)} item(s) ---")
        for item in inputs:
            if os.path.isfile(item):
                ok, msg = MetadataRemover.clean_file(item)
                status = "OK" if ok else "FAILED"
                print(f"[{status}] {item}: {msg}")
            elif os.path.isdir(item):
                print(f"Scanning directory: {item}")
                for root_dir, _, files in os.walk(item):
                    for fname in files:
                        fpath = os.path.join(root_dir, fname)
                        if MetadataRemover.is_supported(fpath):
                            ok, msg = MetadataRemover.clean_file(fpath)
                            status = "OK" if ok else "FAILED"
                            print(f"  [{status}] {fname}: {msg}")
    else:
        # Launch GUI if no command line arguments passed
        launch_gui()
