from unittest.mock import patch, MagicMock
from contextlib import ExitStack

import pytest
from PySide6.QtCore import QSize, QRect, QPoint
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QWidget

import ui.dialogs.update_checker as update_checker

@pytest.fixture
def dialog(app):
    return update_checker.Dialog()

def test_dialog_init(dialog):
    pass

def test_dialog_resizeToContent(dialog):
    sample_size_hint = MagicMock(spec=QSize)
    mock_main_lt = MagicMock()
    mock_main_lt.sizeHint = sample_size_hint
    mock_qr = MagicMock(spec=QRect)
    mock_cp = MagicMock(spec=QPoint)

    mock_screen = MagicMock()
    mock_screen.availableGeometry.return_value.center.return_value = mock_cp

    with (
        patch.object(dialog, "setMinimumSize") as mock_setMinimumSize,
        patch.object(dialog.main_lt, "sizeHint", return_value=sample_size_hint),
        patch.object(dialog, "frameGeometry", return_value=mock_qr) as mock_frameGeometry,
        patch("ui.dialogs.update_checker.QGuiApplication.primaryScreen", return_value=mock_screen),
        patch.object(dialog, "move") as mock_move,
    ):
        dialog.resizeToContent()

        mock_setMinimumSize.assert_called_once_with(sample_size_hint)
        mock_frameGeometry.assert_called_once()
        mock_qr.moveCenter.assert_called_once_with(mock_cp)
        mock_move.assert_called_once_with(mock_qr.topLeft())

def test_dialog_onLinkBtnPress_link_exists(dialog):
    sample_url = "sample_url"
    dialog.link_btn_url = sample_url
    with (
        patch("ui.dialogs.update_checker.openRemoteUrl") as mock_openRemoteUrl,
        patch.object(dialog, "close") as mock_close,
    ):
        dialog._onLinkBtnPress()

        mock_openRemoteUrl.assert_called_once_with(sample_url)
        mock_close.assert_called_once()

def test_dialog_onLinkBtnPress_no_link(dialog):
    dialog.link_btn_url = None
    with (
        patch("ui.dialogs.update_checker.openRemoteUrl") as mock_openRemoteUrl,
    ):
        dialog._onLinkBtnPress()

        mock_openRemoteUrl.assert_not_called()

@pytest.fixture
def dialog_show_patched(dialog):
    mocks = {
        "text_l.setText": patch.object(dialog.text_l, "setText"),
        "link_btn.setText": patch.object(dialog.link_btn, "setText"),
        "link_btn.setVisible": patch.object(dialog.link_btn, "setVisible"),
        "resizeToContent": patch.object(dialog, "resizeToContent"),
    }

    with ExitStack() as stack:
        _mocks = {name: stack.enter_context(patcher) for name, patcher in mocks.items()}
        yield dialog, _mocks

def test_dialog_show_only_message(dialog_show_patched):
    dialog, mocks = dialog_show_patched
    sample_msg = "sample message"

    dialog.show(sample_msg)

    mocks["text_l.setText"].assert_called_once_with(sample_msg)
    mocks["link_btn.setText"].assert_not_called()
        
def test_dialog_show_message_and_url(dialog_show_patched):
    dialog, mocks = dialog_show_patched
    sample_msg, sample_url = "sample message", "sample_url"
    
    dialog.show(
        sample_msg,
        sample_url
    )

    mocks["text_l.setText"].assert_called_once_with(sample_msg)
    mocks["link_btn.setText"].assert_called_once_with("Open Link")
    assert dialog.link_btn_url == sample_url
        
def test_dialog_show_message_and_url_text(dialog_show_patched):
    dialog, mocks = dialog_show_patched
    sample_msg, sample_url, sample_url_text = "sample message", "sample_url", "sample_url_text"
    dialog.show(
        sample_msg,
        sample_url,
        sample_url_text,
    )

    mocks["text_l.setText"].assert_called_once_with(sample_msg)
    mocks["link_btn.setText"].assert_called_once_with(sample_url_text)
    assert dialog.link_btn_url == sample_url

