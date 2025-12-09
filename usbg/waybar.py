import json
import sys
import time
from typing import Optional
from gi.repository import GLib

# Import the mainloop for dbus-python to work with GLib
from dbus.mainloop.glib import DBusGMainLoop

from .dbus_client import USBGuardDBus, Target
from .notifications import NotificationManager

class WaybarOutput:
    def __init__(self, continuous=False):
        self.usbguard = USBGuardDBus()
        self.continuous = continuous
        
        if continuous:
            # Initialize Notifications
            self.notifier = NotificationManager(self.usbguard)

    def get_device_count(self) -> dict:
        try:
            devices = self.usbguard.list_devices()
            allowed = sum(1 for d in devices if d['target'] == Target.ALLOW)
            blocked = sum(1 for d in devices if d['target'] == Target.BLOCK)
            total = len(devices)
            
            return {
                'total': total,
                'allowed': allowed,
                'blocked': blocked
            }
        except Exception:
            return {'total': 0, 'allowed': 0, 'blocked': 0}
      
    def format_output(self) -> dict:
        counts = self.get_device_count()
          
        if counts['blocked'] > 0:
            icon = "🔒"
            tooltip_class = "blocked"
        elif counts['total'] > 0:
            icon = "🔓"
            tooltip_class = "allowed"
        else:
            icon = "⚫"
            tooltip_class = "none"
          
        text = f"{icon} {counts['allowed']}/{counts['total']}"
        tooltip = f"USB Devices: {counts['allowed']} allowed, {counts['blocked']} blocked"
          
        return {
            "text": text,
            "tooltip": tooltip,
            "class": tooltip_class,
            "percentage": int((counts['allowed'] / counts['total'] * 100) if counts['total'] > 0 else 0)
        }
      
    def print_status(self):
        output = self.format_output()
        print(json.dumps(output), flush=True)
        return True # Return True to keep the GLib timeout running

    def run(self):
        if not self.continuous:
            self.print_status()
            return

        # Continuous mode
        print('{"version": 1}')
        print('[', flush=True)
          
        # Set up GLib MainLoop
        loop = GLib.MainLoop()
          
        # Initial print
        self.print_status()
          
        # Make the JSON array syntax valid by printing comma before subsequent updates
        # (This is a simplified version; proper JSON stream handling in Waybar 
        # usually tolerates newline delimited JSON objs too, but let's stick to your format)
        def print_comma_wrapper():
            print(',', flush=True)
            return self.print_status()

        # Schedule periodic updates (polling is still useful for state consistency)
        # but now we also have event support for notifications
        GLib.timeout_add_seconds(2, print_comma_wrapper)

        try:
            loop.run()
        except KeyboardInterrupt:
            pass

def waybar_main(continuous: bool = False):
    # IMPORTANT: Initialize DBus GMainLoop BEFORE creating the client
    if continuous:
        DBusGMainLoop(set_as_default=True)
          
    waybar = WaybarOutput(continuous)
    waybar.run()
