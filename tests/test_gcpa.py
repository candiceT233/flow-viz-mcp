import unittest
import networkx as nx
from src.dfl_mcp.analysis.critical_path import calculate_critical_path_gcpa, extend_to_caterpillar_tree

class TestCriticalPathAnalysis(unittest.TestCase):

    def setUp(self):
        self.graph = nx.DiGraph()
        # Nodes: T (Task), F (File)
        # Edges with 'volume' property
        self.graph.add_edge('T1', 'F1', volume=10, op_count=1)
        self.graph.add_edge('F1', 'T2', volume=10, op_count=1)
        self.graph.add_edge('T2', 'F2', volume=5, op_count=1)
        self.graph.add_edge('F2', 'T3', volume=5, op_count=1)
        self.graph.add_edge('T1', 'F3', volume=20, op_count=1)
        self.graph.add_edge('F3', 'T3', volume=20, op_count=1)
        self.graph.add_edge('T3', 'F4', volume=15, op_count=1)

        # Another path to make it interesting
        self.graph.add_edge('T1', 'F5', volume=8, op_count=1)
        self.graph.add_edge('F5', 'T4', volume=8, op_count=1)
        self.graph.add_edge('T4', 'F4', volume=8, op_count=1)

    def test_calculate_critical_path_gcpa_volume(self):
        critical_path = calculate_critical_path_gcpa(self.graph, 'volume')
        # Expected critical path based on volume: T1 -> F3 -> T3 -> F4 (20 + 15 = 35)
        expected_path = [('T1', 'F3'), ('F3', 'T3'), ('T3', 'F4')]
        self.assertListEqual(critical_path, expected_path)

    def test_calculate_critical_path_gcpa_op_count(self):
        # Let's add some edges with different op_count to test this property
        self.graph.add_edge('T1', 'F6', volume=1, op_count=100)
        self.graph.add_edge('F6', 'T5', volume=1, op_count=100)
        self.graph.add_edge('T5', 'F4', volume=1, op_count=100)

        critical_path = calculate_critical_path_gcpa(self.graph, 'op_count')
        # Expected critical path based on op_count: T1 -> F6 -> T5 -> F4 (100 + 100 + 100 = 300)
        expected_path = [('T1', 'F6'), ('F6', 'T5'), ('T5', 'F4')]
        self.assertListEqual(critical_path, expected_path)

    def test_extend_to_caterpillar_tree(self):
        critical_path = calculate_critical_path_gcpa(self.graph, 'volume')
        ct_subgraph = extend_to_caterpillar_tree(self.graph, critical_path)

        # Nodes in critical path: T1, F3, T3, F4
        # Fan-in/out for T1: F1, F3, F5
        # Fan-in/out for F3: T1, T3
        # Fan-in/out for T3: F2, F3, F4
        # Fan-in/out for F4: T3, T4

        expected_nodes = {'T1', 'F1', 'F2', 'T3', 'F3', 'F4', 'F5', 'T4'}
        self.assertSetEqual(set(ct_subgraph.nodes()), expected_nodes)

        # Check some edges are present
        self.assertTrue(ct_subgraph.has_edge('T1', 'F1'))

        self.assertTrue(ct_subgraph.has_edge('T1', 'F3'))
        self.assertTrue(ct_subgraph.has_edge('F3', 'T3'))
        self.assertTrue(ct_subgraph.has_edge('T3', 'F4'))
        self.assertTrue(ct_subgraph.has_edge('T1', 'F5'))
        self.assertTrue(ct_subgraph.has_edge('F5', 'T4'))
        self.assertTrue(ct_subgraph.has_edge('T4', 'F4'))

if __name__ == '__main__':
    unittest.main()
