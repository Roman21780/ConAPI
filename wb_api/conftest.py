import os
import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass