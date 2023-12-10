import unittest, sys, shutil, binascii
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
SAMPLE_IMG_FOLDER = Path(".").resolve() / "test_img"
TMP_IMG_FOLDER = Path(".").resolve() / "unit_tests_tmp"
app = QApplication(sys.argv)    # It needs to be declared here

# ---------------------------------------------------------------
#                           Tools
# ---------------------------------------------------------------

def scan_dir(path):
    items = set()   # No duplicates
    for i in Path(path).rglob("*"):
        if i.is_file():
            items.add(i.resolve())
    return list(items)  # So it can be access by an index

def rmtree(path):
    path = Path(path).resolve()
    if path.is_dir():
        shutil.rmtree(path)

def CRC32(path):
    crc32_val = 0

    with open(path, "rb") as file:
        buff_size = 8192
        for buf in iter(lambda: file.read(buff_size), b""):
            crc32_val = binascii.crc32(buf, crc32_val)

    return crc32_val & 0xffffffff

def sleep(ms):
    QTest.qWait(ms)

class Data:
    """Sample data and tmp folder management system."""
    
    def __init__(self, sample_img_folder, tmp_img_folder):
        self.sample_img_folder = sample_img_folder
        self.tmp_img_folder = tmp_img_folder

        self.cleanup()

    def cleanup(self):
        rmtree(self.tmp_img_folder)
    
    # Tmp Directory
    def get_tmp_folder_path(self, path = None):
        if path == None:
            return self.tmp_img_folder
        else:
            return Path(self.tmp_img_folder) / path

    def get_tmp_folder_content(self, subfolder=None):
        if subfolder:
            return scan_dir(Path(self.tmp_img_folder) / subfolder)
        else:
            return scan_dir(self.tmp_img_folder)

    def make_tmp_subfolder(self, name):
        path = Path(self.tmp_img_folder) / name
        path.mkdir(parents=True)
        return path

    # Samples Directory
    def get_sample_imgs(self):
        return scan_dir(self.sample_img_folder)
    
    def get_sample_img_folder(self):
        return self.sample_img_folder


class Interact:
    """Translation layer between unit tests and the application."""
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = self.main_window.input_tab.file_view.invisibleRootItem()

    def add_item(self, path):
        self.main_window.input_tab._addItems([path])

    def add_items(self, paths):
        self.main_window.input_tab._addItems(paths)

    def get_items(self):
        return [self.root.child(i).text(2) for i in range(self.root.childCount())]

    def get_item_count(self):
        return self.main_window.input_tab.file_view.invisibleRootItem().childCount()

    def clear_list(self):
        self.main_window.input_tab.clearInput()

    def set_format(self, _format):
        idx = self.main_window.output_tab.wm.getWidget("format_cmb").findText(_format)
        self.main_window.output_tab.wm.getWidget("format_cmb").setCurrentIndex(idx)

    def set_custom_output(self, path):
        self.main_window.output_tab.wm.getWidget("choose_output_ct_rb").setChecked(True)
        path = str(path.resolve())
        self.main_window.output_tab.wm.getWidget("choose_output_ct_le").setText(path)
    
    def set_lossless(self, checked):
        self.main_window.output_tab.wm.getWidget("lossless_cb").setChecked(checked)

    def reset_to_default(self):
        self.main_window.output_tab.resetToDefault()
        self.main_window.modify_tab.resetToDefault()
        self.main_window.settings_tab.resetToDefault()
        self.main_window.output_tab.wm.getWidget("threads_sl").setValue(self.main_window.output_tab.MAX_THREAD_COUNT)   # To speed up testing

    def convert(self):
        self.main_window.convert()
        
        # Wait for done
        while True:
            sleep(100)
            if self.main_window.data.getCompletedItemCount() == self.main_window.data.getItemCount():
                break

    def set_effort(self, effort):
        self.main_window.output_tab.wm.getWidget("effort_sb").setValue(effort)
    
    def drag_and_drop(self, urls):
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(url) for url in urls])

        drop_event = QDropEvent(QPoint(), Qt.CopyAction, mime_data, Qt.LeftButton, Qt.NoModifier)

        QTest.mousePress(self.main_window, Qt.LeftButton, pos=QPoint(), delay=100)
        self.main_window.dropEvent(drop_event)
        QTest.mouseRelease(self.main_window, Qt.LeftButton, pos=QPoint(), delay=100)
        QTest.qWait(100)

