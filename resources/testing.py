import math
import json
import matplotlib.pyplot as plt
import pandas as pd
from itertools import permutations
import random


class SignalInformation:
    def __init__(self, signal_power, path):
        self.signal_power = signal_power
        self.noise_power = 0.0
        self.latency = 0.0
        self.path = path

    def update_signal(self, increment):
        self.signal_power += increment

    def update_noise(self, increment):
        self.noise_power += increment

    def update_latency(self, increment):
        self.latency += increment

    def update_path(self):
        if self.path:
            self.path.pop(0)


class Node:
    def __init__(self, label, position, connected_nodes):
        self.label = label
        self.position = position
        self.connected_nodes = connected_nodes
        self.successive = {}

    def propagate(self, signal):
        if signal.path and signal.path[0] == self.label:
            signal.update_path()
            if signal.path:
                next_element = self.successive.get(signal.path[0])
                if next_element:
                    next_element.propagate(signal)


class Line:
    SPEED_OF_LIGHT = 3e8

    def __init__(self, label, length):
        self.label = label
        self.length = length
        self.successive = {}
        self.state = 1  # 1 means 'free', 0 means 'occupied'

    def latency_generation(self):
        return self.length / (2 / 3 * self.SPEED_OF_LIGHT)

    def noise_generation(self, signal_power):
        return 1e-9 * signal_power * self.length

    def propagate(self, signal):
        signal.update_latency(self.latency_generation())
        signal.update_noise(self.noise_generation(signal.signal_power))
        if signal.path:
            next_element = self.successive.get(signal.path[0])
            if next_element:
                next_element.propagate(signal)


class Network:
    def __init__(self, json_file):
        self.nodes = {}
        self.lines = {}
        self._load_network(json_file)

    def _load_network(self, json_file):
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Create Node instances
        for node_label, node_data in data.items():
            self.nodes[node_label] = Node(node_label, tuple(node_data['position']), node_data['connected_nodes'])

        # Create Line instances
        for node_label, node_data in data.items():
            for connected_label in node_data['connected_nodes']:
                line_label = f"{node_label}{connected_label}"
                length = math.dist(self.nodes[node_label].position, self.nodes[connected_label].position)
                self.lines[line_label] = Line(line_label, length)

    def connect(self):
        # Populate successive dictionaries
        for line in self.lines.values():
            node1, node2 = line.label[0], line.label[1]
            self.nodes[node1].successive[node2] = line
            line.successive[node2] = self.nodes[node2]

    def find_paths(self, start, end, visited=None, path=None):
        if visited is None:
            visited = set()
        if path is None:
            path = []

        visited.add(start)
        path.append(start)

        if start == end:
            yield list(path)
        else:
            for neighbor in self.nodes[start].connected_nodes:
                if neighbor not in visited:
                    yield from self.find_paths(neighbor, end, visited, path)

        path.pop()
        visited.remove(start)

    def propagate(self, signal):
        if signal.path:
            start_node = self.nodes.get(signal.path[0])
            if start_node:
                start_node.propagate(signal)

    def draw(self):
        plt.figure(figsize=(8, 8))
        for line in self.lines.values():
            node1, node2 = line.label[0], line.label[1]
            x1, y1 = self.nodes[node1].position
            x2, y2 = self.nodes[node2].position
            plt.plot([x1, x2], [y1, y2], 'b-')
        for node in self.nodes.values():
            x, y = node.position
            plt.plot(x, y, 'ro')
            plt.text(x, y, node.label, fontsize=12, ha='right')
        plt.show()

    def find_best_snr(self, input_node, output_node):
        paths = [path for path in self.find_paths(input_node, output_node) if self._is_path_free(path)]
        best_snr = -float('inf')
        best_path = None

        for path in paths:
            signal = SignalInformation(1e-3, path)
            self.propagate(signal)
            snr = 10 * math.log10(signal.signal_power / signal.noise_power) if signal.noise_power > 0 else float('inf')
            if snr > best_snr:
                best_snr = snr
                best_path = path

        return best_path

    def find_best_latency(self, input_node, output_node):
        paths = [path for path in self.find_paths(input_node, output_node) if self._is_path_free(path)]
        best_latency = float('inf')
        best_path = None

        for path in paths:
            signal = SignalInformation(1e-3, path)
            self.propagate(signal)
            if signal.latency < best_latency:
                best_latency = signal.latency
                best_path = path

        return best_path

    def _is_path_free(self, path):
        return all(self.lines[path[i] + path[i + 1]].state == 1 for i in range(len(path) - 1))

    def stream(self, connections, label="latency"):
        for connection in connections:
            if label == "latency":
                best_path = self.find_best_latency(connection.input, connection.output)
            else:
                best_path = self.find_best_snr(connection.input, connection.output)

            if best_path:
                signal = SignalInformation(connection.signal_power, best_path)
                self.propagate(signal)
                connection.latency = signal.latency
                connection.snr = 10 * math.log10(
                    signal.signal_power / signal.noise_power) if signal.noise_power > 0 else float('inf')
                for i in range(len(best_path) - 1):
                    self.lines[best_path[i] + best_path[i + 1]].state = 0  # Set path to 'occupied'
            else:
                connection.latency = None
                connection.snr = 0

    def run_simulation(self, num_connections=100, label="latency"):
        connections = [
            Connection(random.choice(list(self.nodes.keys())), random.choice(list(self.nodes.keys())), 1e-3)
            for _ in range(num_connections)
        ]
        self.stream(connections, label=label)
        latencies = [conn.latency for conn in connections if conn.latency is not None]
        snrs = [conn.snr for conn in connections if conn.snr > 0]

        if label == "latency":
            plt.hist(latencies, bins=20, color='blue', alpha=0.7, label='Latency (s)')
            plt.xlabel("Latency (s)")
            plt.ylabel("Frequency")
            plt.title("Latency Distribution")
        else:
            plt.hist(snrs, bins=20, color='green', alpha=0.7, label='SNR (dB)')
            plt.xlabel("SNR (dB)")
            plt.ylabel("Frequency")
            plt.title("SNR Distribution")
        plt.legend()
        plt.show()

        return connections
class Connection:
    def __init__(self, input_node, output_node, signal_power):
        self.input = input_node
        self.output = output_node
        self.signal_power = signal_power
        self.latency = None
        self.snr = 0

# Main logic
if __name__ == "__main__":
    network = Network('nodes.json')
    network.connect()

    # Collect all paths and results
    results = []
    for node1, node2 in permutations(network.nodes.keys(), 2):
        for path in network.find_paths(node1, node2):
            signal = SignalInformation(1e-3, path[:])  # Initialize signal with 1 mW
            network.propagate(signal)
            snr = 10 * math.log10(signal.signal_power / signal.noise_power) if signal.noise_power > 0 else float('inf')
            results.append({
                'Path': '->'.join(path),
                'Latency (s)': signal.latency,
                'Noise Power (W)': signal.noise_power,
                'SNR (dB)': snr
            })

    # Create DataFrame
    df = pd.DataFrame(results)
    print(df)
    df.to_csv('network_results.csv', index=False)

    # Draw the network
    network.draw()
    print("Running simulation for latency...")
    latency_results = network.run_simulation(label="latency")
    # Run for SNR
    print("Running simulation for SNR...")
    snr_results = network.run_simulation(label="snr")


