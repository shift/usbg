import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib
from .dbus_client import Target
from .config import Config

class NotificationManager:
    def __init__(self, usbguard_client):
        self.client = usbguard_client
        self.config = Config()
        
        # Initialize libnotify
        if not Notify.init("USBGuard Applet"):
            print("Failed to initialize notifications", flush=True)
            return

        # Subscribe to device events
        self.client.subscribe_device_events(self.on_device_event)

    def on_device_event(self, id, event, target, rule, attributes):
        # event: 0=Present, 1=Insert, 2=Update, 3=Remove
        # target: 0=Allow, 1=Block, 2=Reject
        
        # We only care about Insertions (1) that are Blocked (1)
        if event == 1 and target == 1:
            if self.config.get('usbguard', 'notification_on_block', True):
                self.show_allow_notification(id, rule)

    def show_allow_notification(self, device_id, rule):
        # Extract a readable name from the rule string
        name = "Unknown Device"
        if 'name "' in rule:
            try:
                name = rule.split('name "')[1].split('"')[0]
            except IndexError:
                pass

        notification = Notify.Notification.new(
            "USB Device Blocked",
            f"{name}\n(ID: {device_id})",
            "security-high-symbolic" # or "dialog-warning"
        )
        
        # Add "Allow" action
        # Note: This requires a notification server that supports actions (dunst, mako, etc.)
        notification.add_action(
            "allow",
            "Allow",
            self.on_allow_action,
            device_id # User data
        )
        
        notification.set_timeout(Notify.EXPIRES_NEVER) # Stay on screen
        notification.show()

    def on_allow_action(self, notification, action, device_id):
        try:
            # Apply Allow policy (not permanent by default)
            self.client.apply_device_policy(int(device_id), Target.ALLOW, False)
            
            # Update notification to show success
            notification.update(
                "Device Allowed",
                f"Device {device_id} is now authorized.",
                "security-low-symbolic"
            )
            notification.clear_actions() # Remove the button
            notification.set_timeout(5000) # Expire after 5s
            notification.show()
        except Exception as e:
            print(f"Error allowing device: {e}", flush=True)
