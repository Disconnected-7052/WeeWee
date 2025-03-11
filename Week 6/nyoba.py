import csv
import os

# CSV file finder near this file
Path = os.path.dirname(os.path.abspath(__file__))
TheFile = os.path.join(Path, 'List.csv')
ThePrice = os.path.join(Path, 'Price.csv')
# End of CSF file finder

# CSV file Opener :P
Local_List = []
with open(TheFile, mode='r') as file:
    reader = csv.reader(file)
    for row in reader:
        Local_List.extend(row)
    
Local_Price = []
with open(ThePrice, mode='r') as file:
    reader = csv.reader(file)
    Local_Price = [row for row in reader]
# Ends here

def Listing():
    Final_List = []
    Sum_Price = 0
    for A in range(len(Local_List)):
        Item_Name = Local_List[A]
        Item_Price = Find_Price(Item_Name)
        Final_List.append([Item_Name, int(Item_Price)])
        Sum_Price += int(Item_Price)
    return Finilazing(Final_List, Sum_Price)

def Find_Price(Item_Name):
    Price = 0
    for A in range(len(Local_Price)):
        if Item_Name == Local_Price[A][0]:
            Price = Local_Price[A][1]
    return Price

def Finilazing(Final_List, Sum):
    Display_List = []
    for A in range(len(Final_List)):
        Key = False
        for B in range(len(Display_List)):
            if Final_List[A][0] == Display_List[B][0]:
                Display_List[B][1] += 1
                Display_List[B][2] += Final_List[A][1]
                Key = True
        if Key == False:
            Display_List.append([Final_List[A][0], 1, Final_List[A][1]])
    Print_This = ""
    for A in range(len(Display_List)):
        Text = str(Display_List[A][0]) + " * " + str(Display_List[A][1]) + " = " + str(Display_List[A][2]) + "\n"
        Print_This += Text
    Print_This += "Total Sum = " + str(Sum)
    return Print_This

A = Listing()
print(A)