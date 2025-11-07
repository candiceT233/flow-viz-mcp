import unittest
import os
import json
from unittest.mock import patch, mock_open

from src.dfl_mcp.data_parser import SchemaLoader, TraceParser
from src.dfl_mcp.models import WorkflowSchema, Task, BlockTrace, DatalifeTrace, CorrelatedTrace

class TestSchemaLoader(unittest.TestCase):

    def test_load_schema(self):
        schema_content = {
            "taskA": {
                "stage_order": 1,
                "parallelism": 1,
                "num_tasks": 1,
                "predecessors": [],
                "outputs": ["fileA.txt"]
            },
            "taskB": {
                "stage_order": 2,
                "parallelism": 1,
                "num_tasks": 1,
                "predecessors": ["taskA"],
                "outputs": ["fileB.txt"]
            }
        }
        
        mock_file_path = "/tmp/test_schema.json"
        with open(mock_file_path, 'w') as f:
            json.dump(schema_content, f)

        loader = SchemaLoader()
        schema = loader.load_schema(mock_file_path)
        
        self.assertIsInstance(schema, WorkflowSchema)
        self.assertEqual(len(schema.tasks), 2)
        self.assertIn('taskA', schema.tasks)
        self.assertIn('taskB', schema.tasks)

        taskA = schema.tasks['taskA']
        self.assertEqual(taskA.stage_order, 1)
        self.assertEqual(taskA.parallelism, 1)
        self.assertEqual(taskA.num_tasks, 1)
        self.assertEqual(taskA.predecessors, [])
        self.assertEqual(taskA.outputs, ["fileA.txt"])

        taskB = schema.tasks['taskB']
        self.assertEqual(taskB.stage_order, 2)
        self.assertEqual(taskB.predecessors, ["taskA"])
        
        os.remove(mock_file_path)

    def test_load_schema_with_offset(self):
        schema_content = {
            "taskA": {
                "stage_order": 0,
                "parallelism": 1,
                "num_tasks": 1,
                "predecessors": [],
                "outputs": ["fileA.txt"]
            },
            "taskB": {
                "stage_order": 1,
                "parallelism": 1,
                "num_tasks": 1,
                "predecessors": ["taskA"],
                "outputs": ["fileB.txt"]
            }
        }
        
        mock_file_path = "/tmp/test_schema_offset.json"
        with open(mock_file_path, 'w') as f:
            json.dump(schema_content, f)

        loader = SchemaLoader()
        schema = loader.load_schema(mock_file_path)
        
        self.assertEqual(schema.tasks['taskA'].stage_order, 1) # 0 + 1
        self.assertEqual(schema.tasks['taskB'].stage_order, 2) # 1 + 1
        
        os.remove(mock_file_path)

class TestTraceParser(unittest.TestCase):

    def setUp(self):
        self.test_dir = "/tmp/test_traces"
        os.makedirs(self.test_dir, exist_ok=True)

        self.block_trace_filename = "file.h5.123-host.r_blk_trace.json"
        self.block_trace_content = {
            "io_blk_range": [0, 100, 101, "sequential"]
        }
        with open(os.path.join(self.test_dir, self.block_trace_filename), 'w') as f:
            json.dump(self.block_trace_content, f)

        self.datalife_trace_filename = "monitor_timer.123-host.datalife.json"
        self.datalife_trace_content = {
            "process_name": {
                "monitor": {
                    "read": [10, 5, 1024],
                    "write": [20, 10, 2048]
                }
            }
        }
        with open(os.path.join(self.test_dir, self.datalife_trace_filename), 'w') as f:
            json.dump(self.datalife_trace_content, f)

        self.parser = TraceParser()

    def tearDown(self):
        for f in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, f))
        os.rmdir(self.test_dir)

    def test_parse_block_trace(self):
        match = self.parser.block_trace_pattern.match(self.block_trace_filename)
        block_trace = self.parser._parse_block_trace(os.path.join(self.test_dir, self.block_trace_filename), match)
        
        self.assertIsInstance(block_trace, BlockTrace)
        self.assertEqual(block_trace.file_name, 'file.h5')
        self.assertEqual(block_trace.pid, 123)
        self.assertEqual(block_trace.hostname, 'host')
        self.assertEqual(block_trace.operation, 'read')
        self.assertEqual(block_trace.start_block, 0)
        self.assertEqual(block_trace.end_block, 100)
        self.assertEqual(block_trace.total_blocks_accessed, 101)
        self.assertEqual(block_trace.access_pattern, 'sequential')

    def test_parse_datalife_trace(self):
        match = self.parser.datalife_trace_pattern.match(self.datalife_trace_filename)
        datalife_traces = self.parser._parse_datalife_trace(os.path.join(self.test_dir, self.datalife_trace_filename), match)
        
        self.assertEqual(len(datalife_traces), 2)
        
        read_trace = next(t for t in datalife_traces if t.operation == 'read')
        self.assertIsInstance(read_trace, DatalifeTrace)
        self.assertEqual(read_trace.pid, 123)
        self.assertEqual(read_trace.hostname, 'host')
        self.assertEqual(read_trace.io_time, 10)
        self.assertEqual(read_trace.op_count, 5)
        self.assertEqual(read_trace.total_bytes, 1024)
        self.assertEqual(read_trace.operation, 'read')

        write_trace = next(t for t in datalife_traces if t.operation == 'write')
        self.assertIsInstance(write_trace, DatalifeTrace)
        self.assertEqual(write_trace.pid, 123)
        self.assertEqual(write_trace.hostname, 'host')
        self.assertEqual(write_trace.io_time, 20)
        self.assertEqual(write_trace.op_count, 10)
        self.assertEqual(write_trace.total_bytes, 2048)
        self.assertEqual(write_trace.operation, 'write')

    def test_parse_and_correlate_traces(self):
        correlated_traces = self.parser.parse_and_correlate_traces(self.test_dir)
        
        self.assertEqual(len(correlated_traces), 1)
        correlated_trace = correlated_traces[0]

        self.assertIsInstance(correlated_trace, CorrelatedTrace)
        self.assertEqual(correlated_trace.file_name, 'file.h5')
        self.assertEqual(correlated_trace.pid, 123)
        self.assertEqual(correlated_trace.hostname, 'host')
        self.assertEqual(correlated_trace.operation, 'read')
        self.assertEqual(correlated_trace.start_block, 0)
        self.assertEqual(correlated_trace.end_block, 100)
        self.assertEqual(correlated_trace.total_blocks_accessed, 101)
        self.assertEqual(correlated_trace.access_pattern, 'sequential')
        self.assertEqual(correlated_trace.io_time, 10)
        self.assertEqual(correlated_trace.op_count, 5)
        self.assertEqual(correlated_trace.total_bytes, 1024)

if __name__ == '__main__':
    unittest.main()
