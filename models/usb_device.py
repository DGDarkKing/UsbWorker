import datetime
import os
import shutil
from dataclasses import dataclass, field
from distutils.dir_util import copy_tree


@dataclass
class UsbDevice:
    device_path: str
    mount_path: str
    dt_connect: datetime.datetime = field(default_factory=datetime.datetime.now)

    def clear(self):
        for filename in os.listdir(self.mount_path):
            file_path = os.path.join(self.mount_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                # TODO: Logging
                print(f'Failed to delete "{file_path}".\n\tReason: {e}')

    def copy(self, src_path, dist_dir = './'):
        dist_path = os.path.join(self.mount_path, dist_dir)
        try:
            if os.path.isfile(src_path):
                shutil.copy(src_path, dist_path)
            elif os.path.isdir(src_path):
                copy_tree(src_path, dist_path)
        except Exception as e:
            # TODO: Logging
            print(f'Failed to copy "{src_path}" to "{dist_path}".\n\tReason: {e}')
            raise

    @property
    def check_mount(self):
        return os.path.exists(self.mount_path)
