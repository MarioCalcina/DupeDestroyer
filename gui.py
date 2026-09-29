import os
import sys
from collections.abc import Callable

from PyQt6.QtCore import QObject
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QThread
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QFrame
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from dupe_core import DuplicateGroup
from dupe_core import ScanResult
from dupe_core import build_duplicate_plan
from dupe_core import count_duplicate_files
from dupe_core import count_reclaimable_bytes
from dupe_core import delete_duplicate_files


APP_STYLESHEET = """
#Root {
    background-color: #090f14;
    background-image: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #10222f, stop:0.45 #101a25, stop:1 #0b1118
    );
}
QFrame#HeroCard {
    border: 1px solid #2a4f64;
    border-radius: 18px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #173446, stop:1 #1c2f3f
    );
}
QFrame#Card {
    border: 1px solid #23394a;
    border-radius: 16px;
    background-color: #0f1b25;
}
QLabel#Title {
    font-family: "Bahnschrift SemiBold", "Segoe UI Variable Text", "Segoe UI";
    font-size: 27px;
    color: #eff7ff;
}
QLabel#Subtitle {
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: 13px;
    color: #9fbbce;
}
QLabel#SectionTitle {
    font-family: "Bahnschrift SemiBold", "Segoe UI Variable Text", "Segoe UI";
    font-size: 17px;
    color: #ecf5ff;
}
QLabel#FieldLabel {
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: 12px;
    color: #acc5d8;
}
QLabel#StatusBadge {
    border: 1px solid #315971;
    border-radius: 14px;
    padding: 5px 12px;
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: 11px;
    color: #d9ebf8;
    background-color: #244256;
}
QLabel#StatusBadge[state="busy"] {
    border-color: #3b647c;
    color: #def2ff;
    background-color: #2d546a;
}
QLabel#StatusBadge[state="ok"] {
    border-color: #356649;
    color: #ddffe8;
    background-color: #2a5a40;
}
QLabel#StatusBadge[state="warn"] {
    border-color: #8c7040;
    color: #fff1d1;
    background-color: #6f572f;
}
QLabel#StatusBadge[state="error"] {
    border-color: #8a4a4a;
    color: #ffe0e0;
    background-color: #673535;
}
QFrame#MetricCard {
    border: 1px solid #2e4a5f;
    border-radius: 12px;
    background-color: rgba(8, 16, 23, 0.35);
}
QLabel#MetricLabel {
    color: #a8c0d2;
    font-size: 11px;
    font-family: "Segoe UI Variable Text", "Segoe UI";
}
QLabel#MetricValue {
    color: #f3fbff;
    font-size: 19px;
    font-family: "Bahnschrift SemiBold", "Segoe UI Variable Text", "Segoe UI";
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
    border: 1px solid #2c4659;
    border-radius: 10px;
    background-color: #0b151d;
    color: #eef8ff;
    padding: 7px 10px;
    selection-background-color: #2f607a;
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: 12px;
}
QPlainTextEdit#SummaryBox {
    font-family: "Consolas", "Cascadia Mono", "Segoe UI";
    padding: 8px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {
    border: 1px solid #4f7c96;
}
QComboBox::drop-down {
    width: 24px;
    border: none;
}
QComboBox QAbstractItemView {
    border: 1px solid #2f4a5f;
    background: #101d28;
    color: #e8f4ff;
    selection-background-color: #2f607a;
}
QPushButton {
    border: 1px solid #35576d;
    border-radius: 12px;
    color: #e8f3fb;
    background-color: #213847;
    font-family: "Bahnschrift SemiBold", "Segoe UI Variable Text", "Segoe UI";
    font-size: 12px;
    min-height: 34px;
    padding: 4px 14px;
}
QPushButton:hover {
    background-color: #29465a;
}
QPushButton:pressed {
    background-color: #1b2e3d;
}
QPushButton:disabled {
    border-color: #2a3f4f;
    color: #7e98aa;
    background-color: #172631;
}
QPushButton[role="primary"] {
    border: 1px solid #4a8bb4;
    background-color: #2f6d93;
    color: #f4fbff;
}
QPushButton[role="primary"]:hover {
    background-color: #3d7da5;
}
QPushButton[role="danger"] {
    border: 1px solid #9d5252;
    background-color: #7f3f3f;
    color: #fff0f0;
}
QPushButton[role="danger"]:hover {
    background-color: #955050;
}
QTableWidget {
    border: 1px solid #2b4455;
    border-radius: 12px;
    background-color: #0b151d;
    color: #e7f3fd;
    gridline-color: #172530;
    selection-background-color: #2b556d;
    selection-color: #f7fcff;
    outline: none;
}
QHeaderView::section {
    border: none;
    border-right: 1px solid #223646;
    padding: 8px 10px;
    background-color: #132635;
    color: #b9d3e4;
    font-family: "Bahnschrift SemiBold", "Segoe UI Variable Text", "Segoe UI";
    font-size: 11px;
}
QTableCornerButton::section {
    border: none;
    background-color: #132635;
}
QTableWidget::item {
    padding: 5px 8px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #2b556d;
}
QScrollBar:vertical {
    width: 11px;
    background: transparent;
    margin: 2px;
}
QScrollBar::handle:vertical {
    border-radius: 5px;
    background: #325265;
    min-height: 28px;
}
QScrollBar:horizontal {
    height: 11px;
    background: transparent;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    border-radius: 5px;
    background: #325265;
    min-width: 28px;
}
QStatusBar {
    background-color: #0d1720;
    color: #b7d0df;
    border-top: 1px solid #223646;
}
"""


