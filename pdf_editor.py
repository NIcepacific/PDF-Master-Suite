# ================================================
# MY PDF EDITOR - SINGLE WINDOW (Final Version)
# ================================================

import PyPDF2
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO

import fitz
from PIL import Image, ImageTk
import updater

current_photo = None
current_zoom = 1.2
preview_pdf_path = None
preview_page_num = 0

# ================== WATERMARK ==================
def create_watermark(text):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 50)
    can.setFillGray(0.5, 0.5)
    can.saveState()
    can.translate(4*inch, 4*inch)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    return PyPDF2.PdfReader(packet)

# ================== PREVIEW ==================
def show_preview(pdf_path=None, page_num=None):
    global current_photo, preview_pdf_path, preview_page_num
    
    if pdf_path: preview_pdf_path = pdf_path
    if page_num is not None: preview_page_num = page_num
    
    if not preview_pdf_path: return

    try:
        doc = fitz.open(preview_pdf_path)
        page = doc[preview_page_num]
        
        # Render with current zoom level
        pix = page.get_pixmap(matrix=fitz.Matrix(current_zoom, current_zoom))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        photo = ImageTk.PhotoImage(img)
        preview_label.config(image=photo)
        preview_label.image = photo
        current_photo = photo
        status_label.config(text=f"Preview: {os.path.basename(preview_pdf_path)} (Page {preview_page_num+1}) | Zoom: {int(current_zoom*100)}%")
        
        # Update scroll region
        canvas_preview.configure(scrollregion=canvas_preview.bbox("all"))
        doc.close()
    except:
        status_label.config(text="Preview not available")

# ================== PROGRESS ==================
def start_progress():
    progress_bar.start(10)
    status_text.config(text="Processing... Please wait")

def stop_progress():
    progress_bar.stop()
    status_text.config(text="Ready")

# ================== HELPER ==================
def parse_pages_to_delete(text):
    to_delete = set()
    for part in text.strip().split(','):
        part = part.strip()
        if '-' in part:
            try:
                s, e = map(int, part.split('-'))
                to_delete.update(range(s, e+1))
            except: pass
        elif part.isdigit():
            to_delete.add(int(part))
    return {p-1 for p in to_delete}