def test_dialog_show_resize_to_content(dialog_show_patched):
    dialog, mocks = dialog_show_patched
    sample_msg = "sample message"
   
    dialog.show(
        sample_msg,
        resize_to_content=True,
    )

    mocks["resizeToContent"].assert_called_once()

def test_dialog_reject(dialog):
    closed_spy = QSignalSpy(dialog.closed)
    dialog.reject()
    assert closed_spy.count() == 1

def test_dialog_accept(dialog):
    closed_spy = QSignalSpy(dialog.closed)
    dialog.accept()
    assert closed_spy.count() == 1

@pytest.fixture
def update_checker_object(app):
    return update_checker.UpdateChecker()

def test_update_checker_init(app):
    mock_parent = QWidget()
    uc = update_checker.UpdateChecker(mock_parent)
    
    assert uc.parent is mock_parent

    # Vars
    assert uc.dlg is None
    assert uc.runner is None
    assert uc.update_info is None
    
    # Settings
    assert uc.prompt_on_update_only is False

    # Flags
    assert uc.initialized is False
    assert uc.message_viewed is False

def test_update_checker_lazy_init(update_checker_object):
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    mock_parent = MagicMock(spec=QWidget)
    update_checker_object.parent = mock_parent
    mock_update_checker_runner = MagicMock(spec=update_checker.UpdateCheckerRunner)

    
    with (
        patch("ui.dialogs.update_checker.Dialog", return_value=mock_dialog) as mock_dialog_init,
        patch("ui.dialogs.update_checker.UpdateCheckerRunner", return_value=mock_update_checker_runner),
    ):    
        update_checker_object._lazyInit()

    assert update_checker_object.initialized == True
    mock_dialog_init.assert_called_once_with(parent=mock_parent)
    mock_dialog.closed.connect.assert_called_once_with(update_checker_object._onDialogClosed)
    assert update_checker_object.runner == mock_update_checker_runner
    mock_update_checker_runner.json_received.connect.assert_called_once_with(update_checker_object._jsonReceived)
    mock_update_checker_runner.error_occurred.connect.assert_called_once_with(update_checker_object._errorOccurred)

def test_update_checker_errorOccurred(update_checker_object):
    sample_error = "sample error"
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog

    update_checker_object._errorOccurred(sample_error)

    mock_dialog.show.assert_called_once_with(sample_error)

def test_update_checker_errorOccurred_no_prompt(update_checker_object):
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog
    update_checker_object.prompt_on_update_only = True

    update_checker_object._errorOccurred("error")

    mock_dialog.show.assert_not_called()

def test_update_checker_onDialogClosed_update_info_none(update_checker_object):
    update_checker_object.update_info = None
    finished_spy = QSignalSpy(update_checker_object.finished)
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog

    update_checker_object._onDialogClosed()

    assert finished_spy.count() == 1
    mock_dialog.show.assert_not_called()

def test_update_checker_onDialogClosed_message_already_viewed(update_checker_object):
    mock_update_info = update_checker.UpdateInfo(latest_version="1.0.0")
    mock_update_info.message = "some message"
    update_checker_object.update_info = mock_update_info
    update_checker_object.message_viewed = True
    finished_spy = QSignalSpy(update_checker_object.finished)
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog

    update_checker_object._onDialogClosed()

    assert finished_spy.count() == 1
    mock_dialog.show.assert_not_called()

@pytest.mark.parametrize("message_url, expected_arg", [
    ("", None),
    ("https://example.org", "https://example.org"),
])
def test_update_checker_onDialogClosed_display_message_no_url(message_url, expected_arg, update_checker_object):
    mock_update_info = update_checker.UpdateInfo(
        latest_version="1.0.0",
        message="some message",
        message_url=message_url,
    )
    update_checker_object.update_info = mock_update_info
    update_checker_object.message_viewed = False
    finished_spy = QSignalSpy(update_checker_object.finished)
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog

    update_checker_object._onDialogClosed()

    assert finished_spy.count() == 0
    mock_dialog.show.assert_called_once_with(
        mock_update_info.message,
        expected_arg,
        "Read More"
    )
    assert update_checker_object.message_viewed == True

