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

# Randomize
def randomize_map_weights():
    """Randomize weights while maintaining connectivity"""
    global Local_Map
    locations = list(Local_Map.keys())
    
    # Ensure basic connectivity
    for i in range(len(locations)-1):
        current = locations[i]
        next_loc = locations[i+1]
        if next_loc not in Local_Map[current]:
            Local_Map[current][next_loc] = random.randint(2, 15)
        if current not in Local_Map[next_loc]:
            Local_Map[next_loc][current] = Local_Map[current][next_loc]
    
    # Randomize existing connections
    for location in Local_Map:
        for neighbor in list(Local_Map[location].keys()):
            # Keep 70% of connections, randomize 30%
            if random.random() < 0.3:
                new_weight = random.randint(1, 20)
                Local_Map[location][neighbor] = new_weight
                # Make sure reverse connection matches
                if location in Local_Map.get(neighbor, {}):
                    Local_Map[neighbor][location] = new_weight
        
def randomize_driver_locations():
    """Randomize locations for all drivers ensuring unique positions"""
    global Local_Driver_List
    all_locations = list(Local_Map.keys())
    
    # Make sure we have enough unique locations
    if len(all_locations) < len(Local_Driver_List):
        raise ValueError("Not enough unique locations for all drivers")
    
    # Create a shuffled list of available locations
    available_locs = random.sample(all_locations, len(all_locations))
    
    # Assign each driver to a unique location
    for i, driver in enumerate(Local_Driver_List):
        # Wrap around if we have more drivers than locations (shouldn't happen due to check above)
        loc_index = i % len(available_locs)
        driver['Location'] = available_locs[loc_index]
    
    # Update CSV to persist changes
    with open(Driver_List, 'w', newline='') as file:
        fieldnames = ['Name', 'Max_Passenger', 'Location', 'Available', 'Work_Minutes']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(Local_Driver_List)

################################################################################################

# Generate map coordinates for visualization - RANDOMIZED VERSION
def generate_map_coordinates(map_data):
    """Generate randomized coordinates with cluster prevention"""
    locations = list(map_data.keys())
    coordinates = {}

    # Random initialization with collision avoidance
    used_points = set()
    for location in locations:
        while True:
            x = random.uniform(5, 95)
            y = random.uniform(5, 95)
            # Ensure no two points start too close
            if all(math.hypot(x-px, y-py) > 10 for (px, py) in used_points):
                coordinates[location] = (x, y)
                used_points.add((x, y))
                break
    
    # Random initial placement with some structure
    grid_size = math.ceil(math.sqrt(len(locations)))
    random.seed()  # Seed with current time
    
    # Generate positions in a grid with random offsets
    for i, location in enumerate(locations):
        row = i // grid_size
        col = i % grid_size
        x = 10 + (80/grid_size) * col + random.uniform(-5, 5)
        y = 10 + (80/grid_size) * row + random.uniform(-5, 5)
        coordinates[location] = (x, y)

    # Force-directed layout algorithm with randomness
    for _ in range(150):  # Reduced iterations for faster randomization
        for location in locations:
            force_x, force_y = 0, 0
            
            # Add random jitter to forces
            jitter = 0.3
            force_x += random.uniform(-jitter, jitter)
            force_y += random.uniform(-jitter, jitter)
            
            for other in locations:
                if other != location:
                    ox, oy = coordinates[other]
                    x, y = coordinates[location]
                    
                    # Vector from this location to other location
                    dx = x - ox
                    dy = y - oy
                    
                    # Avoid division by zero
                    distance = max(0.1, math.sqrt(dx*dx + dy*dy))
                    
                    # Repulsive force
                    if distance < 30:
                        repulsion = 8.0 / (distance * distance)
                        force_x += dx * repulsion / distance
                        force_y += dy * repulsion / distance
            
            # Attractive forces for connected nodes
            for neighbor, weight in map_data[location].items():
                if neighbor in coordinates:
                    nx, ny = coordinates[neighbor]
                    x, y = coordinates[location]
                    
                    dx = nx - x
                    dy = ny - y
                    
                    distance = max(0.1, math.sqrt(dx*dx + dy*dy))
                    attraction = distance * 0.03 / max(1, weight)
                    force_x += dx * attraction / distance
                    force_y += dy * attraction / distance
            
            # Apply forces with damping
            damping = 0.7
            coordinates[location] = (
                coordinates[location][0] + force_x * damping,
                coordinates[location][1] + force_y * damping
            )

    # Add final random scaling and small offsets
    scale_factor = random.uniform(0.8, 1.2)
    for location in coordinates:
        x, y = coordinates[location]
        coordinates[location] = (
            x * scale_factor + random.uniform(-2, 2),
            y * scale_factor + random.uniform(-2, 2)
        )
    
    # Ensure all points are within canvas bounds with padding
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

