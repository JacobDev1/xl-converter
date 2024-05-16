import time
import logging

from PySide6.QtCore import QObject, Signal, QTimer

class TimeLeft(QObject):
    update_time_left = Signal(str)

    def __init__(self):
        super().__init__()
        
        self.est_time_left_s = None
        self.start_time = None
        self.item_count = 0
        self.completed_item_count = 0

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._updateEstimationTimer)

    # Public methods
    def startCounting(self, item_count: int):
        """Call right before starting the conversion."""
        self.start_time = time.time()
        self.item_count = item_count
        self.completed_item_count = 0
        self.timer.start()
        self._updateEstimation()
        self._emitEstimationUpdated()

    def stopCounting(self):
        """Call when stopping conversion."""
        self.timer.stop()
        self.est_time_left_s = None
        self.start_time = None
        self.item_count = 0
        self.completed_item_count = 0

    def addCompletedItem(self):
        """Call on item completed. Updates estimated time left data."""
        if self.start_time is None:
            return
        
        self.completed_item_count += 1
        self._updateEstimation()
        # self._emitEstimationUpdated()

    # Private methods
    def _updateEstimation(self):
        """Updates estimation without subtracting one."""
        if self.item_count <= 0 or self.start_time is None:
            logging.error(f"[TimeLeft] Setup error")
            self.est_time_left_s = None
            return

        if self.completed_item_count < 1:
            self.est_time_left_s = None     # Returns "Time left: <calculating>"
            return
        
        try:
            alpha = 0.1
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            items_left = self.item_count - self.completed_item_count

            if self.est_time_left_s is None:
                self.est_time_left_s = (elapsed_time / self.completed_item_count) * items_left
            else:
                if items_left <= 0:
                    self.est_time_left_s = 0        # Returns "Almost done..."
                else:
                    new_est_time_per_item = elapsed_time / self.completed_item_count
                    self.est_time_left_s = (new_est_time_per_item * items_left) * alpha + self.est_time_left_s * (1 - alpha)
        except Exception as e:
            logging.error(f"[TimeLeft] {e}")
            self.est_time_left_s = None

    def _emitEstimationUpdated(self):
        """Call after calling _updateEstimation."""
        if self.est_time_left_s is None:
            self.update_time_left.emit("Calculating time left...")
        else:
            self.update_time_left.emit(self._formatOutput(self.est_time_left_s))

    def _updateEstimationTimer(self):
        """To be used by the timer object only. Estimates then subtracts a second from the est. time."""
        self._updateEstimation()
        if self.est_time_left_s is not None:
            self.est_time_left_s -= 1
        self._emitEstimationUpdated()
    
    def _formatOutput(self, remaining_s: float) -> str:
        """Get nicely formatted time estimation."""
        if remaining_s <= 1:
            return "Almost done..."
        
        d = int(remaining_s / (3600 * 24))
        h = int((remaining_s // 3600) % 24)
        m = int((remaining_s // 60) % 60)
        s = int(remaining_s % 60)
        
        output = ""
        if d:   output += f"{d} d "
        if h:   output += f"{h} h "
        if m:   output += f"{m} m "
        if s:   output += f"{s} s "

        output += "left"
        return output