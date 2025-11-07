import unittest
import os
import networkx as nx
from src.dfl_mcp.analysis.sankey_utils import filter_subgraph, create_sankey_html

class TestSankeyUtils(unittest.TestCase):

    def setUp(self):
        self.graph = nx.DiGraph()
        self.graph.add_node('T1', type='task', pos=(1, 0.5))
        self.graph.add_node('F1', type='file', pos=(2, 0.5))
        self.graph.add_node('T2', type='task', pos=(3, 0.5))
        self.graph.add_node('F2', type='file', pos=(4, 0.5))
        self.graph.add_edge('T1', 'F1', volume=100)
        self.graph.add_edge('F1', 'T2', volume=100)
        self.graph.add_edge('T2', 'F2', volume=50)

    def test_filter_subgraph_no_selection(self):
        subgraph = filter_subgraph(self.graph, [], [])
        self.assertEqual(subgraph.number_of_nodes(), self.graph.number_of_nodes())
        self.assertEqual(subgraph.number_of_edges(), self.graph.number_of_edges())

    def test_filter_subgraph_select_task(self):
        subgraph = filter_subgraph(self.graph, ['T1'], [])
        self.assertIn('T1', subgraph.nodes)
        self.assertIn('F1', subgraph.nodes) # Successor of T1
        self.assertNotIn('T2', subgraph.nodes)
        self.assertNotIn('F2', subgraph.nodes)
        self.assertEqual(subgraph.number_of_nodes(), 2)
        self.assertEqual(subgraph.number_of_edges(), 1)

    def test_filter_subgraph_select_file(self):
        subgraph = filter_subgraph(self.graph, [], ['F1'])
        self.assertIn('F1', subgraph.nodes)
        self.assertIn('T1', subgraph.nodes) # Predecessor of F1
        self.assertIn('T2', subgraph.nodes) # Successor of F1
        self.assertNotIn('F2', subgraph.nodes)
        self.assertEqual(subgraph.number_of_nodes(), 3)
        self.assertEqual(subgraph.number_of_edges(), 2)

    def test_filter_subgraph_select_task_and_file(self):
        subgraph = filter_subgraph(self.graph, ['T1'], ['F2'])
        self.assertIn('T1', subgraph.nodes)
        self.assertIn('F2', subgraph.nodes)
        self.assertNotIn('F1', subgraph.nodes)
        self.assertNotIn('T2', subgraph.nodes)
        self.assertEqual(subgraph.number_of_nodes(), 2)
        self.assertEqual(subgraph.number_of_edges(), 0)

    def test_create_sankey_html(self):
        output_path = "/tmp/test_sankey.html"
        create_sankey_html(self.graph, 'volume', output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            html_content = f.read()
        
        self.assertIn('T1', html_content)
        self.assertIn('F1', html_content)
        self.assertIn('T2', html_content)
        self.assertIn('F2', html_content)
        self.assertIn('100', html_content) # volume from T1->F1 and F1->T2
        self.assertIn('50', html_content) # volume from T2->F2
        
        os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
