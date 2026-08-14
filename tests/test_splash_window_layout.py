import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel

from fast_start import SplashWindow


class SplashWindowLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_splash_controls_are_visible_ordered_and_inside_card(self):
        splash = SplashWindow()
        splash.show()
        self.app.processEvents()

        controls = [
            splash.findChild(QLabel, "splashIcon"),
            splash.findChild(QLabel, "splashTitle"),
            splash.findChild(QLabel, "splashVersion"),
            splash.loading_label,
            splash.progress,
        ]
        self.assertTrue(all(controls))

        previous_bottom = -1
        for control in controls:
            self.assertTrue(control.isVisible())
            top_left = control.mapTo(splash.card, control.rect().topLeft())
            bottom_right = control.mapTo(splash.card, control.rect().bottomRight())
            self.assertGreater(top_left.y(), previous_bottom)
            self.assertGreaterEqual(top_left.x(), splash.card.contentsRect().left())
            self.assertLessEqual(bottom_right.x(), splash.card.contentsRect().right())
            self.assertLessEqual(bottom_right.y(), splash.card.contentsRect().bottom())
            previous_bottom = bottom_right.y()

        splash.close()


if __name__ == "__main__":
    unittest.main()
