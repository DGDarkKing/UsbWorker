import time

import settings
from backend_reporter import BackendReporter
from copy_by_video_stategy import CopyByVideoStrategy
from copy_facade import HttpCopyFacade
import models.db_models as db


def main():
    db.init_db(db.SRC_DB)

    prefixes = ['video']
    target_strategies = {
        prefixes[0]: CopyByVideoStrategy(None, None, None,
                                         prefix=prefixes[0],
                                         target_event_name='Подача')
    }

    HttpCopyFacade.create_report_file(settings.REPORT_FILE, prefixes)
    backend_reporter = BackendReporter(settings.PROTOCOL, settings.HOST, settings.PORT)
    copier = HttpCopyFacade(backend_reporter, settings.REPORT_FILE, target_strategies, settings.COPY_TIME)

    while True:
        copier.copy()
        time.sleep(settings.COPY_TIME.total_seconds())


if __name__ == '__main__':
    main()
