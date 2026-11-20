# AI & File Metadata Remover 🛡️

Ye tool aapki **PDF, Word (.docx), aur Images (PNG, JPG, WEBP, etc.)** se saara hidden metadata, AI generation prompt details, author info, camera/GPS tags aur editing history clean kar deta hai.

---

## 🚀 Ise Kaise Use Karein (How to Use)

### Tarika 1: Double-Click karke GUI chalayein (Sabse Aasan)
1. Is folder me maujood **`Start_Metadata_Remover.bat`** par double click karein.
2. Ek graphical window (GUI) khul jayegi:
   - **📄 Add Files:** Apni PDF, Word file, ya Image select karein.
   - **📁 Add Folder:** Agar poore folder ki saari files ek saath clean karni hain.
   - **✨ Clean Metadata Now:** Click karein aur aapki cleaned files `cleaned_files` folder me save ho jayengi (original file safe rahegi).
   - **📂 Open Output Folder:** Click karke direct cleaned files dekh sakte hain.

### Tarika 2: Drag & Drop
* Kisi bhi file (PDF, DOCX, Image) ko pakad kar **`Start_Metadata_Remover.bat`** ke upar drag and drop kar dein. Wo turant metadata remove karke `_clean` file bana dega.

### Tarika 3: Command Line (CLI)
Terminal ya PowerShell me chalayein:
```powershell
python metadata_cleaner.py "meri_file.pdf"
```
Ya poora folder clean karne ke liye:
```powershell
python metadata_cleaner.py "C:\path\to\my_folder"
```

---

## 🔍 Ye Script Kya-Kya Remove Karti Hai?

1. **PDF Files (.pdf):**
   - Author, Creator, Producer (jaise AI generator tools, Canva, ReportLab, etc.)
   - Title, Subject, Keywords
   - Creation Date aur Modification Date
   - XMP XML metadata streams

2. **Word Documents (.docx):**
   - Author name aur Last Modified By
   - Revision history, Total Editing Time, Comments
   - Company name, Template tags, aur Custom document properties

3. **Images (.jpg, .jpeg, .png, .webp, .tiff):**
   - Midjourney, Stable Diffusion, DALL-E ke embedded prompts aur parameters
   - Camera EXIF data (Camera model, lens, exposure)
   - GPS coordinates (Location data)
   - Photoshop/Lightroom history aur text chunks

---

> ⚠️ **Important Note (AI Text Detection ke bare me):**
> Ye script file ke **technical metadata** (file properties, creator stamps, AI tags) ko 100% remove kar deti hai. Lekin agar file ke andar ka **written text** poori tarah Claude/ChatGPT se likha gaya hai, toh Turnitin ya GPTZero jaise AI text detectors text ke *writing style aur patterns* ko analyse karte hain. Isliye file submit karne se pehle text ko thoda apne shabdon mein edit (humanize) zaroor kar lein!
