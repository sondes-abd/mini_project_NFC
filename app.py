import tkinter as tk
from tkinter import ttk, messagebox
import serial
import datetime
from serial.tools import list_ports
import threading

class SmartParkingMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Parking Monitor")
        self.root.geometry("1000x700")
        self.root.config(bg="#F5F5F5")  # Background color
        
        # Variables
        self.available_places = tk.StringVar(value="10")
        self.serial_port = None
        
        # Create main frame with padding
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status Display Section
        status_frame = ttk.LabelFrame(main_frame, text="Parking Status", padding="15")
        status_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Available places display
        places_display = ttk.Frame(status_frame)
        places_display.pack(fill=tk.X, pady=10)
        
        ttk.Label(places_display, text="Available Places:", font=('Segoe UI', 14, 'bold'), foreground="#444444").pack(side=tk.LEFT, padx=10)
        ttk.Label(places_display, textvariable=self.available_places, font=('Segoe UI', 24, 'bold'), foreground='#2C7BFF').pack(side=tk.LEFT, padx=10)
        
        # Current Activity Section
        current_frame = ttk.LabelFrame(main_frame, text="Current Activity", padding="15")
        current_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Latest card info
        self.current_uid = tk.StringVar(value="-")
        self.current_person = tk.StringVar(value="-")
        self.current_action = tk.StringVar(value="-")
        
        info_grid = ttk.Frame(current_frame)
        info_grid.pack(fill=tk.X, pady=10)
        
        # Current activity labels
        labels = [
            ("Last Card UID:", self.current_uid),
            ("Person:", self.current_person),
            ("Action:", self.current_action)
        ]
        
        for i, (label_text, var) in enumerate(labels):
            ttk.Label(info_grid, text=label_text, font=('Segoe UI', 10, 'bold'), foreground="#444444").grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            ttk.Label(info_grid, textvariable=var, font=('Segoe UI', 10), foreground="#2C7BFF").grid(row=i, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Activity Log
        log_frame = ttk.LabelFrame(main_frame, text="Parking History", padding="15")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create Treeview
        self.tree = ttk.Treeview(log_frame, columns=('Time', 'Action', 'UID', 'Person', 'Entry', 'Exit', 'Places'), show='headings')
        
        # Configure columns
        columns = [
            ('Time', 'Timestamp', 150),
            ('Action', 'Action', 80),
            ('UID', 'Card UID', 100),
            ('Person', 'Person', 150),
            ('Entry', 'Entry Time', 100),
            ('Exit', 'Exit Time', 100),
            ('Places', 'Places', 80)
        ]
        
        for col, heading, width in columns:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid the tree and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Connection controls
        control_frame = ttk.Frame(main_frame, padding="15")
        control_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E))
        
        # Port selection
        self.port_var = tk.StringVar()
        self.port_select = ttk.Combobox(control_frame, textvariable=self.port_var, font=('Segoe UI', 10), state="readonly")
        self.port_select['values'] = [port.device for port in list_ports.comports()]
        self.port_select.grid(row=0, column=0, padx=10, pady=5)
        
        # Connect button
        self.connect_button = ttk.Button(control_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=1, padx=10, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Initialize serial connection status
        self.connected = False
        
    def toggle_connection(self):
        if not self.connected:
            try:
                port = self.port_var.get()
                self.serial_port = serial.Serial(port, 115200, timeout=1)
                self.connected = True
                self.connect_button.config(text="Disconnect")
                # Start reading thread
                self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
                self.read_thread.start()
            except Exception as e:
                print(f"Connection error: {e}")
        else:
            if self.serial_port:
                self.serial_port.close()
            self.connected = False
            self.connect_button.config(text="Connect")
    
    def read_serial(self):
        while self.connected:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if '|' in line:
                        self.process_data(line)
            except:
                break
    
    def process_data(self, data):
        # Format: ACTION|UID|NAME|ENTRY_TIME|EXIT_TIME|PLACES
        parts = data.split('|')
        if len(parts) == 6:
            action, uid, person, entry_time, exit_time, places = parts
            
            # Check if UID matches the allowed ones
            allowed_uids = ["93064AFC"]  # Example allowed UID, you can add more
            if uid not in allowed_uids:
                action = "Access Denied"  # Update action to "Access Denied"
                person = "N/A"  # Person name is not available for denied access
                entry_time = "N/A"
                exit_time = "N/A"
                places = str(int(self.available_places.get()) + 1)  # Revert places if access is denied
                
                # Display Access Denied popup
                messagebox.showerror("Access Denied", "This UID is not authorized for access.")
                print("Access Denied: UID does not match allowed list.")
            
            # Update current status
            self.current_uid.set(uid)
            self.current_person.set(person)
            self.current_action.set(action)
            self.available_places.set(places)
            
            # Add to tree
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.tree.insert('', 0, values=(current_time, action, uid, person, 
                                          entry_time, exit_time, places))
            
            # Keep only last 100 entries
            if len(self.tree.get_children()) > 100:
                self.tree.delete(self.tree.get_children()[-1])

def main():
    root = tk.Tk()
    app = SmartParkingMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()