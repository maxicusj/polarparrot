import matplotlib.pyplot as plt
import networkx as nx

# Initialize the directed graph
G = nx.DiGraph()

# Nodes in the architecture
nodes = [
    "Dash App", 
    "Backend (Flask)", 
    "YAML Files (e.g., calculation_average.yaml)", 
    "Positions Data (JSON)", 
    "Data Service (Flask)", 
    "Instrument Categorization Table"
]

# Add nodes to the graph
G.add_nodes_from(nodes)

# Define edges (data flow)
edges = [
    ("Dash App", "Backend (Flask)"),
    ("Backend (Flask)", "YAML Files (e.g., 0001.yaml)"),
    ("Backend (Flask)", "Positions Data (JSON)"),
    ("YAML Files (e.g., 0001.yaml)", "Backend (Flask)"),
    ("Backend (Flask)", "Data Service (Flask)"),
    ("Data Service (Flask)", "Instrument Categorization Table (SQL Server)"),
    ("Instrument Categorization Table", "Data Service (Flask)"),
    ("Data Service (Flask)", "Backend (Flask)"),
    ("Backend (Flask)", "Dash App")
]

# Add edges to the graph
G.add_edges_from(edges)

# Draw the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)
nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='skyblue')
nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, edge_color='gray')
nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', font_color='black')
plt.title("Solution Architecture Diagram", fontsize=16)
plt.axis('off')
plt.show()
