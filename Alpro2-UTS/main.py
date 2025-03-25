import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json

# "This File" Finder Cuz Windows Fucking Suck
This_File_Path = os.path.dirname(os.path.abspath(__file__))
Driver_List = os.path.join(This_File_Path, 'Driver_List.csv')
Map = os.path.join(This_File_Path, 'Map.json')

# Extract csf file
Local_Driver_List = []
with open(Driver_List, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        Local_Driver_List.append(row)
# Extract Map (json)
with open(Map, mode='r') as file:
    Local_Map = json.load(file)

# Tujuan Utama :
# 1. Memadankan Setiap Pesanan dengan Driver yang paling sesuai
# 2. Meminimalkan jarak tempuh driver ke lokasi penumpang
# 3. Menghindari konflik (1 pesanan per time)
# Note : Input e ([Ditance_Driver1,Distance_Driver2,...],[Max_Passenger_Driver1,...],Amount_Passenger)
def Driver_Matching(Distance,Max_Passenger,Amount_Passenger):
    Shortest_Distance = None
    Index_Result = None
    Priority = None
    for Index in range(len(Distance)):
        Worth = Worth_Value(Distance[Index], Priority, Max_Passenger[Index], Amount_Passenger)
        if Amount_Passenger > Max_Passenger[Index]:
            continue
        if Shortest_Distance == None:
            Shortest_Distance = Distance[Index]
            Index_Result = Index
            Priority = Worth
            continue
        if Distance[Index] < Shortest_Distance and Worth > Priority:
            Shortest_Distance = Distance[Index]
            Index_Result = Index
            Priority = Worth
    return Index_Result

def Worth_Value(Distance, Priority, Max_Passenger, Amount_Passenger):
    Priority = (Distance // 10)*-1
    Priority += (Max_Passenger - Amount_Passenger)*-1
    return Priority

# Distance check
def Distance_Check(Location, Driver_Location):
    Distance = []
    for Point in Driver_Location:
        Distance.append(dijkstra(Local_Map, Location, Point))
    return Distance

# idfk how to make map and path finding algorithm
# Shit i got from AI
import heapq
def dijkstra(graph, start, end):
    queue = [(0, start)]
    visited = {}
    while queue:
        (cost, node) = heapq.heappop(queue)
        if node in visited:
            continue
        visited[node] = cost
        if node == end:
            return cost
        for neighbor, weight in graph[node].items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor))
    return float('inf')

# Main
def Main():
    Current_Location = input('Where are you right now : ').upper()
    if Current_Location not in Local_Map:
        return -1
    Amount_Passenger = int(input('How many passenger : '))
    
    # Additional Error Fixer - Making sure Driver cant work more than 8 hours (480 mnt)
    for Row in Local_Driver_List:
        for Work_Duration in Row['Work_Minutes']:
            if int(Work_Duration) > 480:
                Row['Available'] = 'False'
        
    # Availability Check
    Name_Driver = []
    Max_Passenger_Driver = []
    Location_Driver = []
    for Row in Local_Driver_List:
        if Row['Available'] == 'False':
            continue
        Name_Driver.append(Row['Name'])
        Max_Passenger_Driver.append(int(Row['Max_Passenger']))
        Location_Driver.append(Row['Location'])
    
    # The rest
    try:
        Driver_Customer_Distance = Distance_Check(Current_Location, Location_Driver)
        Your_Driver_Index = Driver_Matching(Driver_Customer_Distance,Max_Passenger_Driver,Amount_Passenger)
    except:
        print('No Available Driver, try again later')
    print(f"Your Driver will be {Name_Driver[Your_Driver_Index]}")
    return 0

while True:
    Key = Main()
    if Key == -1:
        print("Unreached Location, Try again.")
        continue
    if Key == 0:
        break
