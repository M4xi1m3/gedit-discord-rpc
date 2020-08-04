import threading
from pypresence import Presence
import time
import asyncio
import os

from gi.repository import GObject, Gedit

class ExamplePyWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "ExamplePyWindowActivatable"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        os.chdir(os.path.dirname(__file__))
        GObject.Object.__init__(self)
        GObject.Object.__init__(self)
        with open("token", "r") as token_file:
            self.CLIENT_ID = ''.join(c for c in token_file.readline() if c.isdigit())
        print(self.CLIENT_ID)
        self.shall_update = False
        self.langage = ""
        self.name = ""

    def tab_change_state(self, data):
        document = self.window.get_active_tab().get_document()
        self.update_status(document)

    def tab_change(self, tab, data):
        document = tab.get_active_tab().get_document()
        self.update_status(document)

    def update_status(self, document):
        langage = document.get_language()

        if (langage == None):
            langage = ""
        else:
            langage = langage.get_name()

        name = document.get_uri_for_display()
        
        if (name != self.name or self.langage != langage):
            self.name = name
            self.langage = langage
            self.epoch_start = time.time()
            self.shall_update = True
    
    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.RPC = Presence(self.CLIENT_ID)
        self.RPC.connect()
        while True:
            if self.shall_update:
                self.RPC.update(large_image="default", state="Editing " + os.path.basename(self.name), details="Writing " + self.langage + " code", start=self.epoch_start)
                self.shall_update = False
                for i in range(15):
                    time.sleep(1)
            else:
                time.sleep(1)

    def do_activate(self):
        self.window.connect("active-tab-changed", self.tab_change)
        self.window.connect("active-tab-state-changed", self.tab_change_state)
        
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def do_deactivate(self):
        pass

    def do_update_state(self):
        pass

