import json
import math
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class Signal_information(object):
    def __init__(self, path : list, signal_power : float):
        self._signal_power = signal_power
        self._noise_power = 0
        self._latency = 0
        self._path = path


    @property
    def signal_power(self):
        return self._signal_power
    @signal_power.setter
    def signal_power(self, x):
        self._signal_power = x

    def update_signal_power(self, inr : float):
        self._signal_power += inr

    @property
    def noise_power(self):
        return self._noise_power

    @noise_power.setter
    def noise_power(self):
        pass

    def update_noise_power(self, inr : float):
        self._noise_power += inr

    @property
    def latency(self):
        return self._latency

    @latency.setter
    def latency(self):
        pass

    def update_latency(self, inr : float):
        self._latency += inr

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, a,b):
        pass

    def update_path(self):
        if len(self._path) > 0:
            self._path.pop(0)
            print(self._path)
        else:
            print("No more nodes to croos")

class Node(object):
    def __init__(self, lab : str , pos : list, connection : list ):
        self._label = lab
        self._position = pos
        self._connected_nodes = connection

        # Successive will store connected Node objects
        self._successive = {}

    @property
    def label(self):
        return self._label

    @property
    def position(self):
        return self._position

    @property
    def connected_nodes(self):
        return self._connected_nodes

    @property
    def successive(self):
        return self._successive

    @successive.setter
    def successive(self, connected_node_dict):
        # Set successive nodes as a dictionary of connected nodes
        self._successive = connected_node_dict

    def propagate(self, signal_information):
        # Update the signal's path
        signal_information.update_path()

        # Check if there are nodes left in the path
        if len(signal_information.path) > 0:
            next_node_label = signal_information.path[0]

            # Check if the next node is in the successive nodes (dictionary)
            if next_node_label in self.successive:
                # Propagate the signal through the next connected node
                self.successive[next_node_label].propagate(signal_information)
            else:
                print(f"Next node '{next_node_label}' is not connected to node '{self.label}'")
        else:
            print("No more nodes to propagate to.")



class Line(object):
    def __init__(self, label: str, length: float):
        self._label = label
        self._length = length
        self._successive = {}

    @property
    def label(self):
        return self._label

    @property
    def length(self):
        return self._length

    @property
    def successive(self):
        return self._successive

    @successive.setter
    def successive(self):
        pass

    def latency_generation(self):
        speed_light = 3e8
        latency = self.length * 1000 / (2/3 * speed_light)
        return latency
    def noise_generation(self, signal_power):
        noise = 1e-9 * signal_power * self.length
        return noise

    def propagate(self):

        signal_information.update_noise_power(self.noise_generation(signal_information.signal_power))
        signal_information.update_latency(self.latency_generation())

        if len(signal_information.path) > 0:
            next_node_label = signal_information.path[0]
            if next_node_label in self.successive:
                self.successive[next_node_label].propagate(signal_infomation)
            else:
                print(f"Next node '{next_node_label}' is not connected to line '{self.label}'")
        else:
            print("No more nodes to propagate to.")

class Network:
    def __init__(self):
        self._nodes = {}
        self._lines = {}

        with open('resources/nodes.json', 'r') as file:
            data = json.load(file)
            labels = data.keys()
            for label in labels:
                info = data[label]
                self._nodes[label] = Node(label, info['position'], info['connected_nodes'])

        for node_label, node in self._nodes.items():
            for connected_node_label in node.connected_nodes:
                if connected_node_label in self._nodes:
                    self._create_line(node_label, connected_node_label)
                    self._create_line(connected_node_label, node_label)

    def _create_line(self, node1_label: str, node2_label: str):
        node1 = self._nodes[node1_label]
        node2 = self._nodes[node2_label]
        x1, y1 = node1.position
        x2, y2 = node2.position
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        line_label = node1_label + node2_label
        self._lines[line_label] = Line(line_label, length)

    @property
    def nodes(self):
        return self._nodes

    @property
    def lines(self):
        return self._lines

    def draw(self):
        pass  # Optionally, add visualization code here

    def find_paths(self, label1, label2):
        def find_paths_recursive(current_label, end_label, path, visited):
            visited.add(current_label)
            path.append(current_label)
            if current_label == end_label:
                paths.append(path.copy())
            else:
                for neighbor_label in self.nodes[current_label].connected_nodes:
                    if neighbor_label not in visited:
                        find_paths_recursive(neighbor_label, end_label, path, visited)
            path.pop()
            visited.remove(current_label)

        paths = []
        find_paths_recursive(label1, label2, [], set())
        return paths

    def connect(self):
        # Set successive lines for each node
        for node_label, node in self.nodes.items():
            for connected_node_label in node.connected_nodes:
                line_label = node_label + connected_node_label
                if line_label in self.lines:
                    node.successive[connected_node_label] = self.lines[line_label]

        # Set successive nodes for each line
        for line_label, line in self.lines.items():
            node2_label = line_label[1]  # Destination node label
            if node2_label in self.nodes:
                line.successive[node2_label] = self.nodes[node2_label]

    def propagate(self, signal_information):
        # Start propagation from the initial node in the path
        start_node_label = signal_information.path[0]
        if start_node_label in self.nodes:
            self.nodes[start_node_label].propagate(signal_information)
        return signal_information

    def draw(self):
        plt.figure(figsize=(10, 8))

        # Plot each node
        for label, node in self.nodes.items():
            x, y = node.position
            plt.scatter(x, y, s=100, label=label)
            plt.text(x, y, label, ha='right', va='bottom', fontsize=12, color='blue')

        # Plot each line as a connection between nodes
        for line in self.lines.values():
            node1_label = line.label[0]
            node2_label = line.label[1]
            node1_pos = self.nodes[node1_label].position
            node2_pos = self.nodes[node2_label].position
            plt.plot([node1_pos[0], node2_pos[0]], [node1_pos[1], node2_pos[1]], 'k-', lw=1)

        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("Network Topology")
        plt.legend()
        plt.grid(True)
        plt.show()

    def generate_path_dataframe(self):
        # Initialize a DataFrame to store paths, latency, noise, and SNR
        df = pd.DataFrame(columns=["Path", "Total Latency (s)", "Total Noise Power (W)", "SNR (dB)"])

        # Loop through each pair of nodes
        for start_label in self.nodes:
            for end_label in self.nodes:
                if start_label != end_label:
                    # Find all paths between the start and end nodes
                    paths = self.find_paths(start_label, end_label)

                    for path in paths:
                        # Create a SignalInformation instance with 1 mW (0.001 W) signal power
                        signal_information = Signal_information(0.001, path.copy())

                        # Propagate signal information along the path
                        self.propagate(signal_information)

                        # Calculate SNR (in dB)
                        if signal_information.noise_power > 0:
                            snr_db = 10 * np.log10(signal_information.signal_power / signal_information.noise_power)
                        else:
                            snr_db = float('inf')  # Infinite SNR if noise is zero

                        # Create path string as "A->B->C"
                        path_string = "->".join(path)

                        # Append to DataFrame
                        df = df.append({
                            "Path": path_string,
                            "Total Latency (s)": signal_information.latency,
                            "Total Noise Power (W)": signal_information.noise_power,
                            "SNR (dB)": snr_db
                        }, ignore_index=True)

        return df



