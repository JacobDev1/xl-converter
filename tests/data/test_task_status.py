import data.task_status as task_status


def test_task_status_init():
    assert task_status.wasCanceled() == False

def test_task_status_cancel():
    assert task_status.wasCanceled() == False
    task_status.cancel()
    assert task_status.wasCanceled() == True
    task_status.reset()
    assert task_status.wasCanceled() == False
