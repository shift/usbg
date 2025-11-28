import dbus
from enum import IntEnum
from typing import List, Dict, Any, Optional

class Target(IntEnum):
    ALLOW = 0
    BLOCK = 1
    REJECT = 2

class DevicePolicy(IntEnum):
    ALLOW = 0
    BLOCK = 1
    REJECT = 2
    KEEP = 3
    APPLY_POLICY = 4

class USBGuardDBus:
    DBUS_SERVICE = "org.usbguard1"
    DBUS_POLICY_PATH = "/org/usbguard1/Policy"
    DBUS_DEVICES_PATH = "/org/usbguard1/Devices"
    
    def __init__(self):
        self.bus = dbus.SystemBus()
        self._policy = None
        self._devices = None
        
    @property
    def policy(self):
        if self._policy is None:
            self._policy = self.bus.get_object(
                self.DBUS_SERVICE,
                self.DBUS_POLICY_PATH
            )
        return self._policy
    
    @property
    def devices(self):
        if self._devices is None:
            self._devices = self.bus.get_object(
                self.DBUS_SERVICE,
                self.DBUS_DEVICES_PATH
            )
        return self._devices
    
    def list_devices(self, query: str = "match") -> List[Dict[str, Any]]:
        devices_raw = self.devices.listDevices(query, dbus_interface="org.usbguard.Devices1")
        devices = []
        for dev in devices_raw:
            device_id = dev[0]
            rule = dev[1]
            
            rule_parts = rule.split()
            target_str = rule_parts[0] if rule_parts else "block"
            
            target_map = {
                'allow': Target.ALLOW,
                'block': Target.BLOCK,
                'reject': Target.REJECT
            }
            target = target_map.get(target_str.lower(), Target.BLOCK)
            
            name_start = rule.find('name "')
            name = "Unknown Device"
            if name_start != -1:
                name_start += 6
                name_end = rule.find('"', name_start)
                if name_end != -1:
                    name = rule[name_start:name_end]
            
            serial_start = rule.find('serial "')
            serial = ""
            if serial_start != -1:
                serial_start += 8
                serial_end = rule.find('"', serial_start)
                if serial_end != -1:
                    serial = rule[serial_start:serial_end]
            
            port_start = rule.find('via-port "')
            port = ""
            if port_start != -1:
                port_start += 10
                port_end = rule.find('"', port_start)
                if port_end != -1:
                    port = rule[port_start:port_end]
            
            device = {
                'id': device_id,
                'name': name,
                'target': target,
                'serial': serial,
                'port': port,
                'interface_types': [],
                'device_hash': '',
                'parent_hash': '',
                'via_port': port,
                'with_interface': '',
                'rule': rule
            }
            devices.append(device)
        return devices
    
    def apply_device_policy(self, device_id: int, target: Target, permanent: bool = False) -> int:
        rule_id = self.devices.applyDevicePolicy(
            dbus.UInt32(device_id),
            dbus.UInt32(target),
            dbus.Boolean(permanent),
            dbus_interface="org.usbguard.Devices1"
        )
        return rule_id
    
    def list_rules(self) -> List[str]:
        rules = self.policy.listRules(dbus.String(""), dbus_interface="org.usbguard.Policy1")
        return [rule[1] for rule in rules]
    
    def append_rule(self, rule: str, parent_id: int = 0) -> int:
        rule_id = self.policy.appendRule(
            dbus.String(rule),
            dbus.UInt32(parent_id),
            dbus_interface="org.usbguard.Policy1"
        )
        return rule_id
    
    def remove_rule(self, rule_id: int) -> None:
        self.policy.removeRule(
            dbus.UInt32(rule_id),
            dbus_interface="org.usbguard.Policy1"
        )
    
    def generate_policy(self) -> str:
        devices = self.list_devices()
        policy_lines = []
        
        for device in devices:
            if device['target'] == Target.ALLOW:
                policy_lines.append(device['rule'])
        
        return '\n'.join(policy_lines)
    
    def subscribe_device_events(self, callback):
        self.bus.add_signal_receiver(
            callback,
            dbus_interface="org.usbguard.Devices1",
            signal_name="DevicePresenceChanged"
        )
    
    def subscribe_policy_events(self, callback):
        self.bus.add_signal_receiver(
            callback,
            dbus_interface="org.usbguard.Policy1",
            signal_name="PolicyChanged"
        )
