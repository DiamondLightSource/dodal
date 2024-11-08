from dodal.utils import is_test_mode

ZOCALO_ENV = "dev_bluesky" if is_test_mode() else "bluesky"
