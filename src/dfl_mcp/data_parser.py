import json
import os
import re
from typing import List, Dict, Tuple, Any

from .models import BlockTrace, DatalifeTrace, WorkflowSchema, Task, CorrelatedTrace

class SchemaLoader:
    """
    Loads the workflow schema from a JSON file.
    """

    def load_schema(self, file_path: str) -> WorkflowSchema:
        """
        Loads the workflow schema from a JSON file.

        Args:
            file_path: The path to the JSON schema file.

        Returns:
            A WorkflowSchema object.
        """
        with open(file_path, 'r') as f:
            schema_data = json.load(f)

        min_stage = min(task_data['stage_order'] for task_data in schema_data.values())
        stage_offset = 1 - min_stage if min_stage < 1 else 0

        tasks = {}
        for task_name, task_data in schema_data.items():
            tasks[task_name] = Task(
                stage_order=task_data['stage_order'] + stage_offset,
                parallelism=task_data['parallelism'],
                num_tasks=task_data['num_tasks'],
                predecessors=task_data['predecessors'],
                outputs=task_data['outputs']
            )
        
        return WorkflowSchema(tasks=tasks)


class TraceParser:
    """
    Parses the trace files from a directory and correlates them.
    """
    def __init__(self):
        self.block_trace_pattern = re.compile(r'(.*)\.(\d+)-([\w\.-]+)\.(r|w)_blk_trace\.json')
        self.datalife_trace_pattern = re.compile(r'monitor_timer\.(\d+)-([\w\.-]+)\.datalife\.json')

    def parse_and_correlate_traces(self, dir_path: str) -> List[CorrelatedTrace]:
        """
        Parses and correlates the trace files from a directory.

        Args:
            dir_path: The path to the directory containing the trace files.

        Returns:
            A list of CorrelatedTrace objects.
        """
        block_traces, datalife_traces = self._parse_traces(dir_path)
        
        datalife_map = {(trace.pid, trace.hostname, trace.operation): trace for trace in datalife_traces}
        
        correlated_traces = []
        for block_trace in block_traces:
            key = (block_trace.pid, block_trace.hostname, block_trace.operation)
            datalife_trace = datalife_map.get(key)
            
            # If we have a matching datalife trace, use it for complete data
            if datalife_trace:
                correlated_traces.append(CorrelatedTrace(
                    file_name=block_trace.file_name,
                    pid=block_trace.pid,
                    hostname=block_trace.hostname,
                    operation=block_trace.operation,
                    start_block=block_trace.start_block,
                    end_block=block_trace.end_block,
                    total_blocks_accessed=block_trace.total_blocks_accessed,
                    access_pattern=block_trace.access_pattern,
                    io_time=datalife_trace.io_time,
                    op_count=datalife_trace.op_count,
                    total_bytes=datalife_trace.total_bytes,
                    task_name=block_trace.task_name
                ))
            elif block_trace.task_name:
                # If task_name is present in block trace but no datalife match,
                # create trace anyway - task_name takes priority over schema correlation
                correlated_traces.append(CorrelatedTrace(
                    file_name=block_trace.file_name,
                    pid=block_trace.pid,
                    hostname=block_trace.hostname,
                    operation=block_trace.operation,
                    start_block=block_trace.start_block,
                    end_block=block_trace.end_block,
                    total_blocks_accessed=block_trace.total_blocks_accessed,
                    access_pattern=block_trace.access_pattern,
                    io_time=0,  # No datalife data available
                    op_count=block_trace.total_blocks_accessed,  # Use block count as approximation
                    total_bytes=block_trace.total_blocks_accessed * 4096,  # Approximate: blocks * typical block size
                    task_name=block_trace.task_name
                ))
        
        return correlated_traces

    def _parse_traces(self, dir_path: str) -> Tuple[List[BlockTrace], List[DatalifeTrace]]:
        """
        Parses the trace files from a directory.

        Args:
            dir_path: The path to the directory containing the trace files.

        Returns:
            A tuple containing a list of BlockTrace objects and a list of DatalifeTrace objects.
        """
        block_traces = []
        datalife_traces = []

        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                file_path = os.path.join(dir_path, filename)
                
                block_match = self.block_trace_pattern.match(filename)
                if block_match:
                    block_traces.append(self._parse_block_trace(file_path, block_match))
                    continue

                datalife_match = self.datalife_trace_pattern.match(filename)
                if datalife_match:
                    datalife_traces.extend(self._parse_datalife_trace(file_path, datalife_match))

        return block_traces, datalife_traces

    def _parse_block_trace(self, file_path: str, match: re.Match) -> BlockTrace:
        """
        Parses a block trace file.
        """
        file_name, pid, hostname, operation_char = match.groups()
        operation = 'read' if operation_char == 'r' else 'write'

        with open(file_path, 'r') as f:
            data = json.load(f)
        
        io_blk_range = data['io_blk_range']
        
        # Extract task_name if present in the trace file
        task_name = data.get('task_name', None)
        
        return BlockTrace(
            file_name=file_name,
            pid=int(pid),
            hostname=hostname,
            operation=operation,
            start_block=io_blk_range[0],
            end_block=io_blk_range[1],
            total_blocks_accessed=io_blk_range[2],
            access_pattern=io_blk_range[3],
            task_name=task_name
        )

    def _parse_datalife_trace(self, file_path: str, match: re.Match) -> List[DatalifeTrace]:
        """
        Parses a datalife trace file.
        """
        pid, hostname = match.groups()

        with open(file_path, 'r') as f:
            data = json.load(f)

        process_name = list(data.keys())[0]
        monitor_data = data[process_name]['monitor']
        read_data = monitor_data.get('read', [0, 0, 0])
        write_data = monitor_data.get('write', [0, 0, 0])

        traces = []
        if sum(read_data) > 0:
            traces.append(DatalifeTrace(
                pid=int(pid),
                hostname=hostname,
                io_time=read_data[0],
                op_count=read_data[1],
                total_bytes=read_data[2],
                operation='read'
            ))
        
        if sum(write_data) > 0:
            traces.append(DatalifeTrace(
                pid=int(pid),
                hostname=hostname,
                io_time=write_data[0],
                op_count=write_data[1],
                total_bytes=write_data[2],
                operation='write'
            ))
        return traces

