import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# Para geocodificar direcciones (se puede usar un caché)
geolocator = Nominatim(user_agent="supplychain-optiflow")

class RoutingOptimizer:
    def __init__(self, locations, demands, vehicle_capacities, distance_matrix):
        self.locations = locations  # lista de tuplas (lat, lon)
        self.demands = demands
        self.vehicle_capacities = vehicle_capacities
        self.distance_matrix = distance_matrix
        self.num_vehicles = len(vehicle_capacities)
        self.depot = 0

    def solve(self):
        manager = pywrapcp.RoutingIndexManager(len(self.distance_matrix), 
                                               self.num_vehicles, self.depot)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Capacidad
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return self.demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            self.vehicle_capacities,
            True,
            'Capacity'
        )

        # Tiempo de viaje (si se tiene tiempo de servicio, se puede agregar)
        # Por simplicidad, usamos distancia como proxy de tiempo.

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            routes = []
            for vehicle_id in range(self.num_vehicles):
                index = routing.Start(vehicle_id)
                route = []
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    route.append(node)
                    index = solution.Value(routing.NextVar(index))
                route.append(manager.IndexToNode(index))
                routes.append(route)
            return routes
        else:
            return None

    @staticmethod
    def build_distance_matrix_from_addresses(addresses):
        """
        Construye matriz de distancias a partir de direcciones usando geopy.
        """
        coords = []
        for addr in addresses:
            try:
                location = geolocator.geocode(addr)
                if location:
                    coords.append((location.latitude, location.longitude))
                else:
                    coords.append((0, 0))
            except:
                coords.append((0, 0))
        n = len(coords)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = geodesic(coords[i], coords[j]).kilometers
        return matrix.tolist()