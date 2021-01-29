#! /bin/python
###############################################################################
# A python script to visualize nodes. Code is adapted from the following links.
# https://github.com/rweng18/midsummer_network/blob/master/process.py
# https://github.com/rweng18/midsummer_network/blob/master/midsummer_graph.ipynb
# https://towardsdatascience.com/tutorial-network-visualization-basics-with-networkx-and-plotly-and-a-little-nlp-57c9bbb55bb9
# https://pythonbasics.org/webserver/
###############################################################################

import argparse
import json
import re
import os
import urllib.request
import plotly.offline as py
import plotly.graph_objects as go
import networkx as nx
import http.server


class MyServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # If the root dir is requested
        if self.path == "/":
            self.do_update_content()
            self.path = "mesh_network_graph.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    # Custom function to create an edge between node x and node y, with a given text and width
    def make_edge(self, x, y, text, width):
        return go.Scatter(x=x,
                          y=y,
                          line=dict(width=width,
                                    color='cornflowerblue'),
                          hoverinfo='text',
                          text=([text]),
                          mode='lines')

    def get_webpage(self):
        # Request the age http://192.168.4.1/logfile.txt
        response = urllib.request.urlopen("http://192.168.4.1/logfile.txt")
        # Decode the content and convert it to a string
        content = response.read().decode("UTF-8")
        return content

    def parse_webpage_content(self, content):
        # Here is our testdata. We need to read it in from a file and parse it
        # This line here will match our JSON strings in the form of "node: {"3": [{"n":2,"r":0},{"n":2,"r":-24},{"n":255,"r":0}]}"
        # It will find all occurrences and put them into a list.
        data = [re.findall(r'^node: ({\"[0-9]+\": .*)', content)]
        data_list_dict = []
        for item in data:
            # Convert each JSON string into a dict, but check for emtpy items
            if item != []:
                json_str = ""
                json_str = json_str.join(item)
                data_list_dict.append(json.loads(json_str))
        
        return data_list_dict
    
    def find_all_nodes(self, list_dict_to_search):
        # Here is what we know:
        # {"2": [{"n":1,"r":-44},{"n":255,"r":0},{"n":3,"r":-13}]}
        # In the string above node 2 has valid connections to
        # node 1 @ -44 dB and node 3 @ -13 db

        # First let's find all the unique node names (keys) in the data list of dictionaries
        # Now we try to create a nx graph
        net = nx.Graph()

        unique_node_list = []
        for item in list_dict_to_search:
            for key, value in item.items():
                if key in unique_node_list:
                    continue
                else:
                    unique_node_list.append(key)
                    net.add_node(str(key), size=2)
        
        return net, unique_node_list

    def add_edges_to_net_graph(self, list_dict_to_search, nodes_list, network_graph):
        for item in list_dict_to_search:
            for nodeid in nodes_list:
                if nodeid in item:
                    for node in item[nodeid]:
                        node_name = node["n"]
                        node_sigstrength = node["r"]

                        # If the connection has a dB
                        if node_sigstrength != 0:
                            # Check if its a valid edge.  Valid: 3 -> 1,  Invalid: 3 -> 0
                            if node_name != 0:
                                #print("node:", ukey, "connects to:", node_name)
                                network_graph.add_edge(
                                    str(nodeid), str(node_name), weight=2)
        
        return network_graph



    def do_update_content(self):
        # Make a node trace
        node_trace = go.Scatter(x=[],
                                y=[],
                                text=[],
                                textposition="top center",
                                textfont_size=25,
                                mode='markers+text',
                                hoverinfo='none',
                                marker=dict(color=[],
                                            size=[],
                                            line=None))
        # Grab the web page content
        webpage_content = self.get_webpage()
        # Parse the web page content
        data_list_dict = self.parse_webpage_content(webpage_content)
        # Get a network graph an unique node list
        mesh_net, nodes_list = self.find_all_nodes(data_list_dict)
        # Find all the edges in network graph
        mesh_net = self.add_edges_to_net_graph(data_list_dict, nodes_list, mesh_net)

        # Get positions for the nodes in G
        pos_ = nx.spring_layout(mesh_net)
        edge_trace = []

        print("Edges:", mesh_net.edges())
        for edge in mesh_net.edges():
            char_1 = edge[0]
            char_2 = edge[1]
            x0, y0 = pos_[char_1]
            x1, y1 = pos_[char_2]
            text = str(char_1) + "--" + str(char_2) + ":" + \
                str(mesh_net.edges()[edge]['weight'])
            print(text)
            trace = self.make_edge([x0, x1, None], [y0, y1, None], text,
                                   width=0.3*mesh_net.edges()[edge]['weight']**1.75)
            edge_trace.append(trace)

        print("Nodes:", mesh_net.nodes())
        for node in mesh_net:
            x, y = pos_[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['marker']['color'] += tuple(['red'])
            node_trace['marker']['size'] += tuple([25])
            node_trace['text'] += tuple(['<b>' + str(node) + '</b>'])

        # Customize layout
        layout = go.Layout(
            paper_bgcolor='rgba(0,0,0,0)',  # transparent background
            plot_bgcolor='rgba(0,0,0,0)',  # transparent 2nd background
            xaxis={'showgrid': False, 'zeroline': False},
            yaxis={'showgrid': False, 'zeroline': False},
        )
        # Create figure
        fig = go.Figure(layout=layout)
        # Add all edge traces
        for trace in edge_trace:
            fig.add_trace(trace)

        # Add node trace
        fig.add_trace(node_trace)
        # Remove legend
        fig.update_layout(showlegend=False)
        # Remove tick labels
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        # Show figure
        fig.write_html("mesh_network_graph.html")
        fig.write_image("mesh_network_graph.svg")
        fig.write_image("mesh_network_graph.pdf")


# main like in C/C++
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mesh Server: server content on specified IP")
    parser.add_argument("-ip", type=str, required=True,
                        dest="ipaddress", help="IP address to server content on")
    parser.add_argument("-p", type=int, required=True,
                        dest="port", help="Port number to server content on")
    args = parser.parse_args()

    if args.ipaddress and args.port:
        hostname = args.ipaddress
        serverport = args.port

    # Change Directory and host from web folder
    webdir = os.path.join(os.path.dirname(__file__), 'web')
    os.chdir(webdir)

    webserver = http.server.HTTPServer((hostname, serverport), MyServer)
    print("Server started http://" + hostname + ":" + str(serverport))

    try:
        webserver.serve_forever()

    except KeyboardInterrupt:
        pass

    webserver.server_close()
    print("Server stopped")
