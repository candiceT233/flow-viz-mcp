import os
import tempfile
import unittest

import networkx as nx

from src.dfl_mcp.analysis.metrics import calculate_flow_summary_stats


class TestMetrics(unittest.TestCase):

    def setUp(self):
        self.graph = nx.DiGraph()
        self.graph.add_node('T1', type='task')
        self.graph.add_node('F1', type='file')
        self.graph.add_node('T2', type='task')
        self.graph.add_node('F2', type='file')

        one_gb = 1024 ** 3

        self.graph.add_edge(
            'T1', 'F1',
            volume=one_gb,
            op_count=2,
            io_time=2.0,
            op_type='write'
        )
        self.graph.add_edge(
            'F1', 'T2',
            volume=one_gb,
            op_count=1,
            io_time=1.0,
            op_type='read'
        )
        self.graph.add_edge(
            'T2', 'F2',
            volume=2 * one_gb,
            op_count=3,
            io_time=4.0,
            op_type='write'
        )

    def test_calculate_flow_summary_stats_default_filename(self):
        result = calculate_flow_summary_stats(self.graph, workflow_name='test_workflow')
        expected_path = os.path.join("output", "test_workflow_summary.txt")
        self.assertEqual(result["output_file"], expected_path)
        self.assertTrue(os.path.exists(expected_path))

        self.assertAlmostEqual(result["totals"]["all"]["volume_gb"], 4.0, places=5)
        self.assertAlmostEqual(result["totals"]["read"]["volume_gb"], 1.0, places=5)
        self.assertAlmostEqual(result["totals"]["write"]["volume_gb"], 3.0, places=5)

        per_task = result["per_task"]
        self.assertAlmostEqual(per_task['T1']["write"]["volume_gb"], 1.0, places=5)
        self.assertAlmostEqual(per_task['T2']["all"]["volume_gb"], 3.0, places=5)
        self.assertIn("Workflow: test_workflow", result["summary_text"])

        os.remove(expected_path)

    def test_calculate_flow_summary_stats_provided_filename(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            output_path = tmp.name

        try:
            result = calculate_flow_summary_stats(self.graph, output_file=output_path)
            self.assertEqual(result["output_file"], output_path)
            self.assertTrue(os.path.exists(output_path))
            self.assertIn("Workflow Totals", result["summary_text"])
        finally:
            os.remove(output_path)


if __name__ == '__main__':
    unittest.main()
