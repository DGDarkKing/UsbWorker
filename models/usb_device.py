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

    def clear(self, except_files: list[str] = None):
        except_files = [os.path.join(self.mount_path, file) for file in except_files]
        for filename in os.listdir(self.mount_path):
            file_path = os.path.join(self.mount_path, filename)
            try:
                if os.path.isfile(file_path):
                    if file_path not in except_files:
                        os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                # TODO: Logging
                print(f'Failed to delete "{file_path}".\n\tReason: {e}')

    def copy(self, src_path: str, dist_dir = './', rewrite=False):
        dist_path = os.path.join(self.mount_path, dist_dir)
        name = src_path[src_path.rfind('/')+1 :]
        if name == src_path:
            name = src_path[src_path.rfind('\\')+1 :]
        dist_view = os.path.join(dist_path, name)
        try:
            if os.path.isfile(src_path):
                if (not os.path.isfile(dist_view)
                        or os.stat(src_path).st_size > os.stat(dist_view).st_size) :
                    shutil.copy(src_path, dist_path)

            elif os.path.isdir(src_path) and not os.path.isdir(dist_view):
                copy_tree(src_path, dist_path)
        except Exception as e:
            # TODO: Logging
            print(f'Failed to copy "{src_path}" to "{dist_path}".\n\tReason: {e}')
            raise

    @property
    def mount_exists(self):
        return self.mount_path and os.path.exists(self.mount_path)

    def get_file(self, filename):
        file_path = os.path.join(self.mount_path, filename)
        if os.path.isfile(file_path):
            return file_path
        return None
