import unittest, sys, os, shutil
from pathlib import Path

from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QKeySequence
)

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog
)

from PySide6.QtTest import (
    QTest,
    QSignalSpy
)

from PySide6.QtCore import (
    Qt,
    QMimeData,
    QUrl,
    QPoint
)

from main import MainWindow

# CONFIG
SAMPLE_IMG_FOLDER = os.path.join(".", "test_img")
app = QApplication(sys.argv)    # It needs to be declared here

def scanDir(path):
    items = set()   # No duplicates
    for i in Path(path).rglob("*"):
        if os.path.isfile(i):
            items.add(os.path.abspath(i))
    return list(items)  # So it can be access by an index

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.main_window = MainWindow()
        self.delete_tmp_dir("jxl")
        self.sample_img_list = scanDir(SAMPLE_IMG_FOLDER)
    
    def tearDown(self):
        del self.main_window
        del self.sample_img_list

    # Helper functions
    def drag_and_drop(self, urls):
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(url) for url in urls])

        drop_event = QDropEvent(QPoint(), Qt.CopyAction, mime_data, Qt.LeftButton, Qt.NoModifier)

        QTest.mousePress(self.main_window, Qt.LeftButton, pos=QPoint(), delay=100)
        self.main_window.dropEvent(drop_event)
        QTest.mouseRelease(self.main_window, Qt.LeftButton, pos=QPoint(), delay=100)
        QTest.qWait(100)

    def get_items(self):
        root = self.main_window.input_tab.file_view.invisibleRootItem()
        items = []
        for i in range(root.childCount()):
            items.append(root.child(i).text(2))
        return items

    def clear_list(self):
        self.main_window.input_tab.clearInput()
    
    def add_files(self, file_paths):
        self.main_window.input_tab._addItems(file_paths)
    
    def add_file(self, file_path):
        self.main_window.input_tab._addItems([file_path])

    def set_format(self, _format):
        idx = self.main_window.output_tab.wm.getWidget("format_cmb").findText(_format)
        self.main_window.output_tab.wm.getWidget("format_cmb").setCurrentIndex(idx)

    def set_custom_output(self, path):
        self.main_window.output_tab.wm.getWidget("choose_output_ct_rb").setChecked(True)
        self.main_window.output_tab.wm.getWidget("choose_output_ct_le").setText(path)

    def reset_to_default(self):
        self.main_window.output_tab.resetToDefault()
        self.main_window.modify_tab.resetToDefault()
        self.main_window.settings_tab.resetToDefault()
        self.main_window.output_tab.wm.getWidget("threads_sl").setValue(self.main_window.output_tab.MAX_THREAD_COUNT)   # To speed up testing

    def convert(self):
        self.main_window.convert()
    
    def delete_tmp_dir(self, name):
        try:
            shutil.rmtree(os.path.join(SAMPLE_IMG_FOLDER, name))
        except OSError as err:
            pass
    
    def get_tmp_path(self, folder):
        return os.path.join(SAMPLE_IMG_FOLDER, folder)

    def set_effort(self, effort):
        self.main_window.output_tab.wm.getWidget("effort_sb").setValue(effort)
    
    def wait_for_done(self):
        self.main_window.threadpool.waitForDone()

    # Tests
    def test_initialization(self):
        self.assertEqual(self.main_window.windowTitle(), "XL Converter")
    
    def test_drag_n_drop_files(self):
        root = self.main_window.input_tab.file_view.invisibleRootItem()
        self.drag_and_drop(self.sample_img_list)

        items = self.get_items()
        for i in self.sample_img_list:
            self.assertIn(i, items)

    def test_clear_list(self):
        self.main_window.input_tab.clearInput()
        self.assertTrue(self.main_window.input_tab.file_view.invisibleRootItem().childCount() == 0)

    def test_drag_n_drop_folders(self):
        self.drag_and_drop([SAMPLE_IMG_FOLDER])

        items = self.get_items()        
        for i in self.sample_img_list:
            self.assertIn(i, items)

    def test_duplicate_detection(self):
        self.clear_list()
        self.add_files(self.sample_img_list)
        self.add_files(self.sample_img_list)
        self.assertEqual(self.main_window.input_tab.file_view.invisibleRootItem().childCount(), len(self.sample_img_list))
        self.clear_list()

    def test_jpeg_xl_lossy(self):
        self.clear_list()
        self.reset_to_default()

        self.add_files(self.sample_img_list)
        self.set_format("JPEG XL")
        self.set_custom_output("jxl")
        self.convert()
        
        self.wait_for_done()
        converted = scanDir(os.path.join(SAMPLE_IMG_FOLDER, "jxl"))
        self.assertEqual(len(converted), len(self.get_items()))

        self.delete_tmp_dir("jxl")
    
    def test_jpeg_xl_effort(self):
        self.clear_list()
        self.reset_to_default()

        self.add_file(self.sample_img_list[0])
        self.set_format("JPEG XL")
        self.set_custom_output("jxl")

        self.set_effort(7)
        self.convert()
        
        self.set_effort(9)
        self.convert()

        self.wait_for_done()
        converted = scanDir(self.get_tmp_path("jxl"))
        self.assertNotEqual(os.path.getsize(converted[0]), os.path.getsize(converted[1]))
        self.delete_tmp_dir("jxl")

    # def test_jpeg_xl_int_effort(self):
    #     pass

    # def test_jpeg_xl_lossless(self):
    #     # First, convert to jpg. This should result in effort 9
    #     pass

    # def test_jpeg_xl_jpg_reconstruction(self):
    #     pass    # jxlinfo bin / check_output

    # def test_avif(self):
    #     pass

    # def test_proxy(self):
    #     # convert file to jpg -> webp -> jxl -> avif to test proxy
    #     pass

    # def test_rename(self):
    #     pass

    # def test_replace(self):
    #     pass

    # def test_skip(self):
    #     pass

if __name__ == "__main__":
    unittest.main()