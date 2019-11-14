import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileReaderThread(object):
    def __init__(self, controller, path, filename, fun, *args, **kwargs):
        self.controller = controller
        self.path = path
        self.filename = filename
        self.function = fun
        self.observer = Observer()
        self.args = args
        self.kwargs = kwargs
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.event_handler = None

    def start(self):
        self.thread.start()

    def run(self):
        """Method that runs forever"""
        self.event_handler = FileChangedHandler(self.controller, self.path, self.filename, self.function, self.args,
                                                self.kwargs)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=self.path, recursive=False)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()


class FileChangedHandler(FileSystemEventHandler):
    def __init__(self, controller, path, filename, fun, *args, **kwargs):
        self.controller = controller
        self.path = path
        self.filename = filename
        self.function = fun
        self.args = args
        self.kwargs = kwargs

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.filename):
            self.function(self.args)
