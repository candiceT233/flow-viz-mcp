import networkx as nx

def calculate_flow_summary_stats(G: nx.DiGraph, output_file: str = None, workflow_name: str = 'ddmd') -> str:
    """
    Calculates summary statistics for a given DFL-DAG and saves it to a file.

    Args:
        G: The DFL-DAG.
        output_file: Optional path to save the summary file.
        workflow_name: The name of the workflow, used as default filename.

    Returns:
        The path to the saved summary file.
    """
    total_volume_gb = 0
    producer_writes_count = 0
    consumer_reads_count = 0
    producer_total_volume_gb = 0

    for source, target, data in G.edges(data=True):
        volume = data.get('volume', 0)
        total_volume_gb += volume

        if G.nodes[source].get('type') == 'task': # Producer (Task -> File)
            producer_writes_count += 1
            producer_total_volume_gb += volume
        else: # Consumer (File -> Task)
            consumer_reads_count += 1
            
    # Convert bytes to GB
    total_volume_gb /= (1024**3)
    producer_total_volume_gb /= (1024**3)

    summary = {
        "total_volume_GB": total_volume_gb,
        "producer_writes_count": producer_writes_count,
        "consumer_reads_count": consumer_reads_count,
        "producer_total_volume_GB": producer_total_volume_gb,
    }

    if output_file is None:
        output_file = f"{workflow_name}_summary.txt"
    
    with open(output_file, 'w') as f:
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
            
    return f"Summary saved to {output_file}"
