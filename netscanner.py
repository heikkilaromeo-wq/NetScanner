import sys
import random
import ipaddress
import socket
import subprocess
import platform
import re
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from PySide6.QtCore import (
    Qt,
    QTimer,
    QRectF,
    QPointF,
    Signal,
    QThread,
    QObject,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPixmap,
    QPainter,
    QPen,
    QLinearGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QTabWidget,
    QSizePolicy,
    QScrollArea,
    QLayout,
)


# ============================================================
# MATRIX / FALLING CODE ANIMATION
# ============================================================

class CodeColumn:
    """Yksi jatkuvasti alhaalta ylös liikkuva binäärikoodivirta."""

    def __init__(self, x, height):
        self.x = x
        self.char_height = random.choice([16, 17, 18])
        self.speed = random.uniform(1.0, 2.0)
        self.offset = random.uniform(0, self.char_height)
        self.configure(height)

    def configure(self, height):
        # Virta on ruutua pidempi. Sama virta piirretään jatkuvana
        # silmukkana, joten se ei koskaan katoa
        self.length = max(50, int(height / self.char_height) + 12)
        self.characters = [random.choice("01") for _ in range(self.length)]
        # highlight_count = max(5, min(15, self.length // 7)) varalla (korvaa alemman rivin)
        highlight_count = max(3, min(1, self.length // 1))
        self.highlight_positions = set(
            random.sample(range(self.length), highlight_count)
        )

    def update(self, height):
        self.offset += self.speed
        cycle = self.length * self.char_height
        if self.offset >= cycle:
            self.offset %= cycle

        # Elävä binääridata: 0 - 1 vaihtuu usein.
        changes = 1
        if random.random() < 0.30:
            changes += 1
        for _ in range(changes):
            index = random.randrange(self.length)
            self.characters[index] = "1" if self.characters[index] == "0" else "0"

        # Vaihtaa korostettua kohtaa mutta määrä = VAKIO
        if random.random() < 0.015:
            old = random.choice(tuple(self.highlight_positions))
            self.highlight_positions.remove(old)
            self.highlight_positions.add(random.randrange(self.length))


# ============================================================
# MATRIX / FALLING CODE ANIMATION
# ============================================================
class MatrixCodeWidget(QWidget):
    """Täysruudun cyber-tausta: jatkuva 0/1-koodi alhaalta ylös."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns = []
        self.column_spacing = 11
        self.setMinimumHeight(420)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)  # noin 33 FPS

    def resizeEvent(self, event):
        super().resizeEvent(event)
        amount = max(8, self.width() // self.column_spacing + 2)
        self.columns = []
        for i in range(amount):
            x = i * self.column_spacing + random.randint(-2, 2)
            column = CodeColumn(x, self.height())

            # Joka toinen ylös, joka toinen alas
            column.direction = -1 if i % 2 == 0 else 1

            column.offset = random.uniform(
                0,
                column.length * column.char_height
            )
            
            self.columns.append(column)

    def animate(self):
        for column in self.columns:
            column.update(self.height())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        painter.fillRect(self.rect(), QColor("#020807"))

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(0, 45, 28, 70))
        gradient.setColorAt(0.5, QColor(0, 10, 7, 20))
        gradient.setColorAt(1.0, QColor(0, 30, 18, 50))
        painter.fillRect(self.rect(), gradient)

        normal_font = QFont("Consolas", 11)
        normal_font.setBold(True)
        highlight_font = QFont("Consolas", 12)
        highlight_font.setBold(True)
        head_font = QFont("Consolas", 13)
        head_font.setBold(True)

        for column in self.columns:
            cycle = column.length * column.char_height

            # 2 sykliä
            for repeat in (-1, 0, 1):
                base_y = ( 
                    column.direction * column.offset
                    + repeat * cycle
                )
                for index, char in enumerate(column.characters):
                    y = base_y + index * column.char_height
                    if y < -30 or y > self.height() + 30:
                        continue

                    if index == 0:
                        painter.setFont(head_font)
                        painter.setPen(QColor(0, 255, 130, ))
                        painter.drawText(QPointF(column.x, y), char)

                    elif index in column.highlight_positions:
                        painter.setFont(highlight_font)

                        # Iso pehmeä neon-hehku.
                        outer = QRectF(
                            column.x - 8,
                            y - column.char_height - 1,
                            28,
                            column.char_height + 12
                        )
                        painter.fillRect(outer, QColor(0, 255, 100, 28))

                        glow = QRectF(
                            column.x - 5,
                            y - column.char_height + 1,
                            22,
                            column.char_height + 8
                        )
                        painter.fillRect(glow, QColor(0, 255, 100, 65))

                        core = QRectF(
                            column.x - 2,
                            y - column.char_height + 3,
                            16,
                            column.char_height + 4
                        )
                        painter.fillRect(core, QColor(35, 255, 130, 210))

                        painter.setPen(QColor(245, 255, 248, 255))
                        painter.drawText(QPointF(column.x, y), char)

                    else:
                        # vaihteleva kirkkaus
                        fade = index / max(1, column.length - 1)
                        alpha = max(35, int(170 - fade * 115))
                        painter.setFont(normal_font)
                        painter.setPen(QColor(25, 205, 92, alpha))
                        painter.drawText(QPointF(column.x, y), char)


# ============================================================
# CUSTOM UI COMPONENTS
# ============================================================

class SectionTitle(QLabel):

    def __init__(self, text):
        super().__init__(text)

        self.setStyleSheet("""
            QLabel {
                color: #56f29a;
                font-family: Consolas;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
                padding-bottom: 6px;
            }
        """)


class StatusValue(QLabel):

    def __init__(self, text="--"):
        super().__init__(text)

        self.setAlignment(
            Qt.AlignRight
        )

        self.setStyleSheet("""
            QLabel {
                color: #57f78e;
                font-family: Consolas;
                font-weight: bold;
            }
        """)



# ============================================================
# REAL NETWORK SCAN WORKER
# ============================================================

class ScanWorker(QObject):
    """Runs network operations outside the GUI thread.

    Safety/operational guardrails: this version only scans RFC1918/private
    addresses and limits network sweeps to 1024 hosts. Port scans use normal
    TCP connect() calls and are limited by the Ports field.
    """

    progress = Signal(int)
    log = Signal(str)
    host_found = Signal(dict)
    port_found = Signal(dict)
    finished = Signal(bool, str)

    def __init__(self, target, scan_type, timeout_ms, threads, ports):
        super().__init__()
        self.target = target
        self.scan_type = scan_type
        self.timeout_ms = timeout_ms
        self.threads = max(1, min(threads, 500))
        self.ports = ports
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            if self.scan_type == 'Port Scan':
                self._run_port_scan()
            elif self.scan_type == 'ARP Scan':
                self._run_host_scan(include_arp=True)
            else:
                self._run_host_scan(include_arp=False)
        except Exception as exc:
            self.finished.emit(False, f'Error: {exc}')

    def _parse_private_target(self):
        raw = self.target.strip()
        try:
            if '/' in raw:
                network = ipaddress.ip_network(raw, strict=False)
                if network.version != 4:
                    raise ValueError('Only IPv4 targets are supported in this version')
                if not network.network_address.is_private:
                    raise ValueError('For safety, only private/local IPv4 ranges are allowed')
                hosts = list(network.hosts()) if network.num_addresses > 2 else [network.network_address]
            else:
                ip = ipaddress.ip_address(raw)
                if ip.version != 4:
                    raise ValueError('Only IPv4 targets are supported in this version')
                if not ip.is_private:
                    raise ValueError('For safety, only private/local IPv4 addresses are allowed')
                hosts = [ip]
        except ValueError:
            raise

        if len(hosts) > 1024:
            raise ValueError('Target range is too large. Maximum is 1024 hosts per scan.')
        return hosts

    def _ping_host(self, ip):
        if self.cancel_event.is_set():
            return False
        timeout = max(100, int(self.timeout_ms))
        ip_text = str(ip)
        try:
            if platform.system().lower().startswith('win'):
                cmd = ['ping', '-n', '1', '-w', str(timeout), ip_text]
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, timeout=(timeout / 1000) + 2,
                                        creationflags=flags)
            else:
                seconds = max(1, int((timeout + 999) / 1000))
                cmd = ['ping', '-c', '1', '-W', str(seconds), ip_text]
                result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, timeout=seconds + 2)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    def _lookup_arp(self, ip):
        """Read the OS ARP/neighbor cache after an active probe."""
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            if platform.system().lower().startswith('win'):
                out = subprocess.check_output(['arp', '-a', str(ip)], text=True,
                                              errors='ignore', creationflags=flags)
                match = re.search(r'([0-9a-f]{2}(?:-[0-9a-f]{2}){5})', out, re.I)
            else:
                out = subprocess.check_output(['arp', '-n', str(ip)], text=True, errors='ignore')
                match = re.search(r'([0-9a-f]{2}(?::[0-9a-f]{2}){5})', out, re.I)
            return match.group(1).replace('-', ':').upper() if match else '--'
        except Exception:
            return '--'

    def _resolve_name(self, ip):
        try:
            name = socket.gethostbyaddr(str(ip))[0]
            return name
        except Exception:
            return '--'

    def _run_host_scan(self, include_arp=False):
        hosts = self._parse_private_target()
        total = len(hosts)
        self.log.emit(f'[SYSTEM] Real {self.scan_type} started: {total} host(s)')
        completed = 0
        found = 0

        with ThreadPoolExecutor(max_workers=min(self.threads, total)) as pool:
            futures = {pool.submit(self._ping_host, ip): ip for ip in hosts}
            for future in as_completed(futures):
                if self.cancel_event.is_set():
                    break
                ip = futures[future]
                online = False
                try:
                    online = future.result()
                except Exception:
                    online = False
                completed += 1
                self.progress.emit(int(completed * 100 / total))
                if online:
                    found += 1
                    mac = self._lookup_arp(ip) if include_arp else '--'
                    hostname = self._resolve_name(ip)
                    data = {'ip': str(ip), 'mac': mac, 'hostname': hostname, 'status': 'ONLINE'}
                    self.host_found.emit(data)
                    suffix = f' | MAC: {mac}' if include_arp else ''
                    self.log.emit(f'[DETECTED] Host online: {ip}{suffix}')

        if self.cancel_event.is_set():
            self.finished.emit(False, 'Scan stopped by user')
        else:
            self.progress.emit(100)
            self.finished.emit(True, f'Completed. {found} host(s) online.')

    def _parse_ports(self):
        text = self.ports.strip()
        ports = set()
        for part in text.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                a, b = part.split('-', 1)
                start, end = int(a), int(b)
                if start > end:
                    start, end = end, start
                ports.update(range(start, end + 1))
            else:
                ports.add(int(part))
        ports = sorted(p for p in ports if 1 <= p <= 65535)
        if not ports:
            raise ValueError('No valid ports specified')
        if len(ports) > 2048:
            raise ValueError('Maximum is 2048 ports per scan')
        return ports

    def _run_port_scan(self):
        hosts = self._parse_private_target()
        if len(hosts) != 1:
            raise ValueError('Port Scan requires a single IP address, for example 192.168.1.10')
        host = str(hosts[0])
        ports = self._parse_ports()
        total = len(ports)
        timeout = max(0.1, self.timeout_ms / 1000)
        self.log.emit(f'[SYSTEM] Real TCP connect scan started on {host} ({total} ports)')
        completed = 0
        open_count = 0

        def probe(port):
            if self.cancel_event.is_set():
                return port, False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                return port, sock.connect_ex((host, port)) == 0
            finally:
                sock.close()

        with ThreadPoolExecutor(max_workers=min(self.threads, total)) as pool:
            futures = {pool.submit(probe, port): port for port in ports}
            for future in as_completed(futures):
                if self.cancel_event.is_set():
                    break
                port = futures[future]
                is_open = False
                try:
                    _, is_open = future.result()
                except Exception:
                    is_open = False
                completed += 1
                self.progress.emit(int(completed * 100 / total))
                if is_open:
                    open_count += 1
                    try:
                        service = socket.getservbyport(port, 'tcp')
                    except OSError:
                        service = 'unknown'
                    data = {'ip': host, 'port': port, 'service': service, 'status': 'OPEN'}
                    self.port_found.emit(data)
                    self.log.emit(f'[OPEN] {host}:{port} ({service})')

        if self.cancel_event.is_set():
            self.finished.emit(False, 'Scan stopped by user')
        else:
            self.progress.emit(100)
            self.finished.emit(True, f'Completed. {open_count} open port(s).')

# ============================================================
# MAIN WINDOW
# ============================================================

class ServiceInspectorWorker(QObject):

    finished = Signal(dict, dict)

    def __init__(self, port_data, inspector):
        super().__init__()
        self.port_data = port_data
        self.inspector = inspector

    def run(self):
        try:
            info = self.inspector(
                self.port_data['ip'],
                self.port_data['port']
            )
        except Exception as exc:
            info = {'error': str(exc)}

        self.finished.emit(
            self.port_data,
            info
        )


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Net Scanner v1.0"
        )

        self.setMinimumSize(
            1200,
            750
        )

        # Sovelluksen koko avattaessa
        self.resize(
            1500,
            900
        )

        self.scan_running = False
        self.progress_value = 0
        self.devices_found = 0
        self.open_ports_found = 0
        self.scan_started_at = None
        self.scan_thread = None
        self.scan_worker = None

        self.setup_ui()
        self.setup_timer()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        central.setStyleSheet("""
            QWidget {
                background-color: #030706;
                color: #c7d3cc;
                font-family: Consolas;
            }
        """)

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        main_layout.setSpacing(10)

        # ----------------------------------------------------
        # TOP BAR
        # ----------------------------------------------------

        top_bar = self.create_top_bar()

        main_layout.addWidget(
            top_bar
        )

        # ----------------------------------------------------
        # MAIN CONTENT
        # ----------------------------------------------------

        content_layout = QHBoxLayout()

        content_layout.setSpacing(12)

        # LEFT SIDEBAR
        sidebar = self.create_sidebar()

        sidebar.setFixedWidth(380)

        content_layout.addWidget(
            sidebar
)
        

        # RIGHT CONTENT
        right_side = QVBoxLayout()

        right_side.setSpacing(10)

        # Matrix area
        self.matrix_widget = MatrixCodeWidget()
        self.matrix_widget.setStyleSheet("background: #020807;")

        matrix_container = QFrame()

        matrix_container.setStyleSheet("""
            QFrame {
                border: 1px solid #126c4c;
                background-color: #020706;
            }
        """)

        matrix_layout = QVBoxLayout(
            matrix_container
        )

        matrix_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        matrix_layout.addWidget(
            self.matrix_widget
        )

        # Overlay texts

        right_side.addWidget(
            matrix_container,
            stretch=5
        )

        # ----------------------------------------------------
        # TABS + LOG
        # ----------------------------------------------------

        self.tabs = QTabWidget()

        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #126c4c;
                background: #020706;
            }

            QTabBar::tab {
                background: #07100d;
                color: #9ca9a2;
                border: 1px solid #124f3b;
                padding: 10px 25px;
                font-family: Consolas;
                font-size: 12px;
            }

            QTabBar::tab:selected {
                color: #60ff9c;
                background: #071b12;
                border-top: 2px solid #2cff76;
            }
        """)

        self.live_log = QTextEdit()

        self.live_log.setReadOnly(
            True
        )

        self.live_log.setStyleSheet("""
            QTextEdit {
                background-color: #020706;
                color: #58f493;
                border: none;
                padding: 12px;
                font-family: Consolas;
                font-size: 12px;
            }
        """)

        self.devices_tab = QTextEdit()
        self.devices_tab.setReadOnly(True)

        self.ports_tab = QTextEdit()
        self.ports_tab.setReadOnly(True)

        self.history_tab = QTextEdit()
        self.history_tab.setReadOnly(True)

        self.inspector_tab = QTextEdit()
        self.inspector_tab.setReadOnly(True)
        self.inspector_tab.setPlaceholderText("Scan a local IP to identify the process/service behind open ports.")

        self.tabs.addTab(
            self.live_log,
            "LIVE LOG"
        )

        self.tabs.addTab(
            self.devices_tab,
            "DEVICES (0)"
        )

        self.tabs.addTab(
            self.ports_tab,
            "OPEN PORTS (0)"
        )

        self.tabs.addTab(
            self.history_tab,
            "SCAN HISTORY"
        )
        self.tabs.addTab(
            self.inspector_tab,
            "SERVICE INSPECTOR"
        )

        self.add_log(
            "[SYSTEM] Net Scanner initialized"
        )

        self.add_log(
            "[SYSTEM] Waiting for target..."
        )

        right_side.addWidget(
            self.tabs,
            stretch=3
        )

        content_layout.addLayout(
            right_side,
            stretch=1
        )

        main_layout.addLayout(
            content_layout,
            stretch=1
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = self.create_footer()

        main_layout.addWidget(
            footer
        )

    # ========================================================
    # RESIZE MATRIX OVERLAY
    # ========================================================

    def matrix_resize_event(self, original_event):

        def event(event_obj):

            original_event(event_obj)

            self.overlay.setGeometry(
                self.matrix_widget.rect()
            )

        return event

    # ========================================================
    # TOP BAR
    # ========================================================

    def create_top_bar(self):

        frame = QFrame()

        frame.setFixedHeight(80)

        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #126c4c;
                background-color: #030907;
            }
        """)

        layout = QHBoxLayout(frame)

        import os

        logo = QLabel()

        image_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "images",
            "logo.png.png"
        )

        pixmap = QPixmap(image_path)

        print("IMAGE PATH:", image_path)
        print("EXISTS:", os.path.exists(image_path))
        print("PIXMAP IS NULL:", pixmap.isNull())

        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                60,
                60,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        else:
            print("ERROR: Qt could not load the image!")

        logo.setFixedSize(60, 60)
        logo.setAlignment(Qt.AlignCenter)

        logo.setStyleSheet("""
            QLabel {
                border:none;
                background: transparent;
            }
        """)
        
        title_layout = QVBoxLayout()

        title = QLabel(
            "NET SCANNER"
        )

        title.setStyleSheet("""
            QLabel {
                color: #42c77a;
                font-size: 24px;
                font-family: Consolas;
                font-weight: bold;
                letter-spacing: 3px;
            }
        """)

        subtitle = QLabel(
            "NETWORK DISCOVERY & SECURITY TOOL"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #42c77a;
                font-size: 10px;
                font-family: Consolas;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        layout.addWidget(logo)
        layout.addLayout(title_layout)

# ========================================================
# SCAN STATUS TOP BAR
# ========================================================

        scan_status_layout = QVBoxLayout()

        scan_status_layout.setSpacing(2)

# SCANNING NETWORK
        self.scanning_label = QLabel("SCANNING NETWORK")

        self.scanning_label.setAlignment(Qt.AlignCenter)

        self.scanning_label.setStyleSheet("""
            QLabel {
                color: #57f78e;
                background: transparent;
                font-family: Consolas;
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)

# IP ADDRESS
        self.target_display = QLabel("192.168.1.0/24")

        self.target_display.setAlignment(Qt.AlignCenter)

        self.target_display.setStyleSheet("""
            QLabel {
                color: #c8d6d0;
                background: transparent;
                font-family: Consolas;
                font-size: 13px;
            }
        """)

# PROGRESS %
        self.big_progress = QLabel("0%")

        self.big_progress.setAlignment(Qt.AlignCenter)

        self.big_progress.setStyleSheet("""
            QLabel {
                color: #57ff8a;
                background: transparent;
                font-family: Consolas;
                font-size: 20px;
                font-weight: bold;
            }
        """)

        scan_status_layout.addWidget(self.scanning_label)
        scan_status_layout.addWidget(self.target_display)
        scan_status_layout.addWidget(self.big_progress)

# Keskittää koko scan-statusalueen
        layout.addStretch()
        layout.addLayout(scan_status_layout)
        layout.addStretch()

# ========================================================
# SYSTEM STATUS
# ========================================================

        status = QLabel("● SYSTEM READY")          

        status.setStyleSheet("""
            color: #60ff9c;
            background: transparent;
            font-family: Consolas;
            font-size: 12px;
            font-weight: bold;
            padding: 5px;
        """)

        layout.addWidget(status)

        return frame

    # ========================================================
    # SIDEBAR
    # ========================================================

    def create_sidebar(self):

        sidebar = QWidget()

        layout = QVBoxLayout(
            sidebar
        )

        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        # SCAN TARGET
        target_frame = self.create_panel()

        target_layout = QVBoxLayout(
            target_frame
        )
        target_layout.setSpacing(6)
        target_layout.setContentsMargins(12, 10, 12, 10)

        target_layout.addWidget(
            SectionTitle("⌖ SCAN TARGET")
        )

        self.target_input = QLineEdit()

        self.target_input.setPlaceholderText(
            "192.168.1.0/24"
        )

        self.target_input.setText(
            "192.168.1.0/24"
        )

        self.target_input.setStyleSheet(
            self.input_style()
        )

        target_layout.addWidget(
            self.target_input
        )

        hint = QLabel(
            "Enter an IP address or network range"
        )

        hint.setStyleSheet("""
            QLabel {
                color: #7f8f87;
                font-family: Consolas;
                font-size: 10px;
            }
        """)

        target_layout.addWidget(hint)

        layout.addWidget(
            target_frame
        )

        # OPTIONS
        options_frame = self.create_panel()

        options_frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        options_layout = QVBoxLayout(options_frame)

        options_layout.setSizeConstraint(
            QLayout.SetMinimumSize
        )

        options_layout.setSpacing(2)
        options_layout.setContentsMargins(15, 5, 15, 5)

        options_layout.addWidget(
            SectionTitle("⚙ SCAN OPTIONS")
)

        # SCAN TYPE
        scan_type_label = QLabel("Scan Type")

        self.scan_type = self.create_combo(
            ["Ping Sweep", "ARP Scan", "Port Scan"]
)

        self.scan_type.setFixedHeight(30)

        self.scan_type.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
)

        options_layout.addWidget(scan_type_label)
        options_layout.addWidget(self.scan_type)


        # TIMEOUT
        timeout_label = QLabel("Timeout (ms)")

        self.timeout = self.create_combo(
            ["500", "1000", "2000", "5000"]
)

        self.timeout.setFixedHeight(32)

        self.timeout.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
)

        options_layout.addWidget(timeout_label)
        options_layout.addWidget(self.timeout)


        # THREADS
        threads_label = QLabel("Threads")

        self.threads = self.create_combo(
            ["50", "100", "200", "500"]
)

        self.threads.setFixedHeight(32)

        self.threads.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
)

        options_layout.addWidget(threads_label)
        options_layout.addWidget(self.threads)


        # PORTS
        ports_label = QLabel("Ports")

        self.ports = QLineEdit("1-1000")

        self.ports.setStyleSheet(
            self.input_style()
)

        self.ports.setFixedHeight(32)

        options_layout.addWidget(ports_label)
        options_layout.addWidget(self.ports)


        layout.addWidget(options_frame)

        # ACTIONS
        action_frame = self.create_panel()

        action_layout = QVBoxLayout(
            action_frame
        )
        action_layout.setSpacing(4)
        action_layout.setContentsMargins(12, 8, 12, 8)

        action_layout.addWidget(
            SectionTitle("ϟ ACTIONS")
        )

        self.start_button = QPushButton(
            "▶  START SCAN"
        )

        self.start_button.clicked.connect(
            self.start_scan
        )

        self.stop_button = QPushButton(
            "■  STOP SCAN"
        )

        self.stop_button.clicked.connect(
            self.stop_scan
        )

        self.clear_button = QPushButton(
            "♲  CLEAR RESULTS"
        )

        self.clear_button.clicked.connect(
            self.clear_results
        )

        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #24c968;
                color: #041009;
                border: none;
                padding: 8px;
                font-family: Consolas;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #45ef87;
            }
        """)

        button_style = """
            QPushButton {
                background-color: #050d0a;
                color: #b5c1ba;
                border: 1px solid #124c38;
                padding: 8px;
                font-family: Consolas;
                font-weight: bold;
            }

            QPushButton:hover {
                border-color: #2cff76;
                color: #57ff92;
            }
        """

        self.stop_button.setStyleSheet(
            button_style
        )

        self.clear_button.setStyleSheet(
            button_style
        )

        action_layout.addWidget(
            self.start_button
        )

        action_layout.addWidget(
            self.stop_button
        )

        action_layout.addWidget(
            self.clear_button
        )

        layout.addWidget(
            action_frame
        )

        # STATUS
        status_frame = self.create_panel()

        status_layout = QVBoxLayout(
            status_frame
        )
        status_layout.setSpacing(6)
        status_layout.setContentsMargins(12, 10, 12, 10)

        status_layout.addWidget(
            SectionTitle("⌁ SCAN STATUS")
        )

        self.status_label = QLabel(
            "Status: READY"
        )

        self.status_label.setStyleSheet("""
            QLabel {
                color: #aebbb4;
                font-family: Consolas;
                font-size: 12px;
            }
        """)

        self.side_progress = QProgressBar()

        self.side_progress.setValue(0)

        self.side_progress.setTextVisible(
            False
        )

        self.side_progress.setStyleSheet("""
            QProgressBar {
                background-color: #06110d;
                border: none;
                height: 8px;
            }

            QProgressBar::chunk {
                background-color: #2cff76;
            }
        """)

        self.device_count = QLabel(
            "Devices Found: 0"
        )

        self.elapsed_label = QLabel(
            "Elapsed Time: 00:00:00"
        )

        status_layout.addWidget(
            self.status_label
        )

        status_layout.addWidget(
            QLabel("Progress:")
        )

        status_layout.addWidget(
            self.side_progress
        )

        status_layout.addWidget(
            self.device_count
        )

        status_layout.addWidget(
            self.elapsed_label
        )

        layout.addWidget(
            status_frame
        )
        ##layout.addStretch()

        return sidebar

    # ========================================================
    # PANELS
    # ========================================================

    def create_panel(self):

        frame = QFrame()

        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #124c38;
                background-color: #030b08;
            }

            QLabel {
                border: none;
                background: transparent;
                color: #9aa8a0;
                font-family: Consolas;
                font-size: 11px;
            }
        """)

        return frame

    def input_style(self):

        return """
            QLineEdit {
                background-color: #030806;
                color: #d7e0da;
                border: 1px solid #176448;
                padding: 10px;
                font-family: Consolas;
                font-size: 12px;
            }

            QLineEdit:focus {
                border: 1px solid #36f986;
            }
        """

    def create_combo(self, items):

        combo = QComboBox()

        combo.addItems(items)
        combo.setCurrentIndex(0)

    # Pakotetaan normaali korkeus
        combo.setFixedHeight(44)

        combo.setStyleSheet("""
        QComboBox {
            background-color: #030806;
            color: #d7e0da;

            border: 1px solid #176448;

            padding-left: 12px;
            padding-right: 40px;

            font-family: Consolas;
            font-size: 16px;
        }

        QComboBox::drop-down {
            width: 35px;
            border: none;
        }

        QComboBox QAbstractItemView {
            background-color: #07100c;
            color: #ffffff;

            selection-background-color: #164f39;
            selection-color: #ffffff;
        }
    """)

        return combo

    # ========================================================
    # FOOTER
    # ========================================================

    def create_footer(self):

        frame = QFrame()

        frame.setFixedHeight(55)

        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #124c38;
                background-color: #030b08;
            }

            QLabel {
                color: #61c985;
                font-family: Consolas;
                font-size: 11px;
                border: none;
            }
        """)

        layout = QHBoxLayout(
            frame
        )

        self.local_ip_label = QLabel("▣ LOCAL IP: --")
        layout.addWidget(self.local_ip_label)

        layout.addStretch()

        self.gateway_label = QLabel("⌘ GATEWAY: --")
        layout.addWidget(self.gateway_label)

        layout.addStretch()

        self.dns_label = QLabel("◎ DNS: --")
        layout.addWidget(self.dns_label)

        layout.addStretch()

        layout.addWidget(
            QLabel("SYSTEM: Windows")
        )

        layout.addStretch()

        self.clock_label = QLabel()

        layout.addWidget(
            self.clock_label
        )

        return frame

    # ========================================================
    # TIMERS / LOCAL NETWORK INFO
    # ========================================================

    def setup_timer(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_elapsed)

        self.update_clock()
        self.refresh_network_info()

    def update_clock(self):
        self.clock_label.setText("◷ " + datetime.now().strftime("%H:%M:%S"))

    def update_elapsed(self):
        if not self.scan_started_at:
            return
        seconds = int(time.monotonic() - self.scan_started_at)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        self.elapsed_label.setText(f"Elapsed Time: {h:02d}:{m:02d}:{s:02d}")

    def refresh_network_info(self):
        local_ip = '--'
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            local_ip = sock.getsockname()[0]
            sock.close()
        except OSError:
            pass
        self.local_ip_label.setText(f"▣ LOCAL IP: {local_ip}")

        gateway = '--'
        dns = '--'
        if platform.system().lower().startswith('win'):
            try:
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                route = subprocess.check_output(['route', 'print', '-4'], text=True,
                                                errors='ignore', creationflags=flags)
                for line in route.splitlines():
                    parts = line.split()
                    if len(parts) >= 3 and parts[0] == '0.0.0.0' and parts[1] == '0.0.0.0':
                        gateway = parts[2]
                        break
                ipconfig = subprocess.check_output(['ipconfig', '/all'], text=True,
                                                   errors='ignore', creationflags=flags)
                match = re.search(r'DNS Servers[^:]*:\s*([0-9.]+)', ipconfig, re.I)
                if match:
                    dns = match.group(1)
            except Exception:
                pass
        self.gateway_label.setText(f"⌘ GATEWAY: {gateway}")
        self.dns_label.setText(f"◎ DNS: {dns}")

    # ========================================================
    # REAL SCAN CONTROL
    # ========================================================

    def start_scan(self):
        if self.scan_running:
            return

        target = self.target_input.text().strip()
        scan_type = self.scan_type.currentText()
        if not target:
            self.add_log('[ERROR] No target specified')
            return

        # Fast validation before creating the worker.
        try:
            raw = target
            if '/' in raw:
                network = ipaddress.ip_network(raw, strict=False)
                if network.version != 4 or not network.network_address.is_private:
                    raise ValueError
                host_count = network.num_addresses - (2 if network.num_addresses > 2 else 0)
                if scan_type != 'Port Scan' and host_count > 1024:
                    self.add_log('[ERROR] Target range is too large (maximum 1024 hosts)')
                    return
            else:
                ip = ipaddress.ip_address(raw)
                if ip.version != 4 or not ip.is_private:
                    raise ValueError
        except ValueError:
            self.add_log('[ERROR] Enter a valid private IPv4 target, e.g. 192.168.1.0/24')
            return

        if scan_type == 'Port Scan' and '/' in target:
            network = ipaddress.ip_network(target, strict=False)
            if network.num_addresses > 1:
                self.add_log('[ERROR] Port Scan requires one IP, e.g. 192.168.1.10')
                return

        self.clear_results(silent=True)
        self.scan_running = True
        self.progress_value = 0
        self.scan_started_at = time.monotonic()
        self.elapsed_label.setText('Elapsed Time: 00:00:00')
        self.elapsed_timer.start(250)

        self.target_display.setText(target)
        self.status_label.setText('Status: SCANNING')
        self.scanning_label.setText('SCANNING NETWORK' if scan_type != 'Port Scan' else 'SCANNING PORTS')
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.refresh_network_info()

        self.add_log(f'[SYSTEM] Target set to {target}')
        self.add_log(f'[SYSTEM] Scan type: {scan_type}')
        self.add_log('[SYSTEM] Starting real scan...')

        self.scan_thread = QThread(self)
        self.scan_worker = ScanWorker(
            target=target,
            scan_type=scan_type,
            timeout_ms=int(self.timeout.currentText()),
            threads=int(self.threads.currentText()),
            ports=self.ports.text(),
        )
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progress.connect(self.on_worker_progress)
        self.scan_worker.log.connect(self.add_log)
        self.scan_worker.host_found.connect(self.on_host_found)
        self.scan_worker.port_found.connect(self.on_port_found)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        self.scan_thread.start()

    def stop_scan(self):
        if not self.scan_running:
            return
        self.add_log('[SYSTEM] Stop requested...')
        self.status_label.setText('Status: STOPPING')
        self.scanning_label.setText('STOPPING SCAN')
        self.stop_button.setEnabled(False)
        if self.scan_worker:
            self.scan_worker.cancel()

    def on_worker_progress(self, value):
        self.progress_value = max(0, min(100, value))
        self.update_progress()

    def on_host_found(self, data):
        self.devices_found += 1
        line = f"{data['ip']:<16} {data['status']:<8} MAC: {data['mac']:<17} HOST: {data['hostname']}"
        self.devices_tab.append(line)
        self.update_progress()

    def on_port_found(self, data):

        print("### ON_PORT_FOUND CALLED ###", data, flush=True)

        self.open_ports_found += 1

        self.ports_tab.append(
            f"{data['ip']}:{data['port']:<5} "
            f"{data['service']:<15} "
            f"{data['status']}"
    )

        self.tabs.setTabText(
            2,
            f"OPEN PORTS ({self.open_ports_found})"
    )

        if not self._is_local_ip(data['ip']):
            return

        thread = QThread(self)

        worker = ServiceInspectorWorker(
            data,
            self._inspect_local_port
        )

        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        worker.finished.connect(
            self._show_service_info
        )

        worker.finished.connect(thread.quit)

        worker.finished.connect(worker.deleteLater)

        thread.finished.connect(thread.deleteLater)

            # Estetään Pythonia poistamasta niitä kesken työn
        if not hasattr(self, "_inspector_jobs"):
            self._inspector_jobs = []

        self._inspector_jobs.append(
            (thread, worker)
        )

        def cleanup():
            self._inspector_jobs[:] = [
                job for job in self._inspector_jobs
                if job[0] is not thread
            ]

        thread.finished.connect(cleanup)

        thread.start()

    def _local_ipv4_addresses(self):
        addresses = {'127.0.0.1'}
        try:
            for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                addresses.add(item[4][0])
        except Exception:
            pass
        if platform.system().lower().startswith('win'):
            try:
                flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                out = subprocess.check_output(['ipconfig'], text=True, errors='ignore', creationflags=flags)
                addresses.update(re.findall(r'(?:IPv4[^:]*:\s*)(\d{1,3}(?:\.\d{1,3}){3})', out, re.I))
            except Exception:
                pass
        return addresses

    def _is_local_ip(self, ip):

        local_ips = self._local_ipv4_addresses()

        print("LOCAL IPS:", local_ips, flush=True)
        print("CHECKING IPS:", ip, flush=True)

        return str(ip) in local_ips

    def _inspect_local_port(self, ip, port):
        if not platform.system().lower().startswith('win'):
            return {'error': 'Local service inspection is currently implemented for Windows.'}
        ps = (
            f"$c=Get-NetTCPConnection -State Listen -LocalPort {int(port)} -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.LocalAddress -eq '{ip}' -or $_.LocalAddress -eq '0.0.0.0' }} | Select-Object -First 1; "
            "if (-not $c) { return }; $owner=$c.OwningProcess; $p=Get-Process -Id $owner -ErrorAction SilentlyContinue; "
            "$svc=Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -eq $owner } | Select-Object -First 1; "
            "[PSCustomObject]@{ PID=$owner; ProcessName=$p.ProcessName; ProcessPath=$p.Path; ServiceName=$svc.Name; DisplayName=$svc.DisplayName; State=$svc.State; StartMode=$svc.StartMode } | ConvertTo-Json -Compress"
        )
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            out = subprocess.check_output(['powershell', '-NoProfile', '-Command', ps], text=True, errors='ignore', creationflags=flags, timeout=8).strip()
            return json.loads(out) if out else {'error': 'No matching local listening process was found.'}
        except Exception as exc:
            return {'error': str(exc)}

    def _show_service_info(self, port_data, info):
        self.inspector_tab.append('')
        self.inspector_tab.append('=' * 62)
        self.inspector_tab.append(f"LOCAL PORT: {port_data['ip']}:{port_data['port']}")
        self.inspector_tab.append(f"NETWORK SERVICE: {port_data['service']}")
        if info.get('error'):
            self.inspector_tab.append(f"STATUS: {info['error']}")
            self.add_log(f"[INSPECTOR] {port_data['ip']}:{port_data['port']} - owner not resolved")
            return
        self.inspector_tab.append(f"PROCESS: {info.get('ProcessName') or '--'}")
        self.inspector_tab.append(f"PID: {info.get('PID') or '--'}")
        for key, label in [('ServiceName','SERVICE'), ('DisplayName','DISPLAY NAME'), ('State','SERVICE STATE'), ('StartMode','START MODE'), ('ProcessPath','PATH')]:
            if info.get(key):
                self.inspector_tab.append(f"{label}: {info[key]}")
        self.add_log(f"[INSPECTOR] Identified local owner for port {port_data['port']}: {info.get('ProcessName') or 'unknown'}")

    def on_scan_finished(self, success, message):
        self.scan_running = False
        self.elapsed_timer.stop()
        self.update_elapsed()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)

        if success:
            self.progress_value = 100
            self.status_label.setText('Status: COMPLETE')
            self.scanning_label.setText('SCAN COMPLETE')
            self.add_log(f'[SYSTEM] {message}')
        else:
            self.status_label.setText('Status: STOPPED' if message == 'Scan stopped by user' else 'Status: ERROR')
            self.scanning_label.setText('SCAN STOPPED' if message == 'Scan stopped by user' else 'SCAN ERROR')
            self.add_log(f'[SYSTEM] {message}')

        self.update_progress()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.history_tab.append(
            f"{timestamp} | {self.scan_type.currentText()} | {self.target_input.text().strip()} | {message}"
        )
        self.scan_worker = None
        self.scan_thread = None

    def update_progress(self):
        value = self.progress_value

        self.big_progress.setText(f'{value}%')
        self.side_progress.setValue(value)

        self.device_count.setText(
            f'Devices Found: {self.devices_found}'
        )
        
        self.tabs.setTabText(
            1, 
            f'DEVICES ({self.devices_found})'
        )

        self.tabs.setTabText(
            2,
            f'OPEN PORTS ({self.open_ports_found})'
        )

    def clear_results(self, silent=False):
        if self.scan_running:
            self.add_log('[SYSTEM] Stop the current scan before clearing results')
            return
        self.live_log.clear()
        self.devices_tab.clear()
        self.ports_tab.clear()
        self.history_tab.clear()
        self.inspector_tab.clear()
        self.progress_value = 0
        self.devices_found = 0
        self.open_ports_found = 0
        self.scan_started_at = None
        self.elapsed_label.setText('Elapsed Time: 00:00:00')
        self.update_progress()
        self.status_label.setText('Status: READY')
        self.scanning_label.setText('READY')
        if not silent:
            self.add_log('[SYSTEM] Results cleared')


    def closeEvent(self, event):
        if self.scan_worker:
            self.scan_worker.cancel()
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.quit()
            self.scan_thread.wait(1500)
        event.accept()

    # ========================================================
    # LOG
    # ========================================================

    def add_log(self, text):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.live_log.append(
            f"[{timestamp}] {text}"
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()

    window.showMaximized()

    sys.exit(app.exec())