import enum

class LocationPref(enum.Enum):
    NONE = 0
    Base_Any = 1
    Base_Main = 2
    Base_Frontier = 3
    Base_Center = 4
    
    Pylon_Any = 10
    Pylon_Ramp = 11
    Pylon_Mine = 12
    Pylon_Base_Main = 13
    Pylon_Frontier = 14
    Pylon_Center = 15
    def __repr__(self):
        return f"LocationPref.{self.name}"


for item in LocationPref:
    globals()[item.name] = item