class Worker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, func: Callable[..., object], *args: object) -> None:
        super().__init__()
        self._func = func
        self._args = args

    @pyqtSlot()
    def run(self) -> None:
        try:
            result = self._func(*self._args)
        except Exception as exc:  # pragma: no cover - safety net
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


def _format_bytes(total_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(total_bytes)
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    return f"{value:.2f} {units[unit_index]}"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DupeDestroyer")
        self.resize(1240, 780)
        self.setMinimumSize(980, 640)

        self._busy = False
        self._scan_result: ScanResult | None = None
        self._active_thread: QThread | None = None
        self._active_worker: Worker | None = None
        self._scan_target_directory: str | None = None

        self._build_ui()
        self._wire_events()
        self._apply_theme()
        self._set_status_badge("Listo para escanear", "ok")
        self.statusBar().showMessage("Listo")

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        top_layout = QVBoxLayout(root)
        top_layout.setContentsMargins(22, 18, 22, 18)
        top_layout.setSpacing(14)

        self._hero_card = QFrame()
        self._hero_card.setObjectName("HeroCard")
        hero_layout = QHBoxLayout(self._hero_card)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.setSpacing(18)

        hero_left = QVBoxLayout()
        hero_left.setSpacing(4)
        title_label = QLabel("DupeDestroyer")
        title_label.setObjectName("Title")
        subtitle_label = QLabel(
            "Deteccion profesional de duplicados con eliminacion segura."
        )
        subtitle_label.setObjectName("Subtitle")
        hero_left.addWidget(title_label)
        hero_left.addWidget(subtitle_label)

        hero_right = QVBoxLayout()
        hero_right.setSpacing(10)
        hero_right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._status_badge = QLabel("Estado")
        self._status_badge.setObjectName("StatusBadge")
        self._status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_badge.setMinimumWidth(220)
        hero_right.addWidget(self._status_badge, alignment=Qt.AlignmentFlag.AlignRight)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(8)
        duplicates_card, self._duplicates_value = self._create_metric_card("Duplicados", "0")
        reclaim_card, self._reclaim_value = self._create_metric_card("Recuperable", "0 B")
        metrics_layout.addWidget(duplicates_card)
        metrics_layout.addWidget(reclaim_card)
        hero_right.addLayout(metrics_layout)

        hero_layout.addLayout(hero_left, stretch=3)
        hero_layout.addLayout(hero_right, stretch=2)
        top_layout.addWidget(self._hero_card)

        self._controls_card = QFrame()
        self._controls_card.setObjectName("Card")
        controls_outer = QVBoxLayout(self._controls_card)
        controls_outer.setContentsMargins(18, 14, 18, 16)
        controls_outer.setSpacing(12)

        controls_title = QLabel("Configuracion de escaneo")
        controls_title.setObjectName("SectionTitle")
        controls_outer.addWidget(controls_title)

        controls_layout = QGridLayout()
        controls_layout.setHorizontalSpacing(10)
        controls_layout.setVerticalSpacing(10)
        controls_layout.setColumnStretch(1, 2)
        controls_layout.setColumnStretch(2, 2)
        controls_outer.addLayout(controls_layout)

        directory_label = QLabel("Directorio")
        directory_label.setObjectName("FieldLabel")
        keep_label = QLabel("Regla de conservacion")
        keep_label.setObjectName("FieldLabel")
        passes_label = QLabel("Pasadas de sobrescritura")
        passes_label.setObjectName("FieldLabel")

        self._directory_edit = QLineEdit(os.getcwd())
        self._directory_edit.setPlaceholderText("Carpeta a escanear")
        self._browse_button = QPushButton("Explorar...")

        self._keep_combo = QComboBox()
        self._keep_combo.addItem("Conservar primero creado", userData="oldest")
        self._keep_combo.addItem("Conservar ultimo creado", userData="newest")
        self._keep_combo.addItem("Conservar ruta alfabetica", userData="path")
        self._keep_combo.addItem("Conservar primero encontrado", userData="first")

        self._passes_spin = QSpinBox()
        self._passes_spin.setMinimum(1)
        self._passes_spin.setMaximum(35)
        self._passes_spin.setValue(3)

        self._scan_button = QPushButton("Escanear")
        self._scan_button.setProperty("role", "primary")
        self._delete_button = QPushButton("Eliminar duplicados")
        self._delete_button.setProperty("role", "danger")
        self._delete_button.setEnabled(False)

        controls_layout.addWidget(directory_label, 0, 0)
        controls_layout.addWidget(self._directory_edit, 0, 1, 1, 2)
        controls_layout.addWidget(self._browse_button, 0, 3)

        controls_layout.addWidget(keep_label, 1, 0)
        controls_layout.addWidget(self._keep_combo, 1, 1)
        controls_layout.addWidget(passes_label, 1, 2)
        controls_layout.addWidget(self._passes_spin, 1, 3)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        actions_layout.addWidget(self._scan_button)
        actions_layout.addWidget(self._delete_button)
        actions_layout.addStretch(1)
        controls_outer.addLayout(actions_layout)

        top_layout.addWidget(self._controls_card)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)
        top_layout.addLayout(content_layout, stretch=1)

        self._results_card = QFrame()
        self._results_card.setObjectName("Card")
        results_outer = QVBoxLayout(self._results_card)
        results_outer.setContentsMargins(16, 14, 16, 16)
        results_outer.setSpacing(10)

        results_title = QLabel("Resultados")
        results_title.setObjectName("SectionTitle")
        results_outer.addWidget(results_title)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Hash", "Tamano", "Conservar", "Eliminar"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setShowGrid(False)
        results_outer.addWidget(self._table)

        self._summary_card = QFrame()
        self._summary_card.setObjectName("Card")
        summary_outer = QVBoxLayout(self._summary_card)
        summary_outer.setContentsMargins(16, 14, 16, 16)
        summary_outer.setSpacing(8)
        summary_outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        summary_title = QLabel("Resumen")
        summary_title.setObjectName("SectionTitle")
        summary_outer.addWidget(summary_title)

        self._summary_box = QPlainTextEdit(self._summary_card)
        self._summary_box.setObjectName("SummaryBox")
        self._summary_box.setReadOnly(True)
        self._summary_box.setPlaceholderText("Ejecuta un escaneo para ver el resumen aqui.")
        self._summary_box.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self._summary_box.setMinimumHeight(0)
        self._summary_box.document().setDocumentMargin(6)
        summary_outer.addWidget(self._summary_box)
        summary_outer.setStretchFactor(self._summary_box, 1)

        content_layout.addWidget(self._results_card, stretch=3)
        content_layout.addWidget(self._summary_card, stretch=2)

    def _create_metric_card(self, label_text: str, value_text: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("MetricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(1)

        label = QLabel(label_text)
        label.setObjectName("MetricLabel")
        value = QLabel(value_text)
        value.setObjectName("MetricValue")

        layout.addWidget(label)
        layout.addWidget(value)
        return card, value

    def _apply_theme(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)
        self._apply_shadow(self._hero_card, blur=34, offset_y=10)
        self._apply_shadow(self._controls_card, blur=26, offset_y=8)
        self._apply_shadow(self._results_card, blur=22, offset_y=7)
        self._apply_shadow(self._summary_card, blur=22, offset_y=7)

    def _apply_shadow(self, widget: QWidget, blur: int, offset_y: int) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setXOffset(0)
        shadow.setYOffset(offset_y)
        shadow.setColor(QColor(0, 0, 0, 92))
        widget.setGraphicsEffect(shadow)

    def _animate_summary(self) -> None:
        return

    def _set_status_badge(self, text: str, state: str) -> None:
        self._status_badge.setText(text)
        self._status_badge.setProperty("state", state)
        style = self._status_badge.style()
        if style is not None:
            style.unpolish(self._status_badge)
            style.polish(self._status_badge)
        self._status_badge.update()

    def _wire_events(self) -> None:
        self._browse_button.clicked.connect(self._choose_directory)
        self._scan_button.clicked.connect(self._start_scan)
        self._delete_button.clicked.connect(self._start_delete)
        self._directory_edit.textChanged.connect(self._invalidate_scan)
        self._keep_combo.currentIndexChanged.connect(self._invalidate_scan)

    def _choose_directory(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Selecciona carpeta",
            self._directory_edit.text().strip() or os.getcwd(),
        )
        if chosen:
            self._directory_edit.setText(chosen)

    def _invalidate_scan(self) -> None:
        self._scan_result = None
        self._scan_target_directory = None
        self._table.setRowCount(0)
        self._summary_box.clear()
        self._update_dashboard_metrics(None)
        self._set_status_badge("Listo para escanear", "ok")
        self._refresh_action_state()

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self._directory_edit.setEnabled(not busy)
        self._browse_button.setEnabled(not busy)
        self._keep_combo.setEnabled(not busy)
        self._passes_spin.setEnabled(not busy)
        self._scan_button.setEnabled(not busy)
        self._refresh_action_state()
        self.statusBar().showMessage(message)

    def _refresh_action_state(self) -> None:
        has_duplicates = self._scan_result is not None and count_duplicate_files(self._scan_result) > 0
        self._delete_button.setEnabled((not self._busy) and has_duplicates)

    def _run_async(
        self,
        func: Callable[..., object],
        args: tuple[object, ...],
        on_done: Callable[[object], None],
        start_message: str,
    ) -> None:
        if self._active_thread is not None:
            return

        self._set_busy(True, start_message)
        self._set_status_badge("Procesando...", "busy")
        thread = QThread(self)
        worker = Worker(func, *args)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(on_done)
        worker.finished.connect(self._on_worker_finished)
        worker.failed.connect(self._on_worker_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_active_worker)

        self._active_thread = thread
        self._active_worker = worker
        thread.start()

    def _start_scan(self) -> None:
        if self._busy:
            return

        directory = os.path.abspath(self._directory_edit.text().strip())
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Directorio invalido", "Selecciona una carpeta valida.")
            return

        self._scan_target_directory = directory
        keep_strategy = self._keep_combo.currentData()
        self._run_async(
            func=self._scan_task,
            args=(directory, keep_strategy),
            on_done=self._on_scan_done,
            start_message="Escaneando...",
        )

    @staticmethod
    def _scan_task(directory: str, keep_strategy: str) -> ScanResult:
        return build_duplicate_plan(directory, keep_strategy)

    def _on_scan_done(self, result: object) -> None:
        scan_result = result
        if not isinstance(scan_result, ScanResult):
            raise TypeError("Resultado inesperado del escaneo.")

        self._scan_result = scan_result
        self._scan_target_directory = scan_result.target_directory or self._scan_target_directory
        self._populate_table(scan_result)
        self._update_dashboard_metrics(scan_result)
        self._update_summary_box(animate=True)
        self._refresh_action_state()

        duplicates_count = count_duplicate_files(scan_result)
        reclaimable_bytes = count_reclaimable_bytes(scan_result)
        if duplicates_count > 0:
            self._set_status_badge("Revisar duplicados", "warn")
            self.statusBar().showMessage(
                "Escaneo finalizado. "
                f"Duplicados detectados: {duplicates_count} "
                f"({_format_bytes(reclaimable_bytes)} recuperables)."
            )
        else:
            self._set_status_badge("Sin duplicados", "ok")
            self.statusBar().showMessage("Escaneo finalizado. No se encontraron duplicados.")

    def _update_dashboard_metrics(self, scan_result: ScanResult | None) -> None:
        if scan_result is None:
            self._duplicates_value.setText("0")
            self._reclaim_value.setText("0 B")
            return

        self._duplicates_value.setText(str(count_duplicate_files(scan_result)))
        self._reclaim_value.setText(_format_bytes(count_reclaimable_bytes(scan_result)))

    def _update_summary_box(self, animate: bool) -> None:
        if self._scan_result is None:
            self._summary_box.clear()
            return

        self._summary_box.setPlainText(
            self._render_scan_summary(scan_result=self._scan_result)
        )
        if animate:
            self._animate_summary()

    @staticmethod
    def _format_summary_pairs(pairs: list[tuple[str, str]], minimum_width: int = 30) -> list[str]:
        if not pairs:
            return []
        width = max(minimum_width, max(len(label) for label, _ in pairs))
        return [f"{label:<{width}} : {value}" for label, value in pairs]

    def _start_delete(self) -> None:
        if self._busy:
            return
        if self._scan_result is None:
            QMessageBox.information(self, "Sin escaneo", "Primero ejecuta un escaneo.")
            return

        duplicates_count = count_duplicate_files(self._scan_result)
        if duplicates_count == 0:
            QMessageBox.information(self, "Sin duplicados", "No hay archivos para eliminar.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar eliminacion",
            (
                f"Archivos a eliminar: {duplicates_count}\n"
                f"Pasadas de sobrescritura: {self._passes_spin.value()}\n"
                "Modo: eliminacion segura irreversible\n\n"
                "Continuar?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            self._set_status_badge("Eliminacion cancelada", "warn")
            return

        self._run_async(
            func=self._delete_task,
            args=(self._scan_result.groups, self._passes_spin.value()),
            on_done=self._on_delete_done,
            start_message="Eliminando duplicados...",
        )

    @staticmethod
    def _delete_task(groups: list[DuplicateGroup], passes: int):
        return delete_duplicate_files(
            groups=groups,
            passes=passes,
        )

    def _on_delete_done(self, result: object) -> None:
        delete_result = result
        failed_count = len(delete_result.failures)
        self._scan_result = None
        self._table.setRowCount(0)

        summary_pairs = [
            ("Eliminados de forma segura", str(delete_result.deleted_count)),
            ("Fallidos", str(failed_count)),
        ]
        lines = ["Proceso de eliminacion terminado.", ""]
        lines.extend(self._format_summary_pairs(summary_pairs))

        if failed_count:
            lines.append("")
            lines.append("Detalle de fallos:")
            for failure in delete_result.failures:
                lines.append(f"- {failure.path}: {failure.error}")

        self._summary_box.setPlainText("\n".join(lines))
        self._animate_summary()
        self._update_dashboard_metrics(None)
        self._refresh_action_state()

        if failed_count:
            self._set_status_badge("Eliminacion con fallos", "error")
            QMessageBox.warning(
                self,
                "Eliminacion con fallos",
                "Algunos archivos no pudieron procesarse. Revisa el resumen.",
            )
        else:
            self._set_status_badge("Eliminacion completada", "ok")
            QMessageBox.information(
                self,
                "Proceso completado",
                f"Se eliminaron de forma segura {delete_result.deleted_count} archivos.",
            )

    def _render_scan_summary(self, scan_result: ScanResult) -> str:
        duplicates_count = count_duplicate_files(scan_result)
        reclaimable_bytes = count_reclaimable_bytes(scan_result)
        summary_pairs = [
            ("Grupos duplicados", str(len(scan_result.groups))),
            ("Archivos detectados para eliminar", str(duplicates_count)),
            ("Espacio recuperable total", _format_bytes(reclaimable_bytes)),
        ]
        lines = ["Modo: Escaneo de una carpeta", f"Objetivo escaneado: {scan_result.target_directory or '-'}", ""]
        lines.extend(self._format_summary_pairs(summary_pairs))

        if scan_result.unreadable_files:
            lines.append("")
            lines.extend(
                self._format_summary_pairs(
                    [("Archivos no leidos", str(len(scan_result.unreadable_files)))]
                )
            )
            lines.append("No leidos:")
            for path in scan_result.unreadable_files:
                lines.append(f"- {path}")

        return "\n".join(lines)

    def _populate_table(self, scan_result: ScanResult) -> None:
        row_count = count_duplicate_files(scan_result)
        self._table.setRowCount(row_count)

        row = 0
        for group in scan_result.groups:
            short_hash = group.file_hash[:12]
            for delete_path in group.delete:
                hash_item = QTableWidgetItem(short_hash)
                hash_item.setToolTip(group.file_hash)
                size_item = QTableWidgetItem(_format_bytes(group.size_bytes))
                keep_item = QTableWidgetItem(group.keep)
                delete_item = QTableWidgetItem(delete_path)

                self._table.setItem(row, 0, hash_item)
                self._table.setItem(row, 1, size_item)
                self._table.setItem(row, 2, keep_item)
                self._table.setItem(row, 3, delete_item)
                row += 1

    def _on_worker_finished(self, _result: object) -> None:
        current_message = self.statusBar().currentMessage() or "Listo"
        self._set_busy(False, current_message)

    def _on_worker_failed(self, error_message: str) -> None:
        self._set_busy(False, "Ocurrio un error")
        self._set_status_badge("Error en proceso", "error")
        QMessageBox.critical(self, "Error", error_message)

    def _clear_active_worker(self) -> None:
        self._active_thread = None
        self._active_worker = None


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
