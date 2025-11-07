import unittest
import os
import networkx as nx
from src.dfl_mcp.analysis.metrics import calculate_flow_summary_stats

class TestMetrics(unittest.TestCase):

    def setUp(self):
        self.graph = nx.DiGraph()
        self.graph.add_node('T1', type='task')
        self.graph.add_node('F1', type='file')
        self.graph.add_node('T2', type='task')
        self.graph.add_node('F2', type='file')
        self.graph.add_edge('T1', 'F1', volume=1024**3) # 1 GB
        self.graph.add_edge('F1', 'T2', volume=1024**3) # 1 GB
        self.graph.add_edge('T2', 'F2', volume=2 * (1024**3)) # 2 GB

    def test_calculate_flow_summary_stats_default_filename(self):
        output_path = calculate_flow_summary_stats(self.graph, workflow_name='test_workflow')
        expected_path = "test_workflow_summary.txt"
        self.assertEqual(output_path, f"Summary saved to {expected_path}")
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, 'r') as f:
            content = f.read()
        
        self.assertIn("total_volume_GB: 4.0", content)
        self.assertIn("producer_writes_count: 2", content)
        self.assertIn("consumer_reads_count: 1", content)
        self.assertIn("producer_total_volume_GB: 3.0", content)

        os.remove(expected_path)

    def test_calculate_flow_summary_stats_provided_filename(self):
        output_path = "/tmp/test_summary.txt"
        result_path = calculate_flow_summary_stats(self.graph, output_file=output_path)
        self.assertEqual(result_path, f"Summary saved to {output_path}")
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            content = f.read()
        
        self.assertIn("total_volume_GB: 4.0", content)
        self.assertIn("producer_writes_count: 2", content)
        self.assertIn("consumer_reads_count: 1", content)
        self.assertIn("producer_total_volume_GB: 3.0", content)

        os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
