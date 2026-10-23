# PC Care - Windows System Assistant

**PC Care** is a desktop system maintenance and security utility built with **Python 3** and **PySide6 (Qt)**. It offers a modern dark-mode user interface that monitors system resource utilization in real-time and allows users to run system maintenance tasks, security scans, software updates, and process diagnostics.

---

## 🚀 Features

### 📊 Real-Time Performance Monitoring
* **CPU Usage Tracker:** Live updates on processor load percentage.
* **RAM Usage Tracker:** Live monitoring of physical memory consumption.
* **Disk Usage Tracker:** Real-time tracking of System Drive space utilization.
* **Dynamic Health Indicator:** Automatic alert states (`SYSTEM HEALTHY`, `HIGH MEMORY USAGE`, `LOW DISK SPACE`) based on live resource metrics.

### 🧹 System Maintenance
* **Temporary Files Cleaner:** Removes temporary files from `%TEMP%` and system temporary directories while measuring storage space saved.
* **Cache Cleaner:** Cleans Windows Internet Cache (`INetCache`) and local application temp files.
* **Windows Disk Cleanup Integration:** Launches `cleanmgr.exe` directly for system drive optimization.
* **PC Health Check:** Diagnostic routine reporting on system performance metrics.

### 🛡️ System Security
* **Quick Virus Scan:** Triggers a quick scan using Microsoft Defender (`Start-MpScan`).
* **Full Virus Scan:** Triggers a comprehensive full system scan via Microsoft Defender.

### 💾 Memory & Process Analysis
* **Top Resource Processes:** Analyzes running processes and ranks the top 10 memory-consuming tasks with Process IDs (PIDs) and usage percentages.

### ⚙️ Updates & Command Console
* **Windows Updates:** Executes PowerShell scripts to detect available operating system updates.
* **Software Updates:** Uses `winget` (Windows Package Manager) to scan installed applications for available updates.
* **Command Bar:** Natural text interface supporting simple commands (`clean temp`, `check updates`, `quick scan`, `virus`, etc.).
* **Asynchronous Execution:** Uses `QThread` multi-threading to keep the UI responsive during long-running tasks.

---

## 🛠️ Prerequisites & Requirements

* **Operating System:** Windows 10 or Windows 11
* **Python Version:** Python 3.8 or higher
* **Optional Tools:**
  * **WinGet (App Installer):** Required for checking application software updates.
  * **PSWindowsUpdate PowerShell Module:** Required for full functionality of Windows Update checks.

---

## 📥 Installation

1. **Clone or Download the Repository:**
   ```bash
   git clone https://github.com/your-username/pc-care-assistant.git
   cd pc-care-assistant
   ```

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows (Command Prompt)
   venv\Scripts\activate
   # On Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies:**
   ```bash
   pip install PySide6 psutil
   ```

---

## 🚀 Usage

Run the main application script:

```bash
python main.py
```

> **Note:** For administrative actions (such as running Microsoft Defender scans or deleting certain elevated temporary/system files), run your command prompt or terminal **as Administrator** before launching the script.

---

## 💻 Supported Quick Commands

You can type the following phrases directly into the bottom **Command Bar** and press **Enter** or click **Run**:

| Command Keyword | Action Performed |
| :--- | :--- |
| `windows update` | Runs a check for pending Windows Updates |
| `software update` | Runs `winget upgrade` to check for app updates |
| `clean temp` / `temporary` | Cleans temporary files |
| `cache` | Cleans system and browser cache directories |
| `clean disk` | Launches Windows Disk Cleanup |
| `health` | Triggers a quick system health report |
| `memory` | Lists top memory-consuming processes |
| `quick scan` / `virus` | Runs Microsoft Defender Quick Scan |
| `full scan` | Runs Microsoft Defender Full Scan |

---

## 📁 Project Structure

```text
.
├── main.py            # Main application source code containing UI & Worker threads
└── README.md          # Project documentation
```

---

## 🛡️ License

This project is licensed under the **MIT License**. Feel free to modify and distribute as needed.