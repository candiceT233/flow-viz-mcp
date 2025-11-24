import unittest
import networkx as nx
from unittest.mock import MagicMock

from src.dfl_mcp.graph_builder import (
    _get_pid_to_task_name_map,
    _add_task_nodes,
    _add_file_nodes,
    _add_edges_and_annotate,
    build_dfl_dag
)
from src.dfl_mcp.models import WorkflowSchema, Task, CorrelatedTrace

class TestGraphBuilder(unittest.TestCase):

    def setUp(self):
        # Mock WorkflowSchema and Tasks
        self.mock_task_A = Task(stage_order=1, parallelism=2, num_tasks=2, predecessors=[], outputs=["fileA_output_.*.h5"])
        self.mock_task_B = Task(stage_order=2, parallelism=1, num_tasks=1, predecessors=["task_A"], outputs=["fileB_output.txt"])
        self.mock_schema = WorkflowSchema(tasks={
            "task_A": self.mock_task_A,
            "task_B": self.mock_task_B
        })

        # Mock CorrelatedTraces
        self.mock_traces = [
            CorrelatedTrace(file_name="fileA_output_0.h5", pid=101, hostname="host1", operation="write", start_block=0, end_block=10, total_blocks_accessed=11, access_pattern="seq", io_time=1, op_count=1, total_bytes=1000),
            CorrelatedTrace(file_name="fileA_output_1.h5", pid=102, hostname="host1", operation="write", start_block=0, end_block=10, total_blocks_accessed=11, access_pattern="seq", io_time=1, op_count=1, total_bytes=2000),
            CorrelatedTrace(file_name="fileA_output_0.h5", pid=201, hostname="host1", operation="read", start_block=0, end_block=10, total_blocks_accessed=11, access_pattern="seq", io_time=1, op_count=1, total_bytes=1000),
            CorrelatedTrace(file_name="fileB_input.txt", pid=201, hostname="host1", operation="read", start_block=0, end_block=5, total_blocks_accessed=6, access_pattern="seq", io_time=0.5, op_count=1, total_bytes=500), # Initial file
            CorrelatedTrace(file_name="fileB_output.txt", pid=201, hostname="host1", operation="write", start_block=0, end_block=20, total_blocks_accessed=21, access_pattern="seq", io_time=2, op_count=1, total_bytes=3000),
        ]
        self.pid_to_task_name = _get_pid_to_task_name_map(self.mock_traces, self.mock_schema)

    def test_get_pid_to_task_name_map(self):
        expected_map = {101: 'task_A', 102: 'task_A', 201: 'task_B'}
        self.assertEqual(self.pid_to_task_name, expected_map)

    def test_add_task_nodes(self):
        G = nx.DiGraph()
        _add_task_nodes(G, self.mock_schema, self.mock_traces, self.pid_to_task_name)
        
        self.assertEqual(G.number_of_nodes(), 3) # task_A_0, task_A_1, task_B_0
        self.assertIn('task_A_0', G.nodes)
        self.assertIn('task_A_1', G.nodes)
        self.assertIn('task_B_0', G.nodes)

        self.assertEqual(G.nodes['task_A_0']['type'], 'task')
        self.assertEqual(G.nodes['task_A_0']['task_name'], 'task_A')
        self.assertEqual(G.nodes['task_A_0']['task_instance'], 0)
        self.assertEqual(G.nodes['task_A_1']['task_instance'], 1)
        self.assertEqual(G.nodes['task_B_0']['task_instance'], 0)

        # Check positioning (approximate due to float calculations)
        self.assertAlmostEqual(G.nodes['task_A_0']['pos'][0], 1.0)
        self.assertAlmostEqual(G.nodes['task_A_1']['pos'][0], 1.0)
        self.assertAlmostEqual(G.nodes['task_B_0']['pos'][0], 3.0)

    def test_add_file_nodes(self):
        G = nx.DiGraph()
        _add_task_nodes(G, self.mock_schema, self.mock_traces, self.pid_to_task_name) # Need tasks for file positioning
        _add_file_nodes(G, self.mock_schema, self.mock_traces, self.pid_to_task_name)

        self.assertIn('fileA_output_0.h5', G.nodes)
        self.assertIn('fileA_output_1.h5', G.nodes)
        self.assertIn('fileB_input.txt', G.nodes)
        self.assertIn('fileB_output.txt', G.nodes)

        self.assertEqual(G.nodes['fileB_input.txt']['type'], 'file')
        self.assertEqual(G.nodes['fileA_output_0.h5']['type'], 'file')
        
        # Check positioning for initial file (x=0)
        self.assertAlmostEqual(G.nodes['fileB_input.txt']['pos'][0], 0.0)

        # Check positioning for files from task_A (x=2.0 - task_A stage_order 1 + 1)
        self.assertAlmostEqual(G.nodes['fileA_output_0.h5']['pos'][0], 2.0)
        self.assertAlmostEqual(G.nodes['fileA_output_1.h5']['pos'][0], 2.0)

    def test_add_edges_and_annotate(self):
        G = nx.DiGraph()
        _add_task_nodes(G, self.mock_schema, self.mock_traces, self.pid_to_task_name) # Setup nodes for edges
        _add_file_nodes(G, self.mock_schema, self.mock_traces, self.pid_to_task_name)
        _add_edges_and_annotate(G, self.mock_schema, self.mock_traces, self.pid_to_task_name)

        # Check task A_1 -> fileA_output_0.h5 (pid 101 % 2 = 1)
        self.assertTrue(G.has_edge('task_A_1', 'fileA_output_0.h5'))
        edge_data = G.get_edge_data('task_A_1', 'fileA_output_0.h5')
        self.assertEqual(edge_data['volume'], 1000)
        self.assertEqual(edge_data['op_count'], 1)
        self.assertAlmostEqual(edge_data['rate'], 1000.0)

        # Check task A_0 -> fileA_output_1.h5 (pid 102 % 2 = 0)
        self.assertTrue(G.has_edge('task_A_0', 'fileA_output_1.h5'))
        edge_data = G.get_edge_data('task_A_0', 'fileA_output_1.h5')
        self.assertEqual(edge_data['volume'], 2000)
        self.assertEqual(edge_data['op_count'], 1)
        self.assertAlmostEqual(edge_data['rate'], 2000.0)

        # Check fileA_output_0.h5 -> task_B_0 (read for taskB, written by taskA_0, PID 201 reads it)
        # Note: In mock data, pid 201 reads fileA_output_0.h5, AND writes fileB_output.txt.
        # This means pid 201 is task_B, and it reads fileA_output_0.h5.
        # So we expect F_A_0 -> T_B_0
        self.assertTrue(G.has_edge('fileA_output_0.h5', 'task_B_0'))
        edge_data = G.get_edge_data('fileA_output_0.h5', 'task_B_0')
        self.assertEqual(edge_data['volume'], 1000)
        self.assertEqual(edge_data['op_count'], 1)
        self.assertAlmostEqual(edge_data['rate'], 1000.0)

        # Check task_B_0 -> fileB_output.txt
        self.assertTrue(G.has_edge('task_B_0', 'fileB_output.txt'))
        edge_data = G.get_edge_data('task_B_0', 'fileB_output.txt')
        self.assertEqual(edge_data['volume'], 3000)
        self.assertEqual(edge_data['op_count'], 1)
        self.assertAlmostEqual(edge_data['rate'], 1500.0)
        
    def test_build_dfl_dag(self):
        G = build_dfl_dag(self.mock_schema, self.mock_traces)

        self.assertIsInstance(G, nx.DiGraph)
        
        # Expected nodes: 3 tasks + 4 files = 7 nodes
        self.assertEqual(G.number_of_nodes(), 7)
        
        # Expected edges:
        # task_A_0 -> fileA_output_0.h5
        # task_A_1 -> fileA_output_1.h5
        # fileA_output_0.h5 -> task_B_0
        # fileB_input.txt -> task_B_0
        # task_B_0 -> fileB_output.txt
        self.assertEqual(G.number_of_edges(), 5)
        
        self.assertTrue(G.has_node('task_A_0'))
        self.assertTrue(G.has_node('fileA_output_0.h5'))
        self.assertTrue(G.has_edge('task_A_1', 'fileA_output_0.h5'))

if __name__ == '__main__':
    unittest.main()