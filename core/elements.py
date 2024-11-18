import math
import json
import matplotlib.pyplot as plt
import pandas as pd
from itertools import permutations


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