# ---------------------------------------------------------------
#                         Unit Tests
# ---------------------------------------------------------------

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.app = Interact(MainWindow())
        self.data = Data(SAMPLE_IMG_FOLDER, TMP_IMG_FOLDER)
    
    def tearDown(self):
        self.data.cleanup()

    def test_clear_list(self):
        self.app.clear_list()

        self.app.add_items(self.data.get_sample_imgs())
        assert self.app.get_item_count() > 0, "List shouldn't be empty"
        self.app.clear_list()
        assert self.app.get_item_count() == 0, "List should be empty"

    def test_drag_n_drop_files(self):
        items = self.data.get_sample_imgs()
        self.app.drag_and_drop(items)

        assert self.app.get_item_count() == len(self.data.get_sample_imgs())
    
    def test_drag_n_drop_folders(self):
        self.app.clear_list()
        self.app.drag_and_drop([self.data.get_sample_img_folder()])

        assert self.app.get_item_count() == len(self.data.get_sample_imgs())

    def test_duplicate_detection(self):
        self.app.clear_list()
        items = self.data.get_sample_imgs()

        self.app.add_items(items)
        self.app.add_items(items)
        assert self.app.get_item_count() == len(items)

        self.app.clear_list()

    def test_jpeg_xl_lossy(self):
        self.app.clear_list()
        self.app.reset_to_default()

        self.app.add_item(self.data.get_sample_imgs()[0])
        self.app.set_format("JPEG XL")
        self.app.set_custom_output(self.data.get_tmp_folder_path())
        self.app.convert()

        output = self.data.get_tmp_folder_content()       
        assert len(output) > 0, "Converted image not found"

        self.data.cleanup()
    
    def test_jpeg_xl_effort(self):
        self.app.clear_list()
        self.app.reset_to_default()

        self.app.add_item(self.data.get_sample_imgs()[0])
        self.app.set_format("JPEG XL")
        self.app.set_custom_output(self.data.get_tmp_folder_path())

        self.app.set_effort(7)
        self.app.convert()
        
        self.app.set_effort(9)
        self.app.convert()

        converted = self.data.get_tmp_folder_content()
        assert CRC32(converted[0]) != CRC32(converted[1]), "Images should not be the same"
        self.data.cleanup()

    def test_jpg_reconstruction(self):
        self.app.reset_to_default()

        # Source -> JPG
        self.app.clear_list()
        src_input = self.data.get_sample_imgs()[0]
        self.app.add_item(src_input)

        self.app.set_format("JPG")
        self.app.set_custom_output(self.data.make_tmp_subfolder("jpg"))
        self.app.convert()

        # JPG -> JXL
        self.app.clear_list()
        jpg_input = self.data.get_tmp_folder_content("jpg")[0]
        self.app.add_item(jpg_input)

        self.app.set_format("JPEG XL")
        self.app.set_lossless(True)
        self.app.set_custom_output(self.data.make_tmp_subfolder("jxl"))
        self.app.convert()

        # JXL -> JPG
        self.app.clear_list()
        # Reconstruct JPG from JPEG XL is on by default
        jxl_input = self.data.get_tmp_folder_content("jxl")[0]
        self.app.add_item(jxl_input)

        self.app.set_format("PNG")
        self.app.set_custom_output(self.data.make_tmp_subfolder("reconstructed"))
        self.app.convert()

        reconstructed = self.data.get_tmp_folder_content("reconstructed")[0]

        assert CRC32(jpg_input) == CRC32(reconstructed), "Hash mismatch for reconstructed JPG"
        
        self.data.cleanup()

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