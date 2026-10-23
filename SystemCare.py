import sys
import os
import subprocess
import shutil
import tempfile
import ctypes
import threading
import time
from pathlib import Path
from datetime import datetime

import psutil

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QObject,
    QTimer,
)

from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QLineEdit,
    QMessageBox,
    QFrame,
    QTabWidget,
)


# ============================================================
# ADMINISTRATOR
# ============================================================

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ============================================================
# WORKER
# ============================================================

class Worker(QObject):

    progress = Signal(int)
    status = Signal(str)
    finished = Signal(bool, str)

    def run(self, operation):

        try:

            if operation == "health":
                self.check_health()

            elif operation == "windows_update":
                self.windows_update()

            elif operation == "software_update":
                self.software_update()

            elif operation == "temp":
                self.clean_temp()

            elif operation == "cache":
                self.clean_cache()

            elif operation == "disk":
                self.clean_disk()

            elif operation == "defender_quick":
                self.defender_scan(False)

            elif operation == "defender_full":
                self.defender_scan(True)

            elif operation == "memory":
                self.memory_cleanup()

            else:
                self.finished.emit(False, "Unknown operation")

        except Exception as e:
            self.finished.emit(False, str(e))


    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    def check_health(self):

        self.status.emit("Checking CPU...")
        self.progress.emit(10)

        cpu = psutil.cpu_percent(interval=1)

        self.status.emit("Checking memory...")
        self.progress.emit(30)

        memory = psutil.virtual_memory()

        self.status.emit("Checking disk...")
        self.progress.emit(50)

        disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:\\"))

        self.status.emit(
            f"CPU: {cpu}% | "
            f"RAM: {memory.percent}% | "
            f"Disk: {disk.percent}%"
        )

        self.progress.emit(100)

        self.finished.emit(
            True,
            f"Health check complete. "
            f"CPU {cpu}% | RAM {memory.percent}% | "
            f"Disk {disk.percent}%"
        )


    # --------------------------------------------------------
    # WINDOWS UPDATE
    # --------------------------------------------------------

    def windows_update(self):

        self.status.emit("Checking Windows Update...")
        self.progress.emit(10)

        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-WindowsUpdate"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        self.progress.emit(70)

        if result.returncode != 0:

            self.finished.emit(
                False,
                result.stderr.strip() or
                "Windows Update check failed."
            )
            return

        self.status.emit("Windows Update check completed.")
        self.progress.emit(100)

        output = result.stdout.strip()

        if output:
            message = "Updates may be available:\n" + output[:3000]
        else:
            message = "Windows appears to have no pending updates."

        self.finished.emit(True, message)


    # --------------------------------------------------------
    # SOFTWARE UPDATE
    # --------------------------------------------------------

    def software_update(self):

        self.status.emit("Checking installed applications...")
        self.progress.emit(10)

        try:

            winget = shutil.which("winget")

            if not winget:

                possible_paths = [
                    os.path.expandvars(
                        r"%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe"
                    ),

                    os.path.expandvars(
                        r"%ProgramFiles%\WindowsApps\Microsoft.DesktopAppInstaller_*\winget.exe"
                    ),
                ]

                for path in possible_paths:

                    if "*" not in path and os.path.exists(path):
                        winget = path
                        break

            if not winget:

                self.finished.emit(
                    False,
                    "WinGet was not found on this system.\n\n"
                    "Please install or update 'App Installer' "
                    "from the Microsoft Store."
                )

                return

            self.status.emit("Running WinGet upgrade check...")
            self.progress.emit(30)

            result = subprocess.run(
                [
                    winget,
                    "upgrade",
                    "--accept-source-agreements",
                    "--disable-interactivity"
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self.progress.emit(80)

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode != 0:

                self.finished.emit(
                    False,
                    "WinGet failed.\n\n"
                    + (stderr or stdout or "Unknown WinGet error.")
                )

                return

            self.status.emit(
                "Software update check completed."
            )

            self.progress.emit(100)

            if not stdout:

                self.finished.emit(
                    True,
                    "No software update information was returned."
                )

                return

            self.finished.emit(
                True,
                "Software Update Results:\n\n"
                + stdout[-5000:]
            )

        except FileNotFoundError:

            self.finished.emit(
                False,
                "WinGet executable could not be found."
            )

        except Exception as e:

            self.finished.emit(
                False,
                f"Software update error: {str(e)}"
            )


    # --------------------------------------------------------
    # TEMP CLEANUP
    # --------------------------------------------------------

    def clean_temp(self):

        self.status.emit("Cleaning temporary files...")
        self.progress.emit(5)

        temp_locations = [
            tempfile.gettempdir(),
            os.environ.get("TEMP"),
            os.environ.get("TMP"),
        ]

        files_deleted = 0
        bytes_freed = 0

        for location in set(x for x in temp_locations if x):

            path = Path(location)

            if not path.exists():
                continue

            entries = list(path.iterdir())

            total = max(len(entries), 1)

            for index, item in enumerate(entries):

                try:

                    size = self.get_size(item)

                    if item.is_file():
                        item.unlink(missing_ok=True)
                        files_deleted += 1
                        bytes_freed += size

                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        files_deleted += 1
                        bytes_freed += size

                except Exception:
                    pass

                self.progress.emit(
                    min(95, int((index / total) * 90))
                )

        self.progress.emit(100)

        self.finished.emit(
            True,
            f"Temporary cleanup completed.\n"
            f"Items removed: {files_deleted}\n"
            f"Space freed: {self.format_bytes(bytes_freed)}"
        )


    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    def clean_cache(self):

        self.status.emit("Cleaning application/browser cache...")
        self.progress.emit(10)

        locations = []

        local = os.environ.get("LOCALAPPDATA")

        if local:

            locations.extend([
                Path(local) / "Temp",
                Path(local) / "Microsoft" / "Windows" / "INetCache",
            ])

        removed = 0

        for path in locations:

            if not path.exists():
                continue

            for item in path.iterdir():

                try:

                    if item.is_file():
                        item.unlink(missing_ok=True)
                        removed += 1

                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        removed += 1

                except Exception:
                    pass

        self.progress.emit(100)

        self.finished.emit(
            True,
            f"Cache cleanup completed.\n"
            f"Items removed: {removed}"
        )


    # --------------------------------------------------------
    # DISK CLEANUP
    # --------------------------------------------------------

    def clean_disk(self):

        self.status.emit("Analyzing disk...")
        self.progress.emit(10)

        drive = os.environ.get("SystemDrive", "C:\\")

        usage_before = shutil.disk_usage(drive)

        self.status.emit("Running Windows Disk Cleanup...")
        self.progress.emit(30)

        subprocess.run(
            [
                "cleanmgr.exe",
                "/verylowdisk"
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        self.progress.emit(90)

        usage_after = shutil.disk_usage(drive)

        freed = usage_after.free - usage_before.free

        self.progress.emit(100)

        self.finished.emit(
            True,
            f"Disk cleanup completed.\n"
            f"Approximate space freed: "
            f"{self.format_bytes(max(freed, 0))}"
        )


    # --------------------------------------------------------
    # WINDOWS DEFENDER
    # --------------------------------------------------------

    def defender_scan(self, full=False):

        scan_type = "FullScan" if full else "QuickScan"

        self.status.emit(
            f"Starting Microsoft Defender {scan_type}..."
        )

        self.progress.emit(5)

        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Start-MpScan -ScanType {scan_type}"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        self.progress.emit(100)

        if result.returncode != 0:

            self.finished.emit(
                False,
                result.stderr.strip() or
                "Defender scan failed."
            )
            return

        self.finished.emit(
            True,
            f"Microsoft Defender {scan_type} completed."
        )


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    def memory_cleanup(self):

        self.status.emit("Analyzing memory usage...")
        self.progress.emit(10)

        memory = psutil.virtual_memory()

        self.status.emit(
            f"Current memory usage: {memory.percent}%"
        )

        processes = []

        for process in psutil.process_iter(
            ["pid", "name", "memory_percent"]
        ):

            try:

                info = process.info

                processes.append(
                    (
                        info["pid"],
                        info["name"],
                        info["memory_percent"]
                    )
                )

            except Exception:
                pass

        processes.sort(
            key=lambda x: x[2],
            reverse=True
        )

        self.progress.emit(100)

        top = processes[:10]

        result = "\n".join(
            f"{name} ({pid}) - {usage:.1f}%"
            for pid, name, usage in top
        )

        self.finished.emit(
            True,
            "Top memory-consuming processes:\n\n" + result
        )


    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    @staticmethod
    def get_size(path):

        try:

            if path.is_file():
                return path.stat().st_size

            total = 0

            for item in path.rglob("*"):

                try:
                    if item.is_file():
                        total += item.stat().st_size
                except Exception:
                    pass

            return total

        except Exception:
            return 0


    @staticmethod
    def format_bytes(size):

        for unit in ["B", "KB", "MB", "GB", "TB"]:

            if size < 1024:
                return f"{size:.1f} {unit}"

            size /= 1024

        return f"{size:.1f} PB"


# ============================================================
# MAIN WINDOW
# ============================================================

class PCHealthApp(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("PC Care - Windows System Assistant")
        self.resize(1200, 760)

        self.worker_thread = None
        self.worker = None

        self.setup_ui()
        self.start_monitor()

    # --------------------------------------------------------

    def setup_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main = QVBoxLayout(central)

        # HEADER

        header = QHBoxLayout()

        title = QLabel("PC CARE")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))

        self.health_label = QLabel("● SYSTEM HEALTHY")
        self.health_label.setStyleSheet(
            "color:#35d07f;font-weight:bold;"
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.health_label)

        main.addLayout(header)

        # METRICS

        metrics = QGridLayout()

        self.cpu_card = self.create_metric("CPU", "0%")
        self.ram_card = self.create_metric("MEMORY", "0%")
        self.disk_card = self.create_metric("DISK", "0%")

        metrics.addWidget(self.cpu_card, 0, 0)
        metrics.addWidget(self.ram_card, 0, 1)
        metrics.addWidget(self.disk_card, 0, 2)

        main.addLayout(metrics)

        # TABS

        tabs = QTabWidget()

        tabs.addTab(
            self.create_maintenance_tab(),
            "Maintenance"
        )

        tabs.addTab(
            self.create_security_tab(),
            "Security"
        )

        tabs.addTab(
            self.create_process_tab(),
            "Memory / Processes"
        )

        main.addWidget(tabs)

        # PROGRESS

        self.progress = QProgressBar()
        self.progress.setValue(0)

        main.addWidget(self.progress)

        self.status_label = QLabel(
            "Ready."
        )

        main.addWidget(self.status_label)

        # ACTIVITY LOG

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(160)

        main.addWidget(self.log)

        # COMMAND BOX

        command_layout = QHBoxLayout()

        self.command_input = QLineEdit()

        self.command_input.setPlaceholderText(
            "Type command: clean temp, check updates, scan virus..."
        )

        self.command_input.returnPressed.connect(
            self.process_command
        )

        command_button = QPushButton("Run")

        command_button.clicked.connect(
            self.process_command
        )

        command_layout.addWidget(self.command_input)
        command_layout.addWidget(command_button)

        main.addLayout(command_layout)


    # --------------------------------------------------------

    def create_metric(self, name, value):

        frame = QFrame()

        frame.setStyleSheet("""
            QFrame {
                background:#18202a;
                border-radius:12px;
                padding:12px;
            }
        """)

        layout = QVBoxLayout(frame)

        label = QLabel(name)
        label.setStyleSheet(
            "color:#9ba7b4;font-size:12px;"
        )

        value_label = QLabel(value)

        value_label.setFont(
            QFont("Segoe UI", 22, QFont.Bold)
        )

        layout.addWidget(label)
        layout.addWidget(value_label)

        frame.value_label = value_label

        return frame


    # --------------------------------------------------------

    def create_button(self, text, operation):

        button = QPushButton(text)
        button.setMinimumHeight(42)

        button.clicked.connect(
            lambda: self.start_operation(operation)
        )

        return button


    # --------------------------------------------------------

    def create_maintenance_tab(self):

        widget = QWidget()

        layout = QGridLayout(widget)

        layout.addWidget(
            self.create_button(
                "Check Windows Updates",
                "windows_update"
            ),
            0, 0
        )

        layout.addWidget(
            self.create_button(
                "Check Software Updates",
                "software_update"
            ),
            0, 1
        )

        layout.addWidget(
            self.create_button(
                "Clean Temporary Files",
                "temp"
            ),
            1, 0
        )

        layout.addWidget(
            self.create_button(
                "Clean Cache",
                "cache"
            ),
            1, 1
        )

        layout.addWidget(
            self.create_button(
                "Clean Disk",
                "disk"
            ),
            2, 0
        )

        layout.addWidget(
            self.create_button(
                "PC Health Check",
                "health"
            ),
            2, 1
        )

        return widget


    # --------------------------------------------------------

    def create_security_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            self.create_button(
                "Quick Virus Scan",
                "defender_quick"
            )
        )

        layout.addWidget(
            self.create_button(
                "Full Virus Scan",
                "defender_full"
            )
        )

        return widget


    # --------------------------------------------------------

    def create_process_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            self.create_button(
                "Analyze Memory",
                "memory"
            )
        )

        self.process_label = QLabel(
            "Memory analysis will appear here."
        )

        self.process_label.setWordWrap(True)

        layout.addWidget(self.process_label)

        return widget


    # --------------------------------------------------------
    # OPERATION
    # --------------------------------------------------------

    def start_operation(self, operation):

        self.progress.setValue(0)

        self.status_label.setText(
            "Starting operation..."
        )

        self.log_message(
            f"Starting: {operation}"
        )

        self.worker_thread = QThread()

        self.worker = Worker()

        self.worker.moveToThread(
            self.worker_thread
        )

        self.worker_thread.started.connect(
            lambda: self.worker.run(operation)
        )

        self.worker.progress.connect(
            self.progress.setValue
        )

        self.worker.status.connect(
            self.status_label.setText
        )

        self.worker.finished.connect(
            self.operation_finished
        )

        self.worker.finished.connect(
            self.worker_thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker_thread.finished.connect(
            self.worker_thread.deleteLater
        )

        self.worker_thread.start()


    # --------------------------------------------------------

    def operation_finished(self, success, message):

        self.progress.setValue(
            100 if success else 0
        )

        self.status_label.setText(
            "Completed" if success else "Failed"
        )

        self.log_message(message)

        if len(message) > 200:
            self.process_label.setText(message)


    # --------------------------------------------------------
    # TEXT COMMANDS
    # --------------------------------------------------------

    def process_command(self):

        command = (
            self.command_input.text()
            .strip()
            .lower()
        )

        self.command_input.clear()

        if not command:
            return

        if "windows update" in command:
            self.start_operation("windows_update")

        elif "software update" in command:
            self.start_operation("software_update")

        elif "clean temp" in command:
            self.start_operation("temp")

        elif "temporary" in command:
            self.start_operation("temp")

        elif "cache" in command:
            self.start_operation("cache")

        elif "clean disk" in command:
            self.start_operation("disk")

        elif "health" in command:
            self.start_operation("health")

        elif "memory" in command:
            self.start_operation("memory")

        elif "quick scan" in command:
            self.start_operation("defender_quick")

        elif "virus" in command:
            self.start_operation("defender_quick")

        elif "full scan" in command:
            self.start_operation("defender_full")

        else:
            self.log_message(
                f"Unknown command: {command}"
            )


    # --------------------------------------------------------

    def log_message(self, message):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.log.append(
            f"[{timestamp}] {message}"
        )


    # --------------------------------------------------------
    # LIVE MONITOR
    # --------------------------------------------------------

    def start_monitor(self):

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_metrics
        )

        self.timer.start(1500)

    # --------------------------------------------------------

    def update_metrics(self):

        cpu = psutil.cpu_percent()

        memory = psutil.virtual_memory()

        disk = psutil.disk_usage(
            os.environ.get(
                "SystemDrive",
                "C:\\"
            )
        )

        self.cpu_card.value_label.setText(
            f"{cpu:.0f}%"
        )

        self.ram_card.value_label.setText(
            f"{memory.percent:.0f}%"
        )

        self.disk_card.value_label.setText(
            f"{disk.percent:.0f}%"
        )

        if memory.percent >= 90:

            self.health_label.setText(
                "● HIGH MEMORY USAGE"
            )

            self.health_label.setStyleSheet(
                "color:#ff6b6b;font-weight:bold;"
            )

        elif disk.percent >= 90:

            self.health_label.setText(
                "● LOW DISK SPACE"
            )

            self.health_label.setStyleSheet(
                "color:#ffb347;font-weight:bold;"
            )

        else:

            self.health_label.setText(
                "● SYSTEM HEALTHY"
            )

            self.health_label.setStyleSheet(
                "color:#35d07f;font-weight:bold;"
            )


# ============================================================
# APPLICATION
# ============================================================

def main():

    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background:#0f141a;
            color:#e8edf2;
            font-family:"Segoe UI";
        }

        QPushButton {
            background:#2367f2;
            border:none;
            border-radius:8px;
            padding:10px;
            color:white;
            font-weight:bold;
        }

        QPushButton:hover {
            background:#3477ff;
        }

        QLineEdit {
            background:#18202a;
            border:1px solid #303b48;
            border-radius:8px;
            padding:10px;
            color:white;
        }

        QTextEdit {
            background:#0b1015;
            border:1px solid #27313d;
            border-radius:8px;
        }

        QProgressBar {
            background:#18202a;
            border:none;
            border-radius:5px;
            height:12px;
        }

        QProgressBar::chunk {
            background:#2367f2;
            border-radius:5px;
        }

        QTabWidget::pane {
            border:1px solid #26313d;
            border-radius:8px;
        }

        QTabBar::tab {
            padding:10px 20px;
        }

        QTabBar::tab:selected {
            background:#2367f2;
            border-radius:5px;
        }
    """)

    window = PCHealthApp()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
