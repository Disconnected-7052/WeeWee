import time

def Backtrack(Destinations, Budget, MaxDest, Path=[], Start=0, Results=[]):
    if sum(Cost for _, Cost in Path) <= Budget and 1 <= len(Path) <= MaxDest:
        Results.append(Path.copy())
    
    for i in range(Start, len(Destinations)):
        Cost = Destinations[i][1]
        if sum(Cost for _, Cost in Path) + Cost > Budget:
            continue
        Path.append(Destinations[i])
        Backtrack(Destinations, Budget, MaxDest, Path, i+1, Results)
        Path.pop()
    
    return Results

# Data Destinations in IDR
DestData = [
    {"Name": "Indonesia", "Transport": 50000, "Motel": 150000, "Snack": 20000, 
     "HiddenGem": "Gili Kondo (Lombok)", "Total": 220000},
    
    {"Name": "Tuvalu", "Transport": 350000, "Motel": 200000, "Snack": 50000, 
     "HiddenGem": "Pulau Nanumea", "Total": 600000},
     
    {"Name": "Nauru", "Transport": 400000, "Motel": 180000, "Snack": 40000, 
     "HiddenGem": "Danau Anabar", "Total": 620000},
     
    {"Name": "Komoro", "Transport": 450000, "Motel": 170000, "Snack": 30000, 
     "HiddenGem": "Gunung Karthala", "Total": 650000}
]

# Format Data for Algorithm
Destinations = [
    (f"{D['Name']} | Transport: {D['Transport']:,} | Penginapan: {D['Motel']:,} | Jajanan: {D['Snack']:,} | Hidden Gem: {D['HiddenGem']}", 
     D['Total']) for D in DestData
]

# Measure Execution Time
StartTime = time.time()

# Run Algorithm
Results = Backtrack(Destinations, 500000, 3)

# Calculate Duration
Duration = time.time() - StartTime

# Display Results
print("Rencana Liburan dengan Backtracking (≤500.000 IDR):")
for i, Plan in enumerate(Results, 1):
    Total = sum(Cost for _, Cost in Plan)
    Details = "\n".join([f"  ⦁ {Item[0]}" for Item in Plan])
    print(f"{i}. Paket {len(Plan)} Destinasi (Total: Rp{Total:,}):\n{Details}\n")

# Print Execution Time
print(f"Execution Time: {Duration:.4f} seconds")