# Map coordinates for visualization (global so it can be regenerated)
MAP_COORDINATES = generate_map_coordinates(Local_Map)

class TaxiAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Taxi Booking System")
        
        # Set window size - increased to accommodate driver info panel
        self.root.geometry("1100x700")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (1100 // 2)
        y = (screen_height // 2) - (700 // 2)
        self.root.geometry("+{}+{}".format(x, y))
        
        # Configure style with larger fonts
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 12))  # Increased from 10
        style.configure("TButton", font=("Arial", 12, "bold"))  # Increased from 10
        style.configure("Treeview.Heading", font=("Arial", 12))  # Added for treeview headers
        style.configure("Treeview", font=("Arial", 11))  # Added for treeview content
        style.configure("Available.TLabel", foreground="darkgreen", font=("Arial", 12, "bold"))  # Increased
        style.configure("Unavailable.TLabel", foreground="darkred", font=("Arial", 12, "bold"))  # Increased
        style.configure("Best.TLabelframe", background="#e3f2fd")  # Light blue background for best driver
        style.configure("Best.TLabelframe.Label", background="#e3f2fd", font=("Arial", 12, "bold"))  # Increased
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left frame for inputs (1/4 of window)
        self.input_frame = ttk.Frame(self.main_frame, padding="10", relief="ridge", borderwidth=2)
        self.input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5, expand=False, anchor=tk.NW)
        
        # Create a label frame for inputs
        input_label_frame = ttk.LabelFrame(self.input_frame, text="Booking Details", padding=10)
        input_label_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add randomization buttons
        random_frame = ttk.Frame(self.input_frame)
        random_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Pickup location input
        ttk.Label(input_label_frame, text="Pickup Location:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        self.pickup_entry = ttk.Entry(input_label_frame, width=20, font=("Arial", 12))  # Increased font
        self.pickup_entry.grid(row=0, column=1, padx=5, pady=(0,5), sticky=tk.W)
        
        # Destination input
        ttk.Label(input_label_frame, text="Destination:").grid(row=1, column=0, sticky=tk.W, pady=(0,5))
        self.destination_entry = ttk.Entry(input_label_frame, width=20, font=("Arial", 12))  # Increased font
        self.destination_entry.grid(row=1, column=1, padx=5, pady=(0,5), sticky=tk.W)
        
        # Passenger input
        ttk.Label(input_label_frame, text="Number of Passengers:").grid(row=2, column=0, sticky=tk.W, pady=(0,5))
        self.passenger_entry = ttk.Entry(input_label_frame, width=20, font=("Arial", 12))  # Increased font
        self.passenger_entry.grid(row=2, column=1, padx=5, pady=(0,5), sticky=tk.W)
        
        # Buttons frame
        button_frame = ttk.Frame(self.input_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Available locations button
        self.show_locations_btn = ttk.Button(button_frame, text="Show Locations", 
                                            command=self.show_available_locations)
        self.show_locations_btn.pack(side=tk.LEFT, padx=5)
        
        # Randomize Map button
        self.randomize_btn = ttk.Button(button_frame, text="Randomize Map", 
                                      command=self.randomize_all)
        self.randomize_btn.pack(side=tk.LEFT, padx=5)
        
        # Result frame
        result_frame = ttk.LabelFrame(self.input_frame, text="Results", padding=10)
        result_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        # Result display
        self.result_label = ttk.Label(result_frame, text="", font=("Arial", 12))  # Increased font
        self.result_label.pack(anchor=tk.W, pady=5)
        
        # Error display
        self.error_label = ttk.Label(result_frame, text="", foreground='red', font=("Arial", 12))  # Increased font
        self.error_label.pack(anchor=tk.W, pady=5)
        
        # Create driver information frame
        self.driver_info_frame = ttk.LabelFrame(self.main_frame, text="Driver Information", padding=10)
        self.driver_info_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5, expand=False, anchor=tk.N)
        
        # Create Treeview widget for driver info with larger fonts
        self.driver_tree = ttk.Treeview(self.driver_info_frame, 
                                      columns=("name", "max_passenger", "location", "status", "work_time"),
                                      show="headings",
                                      height=6)
        
        # Define columns
        self.driver_tree.heading("name", text="Driver Name")
        self.driver_tree.heading("max_passenger", text="Max Passengers")
        self.driver_tree.heading("location", text="Location")
        self.driver_tree.heading("status", text="Status")
        self.driver_tree.heading("work_time", text="Work Minutes")
        
        # Set column widths
        self.driver_tree.column("name", width=120)  # Increased width
        self.driver_tree.column("max_passenger", width=120)  # Increased width
        self.driver_tree.column("location", width=100)  # Increased width
        self.driver_tree.column("status", width=100)  # Increased width
        self.driver_tree.column("work_time", width=120)  # Increased width
        
        # Create scrollbar for the treeview
        driver_scrollbar = ttk.Scrollbar(self.driver_info_frame, orient="vertical", command=self.driver_tree.yview)
        self.driver_tree.configure(yscrollcommand=driver_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.driver_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        driver_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add refresh button for driver info
        self.refresh_btn = ttk.Button(self.driver_info_frame, text="Refresh Driver Data", 
                                    command=self.refresh_driver_info)
        self.refresh_btn.pack(pady=10)
        
        # Create map frame (2/3 of window)
        self.map_frame = ttk.Frame(self.main_frame, padding="10", relief="ridge", borderwidth=2)
        self.map_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5, expand=True)
        
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
        
        # Load initial driver information
        self.load_driver_info()

        #Shows driver efficiency
        style.configure("Best.TLabelframe", background="#e3f2fd")  # Light blue background for best driver
        style.configure("Best.TLabelframe.Label", background="#e3f2fd", font=("Arial", 10, "bold"))

        # Add efficiency analysis button to button_frame
        self.efficiency_btn = ttk.Button(button_frame, text="Analyze Driver Efficiency", command=self.show_driver_efficiency_analysis)
        self.efficiency_btn.pack(side=tk.LEFT, padx=5)
        
    # MAPS
    def randomize_weights(self):
        randomize_map_weights()
        self.draw_map()
    
    ########################################################################## ISSUE HERE #####################################
    def randomize_drivers(self):
        try:
            randomize_driver_locations()
            self.refresh_driver_info()
            self.draw_map()
            messagebox.showinfo("Success", "Driver locations randomized with no overlaps")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    ###########################################################################################################################

    def randomize_layout(self):
        global MAP_COORDINATES
        MAP_COORDINATES = generate_map_coordinates(Local_Map)
        self.draw_map()

    def randomize_all(self):
        self.randomize_weights()
        self.randomize_drivers()
        self.randomize_layout()
        messagebox.showinfo("Full Randomization", 
                          "Complete system randomization applied")

    def load_driver_info(self):
        """Load driver information into the treeview"""
        # Clear existing data
        for item in self.driver_tree.get_children():
            self.driver_tree.delete(item)
        
        # Check driver availability
        for Row in Local_Driver_List:
            for Work_Duration in Row.get('Work_Minutes', []):
                if Work_Duration and int(Work_Duration) > 480:
                    Row['Available'] = 'False'
        
        # Insert data into treeview
        for driver in Local_Driver_List:
            status = "Available" if driver.get('Available') == 'True' else "Unavailable"
            status_tag = "available" if status == "Available" else "unavailable"
            
            # Insert the driver data
            driver_id = self.driver_tree.insert("", "end", 
                             values=(driver.get('Name', 'Unknown'),
                                     driver.get('Max_Passenger', '0'),
                                     driver.get('Location', 'Unknown'),
                                     status,
                                     driver.get('Work_Minutes', '0')))
            
            # Apply tag for coloring
            self.driver_tree.tag_configure("available", background="#E0FFE0", foreground= "black")  # Light green
            self.driver_tree.tag_configure("unavailable", background="#FFE0E0", foreground= "black")  # Light red
            self.driver_tree.item(driver_id, tags=(status_tag,))

    def refresh_driver_info(self):
        """Reload driver information from the CSV file"""
        global Local_Driver_List
        # Reload the csv file
        Local_Driver_List = []
        with open(Driver_List, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Local_Driver_List.append(row)
        
        # Update the treeview
        self.load_driver_info()
        
        # Show confirmation message
        messagebox.showinfo("Refresh", "Driver information has been refreshed.")

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
        
        # Draw all driver locations (both available and unavailable)
        all_drivers = []
        for driver in Local_Driver_List:
            loc = driver.get('Location')
            name = driver.get('Name')
            available = driver.get('Available') == 'True'
            if loc in MAP_COORDINATES:
                all_drivers.append((loc, name, available))
        
        for loc, name, available in all_drivers:
            x, y = MAP_COORDINATES[loc]
            
            # Different markers and colors for available vs unavailable drivers
            marker_color = 'go' if available else 'ro'
            marker_size = 6
            
            self.ax.plot(x, y, marker_color, markersize=marker_size)
            
            # Different background colors for available vs unavailable drivers
            bbox_color = 'lightgreen' if available else 'lightcoral'
            self.ax.annotate(name, (x, y), 
                           xytext=(3, 3), textcoords='offset points', fontsize=8,
                           bbox=dict(boxstyle="round,pad=0.1", fc=bbox_color, ec="gray", alpha=0.7))
        
        # Highlight selected driver (also without offset)
        if selected_driver_location and selected_driver_location in MAP_COORDINATES:
            x, y = MAP_COORDINATES[selected_driver_location]
            
            # Plot the selected driver directly at the location (no offset)
            self.ax.plot(x, y, 'gs', markersize=9, zorder=10)
            self.ax.annotate("SELECTED", (x, y), 
                            xytext=(5, 5), textcoords='offset points', fontsize=9, weight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", fc="yellow", ec="g", alpha=0.8),
                            zorder=11)
        
        # Add a legend
        legend_elements = []
        
        # Add path legend elements
        if pickup_path:
            legend_elements.append(plt.Line2D([0], [0], color='blue', lw=2, label='Driver to Pickup'))
        if destination_path:
            legend_elements.append(plt.Line2D([0], [0], color='green', lw=2, label='Pickup to Destination'))
            
        # Add driver status legend elements
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', label='Available Driver',
                             markerfacecolor='g', markersize=8))
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', label='Unavailable Driver',
                             markerfacecolor='r', markersize=8))
            
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
        
        ttk.Label(frame, text="Available Locations:", font=("Arial", 1, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Create a listbox with scrollbar instead of text widget
        location_listbox = tk.Listbox(frame, font=("Arial", 1), selectmode=tk.SINGLE)
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
                if Row.get('Available') != 'True':
                    continue
                    
            # Get driver data
            driver_locations = []
            max_passengers = []
            driver_names = []
            
            for driver in Local_Driver_List:
                if driver.get('Available') == 'True':
                    driver_locations.append(driver.get('Location'))
                    max_passengers.append(int(driver.get('Max_Passenger')))
                    driver_names.append(driver.get('Name'))
            
            if not driver_locations:
                self.error_label.config(text="No available drivers at the moment")
                self.draw_map(pickup_location, destination_location)
                return
            
            # Find the best driver
            best_driver_idx, pickup_dist, dest_dist, total_dist, pickup_path, dest_path, score = find_best_driver(
                driver_locations, max_passengers, pickup_location, destination_location, amount_passenger)
            
            if best_driver_idx is None:
                self.error_label.config(text="No suitable driver found for this route")
                self.draw_map(pickup_location, destination_location)
                return
            
            # Format distances to 2 decimal places
            pickup_dist_formatted = round(pickup_dist, 2)
            dest_dist_formatted = round(dest_dist, 2)
            total_dist_formatted = round(total_dist, 2)
                        
            # Update driver work minutes USING ACCURATE TIME CALCULATIONS
            selected_driver_name = driver_names[best_driver_idx]
            selected_driver_location = driver_locations[best_driver_idx]
            
            # Get time parameters from efficiency analysis
            avg_speed_kph = 40
            traffic_factor = 1.2
            pickup_loading_time = 3
            dropoff_unloading_time = 2
            
            # Calculate actual time spent (using same logic as efficiency analysis)
            pickup_time = (pickup_dist / (avg_speed_kph/60)) * traffic_factor
            dest_time = (dest_dist / (avg_speed_kph/60)) * traffic_factor
            total_trip_time = pickup_time + dest_time + pickup_loading_time + dropoff_unloading_time
            
            for driver in Local_Driver_List:
                if driver.get('Name') == selected_driver_name:
                    current_work = int(driver.get('Work_Minutes', 0))
                    # Use calculated time instead of distance units
                    new_work_minutes = current_work + total_trip_time
                    driver['Work_Minutes'] = str(int(new_work_minutes))
                    
                    # Update location and availability
                    driver['Location'] = destination_location
                    if new_work_minutes > 480:
                        driver['Available'] = 'False'
            
            # Update the CSV file with the new driver information
            self.update_driver_csv()
            
            # Display result
            result_text = f"Driver {selected_driver_name} assigned!\n"
            result_text += f"Distance to pickup: {pickup_dist_formatted} km\n"
            result_text += f"Distance to destination: {dest_dist_formatted} km\n"
            result_text += f"Total trip distance: {total_dist_formatted} km"
            
            self.result_label.config(text=result_text)
            
            # Refresh driver information
            self.load_driver_info()
            
            # Update map with the selected routes
            self.draw_map(
                pickup_location=pickup_location,
                destination_location=destination_location,
                selected_driver_location=selected_driver_location,
                driver_locations=driver_locations,
                pickup_path=pickup_path,
                destination_path=dest_path
            )
        except Exception as e:
            self.error_label.config(text=f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_driver_csv(self):
        """Update the CSV file with the current driver information"""
        with open(Driver_List, mode='w', newline='') as file:
            fieldnames = ['Name', 'Max_Passenger', 'Location', 'Available', 'Work_Minutes']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for driver in Local_Driver_List:
                writer.writerow(driver)
    

    #Just Added
    def show_driver_efficiency_analysis(self):
        """Display a window showing efficiency calculations for all available drivers"""
        # Create a new toplevel window
        efficiency_window = tk.Toplevel(self.root)
        efficiency_window.title("Driver Efficiency Analysis")
        efficiency_window.geometry("900x600")
        
        # Create main frame with scrollable area
        main_frame = ttk.Frame(efficiency_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        ttk.Label(main_frame, text="DRIVER EFFICIENCY ANALYSIS", font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Create a canvas with scrollbar for the content
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Get current trip parameters
        pickup_location = self.pickup_entry.get().strip().upper()
        destination_location = self.destination_entry.get().strip().upper()
        passenger_input = self.passenger_entry.get().strip()
        
        # Validate inputs
        if not pickup_location or not destination_location or not passenger_input:
            ttk.Label(scrollable_frame, text="Please fill in all fields first", 
                    font=("Arial", 12), foreground="red").pack(pady=10)
            return
        
        try:
            passenger_count = int(passenger_input)
        except ValueError:
            ttk.Label(scrollable_frame, text="Invalid passenger number", 
                    font=("Arial", 12), foreground="red").pack(pady=10)
            return
        
        if pickup_location not in Local_Map or destination_location not in Local_Map:
            ttk.Label(scrollable_frame, text="Invalid pickup or destination location", 
                    font=("Arial", 12), foreground="red").pack(pady=10)
            return
        
        # Get available drivers
        available_drivers = []
        for driver in Local_Driver_List:
            if driver.get('Available') == 'True' and int(driver.get('Max_Passenger')) >= passenger_count:
                available_drivers.append(driver)
        
        if not available_drivers:
            ttk.Label(scrollable_frame, text="No available drivers with sufficient capacity", 
                    font=("Arial", 12), foreground="red").pack(pady=10)
            return
        
        # Trip parameters section
        trip_frame = ttk.LabelFrame(scrollable_frame, text="Trip Parameters", padding=10)
        trip_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(trip_frame, text=f"Pickup Location: {pickup_location}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(trip_frame, text=f"Destination: {destination_location}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(trip_frame, text=f"Passenger Count: {passenger_count}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Add time assumptions section
        assumptions_frame = ttk.LabelFrame(scrollable_frame, text="Time Calculation Assumptions", padding=10)
        assumptions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(assumptions_frame, text="• Average Speed: 40 km/h", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(assumptions_frame, text="• Pickup Time (loading): 3 minutes", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(assumptions_frame, text="• Dropoff Time (unloading): 2 minutes", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(assumptions_frame, text="• Traffic Factor: 1.2x (20% buffer for traffic conditions)", font=("Arial", 9)).pack(anchor=tk.W)
        
        # Calculate efficiency for each driver
        driver_results = []
        
        for driver in available_drivers:
            driver_name = driver.get('Name')
            driver_loc = driver.get('Location')
            max_passengers = int(driver.get('Max_Passenger'))
            
            # Calculate distances
            pickup_dist, dest_dist, total_dist, pickup_path, dest_path = calculate_trip_distance(
                Local_Map, driver_loc, pickup_location, destination_location)
            
            # Skip if route is impossible
            if pickup_dist == float('inf') or dest_dist == float('inf'):
                continue
            
            # Calculate efficiency score
            efficiency_score = worth_calculation(pickup_dist, total_dist, max_passengers, passenger_count)
            
            # Show negative to match original function output
            displayed_score = -efficiency_score
            
            # Calculate travel times (in minutes)
            # Assuming average speed of 40km/h = 0.67km/min
            avg_speed_kph = 40
            avg_speed_kpm = avg_speed_kph / 60  # kilometers per minute
            
            # Travel times in minutes with traffic factor
            traffic_factor = 1.2  # Add 20% for traffic
            pickup_time = (pickup_dist / avg_speed_kpm) * traffic_factor
            destination_time = (dest_dist / avg_speed_kpm) * traffic_factor
            
            # Add loading/unloading times
            pickup_loading_time = 3  # minutes
            dropoff_unloading_time = 2  # minutes
            
            # Total times
            total_pickup_time = pickup_time  # Time to reach customer
            total_destination_time = destination_time + pickup_loading_time  # Time from pickup to dropoff, including loading
            total_trip_time = pickup_time + destination_time + pickup_loading_time + dropoff_unloading_time
            
            # Add to results
            driver_results.append({
                'name': driver_name,
                'location': driver_loc,
                'max_passengers': max_passengers,
                'pickup_dist': pickup_dist,
                'dest_dist': dest_dist,
                'total_dist': total_dist,
                'efficiency_score': displayed_score,
                'pickup_path': pickup_path,
                'dest_path': dest_path,
                'pickup_time': pickup_time,
                'destination_time': destination_time,
                'total_pickup_time': total_pickup_time,
                'total_destination_time': total_destination_time,
                'total_trip_time': total_trip_time
            })
        
        # Sort by efficiency score (lower is better since we're displaying negative)
        driver_results.sort(key=lambda x: x['efficiency_score'])
        
        # Display results for each driver
        for i, result in enumerate(driver_results):
            is_best = (i == 0)
            
            # Create frame for each driver
            driver_frame = ttk.LabelFrame(
                scrollable_frame, 
                text=f"{result['name']} {'(MOST EFFICIENT)' if is_best else ''}", 
                padding=10)
            driver_frame.pack(fill=tk.X, padx=5, pady=10)
            
            # Use different background color for the best driver
            if is_best:
                driver_frame.configure(style="Best.TLabelframe")
            
            # Driver basic info
            info_frame = ttk.Frame(driver_frame)
            info_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(info_frame, text=f"Current Location: {result['location']}", 
                    font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
            ttk.Label(info_frame, text=f"Max Passengers: {result['max_passengers']}", 
                    font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
            
            # Distance calculations
            dist_frame = ttk.Frame(driver_frame)
            dist_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(dist_frame, text=f"Distance to Pickup: {result['pickup_dist']:.2f} km", 
                    font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
            ttk.Label(dist_frame, text=f"Distance to Destination: {result['dest_dist']:.2f} km", 
                    font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
            ttk.Label(dist_frame, text=f"Total Trip Distance: {result['total_dist']:.2f} km", 
                    font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
            
            # Time calculations - NEW SECTION
            time_frame = ttk.LabelFrame(driver_frame, text="Estimated Travel Times", padding=5)
            time_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Format minutes and seconds
            def format_time(minutes):
                hours = int(minutes // 60)
                mins = int(minutes % 60)
                secs = int((minutes * 60) % 60)
                
                if hours > 0:
                    return f"{hours}h {mins}m {secs}s"
                else:
                    return f"{mins}m {secs}s"
            
            # Time to reach customer
            ttk.Label(time_frame, text=f"Time to Reach Customer: {format_time(result['pickup_time'])}", 
                    font=("Arial", 9)).pack(anchor=tk.W)
            
            # Time from pickup to destination (including loading)
            ttk.Label(time_frame, text=f"Trip Time (after pickup): {format_time(result['total_destination_time'])}", 
                    font=("Arial", 9)).pack(anchor=tk.W)
            
            # Total trip time
            ttk.Label(time_frame, text=f"Total Trip Time: {format_time(result['total_trip_time'])}", 
                    font=("Arial", 9, "bold")).pack(anchor=tk.W)
            
            # Customer wait and ETA
            ttk.Label(time_frame, text=f"Customer Pickup ETA: {format_time(result['total_pickup_time'])}", 
                    font=("Arial", 9, "bold"), foreground="#1565C0").pack(anchor=tk.W)
            
            # Customer destination ETA
            ttk.Label(time_frame, text=f"Customer Destination ETA: {format_time(result['total_trip_time'])}", 
                    font=("Arial", 9, "bold"), foreground="#1565C0").pack(anchor=tk.W)
            
            # Calculation breakdown
            calc_frame = ttk.LabelFrame(driver_frame, text="Efficiency Calculation Breakdown", padding=5)
            calc_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Show the calculation breakdown based on worth_calculation function
            pickup_score = result['pickup_dist'] * 3
            trip_score = result['total_dist']
            
            capacity_utilization = passenger_count / result['max_passengers']
            if capacity_utilization < 0.5:
                capacity_score = (result['max_passengers'] - passenger_count) * 5
            else:
                capacity_score = 0
            
            ttk.Label(calc_frame, text=f"Pickup Distance Score = {result['pickup_dist']:.2f} × 3 = {pickup_score:.2f}", 
                    font=("Arial", 9)).pack(anchor=tk.W)
            ttk.Label(calc_frame, text=f"Trip Distance Score = {result['total_dist']:.2f}", 
                    font=("Arial", 9)).pack(anchor=tk.W)
            
            capacity_text = f"Capacity Utilization = {passenger_count} / {result['max_passengers']} = {capacity_utilization:.2f}"
            if capacity_utilization < 0.5:
                capacity_text += f" → Penalty: ({result['max_passengers']} - {passenger_count}) × 5 = {capacity_score:.2f}"
            else:
                capacity_text += " → No penalty (good utilization)"
            ttk.Label(calc_frame, text=capacity_text, font=("Arial", 9)).pack(anchor=tk.W)
            
            ttk.Label(calc_frame, text=f"Total Score = {pickup_score:.2f} + {trip_score:.2f} + {capacity_score:.2f} = {result['efficiency_score']:.2f}", 
                    font=("Arial", 9, "bold")).pack(anchor=tk.W)
            
            # Button to view this driver's route on map
            def create_view_route_command(r):
                return lambda: self.view_efficiency_route(r['location'], pickup_location, destination_location, 
                                                        r['pickup_path'], r['dest_path'])
            
            ttk.Button(driver_frame, text="View Route on Map", 
                    command=create_view_route_command(result)).pack(anchor=tk.E, pady=5)
        
        # Add buttons at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Select best driver button
        def select_best_driver():
            if driver_results:
                best_driver_name = driver_results[0]['name']
                # Find the driver in the treeview and highlight it
                for item_id in self.driver_tree.get_children():
                    item_values = self.driver_tree.item(item_id, 'values')
                    if item_values[0] == best_driver_name:
                        self.driver_tree.selection_set(item_id)
                        self.driver_tree.see(item_id)
                # Fill in the form with current values
                self.find_driver()
                efficiency_window.destroy()
        
        ttk.Button(button_frame, text="Select Most Efficient Driver", 
                command=select_best_driver).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Close", 
                command=efficiency_window.destroy).pack(side=tk.RIGHT, padx=5)

    def view_efficiency_route(self, driver_location, pickup_location, destination_location, pickup_path, dest_path):
        """View the selected driver's route on the map"""
        self.draw_map(
            pickup_location=pickup_location,
            destination_location=destination_location,
            selected_driver_location=driver_location,
            pickup_path=pickup_path,
            destination_path=dest_path
        )
    

# Report generating functionality
class ReportGenerator:
    def __init__(self, driver_list):
        self.driver_list = driver_list
        
    def generate_driver_statistics(self):
        """Generate statistics for all drivers"""
        total_drivers = len(self.driver_list)
        available_drivers = sum(1 for driver in self.driver_list if driver.get('Available') == 'True')
        unavailable_drivers = total_drivers - available_drivers
        
        total_work_minutes = sum(int(driver.get('Work_Minutes', 0)) for driver in self.driver_list)
        avg_work_minutes = total_work_minutes / total_drivers if total_drivers > 0 else 0
        
        # Find driver with most work minutes
        most_work_driver = max(self.driver_list, key=lambda x: int(x.get('Work_Minutes', 0)))
        
        # Calculate utilization percentage
        utilization = (avg_work_minutes / 480) * 100  # 480 minutes = 8 hours
        
        report = {
            'total_drivers': total_drivers,
            'available_drivers': available_drivers,
            'unavailable_drivers': unavailable_drivers,
            'total_work_minutes': total_work_minutes,
            'avg_work_minutes': avg_work_minutes,
            'most_work_driver': most_work_driver.get('Name'),
            'most_work_minutes': most_work_driver.get('Work_Minutes'),
            'utilization_percentage': utilization
        }
        
        return report
    
    def display_report(self, parent_window):
        """Display a report window with driver statistics"""
        report = self.generate_driver_statistics()
        
        report_window = tk.Toplevel(parent_window)
        report_window.title("Driver Statistics Report")
        report_window.geometry("600x500")
        
        frame = ttk.Frame(report_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(frame, text="DRIVER STATISTICS REPORT", font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Statistics display
        stats_frame = ttk.Frame(frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Format the statistics
        ttk.Label(stats_frame, text=f"Total Drivers: {report['total_drivers']}", font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        ttk.Label(stats_frame, text=f"Available Drivers: {report['available_drivers']}", font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        ttk.Label(stats_frame, text=f"Unavailable Drivers: {report['unavailable_drivers']}", font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        ttk.Label(stats_frame, text=f"Total Work Minutes: {report['total_work_minutes']}", font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        ttk.Label(stats_frame, text=f"Average Work Minutes: {report['avg_work_minutes']:.2f}", font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        ttk.Label(stats_frame, text=f"Most Active Driver: {report['most_work_driver']} ({report['most_work_minutes']} minutes)", 
                font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        ttk.Label(stats_frame, text=f"Fleet Utilization: {report['utilization_percentage']:.2f}%", 
                font=("Arial", 12)).pack(anchor=tk.W, pady=3)
        
        # Create a visual representation of driver availability
        fig = plt.Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Pie chart for driver availability
        labels = ['Available', 'Unavailable']
        sizes = [report['available_drivers'], report['unavailable_drivers']]
        colors = ['#66bb6a', '#ef5350']
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        ax.set_title("Driver Availability")
        
        # Add the chart to the window
        chart_canvas = FigureCanvasTkAgg(fig, master=frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Close button
        ttk.Button(frame, text="Close Report", command=report_window.destroy).pack(pady=10)

class ResetDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Reset System")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        center_x = parent.winfo_rootx() + parent.winfo_width() // 2 - 200
        center_y = parent.winfo_rooty() + parent.winfo_height() // 2 - 100
        self.dialog.geometry(f"+{center_x}+{center_y}")
        
        # Dialog content
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Reset Driver Locations and Work Minutes?", 
                font=("Arial", 12, "bold")).pack(pady=(0, 20))
        
        ttk.Label(frame, text="This will reset all drivers to their original locations,\n"
                           "set all drivers as available, and clear work minutes.",
                font=("Arial", 10)).pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Reset", style="Accent.TButton", 
                 command=self.confirm).pack(side=tk.RIGHT, padx=10)
        
        # Set special style for the reset button
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white", background="#f44336", font=("Arial", 10, "bold"))
        
        # Wait for the dialog to be closed
        parent.wait_window(self.dialog)
        
    def confirm(self):
        self.result = True
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()

def reset_system():
    """Reset all drivers to their original state"""
    # Create backup of the current file
    import shutil
    import time
    
    backup_filename = f"Driver_List_backup_{int(time.time())}.csv"
    backup_path = os.path.join(This_File_Path, backup_filename)
    shutil.copy2(Driver_List, backup_path)
    
    # Reset driver data
    with open(Driver_List, mode='r') as file:
        reader = csv.DictReader(file)
        drivers = list(reader)
    
    for driver in drivers:
        # Reset work minutes to 0
        driver['Work_Minutes'] = '0'
        # Set all drivers as available
        driver['Available'] = 'True'
        # Reset locations (in a real system, you'd have original locations stored somewhere)
        # Here we'll use a simplistic approach
        import random
        all_locations = list(Local_Map.keys())
        driver['Location'] = random.choice(all_locations)
    
    # Write the updated data back to the CSV
    with open(Driver_List, mode='w', newline='') as file:
        fieldnames = ['Name', 'Max_Passenger', 'Location', 'Available', 'Work_Minutes']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for driver in drivers:
            writer.writerow(driver)
    
    # Update the global driver list
    global Local_Driver_List
    Local_Driver_List = drivers
    
    return True

def main():
    root = tk.Tk()
    app = TaxiAppGUI(root)
    
    # Add a menu bar
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    
    # File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Refresh Driver Data", command=app.refresh_driver_info)
    file_menu.add_command(label="View Available Locations", command=app.show_available_locations)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    # Tools menu
    tools_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Tools", menu=tools_menu)
    
    # Add report generation to the menu
    def show_report():
        report_gen = ReportGenerator(Local_Driver_List)
        report_gen.display_report(root)
    
    tools_menu.add_command(label="Generate Driver Statistics Report", command=show_report)
    tools_menu.add_command(label="Analyze Driver Efficiency", command=app.show_driver_efficiency_analysis)
    
    # System reset option
    def confirm_reset():
        dialog = ResetDialog(root)
        if dialog.result:
            if reset_system():
                app.refresh_driver_info()
                app.draw_map()  # Redraw map with reset data
                messagebox.showinfo("Reset Complete", "All drivers have been reset to their original state.")
    
    tools_menu.add_separator()
    tools_menu.add_command(label="Reset System", command=confirm_reset)
    
    # Help menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Help", menu=help_menu)
    
    def show_about():
        about_window = tk.Toplevel(root)
        about_window.title("About Taxi Booking System")
        about_window.geometry("400x300")
        
        about_frame = ttk.Frame(about_window, padding="20")
        about_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(about_frame, text="Taxi Booking System", 
                font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        ttk.Label(about_frame, text="Version 1.0", 
                font=("Arial", 10)).pack(pady=(0, 20))
        
        ttk.Label(about_frame, text="A Dijkstra's algorithm-based taxi dispatch system\n"
                               "that efficiently matches drivers to passengers.",
                font=("Arial", 10)).pack(pady=(0, 20))
        
        ttk.Label(about_frame, text="© 2025 Taxi Booking Systems Inc.",
                font=("Arial", 8)).pack(side=tk.BOTTOM, pady=10)
        
        ttk.Button(about_frame, text="Close", command=about_window.destroy).pack(pady=10)
    
    help_menu.add_command(label="About", command=show_about)
    help_menu.add_command(label="How to Use", command=lambda: messagebox.showinfo(
        "How to Use", 
        "1. Enter pickup location, destination, and passenger count\n"
        "2. Click 'Find Driver' to match with the best available driver\n"
        "3. Use 'Show Locations' to see all available map locations\n"
        "4. View driver information in the top panel\n"
        "5. Use the map to visualize routes and driver locations"
    ))
    
    root.mainloop()

if __name__ == "__main__":
    main()

# list of drivers available on the taxi booking system - Done 
# list of drivers not available on the taxi booking system - Done 
# add backtracking algorithm
# increase text size
# show which one is most efficeint - Done 
# make a table that includes condition (conditional table), for comparisons to find which driver is the best (performance comparison 3)
# add the time travel as well - Done
# add map randomization - DONE
