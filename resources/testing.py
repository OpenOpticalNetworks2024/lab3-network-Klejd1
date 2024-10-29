import json

from numpy.ma.core import not_equal

class Label():
    def __init__(self, data:dict):
        self._connected_nodes = data['A']['connection']

        @property
        def connected_nodes(self):
            return self._connected_nodes

        @connected_nodes.setter
        def connected_nodes(self, test: dict):
            self._connected_nodes = dict['connected_nodes']


nodes_connected = {}
with open('nodes.json', 'r') as file:
    data = json.load(file)

    label = ['A', 'B', 'C', 'D']

    for i in label:

        nodes_connected[i] = {}
        #nodes_connected[ = data['A']
        nodes_connected[i]['connection'] = data[i]['connected_nodes']
        nodes_connected[i]['position'] = data[i]['position']
        print("Test:" , nodes_connected)

    print("Test:", nodes_connected)

    lab = Label(nodes_connected)

    #a = lab._connected_nodes(nodes_connected)

 #   print(lab._connected_nodes)

    labels = data.keys()

    print(labels)












