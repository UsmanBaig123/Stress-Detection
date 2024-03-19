
# Graph thread to update the graph visual
import time

from PyQt5 import QtCore


class progessThread(QtCore.QThread):
    any_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(progessThread, self).__init__(parent)
        self.stop_thread = False

    def run(self):
        while True:
            time.sleep(0.1)
            if self.stop_thread:
                break
            self.any_signal.emit("")

    def stop(self):
        self.stop_thread = True


