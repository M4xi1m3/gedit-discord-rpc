"""
    Gedit DiscordRPC Plugin
"""
import os

from time import time
from threading import Thread, Event as TEvent
from asyncio import (
    new_event_loop as new_loop,
    set_event_loop as set_loop)
from pypresence.client import Client
from pypresence.exceptions import InvalidID, InvalidPipe


from gi.repository import GObject, Gedit


class DiscordRPC(Thread):
    """
    Discord RPC Thread

    Updates discord rich presence status periodically.
    """
    _client_id = "740171019003756604"  # set discord application id here
    _enabled = False
    _update = False
    tab = None
    langs = []
    _start = -1

    _rpc = None
    _pid = None
    _errors = (
        ConnectionRefusedError,
        InvalidID,
        InvalidPipe,
        FileNotFoundError,
        ConnectionResetError
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pid = os.getpid()
        self.__stop = TEvent()

    def absent(self, tab):
        """
            clear status from DiscordRPC
        """
        if tab is self.tab:
            self.tab = None
            self._update = True

    def present(self, tab=None, start=-1):
        """
        Set status for DiscordRPC.
        """
        if tab:
            self.tab = tab
            self._start = start
        else:
            self.tab = None
        self._update = True

    @property
    def doc(self):
        if self.tab:
            return self.tab.get_document()
        return None

    @property
    def lang(self):
        """Language name"""
        if self.doc and self.doc.props.language:
            return self.doc.props.language.get_name()
        return 'Unknown'

    @property
    def name(self):
        if self.doc:
            return self.doc.props.tepl_short_title
        return ''

    def stop(self):
        """Stop this thread"""
        self.__stop.set()

    def run(self):
        set_loop(new_loop())
        while True:
            if self.__stop.is_set() and not self._enabled:
                break
            try:
                self._reconnect()
                if self.__stop.is_set():
                    if self._enabled:
                        self._rpc.clear_activity(pid=self._pid)
                        self._rpc.close()
                        self._enabled = False
                        continue
                if self._enabled and self._update:
                    if self.doc:
                        data = {
                            'pid': self._pid,
                            'large_image':
                                self.lang.lower()
                                if self.lang.lower() in self.langs
                                else 'default',
                            'large_text': self.name,
                            'small_image':
                                'default'
                                if self.lang.lower() in self.langs
                                else None,
                            'details': "Writing " + self.lang + " code",
                            'state': "Editing " + self.name,
                            'start': self._start
                        }
                        self._rpc.set_activity(**data)
                        if self.lang:
                            self._update = False
                    else:
                        self._rpc.clear_activity(pid=self._pid)
                        self._update = False
            except self._errors:
                self._enabled = False
                try:
                    self._rpc.close()
                except AttributeError:
                    pass

    def _reconnect(self):
        if not self._enabled:
            try:
                self._rpc = Client(self._client_id)
                self._rpc.start()
                self._enabled = True

            except self._errors:
                self._enabled = False


class DiscordRpcWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    """
        DiscordRPC plugin for gedit
    """
    __gtype_name__ = "DiscordRpcWindowActivatable"

    window = GObject.property(type=Gedit.Window)
    _rpc = None
    _events = {}

    def __init__(self):
        GObject.Object.__init__(self)

    def absent(self, _, tab, *args):    # pylint: disable=unused-argument
        """
        absence handler
        """
        self._rpc.absent(tab)

    def present(self, *args):   # pylint: disable=unused-argument
        """
        presence handler
        """
        self._rpc.present(
            self.window.get_active_tab(),   # pylint: disable=no-member
            time()
        )

    def do_activate(self):
        """
            activate the plugin
        """
        # pylint: disable=no-member
        self._events['active-tab-changed'] = self.window.connect(
            "active-tab-changed",
            self.present
        )
        self._events['active-tab-state-changed'] = self.window.connect(
            "active-tab-state-changed",
            self.present
        )
        self._events['tab-removed'] = self.window.connect(
            "tab-removed",
            self.absent
        )

        self._rpc = DiscordRPC()
        self._rpc.start()

        self.present()

    def do_deactivate(self):
        """
            deactivate the plugin
        """
        for each in self._events.values():
            self.window.disconnect(each)    # pylint: disable=no-member
        self._rpc.stop()
        self._rpc.join()

    def do_update_state(self):
        """
            update state
        """
