# SubAdderGUI

🎥 **SubAdderGUI**

[![Version](https://img.shields.io/github/v/release/hybridvamp/SubAdderGUI?label=version\&color=blue)](https://github.com/hybridvamp/SubAdderGUI/releases)
[![License](https://img.shields.io/github/license/hybridvamp/SubAdderGUI?color=green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/hybridvamp/SubAdderGUI)](https://github.com/hybridvamp/SubAdderGUI/issues)

A sleek, modern Python application to add subtitle tracks to MKV files using FFmpeg. It supports drag-and-drop, automatic update checking, and a Material-UI-inspired interface.

---

## 🚀 Features

* ✅ Add new subtitle tracks to MKV files without altering existing ones.
* ✅ Supports multiple subtitle formats: `.srt`, `.ass`, `.sub`, `.pgs`.
* ✅ Modern dark mode interface with Material-UI styling.
* ✅ Drag & drop support for quick file selection.
* ✅ Automatic update checker (pulls latest version from GitHub).
* ✅ Cross-platform (Windows, macOS, Linux).

---

## 📦 Requirements

* Python 3.8+
* FFmpeg (must be installed and added to system PATH)
* Internet connection (for update checking)

### Python Dependencies

Listed in `requirements.txt`:

```
PyQt6
requests
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## 🛠 Installation & Usage

### 1️⃣ Install FFmpeg

* Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager.
* Add FFmpeg to your system PATH.

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/hybridvamp/SubAdderGUI.git
cd SubAdderGUI
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the App

```bash
python subs.py
```

Or double-click the `subs.py` file (Python must be associated).

---

## 🔄 Update Checker

* The app includes a **Check for Updates** button.
* If a new version is found, it allows you to update and restart automatically.

---

## 📁 Project Structure

```
SubAdderGUI/
├── subs.py               # Main application
├── requirements.txt      # Python dependencies
├── version.txt           # Current version
└── README.md             # Project documentation
```

---

## 📜 License

GNU GENERAL PUBLIC LICENSE © 2025 HybridVamp

---

## 🌐 Links

* [GitHub Repo](https://github.com/hybridvamp/SubAdderGUI)
* [FFmpeg Downloads](https://ffmpeg.org/download.html)

---

## 💡 Screenshots

![Add Subtitles](screenshots/image.png)
