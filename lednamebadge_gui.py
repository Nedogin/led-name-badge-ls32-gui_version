import sys
from array import array

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QTextEdit,
)

from lednamebadge import SimpleTextAndIcons, LedNameBadge


class SlotWidget(QGroupBox):
    """UI elements for one memory slot."""

    def __init__(self, index: int, parent=None) -> None:
        super().__init__(f"Slot {index + 1}", parent)
        self._index = index

        layout = QGridLayout(self)

        self.text_edit = QLineEdit()
        self.text_edit.setMaxLength(750)
        self.text_edit.setMinimumWidth(300)
        layout.addWidget(QLabel("Text:"), 0, 0)
        layout.addWidget(self.text_edit, 0, 1, 1, 3)

        self.char_count_label = QLabel("0/750")
        layout.addWidget(self.char_count_label, 0, 4)
        self.text_edit.textChanged.connect(self._update_char_count)
        self._update_char_count()

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 8)
        self.speed_spin.setValue(4)
        layout.addWidget(QLabel("Speed"), 1, 0)
        layout.addWidget(self.speed_spin, 1, 1)

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
        layout.addWidget(QLabel("Mode"), 1, 2)
        layout.addWidget(self.mode_box, 1, 3)

        self.blink_box = QCheckBox("Blink")
        layout.addWidget(self.blink_box, 2, 0)
        self.ants_box = QCheckBox("Ants")
        layout.addWidget(self.ants_box, 2, 1)

    def values(self) -> dict:
        return {
            "text": self.text_edit.text(),
            "speed": self.speed_spin.value(),
            "mode": self.mode_box.currentData(),
            "blink": 1 if self.blink_box.isChecked() else 0,
            "ants": 1 if self.ants_box.isChecked() else 0,
        }

    def _update_char_count(self) -> None:
        length = len(self.text_edit.text())
        self.char_count_label.setText(f"{length}/750")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LED Name Badge Configurator")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.slots = [SlotWidget(i) for i in range(8)]
        for slot in self.slots:
            layout.addWidget(slot)

        brightness_layout = QGridLayout()
        brightness_widget = QWidget()
        brightness_widget.setLayout(brightness_layout)

        brightness_layout.addWidget(QLabel("Brightness"), 0, 0)
        self.brightness_box = QComboBox()
        self.brightness_box.addItem("25%", 25)
        self.brightness_box.addItem("50%", 50)
        self.brightness_box.addItem("75%", 75)
        self.brightness_box.addItem("100%", 100)
        self.brightness_box.setCurrentText("100%")
        brightness_layout.addWidget(self.brightness_box, 0, 1)
        layout.addWidget(brightness_widget)

        icons = ", ".join(f":{n}:" for n in SimpleTextAndIcons._get_named_bitmaps_keys())
        self.icons_desc = QTextEdit()
        self.icons_desc.setReadOnly(True)
        self.icons_desc.setPlainText("Icons (use :name:):\n" + icons)
        layout.addWidget(self.icons_desc)

        self.write_button = QPushButton("Write to Badge")
        self.write_button.clicked.connect(self.write_to_badge)
        layout.addWidget(self.write_button)

    # ------------------------------------------------------------------
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
        brightness = self.brightness_box.currentData()
        header = LedNameBadge.header(lengths, speeds, modes, blinks, ants, brightness)

        buf = array('B')
        buf.extend(header)
        for b in msg_bitmaps:
            buf.extend(b[0])

        LedNameBadge.write(buf)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()