import json
import pickle

# USE VARS() to convert python class objects to dict


class SubItem:
    def __init__(self, itemName):
        self.itemName = itemName


class Item:
    def __init__(self, itemOne, itemTwo, arrayItems):
        self.itemOne = itemOne
        self.itemTwo = itemTwo
        self.arrayItems = arrayItems


subItem1 = SubItem("SubItem1")
subItem2 = SubItem("SubItem2")
subItem3 = SubItem("SubItem3")

item = Item(1, 2, [vars(subItem1), vars(subItem2), vars(subItem3)])

# # Pickle
# pickledObject = pickle.dumps(item.__dict__)
# print(f"pickled object: {pickledObject}")
# unpickledObject = pickle.loads(item)
# print(f"unpickled object: {unpickledObject}")

# JSON
jsonStringItem = json.dumps(vars(item))
print(f"json string: {jsonStringItem}")
jsonObject = json.loads(jsonStringItem)
print(f"json object: {jsonObject}")
print(f"json object array items: {jsonObject['arrayItems']}")