def test_update_checker_jsonReceived_update_info_exception(update_checker_object):
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog
    with (
        patch("ui.dialogs.update_checker.UpdateInfo.fromJson", side_effect=ValueError("Key \"latest_version\" not found")) as mock_UpdateInfo_fromJson,
    ):
        update_checker_object._jsonReceived({})
        
        mock_dialog.show.assert_called_once_with("Key \"latest_version\" not found")

def test_update_checker_jsonReceived_update_info_exception_prompt_on_update_only(update_checker_object):
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog
    update_checker_object.prompt_on_update_only = True
    with (
        patch("ui.dialogs.update_checker.UpdateInfo.fromJson", side_effect=ValueError),
    ):
        update_checker_object._jsonReceived({})
        
        mock_dialog.show.assert_not_called()

def test_update_checker_jsonReceived_up_to_date(update_checker_object):
    mock_update_info = update_checker.UpdateInfo(latest_version="1.0.0")
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog
    with (
        patch("ui.dialogs.update_checker.UpdateInfo.fromJson", return_value=mock_update_info),
        patch("ui.dialogs.update_checker.isNewerVersionAvailable", return_value=False) as mock_isNewerVersionAvailable,
        patch("ui.dialogs.update_checker.VERSION", "1.0.0") as mock_VERSION,
    ):
        update_checker_object._jsonReceived({})
        
        mock_isNewerVersionAvailable.assert_called_once_with(mock_update_info.latest_version)
        mock_dialog.show.assert_called_once_with("This version is up to date.")

def test_update_checker_jsonReceived_new_ver_available(update_checker_object):
    mock_update_info = update_checker.UpdateInfo(latest_version="1.0.0")
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog
    with (
        patch("ui.dialogs.update_checker.UpdateInfo.fromJson", return_value=mock_update_info),
        patch("ui.dialogs.update_checker.isNewerVersionAvailable", return_value=True) as mock_isNewerVersionAvailable,
        patch("ui.dialogs.update_checker.VERSION", "1.0.0") as mock_VERSION,
        patch("ui.dialogs.update_checker.FLATPAK", False),
    ):
        update_checker_object._jsonReceived({})
        
        mock_isNewerVersionAvailable.assert_called_once_with(mock_update_info.latest_version)
        mock_dialog.show.assert_called_once_with(
            "New version is available (1.0.0).",
            None,
            "Download",
        )

def test_update_checker_jsonReceived_new_ver_available_flatpak(update_checker_object):
    mock_update_info = update_checker.UpdateInfo(latest_version="1.0.0")
    mock_dialog = MagicMock(spec=update_checker.Dialog)
    update_checker_object.dlg = mock_dialog
    with (
        patch("ui.dialogs.update_checker.UpdateInfo.fromJson", return_value=mock_update_info),
        patch("ui.dialogs.update_checker.isNewerVersionAvailable", return_value=True) as mock_isNewerVersionAvailable,
        patch("ui.dialogs.update_checker.VERSION", "1.0.0") as mock_VERSION,
        patch("ui.dialogs.update_checker.FLATPAK", True),
    ):
        update_checker_object._jsonReceived({})
        
        mock_isNewerVersionAvailable.assert_called_once_with(mock_update_info.latest_version)
        mock_dialog.show.assert_called_once_with(
            "New version is available (1.0.0).",
        )

def test_update_checker_run_already_initialized(update_checker_object):
    update_checker_object.initialized = True
    update_checker_object.runner = MagicMock()

    with (
        patch.object(update_checker_object, "_lazyInit") as mock_lazyInit,
    ):
        update_checker_object.run()

        mock_lazyInit.assert_not_called()

def test_update_checker_run_happy_path(update_checker_object):
    update_checker_object.initialized = False
    update_checker_object.update_info = MagicMock()
    update_checker_object.message_viewed = True
    update_checker_object.runner = MagicMock()  # So patches can be applied on top of it

    with (
        patch.object(update_checker_object, "_lazyInit") as mock_lazyInit,
        patch.object(update_checker_object.runner, "run") as mock_runner_run,
    ):
        update_checker_object.run()

        mock_lazyInit.assert_called_once()
        assert update_checker_object.update_info is None
        assert update_checker_object.message_viewed == False
        mock_runner_run.assert_called_once()
