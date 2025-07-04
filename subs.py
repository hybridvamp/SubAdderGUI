import sys
import subprocess
import os
import shutil
import requests
import zipfile
import tempfile

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QProgressBar, QTextEdit, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# === GitHub Repo URL ===
GITHUB_REPO = "https://github.com/hybridvamp/SubAdderGUI"
VERSION_FILE_URL = f"{GITHUB_REPO}/raw/main/version.txt"


def get_local_version():
    """Read local version from version.txt"""
    version_file = os.path.join(os.getcwd(), "version.txt")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            return f.read().strip()
    return "0.0.0"  # fallback if version file missing


def get_latest_version():
    try:
        response = requests.get(f"{GITHUB_REPO}/raw/main/version.txt", timeout=5, headers={"Cache-Control": "no-cache"})
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"⚠ Failed to fetch version: {e}")
        return None


class FFmpegWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mkv_file, sub_file, lang_code, parent=None):
        super().__init__(parent)
        self.mkv_file = mkv_file
        self.sub_file = sub_file
        self.lang_code = lang_code

    def run(self):
        output_file = self.mkv_file.rsplit(".", 1)[0] + "_subbed.mkv"

        cmd = [
            "ffmpeg", "-y", "-i", self.mkv_file, "-i", self.sub_file,
            "-map", "0", "-map", "1",
            "-c:v", "copy", "-c:a", "copy",
            "-c:s", "copy", "-c:s:1", "srt",
            f"-metadata:s:s:1", f"language={self.lang_code}",
            f"-metadata:s:s:1", f"title={self.lang_code} Subtitles",
            output_file
        ]

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.progress.emit(line.strip())
            process.wait()
            if process.returncode == 0:
                self.finished.emit(True, output_file)
            else:
                self.finished.emit(False, "FFmpeg failed.")
        except Exception as e:
            self.finished.emit(False, str(e))


class SubtitleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎥 SubAdder GUI (FFmpeg)")
        self.setGeometry(300, 200, 700, 500)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #FFFFFF; font-family: "Segoe UI"; font-size: 14px; }
            QPushButton { background-color: #1F1F1F; border-radius: 10px; padding: 10px; }
            QPushButton:hover { background-color: #333333; }
            QLineEdit { background-color: #1E1E1E; border-radius: 8px; padding: 6px; }
            QTextEdit { background-color: #1E1E1E; border-radius: 8px; }
            QProgressBar { border-radius: 10px; text-align: center; background-color: #1F1F1F; }
            QProgressBar::chunk { background-color: #BB86FC; border-radius: 10px; }
        """)
        self.local_version = get_local_version()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # MKV File
        mkv_layout = QHBoxLayout()
        self.mkv_input = QLineEdit()
        mkv_btn = QPushButton("Browse MKV")
        mkv_btn.clicked.connect(self.browse_mkv)
        mkv_layout.addWidget(QLabel("🎬 MKV File:"))
        mkv_layout.addWidget(self.mkv_input)
        mkv_layout.addWidget(mkv_btn)

        # Subtitle File
        sub_layout = QHBoxLayout()
        self.sub_input = QLineEdit()
        sub_btn = QPushButton("Browse Subtitle")
        sub_btn.clicked.connect(self.browse_sub)
        sub_layout.addWidget(QLabel("📝 Subtitle File:"))
        sub_layout.addWidget(self.sub_input)
        sub_layout.addWidget(sub_btn)

        # Language Code
        lang_layout = QHBoxLayout()
        self.lang_input = QLineEdit()
        self.lang_input.setPlaceholderText("e.g., eng, spa")
        lang_layout.addWidget(QLabel("🌐 Language Code:"))
        lang_layout.addWidget(self.lang_input)

        # Add Subtitles Button
        self.add_btn = QPushButton("➕ Add Subtitles")
        self.add_btn.clicked.connect(self.add_subtitles)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # Check for Updates Button
        self.update_btn = QPushButton(f"🔄 Check for Updates (v{self.local_version})")
        self.update_btn.clicked.connect(self.check_for_updates)

        # Add widgets to layout
        layout.addLayout(mkv_layout)
        layout.addLayout(sub_layout)
        layout.addLayout(lang_layout)
        layout.addWidget(self.add_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_area)
        layout.addWidget(self.update_btn)

        self.setLayout(layout)

    def browse_mkv(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select MKV File", "", "MKV Files (*.mkv)")
        if file:
            self.mkv_input.setText(file)

    def browse_sub(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Subtitle File", "", "Subtitle Files (*.srt *.ass *.sub *.pgs)")
        if file:
            self.sub_input.setText(file)

    def add_subtitles(self):
        mkv_file = self.mkv_input.text()
        sub_file = self.sub_input.text()
        lang_code = self.lang_input.text().strip()

        if not mkv_file or not sub_file or not lang_code:
            QMessageBox.warning(self, "Error", "Please fill all fields.")
            return

        self.progress_bar.setValue(0)
        self.log_area.clear()

        self.worker = FFmpegWorker(mkv_file, sub_file, lang_code)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_log(self, line):
        self.log_area.append(line)
        self.progress_bar.setValue(min(self.progress_bar.value() + 1, 100))

    def on_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Success", f"✅ Subtitles added successfully!\nOutput: {message}")
            self.progress_bar.setValue(100)
        else:
            QMessageBox.critical(self, "Error", f"❌ Failed: {message}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            filepath = url.toLocalFile()
            if filepath.lower().endswith(".mkv"):
                self.mkv_input.setText(filepath)
            elif filepath.lower().endswith((".srt", ".ass", ".sub", ".pgs")):
                self.sub_input.setText(filepath)

    def check_for_updates(self):
        latest_version = get_latest_version()
        if not latest_version:
            QMessageBox.warning(self, "Error", "Could not fetch latest version.")
            return
        if latest_version != self.local_version:
            self.update_btn.setText("⬇️ Update & Restart")
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self.update_and_restart)
            QMessageBox.information(self, "Update Available",
                                    f"A new version ({latest_version}) is available.")
        else:
            QMessageBox.information(self, "Up to Date", "✅ SubAdderGUI is already up to date.")

    def update_and_restart(self):
        try:
            # Download latest release zip from GitHub
            response = requests.get(f"{GITHUB_REPO}/archive/refs/heads/main.zip", timeout=10)
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)

            # Extract and replace files
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            extracted_folder = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))][0]
            for item in os.listdir(extracted_folder):
                src = os.path.join(extracted_folder, item)
                app_dir = os.path.dirname(os.path.realpath(__file__))
                dst = os.path.join(app_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.move(src, dst)
                else:
                    shutil.move(src, dst)

            # Overwrite local version.txt with the new version
            new_version = requests.get(f"{GITHUB_REPO}/raw/main/version.txt", timeout=10).text.strip()
            version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
            with open(version_file, "w") as vf:
                vf.write(new_version)
                
            QMessageBox.information(self, "Update Complete", "✅ Updated successfully. Restarting...")
            # Restart safely
            python_exe = sys.executable
            script_path = os.path.realpath(__file__)
            QApplication.quit()
            subprocess.Popen([python_exe, script_path], cwd=os.getcwd())
            sys.exit(0)
        except Exception as e:
            QMessageBox.critical(self, "Update Failed", f"❌ Failed to update: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleApp()
    window.show()
    sys.exit(app.exec())
