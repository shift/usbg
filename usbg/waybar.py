import json
import sys
from typing import Optional
from .dbus_client import USBGuardDBus, Target

class WaybarOutput:
    def __init__(self):
        self.usbguard = USBGuardDBus()
        
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
            return {
                'total': 0,
                'allowed': 0,
                'blocked': 0
            }
    
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
    
    def output_once(self):
        output = self.format_output()
        print(json.dumps(output), flush=True)
    
    def output_continuous(self):
        print('{"version": 1}')
        print('[', flush=True)
        
        first = True
        while True:
            if not first:
                print(',', flush=True)
            first = False
            
            output = self.format_output()
            print(json.dumps(output), flush=True)
            
            import time
            time.sleep(2)

def waybar_main(continuous: bool = False):
    waybar = WaybarOutput()
    
    if continuous:
        waybar.output_continuous()
    else:
        waybar.output_once()
