"""
Para Controller POC - Virtual Controller with GUI Test Interface

This proof of concept creates a virtual joystick that emulates the Para Controller Mini,
with a GUI interface to test the controller axes and buttons.

Requirements:
- vJoy driver installed and configured
- Python packages: pyvjoy, tkinter (built-in)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pyvjoy
import threading
import time
import sys

class ParaControllerPOC:
    def __init__(self):
        self.vjoy_device = None
        self.running = False
        self.update_thread = None
        
        # Controller state
        self.x_axis = 0      # -127 to 127 (Left brake)
        self.y_axis = 0      # -127 to 127 (Right brake) 
        self.z_axis = 0      # -127 to 127 (Speed bar)
        self.x_rotation = 180  # 0 to 359 (Weight shift)
        self.buttons = [False] * 4  # 4 buttons
        
        # Initialize vJoy
        self.init_vjoy()
        
        # Start continuous update thread
        self.start_update_thread()
        
        # Create GUI
        self.create_gui()
        
    def init_vjoy(self):
        """Initialize vJoy virtual controller"""
        try:
            # Try to acquire vJoy device 1
            self.vjoy_device = pyvjoy.VJoyDevice(1)
            print("vJoy device acquired successfully!")
            
            # Set initial neutral positions
            self.update_controller()
            
        except Exception as e:
            messagebox.showerror("vJoy Error", 
                f"Failed to initialize vJoy device.\n\n"
                f"Error: {str(e)}\n\n"
                f"Please ensure:\n"
                f"1. vJoy driver is installed\n"
                f"2. vJoy device 1 is configured\n"
                f"3. Device has at least 4 axes and 4 buttons")
            sys.exit(1)
    
    def update_controller(self):
        """Update the virtual controller with current values"""
        if self.vjoy_device:
            try:
                # vJoy uses 0x1-0x8000 (1-32768) range, with 0x4000 (16384) as center
                # Para Controller uses -127 to 127, we need to map this properly
                
                # Map -127 to 127 range to 1-32768 range with 16384 as center
                vjoy_x = max(1, min(32768, int(16384 + (self.x_axis * 16384 / 127))))
                vjoy_y = max(1, min(32768, int(16384 + (self.y_axis * 16384 / 127))))
                vjoy_z = max(1, min(32768, int(16384 + (self.z_axis * 16384 / 127))))
                
                # X-rotation: 0-359 degrees to 1-32768 range
                vjoy_rx = max(1, min(32768, int(1 + (self.x_rotation * 32767 / 359))))
                
                # Set axes
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, vjoy_x)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, vjoy_y)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, vjoy_z)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, vjoy_rx)
                
                # Set buttons
                for i, pressed in enumerate(self.buttons):
                    self.vjoy_device.set_button(i + 1, pressed)
                
                # Update diagnostics display
                if hasattr(self, 'diagnostics_label'):
                    self.diagnostics_label.config(text=f"vJoy Values: X={vjoy_x}, Y={vjoy_y}, Z={vjoy_z}, RX={vjoy_rx}")
                
                # Debug output (less frequent)
                if hasattr(self, 'debug_counter'):
                    self.debug_counter += 1
                    if self.debug_counter % 120 == 0:  # Print every 2 seconds
                        print(f"Controller Update: X={vjoy_x}, Y={vjoy_y}, Z={vjoy_z}, RX={vjoy_rx}")
                else:
                    self.debug_counter = 0
                    
            except Exception as e:
                print(f"Error updating controller: {e}")
    
    def start_update_thread(self):
        """Start continuous update thread to keep controller active"""
        self.running = True
        self.update_thread = threading.Thread(target=self.continuous_update, daemon=True)
        self.update_thread.start()
    
    def continuous_update(self):
        """Continuously update controller to keep it active for games"""
        while self.running:
            try:
                self.update_controller()
                time.sleep(0.016)  # ~60 FPS updates
            except Exception as e:
                print(f"Error in continuous update: {e}")
                time.sleep(0.1)
    
    def create_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title("Para Controller POC - Virtual Joystick Test")
        self.root.geometry("600x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Para Controller Virtual Joystick Test", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
            text="Use the sliders below to test the virtual controller.\n"
                 "1. Check 'Open Game Controllers' to verify detection\n"
                 "2. Use 'Test Movement' to verify all axes work\n"
                 "3. Start your game AFTER starting this application",
            font=("Arial", 10))
        instructions.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Axes section
        axes_frame = ttk.LabelFrame(main_frame, text="Controller Axes", padding="10")
        axes_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # X-Axis (Left Brake)
        ttk.Label(axes_frame, text="X-Axis (Left Brake): -127 to 127").grid(row=0, column=0, sticky=tk.W)
        self.x_var = tk.IntVar(value=0)
        self.x_scale = ttk.Scale(axes_frame, from_=-127, to=127, variable=self.x_var, 
                                orient=tk.HORIZONTAL, length=300, command=self.on_x_change)
        self.x_scale.grid(row=0, column=1, padx=10)
        self.x_value_label = ttk.Label(axes_frame, text="0")
        self.x_value_label.grid(row=0, column=2)
        
        # Y-Axis (Right Brake)
        ttk.Label(axes_frame, text="Y-Axis (Right Brake): -127 to 127").grid(row=1, column=0, sticky=tk.W)
        self.y_var = tk.IntVar(value=0)
        self.y_scale = ttk.Scale(axes_frame, from_=-127, to=127, variable=self.y_var,
                                orient=tk.HORIZONTAL, length=300, command=self.on_y_change)
        self.y_scale.grid(row=1, column=1, padx=10)
        self.y_value_label = ttk.Label(axes_frame, text="0")
        self.y_value_label.grid(row=1, column=2)
        
        # Z-Axis (Speed Bar)
        ttk.Label(axes_frame, text="Z-Axis (Speed Bar): -127 to 127").grid(row=2, column=0, sticky=tk.W)
        self.z_var = tk.IntVar(value=0)
        self.z_scale = ttk.Scale(axes_frame, from_=-127, to=127, variable=self.z_var,
                                orient=tk.HORIZONTAL, length=300, command=self.on_z_change)
        self.z_scale.grid(row=2, column=1, padx=10)
        self.z_value_label = ttk.Label(axes_frame, text="0")
        self.z_value_label.grid(row=2, column=2)
        
        # X-Rotation (Weight Shift)
        ttk.Label(axes_frame, text="X-Rotation (Weight Shift): 0 to 359°").grid(row=3, column=0, sticky=tk.W)
        self.rx_var = tk.IntVar(value=180)
        self.rx_scale = ttk.Scale(axes_frame, from_=0, to=359, variable=self.rx_var,
                                 orient=tk.HORIZONTAL, length=300, command=self.on_rx_change)
        self.rx_scale.grid(row=3, column=1, padx=10)
        self.rx_value_label = ttk.Label(axes_frame, text="180°")
        self.rx_value_label.grid(row=3, column=2)
        
        # Buttons section
        buttons_frame = ttk.LabelFrame(main_frame, text="Controller Buttons", padding="10")
        buttons_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.button_vars = []
        for i in range(4):
            var = tk.BooleanVar()
            self.button_vars.append(var)
            btn = ttk.Checkbutton(buttons_frame, text=f"Button {i+1}", variable=var,
                                 command=lambda idx=i: self.on_button_change(idx))
            btn.grid(row=0, column=i, padx=10)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status & Diagnostics", padding="10")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Controller initialized successfully!")
        self.status_label.grid(row=0, column=0, columnspan=2)
        
        # Diagnostics display
        self.diagnostics_label = ttk.Label(status_frame, text="vJoy Values: X=16384, Y=16384, Z=16384, RX=16384", 
                                          font=("Courier", 9))
        self.diagnostics_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(control_frame, text="Reset to Neutral", command=self.reset_neutral).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Test Movement", command=self.test_movement).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Open Game Controllers", command=self.open_game_controllers).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def on_x_change(self, value):
        """Handle X-axis slider change"""
        self.x_axis = int(float(value))
        self.x_value_label.config(text=str(self.x_axis))
        self.update_controller()
        
    def on_y_change(self, value):
        """Handle Y-axis slider change"""
        self.y_axis = int(float(value))
        self.y_value_label.config(text=str(self.y_axis))
        self.update_controller()
        
    def on_z_change(self, value):
        """Handle Z-axis slider change"""
        self.z_axis = int(float(value))
        self.z_value_label.config(text=str(self.z_axis))
        self.update_controller()
        
    def on_rx_change(self, value):
        """Handle X-rotation slider change"""
        self.x_rotation = int(float(value))
        self.rx_value_label.config(text=f"{self.x_rotation}°")
        self.update_controller()
        
    def on_button_change(self, button_index):
        """Handle button state change"""
        self.buttons[button_index] = self.button_vars[button_index].get()
        self.update_controller()
        
    def reset_neutral(self):
        """Reset all controls to neutral positions"""
        self.x_var.set(0)
        self.y_var.set(0)
        self.z_var.set(0)
        self.rx_var.set(180)
        
        for var in self.button_vars:
            var.set(False)
            
        self.on_x_change(0)
        self.on_y_change(0)
        self.on_z_change(0)
        self.on_rx_change(180)
        
        for i in range(4):
            self.on_button_change(i)
    
    def test_movement(self):
        """Test all axes by moving them through their full range"""
        def run_test():
            original_x = self.x_var.get()
            original_y = self.y_var.get()
            original_z = self.z_var.get()
            original_rx = self.rx_var.get()
            
            self.status_label.config(text="Running movement test...")
            
            try:
                # Test X axis
                for value in [-127, 0, 127, 0]:
                    self.x_var.set(value)
                    self.on_x_change(value)
                    time.sleep(0.5)
                
                # Test Y axis
                for value in [-127, 0, 127, 0]:
                    self.y_var.set(value)
                    self.on_y_change(value)
                    time.sleep(0.5)
                
                # Test Z axis
                for value in [-127, 0, 127, 0]:
                    self.z_var.set(value)
                    self.on_z_change(value)
                    time.sleep(0.5)
                
                # Test RX axis
                for value in [0, 90, 180, 270, 180]:
                    self.rx_var.set(value)
                    self.on_rx_change(value)
                    time.sleep(0.5)
                
                # Test buttons
                for i in range(4):
                    self.button_vars[i].set(True)
                    self.on_button_change(i)
                    time.sleep(0.3)
                    self.button_vars[i].set(False)
                    self.on_button_change(i)
                    time.sleep(0.3)
                
                # Restore original values
                self.x_var.set(original_x)
                self.y_var.set(original_y)
                self.z_var.set(original_z)
                self.rx_var.set(original_rx)
                
                self.on_x_change(original_x)
                self.on_y_change(original_y)
                self.on_z_change(original_z)
                self.on_rx_change(original_rx)
                
                self.status_label.config(text="Movement test completed!")
                
            except Exception as e:
                self.status_label.config(text=f"Test failed: {e}")
        
        # Run test in separate thread to avoid blocking GUI
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
    
    def open_game_controllers(self):
        """Open Windows Game Controllers panel"""
        import subprocess
        try:
            subprocess.run(['control', 'joy.cpl'], check=True)
        except Exception as e:
            messagebox.showwarning("Cannot Open", 
                f"Could not open Game Controllers panel.\n"
                f"Please manually open: Control Panel > Hardware and Sound > Game Controllers")
    
    def on_closing(self):
        """Handle window closing"""
        print("Shutting down controller...")
        self.running = False
        
        # Wait for update thread to finish
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        if self.vjoy_device:
            # Reset controller to neutral before closing
            try:
                print("Resetting controller to neutral...")
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_X, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Y, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_Z, 16384)
                self.vjoy_device.set_axis(pyvjoy.HID_USAGE_RX, 16384)
                for i in range(4):
                    self.vjoy_device.set_button(i + 1, False)
                print("Controller cleanup completed.")
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.running = True
        self.root.mainloop()

if __name__ == "__main__":
    print("Para Controller POC Starting...")
    print("Make sure vJoy driver is installed and configured!")
    
    try:
        app = ParaControllerPOC()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...") 