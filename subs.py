import sys
import os
import subprocess
import tempfile
import shutil
import zipfile
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QLineEdit, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

GITHUB_REPO = "https://github.com/hybridvamp/SubAdderGUI"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
VERSION_FILE = "version.txt"


class SubAdderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubAdderGUI")
        self.setWindowIcon(QIcon.fromTheme("video-x-generic"))
        self.setGeometry(300, 300, 500, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-size: 14px;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        self.init_ui()
        self.check_ffmpeg()

    def init_ui(self):
        layout = QVBoxLayout()

        self.info_label = QLabel("🎥 Add subtitle track to MKV file")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self.mkv_path_input = QLineEdit()
        self.mkv_path_input.setPlaceholderText("Select MKV File...")
        layout.addWidget(self.mkv_path_input)

        mkv_browse = QPushButton("Browse MKV")
        mkv_browse.clicked.connect(self.select_mkv_file)
        layout.addWidget(mkv_browse)

        self.subtitle_path_input = QLineEdit()
        self.subtitle_path_input.setPlaceholderText("Select Subtitle File (.srt/.ass)")
        layout.addWidget(self.subtitle_path_input)

        subtitle_browse = QPushButton("Browse Subtitle")
        subtitle_browse.clicked.connect(self.select_subtitle_file)
        layout.addWidget(subtitle_browse)

        self.track_name_input = QLineEdit()
        self.track_name_input.setPlaceholderText("Enter Subtitle Track Name")
        layout.addWidget(self.track_name_input)

        add_button = QPushButton("➕ Add Subtitles")
        add_button.clicked.connect(self.add_subtitles)
        layout.addWidget(add_button)

        self.update_button = QPushButton("🔄 Check for Updates")
        self.update_button.clicked.connect(self.check_for_updates)
        layout.addWidget(self.update_button)

        self.setLayout(layout)

    def select_mkv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select MKV File", "", "MKV Files (*.mkv)")
        if file_path:
            self.mkv_path_input.setText(file_path)

    def select_subtitle_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Subtitle File", "", "Subtitle Files (*.srt *.ass)")
        if file_path:
            self.subtitle_path_input.setText(file_path)

    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            reply = QMessageBox.question(
                self, "FFmpeg Not Found",
                "FFmpeg is not installed or not in PATH.\n\nDo you want to download and use it locally?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.download_ffmpeg()
            else:
                sys.exit(1)

    def download_ffmpeg(self):
        try:
            self.info_label.setText("⬇ Downloading FFmpeg...")
            ffmpeg_zip = requests.get(FFMPEG_URL, stream=True)
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            with open(zip_path, "wb") as f:
                for chunk in ffmpeg_zip.iter_content(chunk_size=8192):
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            ffmpeg_folder = next(os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if "ffmpeg" in d.lower())
            bin_folder = os.path.join(ffmpeg_folder, "bin")

            for file in os.listdir(bin_folder):
                shutil.move(os.path.join(bin_folder, file), os.getcwd())

            QMessageBox.information(self, "FFmpeg Ready", "✅ FFmpeg downloaded and configured.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Failed to download FFmpeg:\n{e}")
            sys.exit(1)

    def add_subtitles(self):
        mkv_file = self.mkv_path_input.text()
        subtitle_file = self.subtitle_path_input.text()
        track_name = self.track_name_input.text()

        if not os.path.isfile(mkv_file) or not os.path.isfile(subtitle_file):
            QMessageBox.critical(self, "Error", "Please select valid MKV and subtitle files.")
            return

        output_file = os.path.splitext(mkv_file)[0] + "_subbed.mkv"

        cmd = [
            "ffmpeg", "-i", mkv_file, "-i", subtitle_file,
            "-map", "0", "-map", "1",
            "-c", "copy",
            "-metadata:s:s:1", f"title={track_name}",
            output_file
        ]

        try:
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "Success", f"✅ Subtitle added successfully!\nSaved as: {output_file}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"❌ Failed to add subtitle:\n{e}")

    def check_for_updates(self):
        try:
            current_version = "0.1.0"
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, "r") as f:
                    current_version = f.read().strip()

            response = requests.get(f"{GITHUB_REPO}/raw/main/version.txt", timeout=5)
            response.raise_for_status()
            latest_version = response.text.strip()

            if current_version == latest_version:
                self.update_button.setText("✅ Up-to-date")
                self.update_button.setEnabled(False)
                QMessageBox.information(self, "No Updates", "🎉 You are already using the latest version.")
            else:
                self.update_button.setText("⬇ Update and Restart")
                self.update_button.clicked.disconnect()
                self.update_button.clicked.connect(self.update_and_restart)
                QMessageBox.information(self, "Update Available", f"🆕 A new version ({latest_version}) is available.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Failed to check for updates:\n{e}")

    def update_and_restart(self):
        try:
            app_dir = os.path.dirname(os.path.realpath(__file__))

            if os.path.exists(os.path.join(app_dir, ".git")):
                result = subprocess.run(["git", "pull"], cwd=app_dir, capture_output=True, text=True)
                if "Already up to date" in result.stdout:
                    QMessageBox.information(self, "Up-to-date", "✅ You already have the latest version.")
                    return
                elif result.returncode != 0:
                    raise Exception(f"Git pull failed:\n{result.stderr}")
            else:
                response = requests.get(f"{GITHUB_REPO}/archive/refs/heads/main.zip", timeout=10)
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, "update.zip")
                with open(zip_path, "wb") as f:
                    f.write(response.content)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                extracted_folder = [os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))][0]
                for item in os.listdir(extracted_folder):
                    src = os.path.join(extracted_folder, item)
                    dst = os.path.join(app_dir, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.move(src, dst)
                    else:
                        shutil.move(src, dst)

            new_version = requests.get(f"{GITHUB_REPO}/raw/main/version.txt", timeout=10).text.strip()
            with open(os.path.join(app_dir, VERSION_FILE), "w") as vf:
                vf.write(new_version)

            QMessageBox.information(self, "Update Complete", "✅ Updated successfully. Restarting...")
            python_exe = sys.executable
            script_path = os.path.realpath(__file__)
            QApplication.quit()
            subprocess.Popen([python_exe, script_path], cwd=app_dir)
            sys.exit(0)
        except Exception as e:
            QMessageBox.critical(self, "Update Failed", f"❌ Failed to update:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubAdderGUI()
    window.show()
    sys.exit(app.exec())
