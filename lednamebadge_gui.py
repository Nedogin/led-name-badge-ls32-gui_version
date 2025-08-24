import sys
from array import array

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QGroupBox, QGridLayout, QLabel, QLineEdit,
                               QSpinBox, QCheckBox, QPushButton)

from lednamebadge import SimpleTextAndIcons, LedNameBadge


class SlotWidget(QGroupBox):
    """UI elements for one memory slot."""

    def __init__(self, index: int, parent=None) -> None:
        super().__init__(f"Slot {index + 1}", parent)
        self._index = index

        layout = QGridLayout(self)

        self.text_edit = QLineEdit()
        layout.addWidget(QLabel("Text:"), 0, 0)
        layout.addWidget(self.text_edit, 0, 1, 1, 3)

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 8)
        self.speed_spin.setValue(4)
        layout.addWidget(QLabel("Speed"), 1, 0)
        layout.addWidget(self.speed_spin, 1, 1)

        self.mode_spin = QSpinBox()
        self.mode_spin.setRange(0, 8)
        layout.addWidget(QLabel("Mode"), 1, 2)
        layout.addWidget(self.mode_spin, 1, 3)

        self.blink_box = QCheckBox("Blink")
        layout.addWidget(self.blink_box, 2, 0)
        self.ants_box = QCheckBox("Ants")
        layout.addWidget(self.ants_box, 2, 1)

    def values(self) -> dict:
        return {
            "text": self.text_edit.text(),
            "speed": self.speed_spin.value(),
            "mode": self.mode_spin.value(),
            "blink": 1 if self.blink_box.isChecked() else 0,
            "ants": 1 if self.ants_box.isChecked() else 0,
        }


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
        header = LedNameBadge.header(lengths, speeds, modes, blinks, ants)

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
