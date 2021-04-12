import threading
from pypresence import Client
import time
import asyncio
import os

from gi.repository import GObject, Gedit


class ExamplePyWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "ExamplePyWindowActivatable"

    window = GObject.property(type=Gedit.Window)
    _enabled = False
    _rpc = None

    def __init__(self):
        GObject.Object.__init__(self)
        self._client_id = "740171019003756604"
        self._pid = os.getpid()
        self.shall_update = False
        self.props = None

    def tab_change_state(self, data):
        document = self.window.get_active_tab().get_document()
        self.update_status(document)

    def tab_change(self, tab, data):
        document = tab.get_active_tab().get_document()
        self.update_status(document)

    def update_status(self, document):
        if document.props is not self.props:
            self.props = document.props
            self.epoch_start = time.time()
            self.shall_update = True

    def _reconnect(self):
        if not self._enabled:
            try:
                self._rpc = Client(self._client_id)
                self._rpc.start()
                self._enabled = True
            except self._errors:
                self._enabled = False

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        while True:
            self._reconnect()
            if self._enabled and self.shall_update:
                self._rpc.set_activity(
                    pid=self._pid,
                    large_image="default",
                    details="Writing " + (
                        self.props.language.get_name()
                        if self.props.language
                        else ''
                    ) + " code",
                    state="Editing " + self.props.tepl_short_title,
                    start=self.epoch_start
                )
                if self.props.language:
                    self.shall_update = False

    def do_activate(self):
        self.window.connect("active-tab-changed", self.tab_change)
        self.window.connect("active-tab-state-changed", self.tab_change_state)

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def do_deactivate(self):
        pass

    def do_update_state(self):
        pass
