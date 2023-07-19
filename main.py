import queue

from usb_monitor import LinuxUsbMonitor


def main():
    usb_ready_queue = queue.SimpleQueue
    usb_monitor = LinuxUsbMonitor(usb_ready_queue)
    usb_monitor.start()
    while True:
        pass




if __name__ == '__main__':
    main()