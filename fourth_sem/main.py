"""Burp Lite — облегчённый аналог Burp Suite."""

import sys
from pathlib import Path

# Добавляем корень в путь
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def main():
    """Точка входа."""
    
    # Включаем High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Burp Lite")
    app.setOrganizationName("BurpLite")
    
    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()