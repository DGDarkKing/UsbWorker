import os.path
import pickle
import queue

import peewee

import settings
from backend_reporter import BackendReporter
from copier import Copier
import models.db_models as db


def main():
    db.init_db(db.SRC_DB)

    backend_reporter = BackendReporter(settings.PROTOCOL, settings.HOST, settings.PORT)
    copier = Copier(backend_reporter, settings.REPORT_FILE, lambda : False)
    copier.start_copy()




if __name__ == '__main__':
    main()