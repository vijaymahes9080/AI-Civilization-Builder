import numpy as np
from typing import Dict, Any

class SpatialMap:
    """
    Handles procedural grid-based terrain generation, resource node deposits, 
    climate, and weather simulation for the civilization world.
    """
    def __init__(self, width: int, height: int, seed: int):
        self.width = width
        self.height = height
        self.seed = seed
        
        # Initialize numpy random generator
        self.rng = np.random.default_rng(seed)
        
        # Terrain type codes: 0=Water, 1=Plain, 2=Forest, 3=Mountain, 4=Desert
        self.terrain = np.zeros((width, height), dtype=int)
        
        # Resource density matrices
        self.food_nodes = np.zeros((width, height))
        self.wood_nodes = np.zeros((width, height))
        self.stone_nodes = np.zeros((width, height))
        self.iron_nodes = np.zeros((width, height))
        
        # Climate / Weather state
        self.temperature = np.full((width, height), 20.0) # Celsius
        self.humidity = np.full((width, height), 0.5)      # 0 to 1
        self.weather = "Sunny"                             # Sunny, Rainy, Stormy, Snowing
        self.season_tick = 0
        self.seasons = ["Spring", "Summer", "Autumn", "Winter"]
        
        self._generate_terrain()

    def _generate_terrain(self):
        """Generates procedural terrain layout using simple sine-wave patterns and noise clusters"""
        for x in range(self.width):
            for y in range(self.height):
                # Pseudo-noise using trig functions based on coordinates + seed
                val = (np.sin(x * 0.15 + self.seed) + np.cos(y * 0.15 + self.seed)) / 2.0
                val += self.rng.uniform(-0.1, 0.1)
                
                # Classify terrain
                if val < -0.3:
                    self.terrain[x, y] = 0  # Water
                    self.humidity[x, y] = 0.9
                elif val < 0.1:
                    self.terrain[x, y] = 1  # Plain
                    self.humidity[x, y] = 0.5
                    self.food_nodes[x, y] = self.rng.choice([0.0, 1.0, 2.0], p=[0.7, 0.2, 0.1])
                elif val < 0.4:
                    self.terrain[x, y] = 2  # Forest
                    self.humidity[x, y] = 0.7
                    self.wood_nodes[x, y] = self.rng.choice([1.0, 3.0, 5.0], p=[0.2, 0.5, 0.3])
                    self.food_nodes[x, y] = self.rng.choice([0.0, 1.0], p=[0.6, 0.4])
                elif val < 0.6:
                    self.terrain[x, y] = 3  # Mountain
                    self.humidity[x, y] = 0.2
                    self.stone_nodes[x, y] = self.rng.choice([2.0, 5.0, 8.0], p=[0.3, 0.5, 0.2])
                    self.iron_nodes[x, y] = self.rng.choice([0.0, 1.0, 3.0], p=[0.8, 0.15, 0.05])
                else:
                    self.terrain[x, y] = 4  # Desert
                    self.humidity[x, y] = 0.05
                    self.temperature[x, y] = 38.0

    def tick_weather(self):
        """Progress weather patterns, temperature seasonal drifts, and natural disasters"""
        self.season_tick += 1
        current_season = self.seasons[(self.season_tick // 100) % 4]
        
        # Modify temperatures based on season
        base_temp = 20.0
        if current_season == "Summer":
            base_temp = 32.0
        elif current_season == "Winter":
            base_temp = 2.0
            
        self.temperature = np.full((self.width, self.height), base_temp) + self.rng.uniform(-3, 3, (self.width, self.height))
        
        # Dynamically change global weather state
        weather_roll = self.rng.random()
        if weather_roll < 0.7:
            self.weather = "Sunny"
        elif weather_roll < 0.9:
            self.weather = "Rainy" if current_season != "Winter" else "Snowing"
        else:
            self.weather = "Stormy"

    def get_cell_data(self, x: int, y: int) -> Dict[str, Any]:
        """Retrieve full state descriptor of a specific map tile"""
        return {
            "x": x,
            "y": y,
            "terrain": int(self.terrain[x, y]),
            "food": float(self.food_nodes[x, y]),
            "wood": float(self.wood_nodes[x, y]),
            "stone": float(self.stone_nodes[x, y]),
            "iron": float(self.iron_nodes[x, y]),
            "temperature": float(self.temperature[x, y]),
            "humidity": float(self.humidity[x, y])
        }
