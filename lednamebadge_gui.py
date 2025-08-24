import sys
from array import array

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMessageBox,
)

from lednamebadge import SimpleTextAndIcons, LedNameBadge


class SlotWidget(QGroupBox):
    """UI elements for one memory slot (strict vertical layout)."""

    MAX_CHARS = 750

    def __init__(self, index: int, parent=None) -> None:
        super().__init__(f"Slot {index + 1}", parent)
        self._index = index

        # Rein vertikal: FormLayout mit genau *einer* Spalte für Labels (oben) und Widget darunter
        root = QVBoxLayout(self)

        # Text + Zähler im Label
        self.text_label = QLabel(f"Text (0/{self.MAX_CHARS}):")
        root.addWidget(self.text_label)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        fm = self.text_edit.fontMetrics()
        self.text_edit.setMinimumWidth(fm.averageCharWidth() * 45)
        self.text_edit.setFixedHeight(fm.lineSpacing() * 4 + 12)
        root.addWidget(self.text_edit)

        self.text_edit.textChanged.connect(self._update_char_count)
        self._update_char_count()

        # Optionen untereinander – jede in eigener Zeile
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        root.addLayout(form)

        # Speed (eigene Zeile)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 8)
        self.speed_spin.setValue(4)
        form.addRow(QLabel("Speed"), self.speed_spin)

        # Mode (eigene Zeile)
        self.mode_box = QComboBox()
        self.mode_box.addItem("Scroll left", 0)
        self.mode_box.addItem("Scroll right", 1)
        self.mode_box.addItem("Scroll up", 2)
        self.mode_box.addItem("Scroll down", 3)
        self.mode_box.addItem("Still", 4)
        self.mode_box.addItem("Animation", 5)
        self.mode_box.addItem("Drop down", 6)
        self.mode_box.addItem("Curtain", 7)
        self.mode_box.addItem("Laser", 8)
        form.addRow(QLabel("Mode"), self.mode_box)

        # Blink (eigene Zeile)
        self.blink_box = QCheckBox("Blink")
        form.addRow(self.blink_box)

        # Ants (eigene Zeile)
        self.ants_box = QCheckBox("Ants")
        form.addRow(self.ants_box)

        # etwas Abstand nach unten
        root.addStretch(1)

    def values(self) -> dict:
        return {
            "text": self.text_edit.toPlainText(),
            "speed": self.speed_spin.value(),
            "mode": self.mode_box.currentData(),
            "blink": 1 if self.blink_box.isChecked() else 0,
            "ants": 1 if self.ants_box.isChecked() else 0,
        }

    def _update_char_count(self) -> None:
        text = self.text_edit.toPlainText()
        if len(text) > self.MAX_CHARS:
            self.text_edit.blockSignals(True)
            self.text_edit.setPlainText(text[: self.MAX_CHARS])
            cursor = self.text_edit.textCursor()
            cursor.setPosition(self.MAX_CHARS)
            self.text_edit.setTextCursor(cursor)
            self.text_edit.blockSignals(False)
            text = self.text_edit.toPlainText()
        self.text_label.setText(f"Text ({len(text)}/{self.MAX_CHARS}):")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LED Name Badge Configurator")
        self.statusBar()

        # Fenster initial breiter öffnen
        self.resize(1000, 700)

        # Gesamte Inhalte in eine ScrollArea packen
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        self.setCentralWidget(scroll)

        root = QVBoxLayout(container)

        # --- Header: Write-Button + Icons oben ---
        header = QHBoxLayout()
        self.write_button = QPushButton("Write to Badge")
        self.write_button.clicked.connect(self.write_to_badge)
        header.addWidget(self.write_button)
        header.addStretch(1)
        root.addLayout(header)

        # Icons-Panel (Filter + Liste + Copy-Button)
        icons_box = QGroupBox("Icons (Doppelklick kopiert :name:)")
        icons_layout = QVBoxLayout(icons_box)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter"))
        self.icon_filter = QLineEdit()
        self.icon_filter.setPlaceholderText("z. B. heart, arrow ...")
        filter_row.addWidget(self.icon_filter)
        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.clicked.connect(self.copy_selected_icons)
        filter_row.addWidget(self.copy_selected_btn)
        icons_layout.addLayout(filter_row)

        self.icon_list = QListWidget()
        self.icon_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.icon_list.itemDoubleClicked.connect(self.copy_single_icon)
        icons_layout.addWidget(self.icon_list)

        root.addWidget(icons_box)

        # Datenquelle für Icons
        self._all_icon_tokens = sorted(f":{n}:" for n in SimpleTextAndIcons._get_named_bitmaps_keys())
        self._refill_icon_list()
        self.icon_filter.textChanged.connect(self._refill_icon_list)

        # --- Slots darunter ---
        self.slots = [SlotWidget(i) for i in range(8)]
        for slot in self.slots:
            root.addWidget(slot)

        # Hinweis
        hint = QLabel("Tipp: Füge Icons einfach als Token wie :heart: in den Text ein.")
        hint.setStyleSheet("color: gray;")
        root.addWidget(hint)

    # ------------------------------------------
    # Icons-Interaktion
    def _refill_icon_list(self):
        self.icon_list.clear()
        q = (self.icon_filter.text() or "").strip().lower()
        for token in self._all_icon_tokens:
            if not q or q in token.lower():
                QListWidgetItem(token, self.icon_list)

    def copy_single_icon(self, item: QListWidgetItem):
        QApplication.clipboard().setText(item.text())
        self.statusBar().showMessage(f"Kopiert: {item.text()}", 1500)

    def copy_selected_icons(self):
        items = self.icon_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Copy Selected", "Bitte wähle einen oder mehrere Einträge aus.")
            return
        text = " ".join(i.text() for i in items)
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Auswahl kopiert", 1500)

    # ------------------------------------------
    # Schreiben zum Badge
    def write_to_badge(self) -> None:
        """Collect data from all slots and write to the device."""
        creator = SimpleTextAndIcons()
        msg_bitmaps = []
        speeds = []
        modes = []
        blinks = []
        ants = []

        for slot in self.slots:
            v = slot.values()
            msg_bitmaps.append(creator.bitmap(v["text"]))
            speeds.append(v["speed"])
            modes.append(v["mode"])
            blinks.append(v["blink"])
            ants.append(v["ants"])

        lengths = [b[1] for b in msg_bitmaps]

        # Helligkeit ist entfernt – setze festen Standard (100%)
        brightness = 100
        header = LedNameBadge.header(lengths, speeds, modes, blinks, ants, brightness)

        buf = array('B')
        buf.extend(header)
        for b in msg_bitmaps:
            buf.extend(b[0])

        LedNameBadge.write(buf)
        self.statusBar().showMessage("Daten wurden an das Badge gesendet.", 2000)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
