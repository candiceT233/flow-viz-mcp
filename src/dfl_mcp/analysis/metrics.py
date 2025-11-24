import os
from typing import Any, Dict

import networkx as nx

BYTES_IN_GB = 1024 ** 3
BYTES_IN_MB = 1024 ** 2


def _empty_stat() -> Dict[str, float]:
    return {"volume_bytes": 0.0, "op_count": 0.0, "io_time_sec": 0.0}


def _accumulate(stat: Dict[str, float], volume: float, op_count: float, io_time: float):
    stat["volume_bytes"] += volume
    stat["op_count"] += op_count
    stat["io_time_sec"] += max(io_time, 0.0)


def _finalize_stat(stat: Dict[str, float]) -> Dict[str, Any]:
    volume_bytes = stat["volume_bytes"]
    io_time = stat["io_time_sec"]
    result = {
        "volume_bytes": volume_bytes,
        "volume_gb": volume_bytes / BYTES_IN_GB if volume_bytes else 0.0,
        "op_count": stat["op_count"],
        "avg_bandwidth_bytes_per_sec": None,
        "avg_bandwidth_MBps": None,
    }
    if io_time > 0:
        bw = volume_bytes / io_time
        result["avg_bandwidth_bytes_per_sec"] = bw
        result["avg_bandwidth_MBps"] = bw / BYTES_IN_MB
    return result


def _format_stat_lines(label: str, stat: Dict[str, Any]) -> str:
    bw = stat.get("avg_bandwidth_MBps")
    bw_str = f"{bw:,.2f} MB/s" if bw is not None else "N/A"
    return (
        f"{label} :: "
        f"Volume = {stat['volume_gb']:,.4f} GiB ({stat['volume_bytes']:,.0f} bytes), "
        f"Ops = {stat['op_count']:,.0f}, "
        f"Avg BW = {bw_str}"
    )


def calculate_flow_summary_stats(G: nx.DiGraph, output_file: str = None, workflow_name: str = 'ddmd') -> Dict[str, Any]:
    """
    Calculates comprehensive I/O summary statistics for a DFL-DAG.

    Returns a dictionary with workflow totals, per-task breakdowns, and the path
    to a human-readable summary file.
    """
    totals = {
        "all": _empty_stat(),
        "read": _empty_stat(),
        "write": _empty_stat(),
    }

    task_stats: Dict[str, Dict[str, Dict[str, float]]] = {}
    for node, data in G.nodes(data=True):
        if data.get("type") == "task":
            task_stats[node] = {
                "all": _empty_stat(),
                "read": _empty_stat(),
                "write": _empty_stat(),
            }

    for source, target, data in G.edges(data=True):
        volume = float(data.get('volume', 0) or 0)
        op_count = float(data.get('op_count', 0) or 0)
        io_time = float(data.get('io_time', 0.0) or 0.0)
        op_type = data.get('op_type')

        _accumulate(totals["all"], volume, op_count, io_time)
        if op_type == 'read':
            _accumulate(totals["read"], volume, op_count, io_time)
        elif op_type == 'write':
            _accumulate(totals["write"], volume, op_count, io_time)

        source_type = G.nodes[source].get('type')
        target_type = G.nodes[target].get('type')

        if op_type == 'write' and source_type == 'task':
            stats = task_stats[source]
            _accumulate(stats["write"], volume, op_count, io_time)
            _accumulate(stats["all"], volume, op_count, io_time)
        elif op_type == 'read' and target_type == 'task':
            stats = task_stats[target]
            _accumulate(stats["read"], volume, op_count, io_time)
            _accumulate(stats["all"], volume, op_count, io_time)

    finalized_totals = {k: _finalize_stat(v) for k, v in totals.items()}

    try:
        topo_order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        topo_order = list(G.nodes())

    ordered_tasks = [
        node for node in topo_order
        if node in task_stats
    ]

    finalized_per_task = {}
    for task in ordered_tasks:
        finalized_per_task[task] = {k: _finalize_stat(v) for k, v in task_stats[task].items()}

    lines = [f"Workflow: {workflow_name}", ""]
    lines.append("== Workflow Totals ==")
    lines.append(_format_stat_lines("All I/O", finalized_totals["all"]))
    lines.append(_format_stat_lines("Read I/O", finalized_totals["read"]))
    lines.append(_format_stat_lines("Write I/O", finalized_totals["write"]))

    lines.append("")
    lines.append("== Per-Task Breakdown ==")
    if not finalized_per_task:
        lines.append("No task nodes present in the filtered graph.")
    else:
        for task, stats in finalized_per_task.items():
            lines.append(f"-- {task} --")
            lines.append(_format_stat_lines("  Combined", stats["all"]))
            lines.append(_format_stat_lines("  Reads", stats["read"]))
            lines.append(_format_stat_lines("  Writes", stats["write"]))
            lines.append("")

    summary_text = "\n".join(lines).rstrip() + "\n"

    if output_file is None:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{workflow_name}_summary.txt")

    with open(output_file, 'w') as f:
        f.write(summary_text)

    return {
        "workflow_name": workflow_name,
        "totals": finalized_totals,
        "per_task": finalized_per_task,
        "output_file": output_file,
        "summary_text": summary_text,
    }
