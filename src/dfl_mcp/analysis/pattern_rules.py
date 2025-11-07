import networkx as nx

def identify_patterns(ct_subgraph: nx.DiGraph, weight_property: str) -> list:
    """
    Identifies key DFL patterns within the DFL Caterpillar Tree (CT).

    Args:
        ct_subgraph: The DFL Caterpillar Tree subgraph.
        weight_property: The property used for weighting and severity calculation.

    Returns:
        A ranked list of identified patterns/opportunities.
    """
    opportunities = []

    # Example Pattern: High Volume Node
    # Identify nodes with a high total incoming/outgoing volume
    node_volumes = {}
    for u, v, data in ct_subgraph.edges(data=True):
        volume = data.get(weight_property, 0)
        node_volumes[u] = node_volumes.get(u, 0) + volume
        node_volumes[v] = node_volumes.get(v, 0) + volume

    # Define a threshold for "high volume" - this can be made dynamic or configurable
    # For now, let's use a simple heuristic: nodes with volume > average volume * 1.5
    if node_volumes:
        avg_volume = sum(node_volumes.values()) / len(node_volumes)
        high_volume_threshold = avg_volume * 1.5

        for node, volume in node_volumes.items():
            if volume > high_volume_threshold:
                opportunities.append({
                    "pattern": f"High {weight_property.capitalize()} Node",
                    "severity_metric": volume,
                    "nodes": [node]
                })

    # Sort opportunities by severity_metric in descending order
    opportunities.sort(key=lambda x: x["severity_metric"], reverse=True)

    return opportunities
