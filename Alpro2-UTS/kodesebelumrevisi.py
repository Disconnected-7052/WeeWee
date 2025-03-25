import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import heapq
import random
import math
import numpy as np
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

# "This File" Finder Cuz Windows Fucking Suck
This_File_Path = os.path.dirname(os.path.abspath(__file__))
Driver_List = os.path.join(This_File_Path, 'Driver_List.csv')
Map = os.path.join(This_File_Path, 'Map.json')

# Extract csv file
Local_Driver_List = []
with open(Driver_List, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        Local_Driver_List.append(row)
# Extract Map (json)
with open(Map, mode='r') as file:
    Local_Map = json.load(file)

# Dijikstra's Algorithm
def dijkstra(graph, start, end):
    queue = [(0, start, [])]  # (cost, node, path)
    visited = {}
    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node in visited:
            continue
        new_path = path + [node]
        visited[node] = (cost, new_path)
        if node == end:
            return cost, new_path
        for neighbor, weight in graph[node].items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, new_path))
    return float('inf'), []

#Used for finding the total trip distance 
def calculate_trip_distance(graph, driver_loc, pickup_loc, dest_loc):
    pickup_dist, pickup_path = dijkstra(graph, driver_loc, pickup_loc)
    dest_dist, dest_path = dijkstra(graph, pickup_loc, dest_loc)
    return pickup_dist, dest_dist, pickup_dist + dest_dist, pickup_path, dest_path

# Worth calculation to find the most efficient driver
def worth_calculation(pickup_distance, total_distance, max_passengers, passenger_count):
    # Lower score is better
    # Factors:
    # 1. Pickup distance (weighted heavily as this is immediate customer wait time)
    # 2. Overall trip efficiency 
    # 3. Vehicle utilization (how well the vehicle capacity is utilized)
    
    # Penalize long pickup distances
    pickup_score = pickup_distance * 3
    
    # Penalize overall inefficient routes
    trip_score = total_distance
    
    # Penalize underutilized vehicles (sending a 6-seater for 1 person)
    # but don't penalize if it's a good fit
    capacity_utilization = passenger_count / max_passengers
    if capacity_utilization < 0.5:
        capacity_score = (max_passengers - passenger_count) * 5
    else:
        capacity_score = 0
        
    # Lower is better
    total_score = pickup_score + trip_score + capacity_score
    return -total_score  # Return negative so higher is better in the selection algorithm

# Find the most efficient driver for the trip
def find_best_driver(driver_locations, max_passengers, pickup_loc, dest_loc, passenger_count):
    best_driver_idx = None
    best_score = float('-inf')  # Higher is better
    best_pickup_dist = None
    best_dest_dist = None
    best_total_dist = None
    best_pickup_path = None
    best_dest_path = None
    
    for idx, driver_loc in enumerate(driver_locations):
        # Skip drivers who can't accommodate the passenger count
        if passenger_count > max_passengers[idx]:
            continue
            
        # Calculate trip metrics
        pickup_dist, dest_dist, total_dist, pickup_path, dest_path = calculate_trip_distance(
            Local_Map, driver_loc, pickup_loc, dest_loc)
        
        # Skip unreachable routes
        if pickup_dist == float('inf') or dest_dist == float('inf'):
            continue
            
        # Calculate driver efficiency score
        score = worth_calculation(pickup_dist, total_dist, max_passengers[idx], passenger_count)
        
        # Update best driver if this one is better
        if best_driver_idx is None or score > best_score:
            best_driver_idx = idx
            best_score = score
            best_pickup_dist = pickup_dist
            best_dest_dist = dest_dist
            best_total_dist = total_dist
            best_pickup_path = pickup_path
            best_dest_path = dest_path
    
    if best_driver_idx is None:
        return None, None, None, None, None, None, None
        
    return (best_driver_idx, best_pickup_dist, best_dest_dist, best_total_dist, 
            best_pickup_path, best_dest_path, best_score)

