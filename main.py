import os
import json
import time
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, simpledialog, messagebox

# Constants
STATE_FILE = 'state.json'
DESKTOP_ENTRY_DIR = os.path.expanduser('~/.local/share/applications')

# Ensure that the desktop entry directory exists
os.makedirs(DESKTOP_ENTRY_DIR, exist_ok=True)

class DesktopEntryManager:
    def __init__(self):
        self.state = []
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    self.state = json.load(f)
            except Exception as e:
                print(f'Error loading state: {e}')
                self.state = []
        else:
            self.state = []

    def save_state(self):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f'Error saving state: {e}')

    def add_entry(self, entry):
        self.state.append(entry)
        self.save_state()

    def remove_entry(self, index):
        if 0 <= index < len(self.state):
            entry = self.state.pop(index)
            self.save_state()
            return entry
        return None

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AppImage Desktop Entry Creator')
        self.geometry('600x400')
        style = ttk.Style(self)
        style.theme_use('clam')

        self.manager = DesktopEntryManager()

        self.create_widgets()
        self.refresh_list()

    def create_widgets(self):
        # Container for the Treeview and scrollbar
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ('Application', 'Desktop File')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('Application', text='Application')
        self.tree.heading('Desktop File', text='Desktop File')
        self.tree.column('Application', anchor=tk.W, width=200)
        self.tree.column('Desktop File', anchor=tk.W, width=380)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame for buttons at bottom
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.btn_create = ttk.Button(btn_frame, text='Create Desktop Entry', command=self.create_desktop_entry)
        self.btn_create.pack(side=tk.LEFT, padx=5)

        self.btn_delete = ttk.Button(btn_frame, text='Delete Selected Entry', command=self.delete_entry)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for entry in self.manager.state:
            self.tree.insert('', 'end', values=(entry.get('app_name', 'Unnamed'), entry.get('desktop_file', '')))

    def create_desktop_entry(self):
        # Open file selection for AppImage
        appimage_path = filedialog.askopenfilename(title='Select AppImage', filetypes=[('AppImage', '*.AppImage'), ('All Files', '*.*')])
        if not appimage_path:
            return

        # Ask for the application name, default from file basename
        default_name = os.path.splitext(os.path.basename(appimage_path))[0]
        app_name = simpledialog.askstring('Application Name', 'Enter the application name:', initialvalue=default_name)
        if not app_name:
            messagebox.showerror('Error', 'Application name cannot be empty.')
            return

        # Ask for the WM Class which helps GNOME match the running window with the desktop entry
        wm_class = simpledialog.askstring('WM Class', 'Enter the WM Class for the application (optional)', initialvalue=app_name)
        if not wm_class:
            wm_class = app_name

        # Generate a unique desktop file name
        timestamp = int(time.time())
        filename = f"{app_name.replace(' ', '_')}_{timestamp}.desktop"
        desktop_file_path = os.path.join(DESKTOP_ENTRY_DIR, filename)

        # Ask for icon file to be used for the desktop entry (optional)
        icon_path = filedialog.askopenfilename(title='Select Icon', filetypes=[('Image Files', '*.png *.xpm *.jpg *.svg'), ('All Files', '*.*')])

        # Create the desktop entry content
        desktop_content = f"[Desktop Entry]\nVersion=1.0\nType=Application\nName={app_name}\nExec=\"{appimage_path}\"\nIcon={icon_path}\nStartupWMClass={wm_class}\nTerminal=false\nCategories=Utility;" 

        try:
            with open(desktop_file_path, 'w') as f:
                f.write(desktop_content)
            # Make the desktop file executable
            os.chmod(desktop_file_path, 0o755)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to create desktop entry: {e}')
            return

        # Save state
        entry = {
            'app_name': app_name,
            'appimage_path': appimage_path,
            'desktop_file': desktop_file_path
        }
        self.manager.add_entry(entry)
        self.refresh_list()
        messagebox.showinfo('Success', f'Desktop entry created: {desktop_file_path}')

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Warning', 'Please select an entry to delete.')
            return

        # Get the index based on the selection order in the treeview (assuming same order as self.manager.state)
        index = self.tree.index(selected[0])
        entry = self.manager.state[index]
        desktop_file = entry.get('desktop_file')

        if messagebox.askyesno('Confirm Delete', f'Are you sure you want to delete the desktop entry for {entry.get("app_name", "Unnamed")}?'):
            try:
                if os.path.exists(desktop_file):
                    os.remove(desktop_file)
            except Exception as e:
                messagebox.showerror('Error', f'Failed to delete desktop entry file: {e}')
                return
            self.manager.remove_entry(index)
            self.refresh_list()
            messagebox.showinfo('Deleted', 'Desktop entry deleted successfully.')

if __name__ == '__main__':
    app = Application()
    app.mainloop() 