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
from variables import *

# CONFIG
SAMPLE_IMG_FOLDER = Path(".").resolve() / "test_img"    # Put some images in there

TMP_IMG_FOLDER = Path(".").resolve() / "unit_tests_tmp"
app = QApplication(sys.argv)

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

def test_dict(data):
    """Recursively verify dictionary's integrity"""
    for key, value in data.items():
        if isinstance(value, dict):
            if test_dict(value) is None:
                return False
        else:
            if value is None:
                return False
    
    return True

class Data:
    """Sample data and tmp folder management system."""
    
    def __init__(self, sample_img_folder, tmp_img_folder):
        self.sample_img_folder = sample_img_folder
        self.sample_img_folder_content_cached = scan_dir(sample_img_folder)
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
    def get_sample_img(self):
        return self.sample_img_folder_content_cached[0]

    def get_sample_imgs(self):
        return self.sample_img_folder_content_cached
    
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

    def convert_preset(self, src, dst, format, lossless=False, effort=7):
        self.clear_list()
        self.set_format(format)
        self.set_custom_output(dst)
        self.add_item(src)
        self.set_lossless(lossless)
        self.set_effort(effort)
        self.convert()

    def convert(self):
        self.main_window.convert()
        self.wait_for_done()

    def wait_for_done(self):
        while True:
            sleep(100)
            if self.main_window.data.getCompletedItemCount() == self.main_window.data.getItemCount():
                break

    def set_effort(self, effort):
        self.main_window.output_tab.wm.getWidget("effort_sb").setValue(effort)
    
    def set_duplicate_handling(self, mode):
        idx = self.main_window.output_tab.wm.getWidget("duplicates_cmb").findText(mode)
        self.main_window.output_tab.wm.getWidget("duplicates_cmb").setCurrentIndex(idx)
    
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
        self.app.reset_to_default()
        self.app.clear_list()
    
    def tearDown(self):
        self.data.cleanup()

    def test_dependencies(self):
        FILES = (
            ICON_SVG,
            LICENSE_PATH,
            LICENSE_3RD_PARTY_PATH,
            CJXL_PATH,
            DJXL_PATH,
            JXLINFO_PATH,
            IMAGE_MAGICK_PATH,
            AVIFENC_PATH,
            AVIFDEC_PATH,
            OXIPNG_PATH,
            EXIFTOOL_PATH,
            Path(EXIFTOOL_FOLDER_PATH) / EXIFTOOL_BIN_NAME,
        )

        DIRS = (
            EXIFTOOL_FOLDER_PATH,   # Trailing comma is very important here
        )

        for i in FILES:
            assert Path(i).is_file(), f"File not found ({i})"

        for i in DIRS:
            assert Path(i).is_dir(), f"Dir not found ({i})"

    def test_clear_list(self):
        self.app.add_items(self.data.get_sample_imgs())
        assert self.app.get_item_count() > 0, "List shouldn't be empty"
        self.app.clear_list()
        assert self.app.get_item_count() == 0, "List should be empty"

    def test_drag_n_drop_files(self):
        self.app.drag_and_drop(self.data.get_sample_imgs())
        assert self.app.get_item_count() == len(self.data.get_sample_imgs())
    
    def test_drag_n_drop_folders(self):
        self.app.drag_and_drop([self.data.get_sample_img_folder()])
        assert self.app.get_item_count() == len(self.data.get_sample_imgs())

    def test_duplicate_detection(self):
        items = self.data.get_sample_imgs()
        self.app.add_items(items)
        self.app.add_items(items)
        assert self.app.get_item_count() == len(items)

    def test_jpeg_xl_lossy(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPEG XL")
        assert len(self.data.get_tmp_folder_content() ) > 0, "Converted image not found"
    
    def test_jpeg_xl_effort(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPEG XL", effort=7)
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPEG XL", effort=9)

        converted = self.data.get_tmp_folder_content()
        assert CRC32(converted[0]) != CRC32(converted[1]), "Images should not be the same"

    def test_jpg_reconstruction(self):
        # Source -> JPG
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("jpg"), "JPG")

        # JPG -> JXL
        self.app.convert_preset(self.data.get_tmp_folder_content("jpg")[0], self.data.make_tmp_subfolder("jxl"), "JPEG XL", lossless=True)

        # JXL -> JPG
        self.app.convert_preset(self.data.get_tmp_folder_content("jxl")[0], self.data.make_tmp_subfolder("reconstructed"), "PNG")

        assert CRC32(self.data.get_tmp_folder_content("jpg")[0]) == CRC32(self.data.get_tmp_folder_content("reconstructed")[0]), "Hash mismatch for reconstructed JPG"

    def test_avif(self): 
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("avif"), "AVIF")
        assert Path(self.data.get_tmp_folder_content()[0]).suffix == ".avif", "AVIF file not found"
    
    def test_webp(self): 
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("webp"), "WEBP")
        assert Path(self.data.get_tmp_folder_content()[0]).suffix == ".webp", "WEBP file not found"
    
    def test_jpg(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("jpg"), "JPG")
        assert Path(self.data.get_tmp_folder_content()[0]).suffix == ".jpg", "JPG file not found"

    def test_jpeg_xl_decode(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("jxl"), "JPEG XL")
        self.app.convert_preset(self.data.get_tmp_folder_content("jxl")[0], self.data.make_tmp_subfolder("jxl_decoded"), "PNG")
        assert len(self.data.get_tmp_folder_content("jxl_decoded")) > 0, "Decoded JPEG XL file not found"

    def test_avif_decode(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("avif"), "AVIF")
        self.app.convert_preset(self.data.get_tmp_folder_content("avif")[0], self.data.make_tmp_subfolder("avif_decoded"), "PNG")
        assert len(self.data.get_tmp_folder_content("avif_decoded")) > 0, "Decoded AVIF file not found"

    def test_webp_decode(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("webp"), "WEBP")
        self.app.convert_preset(self.data.get_tmp_folder_content("webp")[0], self.data.make_tmp_subfolder("webp_decoded"), "PNG")
        assert len(self.data.get_tmp_folder_content("webp_decoded")) > 0, "Decoded WEBP file not found"

    def test_decode_jpg(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("jpg"), "JPG")
        self.app.convert_preset(self.data.get_tmp_folder_content("jpg")[0], self.data.make_tmp_subfolder("jpg_decoded"), "PNG")
        assert len(self.data.get_tmp_folder_content("jpg_decoded")) > 0, "Decoded JPG file not found"
    
    def test_proxy(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.make_tmp_subfolder("jpg"), "JPG")
        assert Path(self.data.get_tmp_folder_content("jpg")[0]).suffix == ".jpg", "JPG file not found"

        self.app.convert_preset(self.data.get_tmp_folder_content("jpg")[0], self.data.make_tmp_subfolder("webp"), "WEBP")
        assert Path(self.data.get_tmp_folder_content("webp")[0]).suffix == ".webp", "WEBP file not found"

        self.app.convert_preset(self.data.get_tmp_folder_content("webp")[0], self.data.make_tmp_subfolder("jxl"), "JPEG XL")
        assert Path(self.data.get_tmp_folder_content("jxl")[0]).suffix == ".jxl", "JPEG XL file not found"

        self.app.convert_preset(self.data.get_tmp_folder_content("jxl")[0], self.data.make_tmp_subfolder("avif"), "AVIF")
        assert Path(self.data.get_tmp_folder_content("avif")[0]).suffix == ".avif", "AVIF file not found"

    def test_smallest_lossless(self):
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "Smallest Lossless")
        assert len(self.data.get_tmp_folder_content()) > 0, "Smallest Lossless did not generate any files"
    
    def test_rename(self):
        self.app.set_duplicate_handling("Rename")
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPG")
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPG")
        assert len(self.data.get_tmp_folder_content()) == 2, "File amount mismatch"

    def test_replace(self):
        self.app.set_duplicate_handling("Replace")
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPG")
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPG")
        assert len(self.data.get_tmp_folder_content()) == 1, "File amount mismatch"

    def test_skip(self):
        self.app.set_duplicate_handling("Skip")
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPG")
        self.app.convert_preset(self.data.get_sample_img(), self.data.get_tmp_folder_path(), "JPG")
        assert len(self.data.get_tmp_folder_content()) == 1, "File amount mismatch"

    def test_get_settings(self):
        settings = self.app.main_window.settings_tab.getSettings()
        output = self.app.main_window.output_tab.getSettings()
        modify = self.app.main_window.modify_tab.getSettings()

        assert test_dict(output), "output_tab.getSettings contains None"
        assert test_dict(modify), "modify_tab.getSettings contains None"
        assert test_dict(settings), "settings.getSettings contains None"
if __name__ == "__main__":
    unittest.main()