# Generate map coordinates for visualization - IMPROVED VERSION
def generate_map_coordinates(map_data):
    """Generate well-distributed coordinates for map visualization"""
    locations = list(map_data.keys())
    coordinates = {}
    
    # Start with evenly distributed coordinates around a circle
    # This gives better initial positions than random
    total_locations = len(locations)
    for i, location in enumerate(locations):
        angle = 2 * 3.14159 * i / total_locations
        radius = 60  # Increased from 40 to 60 for more spread
        x = 50 + radius * math.cos(angle)
        y = 50 + radius * math.sin(angle)
        coordinates[location] = (x, y)
    
    # Force-directed layout algorithm to adjust positions
    # Locations with connections move closer, unconnected ones repel
    for _ in range(200):  # Keeping 200 iterations for thorough layout
        for location in locations:
            # Calculate repulsive forces (from all other nodes)
            force_x, force_y = 0, 0
            for other in locations:
                if other != location:
                    ox, oy = coordinates[other]
                    x, y = coordinates[location]
                    
                    # Vector from this location to other location
                    dx = x - ox
                    dy = y - oy
                    
                    # Avoid division by zero
                    distance = max(0.1, math.sqrt(dx*dx + dy*dy))
                    
                    # Increase repulsive force and apply it at greater distances
                    # Changed from 20 to 30 to repel nodes that are further apart
                    if distance < 30:
                        # Increased from 5.0 to 8.0 for stronger repulsion
                        repulsion = 8.0 / (distance * distance)
                        force_x += dx * repulsion / distance
                        force_y += dy * repulsion / distance
            
            # Calculate attractive forces (only for connected nodes)
            for neighbor, weight in map_data[location].items():
                if neighbor in coordinates:
                    nx, ny = coordinates[neighbor]
                    x, y = coordinates[location]
                    
                    # Vector from this location to connected neighbor
                    dx = nx - x
                    dy = ny - y
                    
                    # Distance
                    distance = max(0.1, math.sqrt(dx*dx + dy*dy))
                    
                    # Reduce attraction strength for more spacing
                    # Changed from 0.05 to 0.03 to make attraction weaker
                    attraction = distance * 0.03 / max(1, weight) 
                    force_x += dx * attraction / distance
                    force_y += dy * attraction / distance
            
            # Apply forces with damping
            x, y = coordinates[location]
            damping = 0.7  # Reduced from 0.8 to 0.7 for smoother movement
            coordinates[location] = (
                x + force_x * damping,
                y + force_y * damping
            )
    
    # Ensure all points are within canvas bounds with padding
    # Increased padding from 10 to 15 for more border space
    padding = 15
    min_x = min(x for x, y in coordinates.values())
    max_x = max(x for x, y in coordinates.values())
    min_y = min(y for x, y in coordinates.values())
    max_y = max(y for x, y in coordinates.values())
    
    # Scale and translate to fit canvas with padding
    scale_x = (100 - 2 * padding) / max(1, max_x - min_x)
    scale_y = (100 - 2 * padding) / max(1, max_y - min_y)
    scale = min(scale_x, scale_y)
    
    for location in locations:
        x, y = coordinates[location]
        x = padding + (x - min_x) * scale
        y = padding + (y - min_y) * scale
        coordinates[location] = (x, y)
    
    return coordinates

# Map coordinates for visualization
MAP_COORDINATES = generate_map_coordinates(Local_Map)

class TaxiAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Taxi Booking System")
        
        # Set window size
        self.root.geometry("900x600")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (900 // 2)
        y = (screen_height // 2) - (600 // 2)
        self.root.geometry("+{}+{}".format(x, y))
        
        # Configure style
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10, "bold"))
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left frame for inputs (1/3 of window)
        self.input_frame = ttk.Frame(self.main_frame, padding="10", relief="ridge", borderwidth=2)
        self.input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5, expand=False)
        
        # Create a label frame for inputs
        input_label_frame = ttk.LabelFrame(self.input_frame, text="Booking Details", padding=10)
        input_label_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Pickup location input
        ttk.Label(input_label_frame, text="Pickup Location:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        self.pickup_entry = ttk.Entry(input_label_frame, width=20)
        self.pickup_entry.grid(row=0, column=1, padx=5, pady=(0,5), sticky=tk.W)
        
        # Destination input
        ttk.Label(input_label_frame, text="Destination:").grid(row=1, column=0, sticky=tk.W, pady=(0,5))
        self.destination_entry = ttk.Entry(input_label_frame, width=20)
        self.destination_entry.grid(row=1, column=1, padx=5, pady=(0,5), sticky=tk.W)
        
        # Passenger input
        ttk.Label(input_label_frame, text="Number of Passengers:").grid(row=2, column=0, sticky=tk.W, pady=(0,5))
        self.passenger_entry = ttk.Entry(input_label_frame, width=20)
        self.passenger_entry.grid(row=2, column=1, padx=5, pady=(0,5), sticky=tk.W)
        
        # Buttons frame
        button_frame = ttk.Frame(self.input_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Find Driver button
        self.find_btn = ttk.Button(button_frame, text="Find Driver", command=self.find_driver)
        self.find_btn.pack(side=tk.LEFT, padx=5)
        
        # Available locations button
        self.show_locations_btn = ttk.Button(button_frame, text="Show Locations", 
                                            command=self.show_available_locations)
        self.show_locations_btn.pack(side=tk.LEFT, padx=5)
        
        # Result frame
        result_frame = ttk.LabelFrame(self.input_frame, text="Results", padding=10)
        result_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        # Result display
        self.result_label = ttk.Label(result_frame, text="")
        self.result_label.pack(anchor=tk.W, pady=5)
        
        # Error display
        self.error_label = ttk.Label(result_frame, text="", foreground='red')
        self.error_label.pack(anchor=tk.W, pady=5)
        
        # Create map frame (2/3 of window)
        self.map_frame = ttk.Frame(self.main_frame, padding="10", relief="ridge", borderwidth=2)
        self.map_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        # Initialize the map figure (larger size)
        self.fig, self.ax = plt.subplots(figsize=(8, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add a toolbar for map interaction
        toolbar = NavigationToolbar2Tk(self.canvas, self.map_frame)
        toolbar.update()
        
        # Draw initial map
        self.draw_map()

    def clear_labels(self):
        self.result_label.config(text="")
        self.error_label.config(text="")

    def draw_map(self, pickup_location=None, destination_location=None, 
                selected_driver_location=None, driver_locations=None, 
                pickup_path=None, destination_path=None):
        self.ax.clear()
        
        # Create a border around the map
        self.ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], 'k-', linewidth=1)
        
        # Draw connections between locations with straight lines only
        for location, neighbors in Local_Map.items():
            loc_x, loc_y = MAP_COORDINATES[location]
            for neighbor in neighbors:
                if neighbor in MAP_COORDINATES:
                    neigh_x, neigh_y = MAP_COORDINATES[neighbor]
                    # Use only straight lines for all connections
                    self.ax.plot([loc_x, neigh_x], [loc_y, neigh_y], 'gray', alpha=0.3, linewidth=0.8)
        
        # Draw all map locations
        for location, (x, y) in MAP_COORDINATES.items():
            self.ax.plot(x, y, 'ko', markersize=4)
            self.ax.annotate(location, (x, y), xytext=(3, 3),
                            textcoords='offset points', fontsize=7, 
                            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="gray", alpha=0.7))
        
        # Draw the pickup path if available
        if pickup_path and len(pickup_path) > 1:
            path_x = []
            path_y = []
            for location in pickup_path:
                if location in MAP_COORDINATES:
                    x, y = MAP_COORDINATES[location]
                    path_x.append(x)
                    path_y.append(y)
            
            if path_x and path_y:
                self.ax.plot(path_x, path_y, 'b-', linewidth=2, alpha=0.6)
                
                # Add arrows along the path to show direction
                for i in range(len(path_x)-1):
                    dx = path_x[i+1] - path_x[i]
                    dy = path_y[i+1] - path_y[i]
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        # Add arrow at midpoint
                        mid_x = (path_x[i] + path_x[i+1]) / 2
                        mid_y = (path_y[i] + path_y[i+1]) / 2
                        self.ax.arrow(mid_x - dx*0.1/length, mid_y - dy*0.1/length, 
                                    dx*0.2/length, dy*0.2/length, 
                                    head_width=1.5, head_length=1.5, 
                                    fc='blue', ec='blue', alpha=0.8)
        
        # Draw the destination path if available
        if destination_path and len(destination_path) > 1:
            path_x = []
            path_y = []
            for location in destination_path:
                if location in MAP_COORDINATES:
                    x, y = MAP_COORDINATES[location]
                    path_x.append(x)
                    path_y.append(y)
            
            if path_x and path_y:
                self.ax.plot(path_x, path_y, 'g-', linewidth=2, alpha=0.6)
                
                # Add arrows along the path to show direction
                for i in range(len(path_x)-1):
                    dx = path_x[i+1] - path_x[i]
                    dy = path_y[i+1] - path_y[i]
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        # Add arrow at midpoint
                        mid_x = (path_x[i] + path_x[i+1]) / 2
                        mid_y = (path_y[i] + path_y[i+1]) / 2
                        self.ax.arrow(mid_x - dx*0.1/length, mid_y - dy*0.1/length, 
                                    dx*0.2/length, dy*0.2/length, 
                                    head_width=1.5, head_length=1.5, 
                                    fc='green', ec='green', alpha=0.8)
        
        # Highlight pickup location
        if pickup_location and pickup_location in MAP_COORDINATES:
            x, y = MAP_COORDINATES[pickup_location]
            self.ax.plot(x, y, 'bs', markersize=8)
            self.ax.annotate("PICKUP", (x, y), xytext=(7, 7),
                            textcoords='offset points', fontsize=9, weight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", fc="yellow", ec="b", alpha=0.8))
        
        # Highlight destination location
        if destination_location and destination_location in MAP_COORDINATES:
            x, y = MAP_COORDINATES[destination_location]
            self.ax.plot(x, y, 'ms', markersize=8)
            self.ax.annotate("DEST", (x, y), xytext=(7, -7),
                            textcoords='offset points', fontsize=9, weight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", fc="pink", ec="m", alpha=0.8))
        
        # Draw driver locations (without offset - they will overlap with locations)
        if driver_locations:
            # Get driver names from Local_Driver_List
            driver_names = []
            for Row in Local_Driver_List:
                if Row.get('Available') == 'True':
                    driver_names.append(Row['Name'])
            
            for i, loc in enumerate(driver_locations):
                if loc in MAP_COORDINATES:
                    x, y = MAP_COORDINATES[loc]
                    
                    # Get the driver name for this location
                    driver_name = driver_names[i] if i < len(driver_names) else f"Driver {i+1}"
                    
                    # Plot the driver directly at the location (no offset)
                    self.ax.plot(x, y, 'ro', markersize=6)
                    self.ax.annotate(driver_name, (x, y), 
                                    xytext=(3, 3), textcoords='offset points', fontsize=8,
                                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="red", alpha=0.7))
        
        # Highlight selected driver (also without offset)
        if selected_driver_location and selected_driver_location in MAP_COORDINATES:
            x, y = MAP_COORDINATES[selected_driver_location]
            
            # Plot the selected driver directly at the location (no offset)
            self.ax.plot(x, y, 'go', markersize=9, zorder=10)
            self.ax.annotate("DRIVER", (x, y), 
                            xytext=(5, 5), textcoords='offset points', fontsize=9, weight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", fc="lightgreen", ec="g", alpha=0.8),
                            zorder=11)
        
        # Add a legend
        if pickup_path or destination_path:
            legend_elements = []
            if pickup_path:
                legend_elements.append(plt.Line2D([0], [0], color='blue', lw=2, label='Driver to Pickup'))
            if destination_path:
                legend_elements.append(plt.Line2D([0], [0], color='green', lw=2, label='Pickup to Destination'))
            if legend_elements:
                self.ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
                
        # Set a more prominent title
        self.ax.set_title("Taxi Map", fontsize=10, weight='bold', pad=0)
        
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xlim(-5, 105)  # Slightly larger than the 0-100 range to give some margin
        self.ax.set_ylim(-5, 105)
        self.fig.tight_layout()
        self.canvas.draw()

    def show_available_locations(self):
        locations = list(Local_Map.keys())
        locations.sort()  # Sort alphabetically for easier reading
        
        locations_window = tk.Toplevel(self.root)
        locations_window.title("Available Locations")
        locations_window.geometry("400x500")
        
        frame = ttk.Frame(locations_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Available Locations:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Create a listbox with scrollbar instead of text widget
        location_listbox = tk.Listbox(frame, font=("Arial", 10), selectmode=tk.SINGLE)
        location_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add locations to listbox
        for location in locations:
            location_listbox.insert(tk.END, location)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(location_listbox, command=location_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        location_listbox.config(yscrollcommand=scrollbar.set)
        
        # Radio buttons for selecting pickup or destination
        selection_var = tk.StringVar(value="pickup")
        
        radio_frame = ttk.Frame(frame)
        radio_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(radio_frame, text="Set as Pickup", variable=selection_var, 
                      value="pickup").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(radio_frame, text="Set as Destination", variable=selection_var, 
                      value="destination").pack(side=tk.LEFT, padx=10)
        
        # Add a button to select the location
        def select_location():
            selection = location_listbox.curselection()
            if selection:
                selected_location = location_listbox.get(selection[0])
                if selection_var.get() == "pickup":
                    self.pickup_entry.delete(0, tk.END)
                    self.pickup_entry.insert(0, selected_location)
                else:
                    self.destination_entry.delete(0, tk.END)
                    self.destination_entry.insert(0, selected_location)
                locations_window.destroy()
        
        select_btn = ttk.Button(frame, text="Select Location", command=select_location)
        select_btn.pack(pady=10)

    def find_driver(self):
        self.clear_labels()
        pickup_location = self.pickup_entry.get().strip().upper()
        destination_location = self.destination_entry.get().strip().upper()
        passenger_input = self.passenger_entry.get().strip()

        # Validate inputs
        if not pickup_location or not destination_location or not passenger_input:
            self.error_label.config(text="Please fill in all fields")
            return
            
        try:
            amount_passenger = int(passenger_input)
        except ValueError:
            self.error_label.config(text="Invalid passenger number")
            return

        if pickup_location not in Local_Map:
            self.error_label.config(text=f"Unreachable pickup location: {pickup_location}")
            return
            
        if destination_location not in Local_Map:
            self.error_label.config(text=f"Unreachable destination: {destination_location}")
            return
            
        if pickup_location == destination_location:
            self.error_label.config(text="Pickup and destination cannot be the same")
            return

        try:
            # Check driver availability
            for Row in Local_Driver_List:
                for Work_Duration in Row.get('Work_Minutes', []):
                    if int(Work_Duration) > 480:
                        Row['Available'] = 'False'

            # Availability Check
            Name_Driver = []
            Max_Passenger_Driver = []
            Location_Driver = []
            for Row in Local_Driver_List:
                if Row.get('Available') == 'False':
                    continue
                Name_Driver.append(Row['Name'])
                Max_Passenger_Driver.append(int(Row['Max_Passenger']))
                Location_Driver.append(Row['Location'])

            if not Location_Driver:  # No available drivers
                self.error_label.config(text="No Available Driver, try again later")
                # Draw map with just user locations
                self.draw_map(pickup_location=pickup_location, 
                            destination_location=destination_location)
                return
                
            # Find best driver for the trip
            (best_driver_idx, pickup_dist, dest_dist, total_dist, 
             pickup_path, dest_path, score) = find_best_driver(
                Location_Driver, Max_Passenger_Driver, 
                pickup_location, destination_location, amount_passenger
            )
            
            if best_driver_idx is None:
                self.error_label.config(text="No suitable driver found for this trip")
                # Draw map with all drivers but no selection
                self.draw_map(pickup_location=pickup_location, 
                            destination_location=destination_location,
                            driver_locations=Location_Driver)
                return
            
            selected_driver = Name_Driver[best_driver_idx]
            selected_location = Location_Driver[best_driver_idx]
            
            # Prepare detailed result text
            result_text = (
                f"Driver: {selected_driver}\n"
                f"Pickup distance: {pickup_dist} km\n"
                f"Trip distance: {dest_dist} km\n"
                f"Total journey: {total_dist} km\n"
                f"Vehicle capacity: {Max_Passenger_Driver[best_driver_idx]} passengers"
            )
            self.result_label.config(text=result_text)
            
            # Update map with pickup, destination, driver and paths
            self.draw_map(
                pickup_location=pickup_location,
                destination_location=destination_location,
                selected_driver_location=selected_location,
                driver_locations=Location_Driver,
                pickup_path=pickup_path,
                destination_path=dest_path
            )
            
        except Exception as e:
            self.error_label.config(text=f"Error: {str(e)}")
            # Draw basic map
            self.draw_map()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaxiAppGUI(root)
    root.mainloop()
