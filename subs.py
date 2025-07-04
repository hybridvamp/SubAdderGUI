import sys
import os
import subprocess
import tempfile
import shutil
import zipfile
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QMessageBox, QTextEdit, QProgressBar, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

GITHUB_REPO = "https://github.com/hybridvamp/SubAdderGUI"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
VERSION_FILE = "version.txt"


class Worker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(
                self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in iter(process.stdout.readline, ''):
                self.log_signal.emit(line.strip())
            process.stdout.close()
            process.wait()
            self.progress_signal.emit(100)
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
            self.progress_signal.emit(0)


class SubAdderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎥 SubAdderGUI")
        self.setWindowIcon(QIcon.fromTheme("video-x-generic"))
        self.setGeometry(400, 200, 600, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #1f1f1f;
                color: #ffffff;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #1a1a1a;
                border-radius: 6px;
                color: #00ff00;
                font-family: Consolas, monospace;
            }
            QProgressBar {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #03dac6;
                border-radius: 6px;
            }
        """)

        self.init_ui()
        self.check_ffmpeg()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("🎥 Add Subtitles to MKV")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        self.mkv_input = QLineEdit()
        self.mkv_input.setPlaceholderText("Select MKV File...")
        layout.addWidget(self.mkv_input)

        mkv_button = QPushButton("📂 Browse MKV File")
        mkv_button.clicked.connect(self.select_mkv_file)
        layout.addWidget(mkv_button)

        self.subtitle_input = QLineEdit()
        self.subtitle_input.setPlaceholderText("Select Subtitle File (.srt/.ass)")
        layout.addWidget(self.subtitle_input)

        subtitle_button = QPushButton("📂 Browse Subtitle File")
        subtitle_button.clicked.connect(self.select_subtitle_file)
        layout.addWidget(subtitle_button)

        self.track_name_input = QLineEdit()
        self.track_name_input.setPlaceholderText("Enter Subtitle Track Name")
        layout.addWidget(self.track_name_input)

        add_button = QPushButton("➕ Add Subtitles")
        add_button.clicked.connect(self.add_subtitles)
        layout.addWidget(add_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Logs will appear here...")
        layout.addWidget(self.log_output)

        self.update_button = QPushButton("🔄 Check for Updates")
        self.update_button.clicked.connect(self.check_for_updates)
        layout.addWidget(self.update_button)

        self.setLayout(layout)

    def log(self, message):
        self.log_output.append(message)

    def select_mkv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select MKV File", "", "MKV Files (*.mkv)")
        if file_path:
            self.mkv_input.setText(file_path)

    def select_subtitle_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Subtitle File", "", "Subtitle Files (*.srt *.ass)")
        if file_path:
            self.subtitle_input.setText(file_path)

    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.log("✅ FFmpeg found in PATH.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            reply = QMessageBox.question(
                self, "FFmpeg Missing",
                "FFmpeg is not installed or in PATH.\nDownload and use a local version?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.download_ffmpeg()
            else:
                self.log("❌ FFmpeg is required. Exiting.")
                sys.exit(1)

    def download_ffmpeg(self):
        self.log("⬇ Downloading FFmpeg...")
        try:
            response = requests.get(FFMPEG_URL, stream=True)
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            ffmpeg_folder = next(
                os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if "ffmpeg" in d.lower()
            )
            bin_folder = os.path.join(ffmpeg_folder, "bin")
            for file in os.listdir(bin_folder):
                shutil.move(os.path.join(bin_folder, file), os.getcwd())

            self.log("✅ FFmpeg downloaded and configured.")
        except Exception as e:
            self.log(f"❌ Failed to download FFmpeg: {e}")
            QMessageBox.critical(self, "Error", f"Failed to download FFmpeg:\n{e}")
            sys.exit(1)

    def add_subtitles(self):
        mkv_file = self.mkv_input.text()
        subtitle_file = self.subtitle_input.text()
        track_name = self.track_name_input.text()

        if not mkv_file or not subtitle_file or not track_name:
            QMessageBox.critical(self, "Error", "Please provide all inputs.")
            return

        output_file = os.path.splitext(mkv_file)[0] + "_subbed.mkv"
        cmd = [
            "ffmpeg", "-i", mkv_file, "-i", subtitle_file,
            "-map", "0", "-map", "1",
            "-c", "copy",
            "-metadata:s:s:1", f"title={track_name}",
            output_file
        ]
        self.run_command(cmd)

    def run_command(self, command):
        self.worker = Worker(command)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.start()

    def check_for_updates(self):
        self.log("🔄 Checking for updates...")
        try:
            current_version = "0.1.0"
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, "r") as f:
                    current_version = f.read().strip()

            response = requests.get(f"{GITHUB_REPO}/raw/main/version.txt", timeout=5)
            response.raise_for_status()
            latest_version = response.text.strip()

            if current_version == latest_version:
                self.log("✅ Already up-to-date.")
                QMessageBox.information(self, "No Updates", "🎉 You are already using the latest version.")
            else:
                self.log(f"🆕 Update available: {latest_version}")
                reply = QMessageBox.question(
                    self, "Update Available",
                    f"A new version ({latest_version}) is available.\nDo you want to update now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.update_and_restart()
        except Exception as e:
            self.log(f"❌ Update check failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to check for updates:\n{e}")

    def update_and_restart(self):
        self.log("⬇ Downloading update...")
        try:
            app_dir = os.path.dirname(os.path.realpath(__file__))
            response = requests.get(f"{GITHUB_REPO}/archive/refs/heads/main.zip", timeout=10)
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_folder = next(os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d)))
            for item in os.listdir(extracted_folder):
                src = os.path.join(extracted_folder, item)
                dst = os.path.join(app_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.move(src, dst)
                else:
                    shutil.move(src, dst)

            self.log("✅ Update applied. Restarting...")
            QMessageBox.information(self, "Update Complete", "Updated successfully. Restarting...")
            python_exe = sys.executable
            script_path = os.path.realpath(__file__)
            QApplication.quit()
            subprocess.Popen([python_exe, script_path], cwd=app_dir)
            sys.exit(0)
        except Exception as e:
            self.log(f"❌ Update failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubAdderGUI()
    window.show()
    sys.exit(app.exec())