# ================== SIMPLE TOOLS ==================
def delete_pages():
    input_pdf = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    pages_str = simpledialog.askstring("Delete Pages", "Pages to delete?\nExample: 2,5-8", initialvalue="2,5-8")
    if not pages_str: return
    to_delete = parse_pages_to_delete(pages_str)
    if not to_delete:
        messagebox.showwarning("Invalid", "No pages selected.")
        return
    output = filedialog.asksaveasfilename(title="Save New PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if os.path.abspath(input_pdf) == os.path.abspath(output):
        messagebox.showerror("Error", "Cannot overwrite the input file.\nPlease save as a new file.")
        return
    start_progress()
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        writer = PyPDF2.PdfWriter()
        for i in range(len(reader.pages)):
            if i not in to_delete:
                writer.add_page(reader.pages[i])
        with open(output, 'wb') as f:
            writer.write(f)
        messagebox.showinfo("✅ Success", f"Deleted {len(to_delete)} page(s)!\nSaved: {output}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed:\n{str(e)}")
    finally:
        stop_progress()

def compress_pdf():
    input_pdf = filedialog.askopenfilename(title="Select PDF to Compress", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    output = filedialog.asksaveasfilename(title="Save Compressed PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if os.path.abspath(input_pdf) == os.path.abspath(output):
        messagebox.showerror("Error", "Cannot overwrite the input file.\nPlease save as a new file.")
        return
    start_progress()
    try:
        before = os.path.getsize(input_pdf) / (1024*1024)
        doc = fitz.open(input_pdf)
        doc.save(output, garbage=4, deflate=True, clean=True)
        doc.close()
        after = os.path.getsize(output) / (1024*1024)
        messagebox.showinfo("✅ Success", f"Compressed!\nBefore: {before:.1f} MB\nAfter: {after:.1f} MB\nSaved: {output}")
    except Exception as e:
        messagebox.showerror("Error", f"Compression failed:\n{str(e)}")
    finally:
        stop_progress()

def merge_pdfs():
    pdfs = filedialog.askopenfilenames(title="Select PDFs to Merge", filetypes=[("PDF Files", "*.pdf")])
    if not pdfs: return
    show_preview(pdfs[0])
    output = filedialog.asksaveasfilename(title="Save Merged PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if any(os.path.abspath(p) == os.path.abspath(output) for p in pdfs):
        messagebox.showerror("Error", "Cannot overwrite an input file.\nPlease save as a new file.")
        return
    start_progress()
    try:
        merger = PyPDF2.PdfMerger()
        for pdf in pdfs: merger.append(pdf)
        merger.write(output)
        merger.close()
        messagebox.showinfo("✅ Success", f"Merged saved!\n{output}")
    finally:
        stop_progress()

def split_pdf():
    input_pdf = filedialog.askopenfilename(title="Select PDF to Split", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir: return
    start_progress()
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        for i in range(len(reader.pages)):
            writer = PyPDF2.PdfWriter()
            writer.add_page(reader.pages[i])
            path = os.path.join(output_dir, f"page_{i+1}.pdf")
            with open(path, 'wb') as f: writer.write(f)
        messagebox.showinfo("✅ Success", f"Split into {len(reader.pages)} pages!\nSaved in: {output_dir}")
    finally:
        stop_progress()

def rotate_pages():
    input_pdf = filedialog.askopenfilename(title="Select PDF to Rotate", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    output = filedialog.asksaveasfilename(title="Save Rotated PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if os.path.abspath(input_pdf) == os.path.abspath(output):
        messagebox.showerror("Error", "Cannot overwrite the input file.\nPlease save as a new file.")
        return
    angle = simpledialog.askinteger("Rotation", "Enter angle (90, 180, 270):", minvalue=0, maxvalue=360)
    if angle is None: return
    start_progress()
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        writer = PyPDF2.PdfWriter()
        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)
        with open(output, 'wb') as f: writer.write(f)
        messagebox.showinfo("✅ Success", f"Rotated saved!\n{output}")
    finally:
        stop_progress()

def extract_text():
    input_pdf = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    reader = PyPDF2.PdfReader(input_pdf)
    text = "".join(page.extract_text() + "\n" for page in reader.pages)
    save_path = filedialog.asksaveasfilename(title="Save Text As", defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if save_path:
        with open(save_path, 'w', encoding='utf-8') as f: f.write(text)
        messagebox.showinfo("✅ Success", f"Text saved!\n{save_path}")

def add_watermark():
    input_pdf = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    text = simpledialog.askstring("Watermark", "Enter watermark text:")
    if not text: return
    output = filedialog.asksaveasfilename(title="Save Watermarked PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if os.path.abspath(input_pdf) == os.path.abspath(output):
        messagebox.showerror("Error", "Cannot overwrite the input file.\nPlease save as a new file.")
        return
    start_progress()
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        writer = PyPDF2.PdfWriter()
        wm = create_watermark(text)
        wm_page = wm.pages[0]
        for page in reader.pages:
            page.merge_page(wm_page)
            writer.add_page(page)
        with open(output, 'wb') as f: writer.write(f)
        messagebox.showinfo("✅ Success", f"Watermark added!\n{output}")
    finally:
        stop_progress()

def clear_preview():
    global current_photo
    preview_label.config(image='')
    status_label.config(text="No PDF previewed yet")
    current_photo = None

# ================== CONVERSION & SECURITY ==================
def pdf_to_images():
    input_pdf = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])

    if not input_pdf: return
    show_preview(input_pdf)
    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir: return
    
    start_progress()
    try:
        doc = fitz.open(input_pdf)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for high quality
            output_file = os.path.join(output_dir, f"page_{i+1}.png")
            pix.save(output_file)
        messagebox.showinfo("✅ Success", f"Converted {len(doc)} pages to images!\nSaved in: {output_dir}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        stop_progress()

def images_to_pdf():
    images = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])

    if not images: return
    output = filedialog.asksaveasfilename(title="Save PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    
    start_progress()
    try:
        img_list = []
        for img_path in images:
            img = Image.open(img_path).convert("RGB")
            img_list.append(img)
        
        if img_list:
            img_list[0].save(output, save_all=True, append_images=img_list[1:])
            messagebox.showinfo("✅ Success", f"Converted {len(images)} images to PDF!\nSaved: {output}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        stop_progress()


def encrypt_pdf():
    input_pdf = filedialog.askopenfilename(title="Select PDF to Encrypt", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    password = simpledialog.askstring("Password", "Enter password to encrypt:", show='*')
    if not password: return
    
    output = filedialog.asksaveasfilename(title="Save Encrypted PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if os.path.abspath(input_pdf) == os.path.abspath(output):
        messagebox.showerror("Error", "Cannot overwrite input file.")
        return

    start_progress()
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        writer = PyPDF2.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(output, 'wb') as f:
            writer.write(f)
        messagebox.showinfo("✅ Success", f"Encrypted PDF saved!\n{output}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        stop_progress()


def decrypt_pdf():
    input_pdf = filedialog.askopenfilename(title="Select PDF to Decrypt", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    password = simpledialog.askstring("Password", "Enter password to decrypt.\nLeave blank if no password:", show='*')
    if password is None: return  # User cancelled
    
    output = filedialog.asksaveasfilename(title="Save Decrypted PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
    if not output: return
    if os.path.abspath(input_pdf) == os.path.abspath(output):
        messagebox.showerror("Error", "Cannot overwrite input file.")
        return

    start_progress()
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        if reader.is_encrypted:
            if not reader.decrypt(password):
                raise Exception("Invalid password!")
        writer = PyPDF2.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output, 'wb') as f:  writer.write(f)
        messagebox.showinfo("✅ Success", f"Decrypted PDF saved!\n{output}")
    except Exception as e:
        messagebox.showerror("Error", f"Decryption failed:\n{str(e)}")
    finally:
        stop_progress()

def edit_metadata():
    input_pdf = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    
    try:
        reader = PyPDF2.PdfReader(input_pdf)
        meta = reader.metadata or {}
    except Exception as e:
        messagebox.showerror("Error", f"Could not read metadata: {e}")
        return

    # Popup window
    win = tk.Toplevel()
    win.title("Edit Metadata")
    win.geometry("450x380")
    win.configure(bg=BG_COLOR)
    
    fields = {"Title": "/Title", "Author": "/Author", "Subject": "/Subject", "Creator": "/Creator", "Producer": "/Producer"}
    entries = {}
    
    ttk.Label(win, text="Edit PDF Metadata", font=("Segoe UI", 12, "bold"), background=BG_COLOR, foreground=PRIMARY).pack(pady=15)
    
    form = ttk.Frame(win, padding=15)
    form.pack(fill='both', expand=True)
    
    row = 0
    for label_text, key in fields.items():
        ttk.Label(form, text=label_text + ":", background=BG_COLOR).grid(row=row, column=0, sticky='w', pady=5)
        ent = ttk.Entry(form, width=40)
        ent.grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        if meta and key in meta:
            ent.insert(0, str(meta[key]))
        entries[key] = ent
        row += 1
        
    def save():
        output = filedialog.asksaveasfilename(title="Save PDF As", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not output: return
        
        new_meta = {key: ent.get() for key, ent in entries.items()}
        
        start_progress()
        try:
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.add_metadata(new_meta)
            with open(output, 'wb') as f:
                writer.write(f)
            messagebox.showinfo("Success", f"Metadata saved!\n{output}")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            stop_progress()

    ttk.Button(win, text="💾 Save Metadata", command=save).pack(pady=15)

def extract_images():
    input_pdf = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
    if not input_pdf: return
    show_preview(input_pdf)
    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir: return

    start_progress()
    try:
        doc = fitz.open(input_pdf)
        count = 0
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha < 4:       # this is GRAY or RGB
                    pix.save(os.path.join(output_dir, f"p{i+1}_img{xref}.png"))
                else:               # CMYK: convert to RGB first
                    pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    pix1.save(os.path.join(output_dir, f"p{i+1}_img{xref}.png"))
                    pix1 = None
                pix = None
                count += 1
        messagebox.showinfo("Success", f"Extracted {count} embedded images!\nSaved in: {output_dir}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        stop_progress()

# ================== SETUP VISUAL MERGER TAB (your code) ==================
def setup_merger_tab(parent):
    merge_files = []

    controls = ttk.Frame(parent, padding=5)
    controls.pack(fill='x', pady=5, padx=5)
    
    ttk.Button(controls, text="📂 Add PDFs", command=lambda: add_pdfs()).pack(side='left', fill='x', expand=True, padx=5)
    ttk.Button(controls, text="🗑️ Clear All", command=lambda: clear_list()).pack(side='left', fill='x', expand=True, padx=5)

    # Modern Treeview instead of Listbox
    tree = ttk.Treeview(parent, columns=("Name", "Path"), show="headings", selectmode="extended", height=15)
    tree.heading("Name", text="File Name", anchor="w")
    tree.heading("Path", text="Full Path", anchor="w")
    tree.column("Name", width=200, stretch=False)
    tree.column("Path", width=300, stretch=True)
    tree.pack(fill='both', expand=True, padx=5, pady=5)

    actions = ttk.Frame(parent, padding=5)
    actions.pack(fill='x', pady=5, padx=5)
    
    ttk.Button(actions, text="↑ Up", command=lambda: move_up()).pack(side='left', fill='x', expand=True, padx=2)
    ttk.Button(actions, text="↓ Down", command=lambda: move_down()).pack(side='left', fill='x', expand=True, padx=2)
    ttk.Button(actions, text="❌ Remove", command=lambda: remove_sel()).pack(side='left', fill='x', expand=True, padx=2)
    
    ttk.Button(parent, text="💾 Merge PDFs", command=lambda: do_merge()).pack(fill='x', padx=10, pady=10)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for f in merge_files:
            tree.insert("", "end", values=(os.path.basename(f), f))

    def add_pdfs():
        files = filedialog.askopenfilenames(title="Select PDFs", filetypes=[("PDF Files", "*.pdf")])
        for f in files:
            merge_files.append(f) # Allow duplicates if user wants to merge same file twice
        refresh()

    def clear_list():
        merge_files.clear()
        refresh()

    def move_up():
        rows = tree.selection()
        indices = sorted([tree.index(row) for row in rows])
        for i in indices:
            if i > 0: merge_files[i], merge_files[i-1] = merge_files[i-1], merge_files[i]
        refresh()
        # Reselect (simplified for single moves, complex for multi-selection but functional)

    def move_down():
        rows = tree.selection()
        indices = sorted([tree.index(row) for row in rows], reverse=True)
        for i in indices:
            if i < len(merge_files)-1: merge_files[i], merge_files[i+1] = merge_files[i+1], merge_files[i]
        refresh()

    def remove_sel():
        rows = tree.selection()
        indices = sorted([tree.index(row) for row in rows], reverse=True)
        for i in indices: merge_files.pop(i)
        refresh()

    def do_merge():
        if len(merge_files) < 2: 
            return messagebox.showwarning("Merge", "Add at least 2 PDFs")
        out = filedialog.asksaveasfilename(filetypes=[("PDF", "*.pdf")], defaultextension=".pdf")
        if not out: return
        start_progress()
        try:
            merger = PyPDF2.PdfMerger()
            for f in merge_files: merger.append(f)
            merger.write(out)
            merger.close()
            messagebox.showinfo("Success", f"Merged!\n{out}")
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: stop_progress()

    def on_select(event):
        sel = tree.selection()
        if sel:
            idx = tree.index(sel[0])
            show_preview(merge_files[idx])
    tree.bind('<<TreeviewSelect>>', on_select)

# ================== SETUP VISUAL PAGE MANAGER TAB ==================
def setup_page_manager_tab(parent):
    current_pdf = None
    current_order = []

    controls = ttk.Frame(parent, padding=5)
    controls.pack(fill='x', pady=5, padx=5)
    
    ttk.Button(controls, text="📂 Open PDF", command=lambda: load_pdf()).pack(side='left', fill='x', expand=True, padx=5)

    # Modern Treeview
    tree = ttk.Treeview(parent, columns=("Page",), show="headings", selectmode="extended", height=15)
    tree.heading("Page", text="Page Number", anchor="center")
    tree.column("Page", anchor="center")
    tree.pack(fill='both', expand=True, padx=5, pady=5)

    actions = ttk.Frame(parent, padding=5)
    actions.pack(fill='x', pady=5, padx=5)
    
    ttk.Button(actions, text="↑ Up", command=lambda: move_up()).pack(side='left', fill='x', expand=True, padx=2)
    ttk.Button(actions, text="↓ Down", command=lambda: move_down()).pack(side='left', fill='x', expand=True, padx=2)
    ttk.Button(actions, text="❌ Delete", command=lambda: delete_selected()).pack(side='left', fill='x', expand=True, padx=2)
    
    ttk.Button(parent, text="💾 Save New PDF", command=lambda: save_new_pdf()).pack(fill='x', padx=10, pady=10)

    def load_pdf():
        nonlocal current_pdf, current_order
        file = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF Files", "*.pdf")])
        if not file: return
        current_pdf = file
        show_preview(file)
        reader = PyPDF2.PdfReader(file)
        current_order = list(range(len(reader.pages)))
        refresh()

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for i in current_order:
            tree.insert("", "end", values=(f"Page {i+1}",))

    def move_up():
        rows = tree.selection()
        indices = sorted([tree.index(row) for row in rows])
        for i in indices:
            if i > 0: current_order[i], current_order[i-1] = current_order[i-1], current_order[i]
        refresh()

    def move_down():
        rows = tree.selection()
        indices = sorted([tree.index(row) for row in rows], reverse=True)
        for i in indices:
            if i < len(current_order)-1: current_order[i], current_order[i+1] = current_order[i+1], current_order[i]
        refresh()

    def delete_selected():
        rows = tree.selection()
        indices = sorted([tree.index(row) for row in rows], reverse=True)
        for i in indices:
            current_order.pop(i)
        refresh()

    def save_new_pdf():
        if not current_pdf or not current_order: 
            return messagebox.showwarning("Error", "Open a PDF first")
        out = filedialog.asksaveasfilename(filetypes=[("PDF", "*.pdf")], defaultextension=".pdf")
        if not out: return
        start_progress()
        try:
            reader = PyPDF2.PdfReader(current_pdf)
            writer = PyPDF2.PdfWriter()
            for i in current_order:
                writer.add_page(reader.pages[i])
            with open(out, 'wb') as f:
                writer.write(f)
            messagebox.showinfo("Success", f"Saved!\n{out}")
        except Exception as e: messagebox.showerror("Error", str(e))
        finally: stop_progress()

    def on_select(event):
        sel = tree.selection()
        if sel and current_pdf:
            idx = tree.index(sel[0])
            show_preview(current_pdf, current_order[idx])
    tree.bind('<<TreeviewSelect>>', on_select)

# ================== MAIN WINDOW ==================
PRIMARY = "#2b5797"
BG_COLOR = "#f0f0f0"
TEXT_COLOR = "#333333"
is_dark = False # Global toggle
canvas_preview = None # Global for canvas access

def zoom_in():
    global current_zoom
    current_zoom += 0.2
    show_preview()

def zoom_out():
    global current_zoom
    if current_zoom > 0.4: current_zoom -= 0.2
    show_preview()

def show_about():
    msg = (
        "PDF MASTER SUITE v2.0\n"
        "--------------------------------\n\n"
        "A streamlined tool for all your PDF needs.\n\n"
        "KEY FEATURES:\n"
        "• Merge, Split, Rotate & Compress\n"
        "• Visual Page Management\n"
        "• PDF ↔ Image Conversion\n"
        "• Encryption & Security\n\n"
        "Developed by Iradukunda Pacific\n"
        "Software Enthusiast"
    )
    messagebox.showinfo("About", msg)

def setup_styles():
    global PRIMARY, BG_COLOR, TEXT_COLOR
    
    if is_dark:
        PRIMARY = "#4ecca3"  # Teal for dark mode
        BG_COLOR = "#232931" # Dark Grey
        TEXT_COLOR = "#eeeeee"
        BTN_BG = "#393e46"
        BTN_ACTIVE = "#4ecca3"
        TAB_BG = "#393e46"
        TREE_BG = "#393e46"
        TREE_FG = "#eeeeee"
    else:
        PRIMARY = "#2b5797"
        BG_COLOR = "#f0f0f0"
        TEXT_COLOR = "#333333"
        BTN_BG = "#e1e1e1"
        BTN_ACTIVE = "#c1c1c1"
        TAB_BG = "#ffffff"
        TREE_BG = "#ffffff"
        TREE_FG = "#333333"

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), background=BG_COLOR, foreground=TEXT_COLOR)
    style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8, background=BTN_BG, foreground=TEXT_COLOR)
    style.map('TButton', background=[('active', BTN_ACTIVE), ('pressed', BTN_ACTIVE)], foreground=[('active', TEXT_COLOR)])
    style.configure('Header.TFrame', background=PRIMARY)
    style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), background=PRIMARY, foreground="white")
    style.configure('TNotebook', tabposition='n', background=BG_COLOR)
    style.configure('TNotebook.Tab', font=('Segoe UI', 11), padding=[15, 5], background=BG_COLOR, foreground=TEXT_COLOR)
    style.map('TNotebook.Tab', background=[('selected', TAB_BG)], foreground=[('selected', PRIMARY)])
    style.configure('TLabelframe', background=BG_COLOR, foreground=TEXT_COLOR)
    style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'), foreground=PRIMARY, background=BG_COLOR)
    
    # Treeview Styles
    style.configure("Treeview", font=('Segoe UI', 10), rowheight=25, background=TREE_BG, fieldbackground=TREE_BG, foreground=TREE_FG, borderwidth=0)
    style.map("Treeview", background=[('selected', PRIMARY)], foreground=[('selected', 'white')])
    style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'), background=BG_COLOR, foreground=TEXT_COLOR)
    
    if canvas_preview:
        canvas_preview.configure(bg="#333333" if is_dark else "#e0e0e0")

def show_welcome(root):
    root.withdraw() # Hide main window initially
    
    welcome = tk.Toplevel(root)
    welcome.title("Welcome")
    welcome.geometry("600x580")
    welcome.configure(bg=BG_COLOR)
    welcome.resizable(False, False)
    
    # Center the window on screen
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - 600) // 2
    y = (sh - 580) // 2
    welcome.geometry(f"+{x}+{y}")

    welcome.protocol("WM_DELETE_WINDOW", root.destroy) # Close app if welcome is closed

    # --- Check for background image ---
    bg_photo_ref = None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "welcome_bg.png")
    if os.path.exists(image_path):
        try:
            bg_img = Image.open(image_path).resize((600, 580), Image.LANCZOS)
            bg_photo_ref = ImageTk.PhotoImage(bg_img)
        except Exception as e:
            print(f"Welcome screen: Could not load background image. {e}")
            bg_photo_ref = None

    canvas = tk.Canvas(welcome, width=600, height=580, highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    if bg_photo_ref:
        canvas.create_image(0, 0, image=bg_photo_ref, anchor="nw")
        canvas.image = bg_photo_ref # Keep a reference!

    # --- Content Frame ---
    # We place the text content in a frame to ensure readability.
    # If no image is loaded, we set the canvas background.
    if not bg_photo_ref:
        canvas.configure(bg=BG_COLOR)

    content_frame = ttk.Frame(canvas, padding=20)
    
    # Header (Only if no image, assuming image has branding)
    if not bg_photo_ref:
        ttk.Label(content_frame, text="Welcome to", font=("Segoe UI", 12), foreground="#666666").pack()
        ttk.Label(content_frame, text="PDF MASTER SUITE", font=("Segoe UI", 24, "bold"), foreground=PRIMARY).pack(pady=5)
        ttk.Label(content_frame, text="v2.0", font=("Segoe UI", 10, "bold"), background=PRIMARY, foreground="white").pack(pady=5)
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=15)

    # Features
    ttk.Label(content_frame, text="What this software does:", font=("Segoe UI", 11, "bold"), foreground=PRIMARY).pack(anchor='w', pady=(0, 5))
    features = [
        "• Merge, Split, Rotate & Compress PDFs",
        "• Visual Page Manager & Reordering",
        "• Edit Metadata & Extract Resources",
        "• Convert PDF ↔ Images",
        "• Encrypt & Decrypt Security"
    ]
    for f in features:
        ttk.Label(content_frame, text=f, font=("Segoe UI", 10)).pack(anchor='w', pady=1)

    ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=15)

    # Promise
    ttk.Label(content_frame, text="Developer Promise:", font=("Segoe UI", 10, "bold"), foreground=PRIMARY).pack(anchor='w')
    ttk.Label(content_frame, text="I will continue to update this software with new features as I get time.", font=("Segoe UI", 9, "italic"), foreground="#555555", wraplength=350).pack(anchor='w', pady=2)
    ttk.Label(content_frame, text="- Iradukunda Pacific", font=("Segoe UI", 9, "bold"), foreground="#333333").pack(anchor='e', pady=(5,0))

    # Place content frame (Centered or slightly lower if image exists)
    cy = 320 if bg_photo_ref else 290
    canvas.create_window(300, cy, window=content_frame, width=450)

    # --- Get Started Button (Bottom Left) ---
    def start():
        welcome.destroy()
        root.deiconify()

    style = ttk.Style(welcome)
    style.configure("Start.TButton", font=('Segoe UI', 11, 'bold'), background=PRIMARY, foreground=TEXT_COLOR)
    start_btn = ttk.Button(welcome, text="🚀 Get Started", command=start, style="Start.TButton")
    
    # Position: Bottom Left (x=30, y=550)
    canvas.create_window(30, 550, window=start_btn, anchor="sw", width=160, height=45)

def main():
    root = tk.Tk()
    root.title("PDF Master Suite")
    root.geometry("1150x750")
    root.configure(bg=BG_COLOR)

    # --- Load Logo ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, "logo.png")
    logo_photo = None

    if os.path.exists(logo_path):
        try:
            # Window Icon
            icon_img = Image.open(logo_path)
            icon_photo = ImageTk.PhotoImage(icon_img)
            root.iconphoto(True, icon_photo)
            
            # Header Logo (Resized)
            header_img = icon_img.resize((32, 32), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(header_img)
        except Exception as e:
            print(f"Logo error: {e}")
    
    setup_styles()
    show_welcome(root)

    # --- Header ---
    header = ttk.Frame(root, style='Header.TFrame', padding=15)
    header.pack(fill='x')
    
    if logo_photo:
        lbl = ttk.Label(header, image=logo_photo, background=PRIMARY)
        lbl.pack(side='left', padx=(0, 10))
        lbl.image = logo_photo

    ttk.Label(header, text="✨ PDF MASTER SUITE", style='Header.TLabel').pack(side='left')
    ttk.Label(header, text="v2.0", font=("Segoe UI", 10), background="#2b5797", foreground="#cccccc").pack(side='left', padx=10, pady=(8,0))

    # --- Main Content (Split Pane) ---
    paned = ttk.PanedWindow(root, orient='horizontal')
    paned.pack(fill='both', expand=True, padx=10, pady=10)

    # Left Side: Tools & Tabs
    left_panel = ttk.Frame(paned)
    paned.add(left_panel, weight=1)

    notebook = ttk.Notebook(left_panel)
    notebook.pack(fill="both", expand=True)

    # Tab 1: Quick Tools
    tab_quick = ttk.Frame(notebook, padding=15)
    notebook.add(tab_quick, text="   Quick Tools   ")
    
    # Group: File Operations
    grp_file = ttk.LabelFrame(tab_quick, text="File Operations", padding=10)
    grp_file.pack(fill='x', pady=5)
    ttk.Button(grp_file, text="🔗 Quick Merge", command=merge_pdfs).pack(fill='x', pady=2)
    ttk.Button(grp_file, text="📦 Compress PDF", command=compress_pdf).pack(fill='x', pady=2)
    ttk.Button(grp_file, text="✂️ Split PDF", command=split_pdf).pack(fill='x', pady=2)

    # Group: Page Operations
    grp_page = ttk.LabelFrame(tab_quick, text="Page Operations", padding=10)
    grp_page.pack(fill='x', pady=5)
    ttk.Button(grp_page, text="🔄 Rotate Pages", command=rotate_pages).pack(fill='x', pady=2)
    ttk.Button(grp_page, text="🗑️ Delete Pages (Simple)", command=delete_pages).pack(fill='x', pady=2)

    # Group: Edit
    grp_edit = ttk.LabelFrame(tab_quick, text="Editing", padding=10)
    grp_edit.pack(fill='x', pady=5)
    ttk.Button(grp_edit, text="💧 Add Watermark", command=add_watermark).pack(fill='x', pady=2)
    ttk.Button(grp_edit, text="📝 Extract Text", command=extract_text).pack(fill='x', pady=2)
    ttk.Button(grp_edit, text="ℹ️ Edit Metadata", command=edit_metadata).pack(fill='x', pady=2)

    # Tab 2: Page Manager
    tab_page = ttk.Frame(notebook, padding=10)
    notebook.add(tab_page, text="   Page Manager   ")
    setup_page_manager_tab(tab_page)

    # Tab 3: Visual Merger
    tab_merge = ttk.Frame(notebook, padding=10)
    notebook.add(tab_merge, text="   Visual Merger   ")
    setup_merger_tab(tab_merge)

    # Tab 4: Conversion & Security
    tab_conv = ttk.Frame(notebook, padding=10)
    notebook.add(tab_conv, text="   Conversion & Security   ")
    
    ttk.Label(tab_conv, text="Conversion Tools", font=("Segoe UI", 11, "bold"), foreground=PRIMARY).pack(anchor='w', pady=(5, 5))
    ttk.Button(tab_conv, text="🖼️ PDF to Images", command=pdf_to_images).pack(fill='x', pady=2)
    ttk.Button(tab_conv, text="📷 Images to PDF", command=images_to_pdf).pack(fill='x', pady=2)
    ttk.Button(tab_conv, text="🧩 Extract Embedded Images", command=extract_images).pack(fill='x', pady=2)
    
    ttk.Label(tab_conv, text="Security Tools", font=("Segoe UI", 11, "bold"), foreground=PRIMARY).pack(anchor='w', pady=(20, 5))
    ttk.Button(tab_conv, text="🔓 Decrypt PDF", command=decrypt_pdf).pack(fill='x', pady=2)
    ttk.Button(tab_conv, text="🔒 Encrypt PDF", command=encrypt_pdf).pack(fill='x', pady=2)

    # Tab 5: About
    tab_about = ttk.Frame(notebook, padding=20)
    notebook.add(tab_about, text="   About   ")
    
    # Header
    ttk.Label(tab_about, text="PDF MASTER SUITE", font=("Segoe UI", 18, "bold")).pack(pady=(10, 5))
    ttk.Label(tab_about, text="v2.0", font=("Segoe UI", 10, "italic")).pack(pady=(0, 20))

    # Description
    ttk.Label(tab_about, text="A lightweight, professional tool designed to streamline your PDF workflows without the bloat of commercial software.", 
              justify="center", wraplength=450).pack(pady=5)

    ttk.Separator(tab_about, orient='horizontal').pack(fill='x', pady=20, padx=50)

    # Features List
    feat_frame = ttk.Frame(tab_about)
    feat_frame.pack(anchor="center")
    features = [
        "•  Merge, Split & Compress PDFs",
        "•  Visual Page Manager & Reordering",
        "•  High-Quality PDF ↔ Image Conversion",
        "•  Secure Encryption & Decryption",
        "•  Watermarking & Text Extraction"
    ]
    for f in features:
        ttk.Label(feat_frame, text=f, font=("Segoe UI", 10)).pack(anchor="w", pady=2)

    # Update Button
    ttk.Button(tab_about, text="🔄 Check for Updates", command=lambda: updater.check_for_updates(silent=False)).pack(pady=15)

    # Footer / Signature
    ttk.Separator(tab_about, orient='horizontal').pack(fill='x', pady=20, padx=50)
    ttk.Label(tab_about, text="Developed by Iradukunda Pacific", font=("Segoe UI", 10, "bold")).pack()
    ttk.Label(tab_about, text="Software Enthusiast & Builder", font=("Segoe UI", 9), foreground="gray").pack()

    def toggle_dark_mode():
        global is_dark
        is_dark = not is_dark
        setup_styles()
        root.configure(bg=BG_COLOR)

    # Dark mode toggle button
    ttk.Button(header, text="🌙 Dark Mode", command=toggle_dark_mode).pack(side='right', padx=10)

    # Right Side: Preview
    right_frame = ttk.Frame(paned, padding=10, relief='flat')
    paned.add(right_frame, weight=3)

    # Zoom Controls Header
    zoom_frame = ttk.Frame(right_frame)
    zoom_frame.pack(fill='x', pady=(0, 5))
    ttk.Label(zoom_frame, text="👁️ Live Preview", font=('Segoe UI', 12, 'bold')).pack(side='left')
    ttk.Button(zoom_frame, text="➕", width=4, command=zoom_in).pack(side='right', padx=2)
    ttk.Button(zoom_frame, text="➖", width=4, command=zoom_out).pack(side='right', padx=2)
    
    # Scrollable Preview Area
    preview_container = ttk.Frame(right_frame, relief='solid', borderwidth=1)
    preview_container.pack(fill='both', expand=True, pady=5)
    
    global canvas_preview
    canvas_preview = tk.Canvas(preview_container, bg="#e0e0e0")
    v_scroll = ttk.Scrollbar(preview_container, orient="vertical", command=canvas_preview.yview)
    h_scroll = ttk.Scrollbar(preview_container, orient="horizontal", command=canvas_preview.xview)
    canvas_preview.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
    
    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    canvas_preview.pack(side="left", fill="both", expand=True)
    
    global preview_label
    preview_label = ttk.Label(canvas_preview)
    canvas_preview.create_window((0, 0), window=preview_label, anchor="nw")

    global status_label
    status_label = ttk.Label(right_frame, text="No PDF previewed yet", foreground="gray")
    status_label.pack(pady=8)

    # Bottom Progress
    bottom_frame = ttk.Frame(root, relief='flat', padding=5)
    bottom_frame.pack(side='bottom', fill='x', pady=5)
    global progress_bar, status_text
    progress_bar = ttk.Progressbar(bottom_frame, mode='indeterminate', length=200)
    progress_bar.pack(side='right', padx=10)
    status_text = ttk.Label(bottom_frame, text="Ready", font=("Segoe UI", 9))
    status_text.pack(side='left', padx=10)

    # Check for updates on startup (silent)
    root.after(2000, lambda: updater.check_for_updates(silent=True))

    # ttk.Button(root, text="❌ Exit", command=root.quit).pack(side="bottom", pady=10) # Removed, standard window close is enough

    root.mainloop()

if __name__ == "__main__":
    main()