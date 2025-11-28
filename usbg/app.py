import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from .dbus_client import USBGuardDBus, Target
from typing import Optional

class DeviceRow(Gtk.ListBoxRow):
    def __init__(self, device_info: dict, usbguard: USBGuardDBus):
        super().__init__()
        self.device_info = device_info
        self.usbguard = usbguard
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        
        status_icon = Gtk.Label()
        if device_info['target'] == Target.ALLOW:
            status_icon.set_markup('<span color="green">●</span>')
        elif device_info['target'] == Target.BLOCK:
            status_icon.set_markup('<span color="red">●</span>')
        else:
            status_icon.set_markup('<span color="orange">●</span>')
        box.append(status_icon)
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        name_label = Gtk.Label(label=device_info['name'])
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class('heading')
        info_box.append(name_label)
        
        details = f"ID: {device_info['id']} | Port: {device_info['port']}"
        if device_info['serial']:
            details += f" | Serial: {device_info['serial']}"
        details_label = Gtk.Label(label=details)
        details_label.set_halign(Gtk.Align.START)
        details_label.add_css_class('dim-label')
        info_box.append(details_label)
        
        box.append(info_box)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        if device_info['target'] != Target.ALLOW:
            allow_btn = Gtk.Button(label="Allow")
            allow_btn.add_css_class('suggested-action')
            allow_btn.connect('clicked', self.on_allow_clicked)
            button_box.append(allow_btn)
        
        if device_info['target'] != Target.BLOCK:
            block_btn = Gtk.Button(label="Block")
            block_btn.add_css_class('destructive-action')
            block_btn.connect('clicked', self.on_block_clicked)
            button_box.append(block_btn)
        
        permanent_btn = Gtk.Button(label="Permanent")
        permanent_btn.connect('clicked', self.on_permanent_clicked)
        button_box.append(permanent_btn)
        
        box.append(button_box)
        
        self.set_child(box)
    
    def on_allow_clicked(self, button):
        self.usbguard.apply_device_policy(self.device_info['id'], Target.ALLOW, False)
        self.get_parent().refresh_devices()
    
    def on_block_clicked(self, button):
        self.usbguard.apply_device_policy(self.device_info['id'], Target.BLOCK, False)
        self.get_parent().refresh_devices()
    
    def on_permanent_clicked(self, button):
        dialog = PermanentPolicyDialog(self.get_root(), self.device_info, self.usbguard)
        dialog.present()

class PermanentPolicyDialog(Adw.MessageDialog):
    def __init__(self, parent, device_info: dict, usbguard: USBGuardDBus):
        super().__init__(
            transient_for=parent,
            modal=True,
            heading="Make Policy Permanent",
            body=f"Choose permanent policy for:\n{device_info['name']}"
        )
        
        self.device_info = device_info
        self.usbguard = usbguard
        
        self.add_response("cancel", "Cancel")
        self.add_response("allow", "Allow Permanently")
        self.add_response("block", "Block Permanently")
        
        self.set_response_appearance("allow", Adw.ResponseAppearance.SUGGESTED)
        self.set_response_appearance("block", Adw.ResponseAppearance.DESTRUCTIVE)
        
        self.connect("response", self.on_response)
    
    def on_response(self, dialog, response):
        if response == "allow":
            self.usbguard.apply_device_policy(self.device_info['id'], Target.ALLOW, True)
        elif response == "block":
            self.usbguard.apply_device_policy(self.device_info['id'], Target.BLOCK, True)

class DeviceListBox(Gtk.ListBox):
    def __init__(self, usbguard: USBGuardDBus):
        super().__init__()
        self.usbguard = usbguard
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.add_css_class('boxed-list')
        
    def refresh_devices(self):
        while True:
            row = self.get_row_at_index(0)
            if row is None:
                break
            self.remove(row)
        
        try:
            devices = self.usbguard.list_devices()
            for device in devices:
                row = DeviceRow(device, self.usbguard)
                self.append(row)
        except Exception as e:
            error_label = Gtk.Label(label=f"Error loading devices: {str(e)}")
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.append(error_label)

class PolicyWindow(Adw.Window):
    def __init__(self, usbguard: USBGuardDBus):
        super().__init__()
        self.usbguard = usbguard
        self.set_default_size(800, 600)
        self.set_title("USBGuard Policy Editor")
        
        toolbar_view = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        
        generate_btn = Gtk.Button(label="Generate Policy")
        generate_btn.connect('clicked', self.on_generate_policy)
        header.pack_end(generate_btn)
        
        toolbar_view.add_top_bar(header)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_monospace(True)
        self.text_view.set_margin_start(12)
        self.text_view.set_margin_end(12)
        self.text_view.set_margin_top(12)
        self.text_view.set_margin_bottom(12)
        
        scrolled.set_child(self.text_view)
        toolbar_view.set_content(scrolled)
        
        self.set_content(toolbar_view)
        self.load_policy()
    
    def load_policy(self):
        try:
            rules = self.usbguard.list_rules()
            text = '\n'.join(rules)
            self.text_view.get_buffer().set_text(text)
        except Exception as e:
            self.text_view.get_buffer().set_text(f"Error loading policy: {str(e)}")
    
    def on_generate_policy(self, button):
        try:
            policy = self.usbguard.generate_policy()
            self.text_view.get_buffer().set_text(policy)
        except Exception as e:
            self.text_view.get_buffer().set_text(f"Error generating policy: {str(e)}")

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app, usbguard: USBGuardDBus):
        super().__init__(application=app)
        self.usbguard = usbguard
        self.set_default_size(600, 400)
        self.set_title("USBGuard Control")
        
        toolbar_view = Adw.ToolbarView()
        
        header = Adw.HeaderBar()
        
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.connect('clicked', self.on_refresh_clicked)
        header.pack_start(refresh_btn)
        
        policy_btn = Gtk.Button(label="Policy Editor")
        policy_btn.connect('clicked', self.on_policy_clicked)
        header.pack_end(policy_btn)
        
        toolbar_view.add_top_bar(header)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        self.device_list = DeviceListBox(usbguard)
        scrolled.set_child(self.device_list)
        
        toolbar_view.set_content(scrolled)
        
        self.set_content(toolbar_view)
        self.device_list.refresh_devices()
    
    def on_refresh_clicked(self, button):
        self.device_list.refresh_devices()
    
    def on_policy_clicked(self, button):
        policy_window = PolicyWindow(self.usbguard)
        policy_window.present()

class USBGuardApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.github.usbg',
                        flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.usbguard = None
    
    def do_activate(self):
        if self.usbguard is None:
            try:
                self.usbguard = USBGuardDBus()
            except Exception as e:
                print(f"Error connecting to USBGuard: {e}")
                return
        
        win = self.get_active_window()
        if not win:
            win = MainWindow(self, self.usbguard)
        win.present()
