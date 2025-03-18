import time
import os
import csv

#Cari alamat file
This_File_Path = os.path.dirname(os.path.abspath(__file__))
List_org = os.path.join(This_File_Path, 'List-org.csv')

#Jadikan sebagai list sementara
Local_List_org = []
with open(List_org, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        Local_List_org.append(row)

#Timer
TimeRN = time.time()

##################################################

def Binary_Search(Array, Target):
    Left = 0
    Right = len(Array) - 1
    
    #LowTierInput
    if Left > Right:
        return -1
    
    #Loop
    while True:
        Middle = (Left + Right) // 2
        if Array[Middle]["Name"] == Target:
            return Middle
        elif Array[Middle]["Name"] < Target:
            Left = Middle + 1
        elif Array[Middle]["Name"] > Target:
            Right = Middle - 1
        else:
            return -1
        
def Linear_Search(Array, Target):
    Index = 0
    for Row in Array:
        if Row["Name"] == Target:
            return Index
        else:
            Index += 1
    return -1

def Asking(Search):
    Name = str(input("Nama : "))
    
    #Process
    Index_Name = -1
    while Index_Name == -1:
        TimeStart = TimeRN
        if Search == 1:
            Index_Name = Binary_Search(Local_List_org, Name)
        if Search == 2:
            Index_Name = Linear_Search(Local_List_org, Name)
        TimeEnd = TimeRN
        Duration = TimeEnd - TimeStart
    print(f"Duration = {Duration} Second")
    #
    
    Key = ''
    while Key == Local_List_org[Index_Name]["Key"]:
        Key = str(input("Key : "))
    
    Insert_Status = str(input("Status : "))
    Local_List_org[Index_Name]["Status"] = Insert_Status
    return

def Type_Search():
    print("Wdyawant?\n1. Binary Search (O(nlogn))\n2. Linear Search (O(n))")
    Answer = int(input("(1/2) : "))
    if Answer != 1 and Answer != 2:
        return -1
    Asking(Answer)
    return

##################################################

#Main - Starter and ender/writer
Type_Search()
with open(List_org, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=Local_List_org[0].keys())
    writer.writeheader()
    writer.writerows(Local_List_org)
