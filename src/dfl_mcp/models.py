from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class BlockTrace:
    """
    Represents a block trace from a *.r_blk_trace.json or *.w_blk_trace.json file.
    """
    file_name: str
    pid: int
    hostname: str
    operation: str  # 'read' or 'write'
    start_block: int
    end_block: int
    total_blocks_accessed: int
    access_pattern: int  # -1 for sequential, -2 for random
    task_name: Optional[str] = None  # Optional: task name from trace file

@dataclass
class DatalifeTrace:
    """
    Represents a datalife trace from a monitor_timer.*.datalife.json file.
    """
    pid: int
    hostname: str
    io_time: float
    op_count: int
    total_bytes: int
    operation: str # 'read' or 'write'

@dataclass
class Task:
    """
    Represents a task in the workflow schema.
    """
    stage_order: int
    parallelism: int
    num_tasks: int
    predecessors: Dict[str, Dict[str, List[str]]]
    outputs: List[str]

@dataclass
class WorkflowSchema:
    """
    Represents the workflow schema.
    """
    tasks: Dict[str, Task]

@dataclass
class DFLProperties:
    """
    Represents the properties to be annotated on the DFL-DAG edges.
    """
    volume: int = 0
    op_count: int = 0
    rate: float = 0.0


@dataclass
class CorrelatedTrace:
    """
    Represents a correlated trace, combining block and datalife information.
    """
    file_name: str
    pid: int
    hostname: str
    operation: str
    start_block: int
    end_block: int
    total_blocks_accessed: int
    access_pattern: int
    io_time: float
    op_count: int
    total_bytes: int
    task_name: Optional[str] = None  # Optional: task name from trace file
