# Future Enhancements TODO

This document outlines potential improvements and new features for the DFL Visualization MCP Server.

---

## Priority Recommendations

Based on current workflow analysis needs, these features would provide the most immediate value:

### Priority 1: Multi-Format Trace Support (HDF5 Traces)
**Critical Need:** Extend the system to handle different trace formats beyond JSON.

**Description:** Add support for HDF5-based I/O traces, which are common in high-performance computing workflows. HDF5 traces often contain richer temporal and spatial data about I/O operations.

**Key Features:**
- Parse HDF5 trace files with hierarchical structure
- Extract task metadata, I/O operations, and timing information
- Support both single-file and multi-file HDF5 trace formats
- Maintain backward compatibility with JSON traces
- Auto-detect trace format and use appropriate parser

**Implementation Approach:**
```python
class HDF5TraceParser:
    """Parser for HDF5-based workflow traces."""
    
    def parse_hdf5_traces(self, trace_file: str) -> List[CorrelatedTrace]:
        """
        Parse HDF5 traces and convert to CorrelatedTrace format.
        
        Args:
            trace_file: Path to HDF5 trace file
            
        Returns:
            List of CorrelatedTrace objects compatible with existing system
        """
```

**Technical Considerations:**
- Use `h5py` library for HDF5 reading
- Map HDF5 schema to existing `CorrelatedTrace` model
- Handle large HDF5 files efficiently (chunked reading)
- Support compressed HDF5 traces
- Document HDF5 trace structure requirements

---

### Priority 2: Multi-Schema Workflow Definition Support
**Critical Need:** Support workflow definitions from different workflow management systems, not just custom JSON schemas.

**Description:** Enable the system to parse workflow structures from multiple sources including Pegasus WMS, Python code analysis, and potentially other workflow systems (Nextflow, Snakemake, etc.).

**Key Features:**

#### A. Pegasus WMS Support
- Parse Pegasus DAX (DAG in XML) files
- Extract task dependencies and data flow
- Map Pegasus jobs to DFL tasks
- Handle abstract vs concrete workflows
- Support Pegasus transformation catalog

**Implementation:**
```python
class PegasusSchemaLoader:
    """Load workflow schema from Pegasus DAX files."""
    
    def load_pegasus_dax(self, dax_file: str) -> WorkflowSchema:
        """
        Parse Pegasus DAX and convert to WorkflowSchema.
        
        Args:
            dax_file: Path to Pegasus DAX XML file
            
        Returns:
            WorkflowSchema compatible with existing system
        """
```

#### B. Python Code Analysis
- Static analysis of Python workflow scripts
- Extract task definitions from popular frameworks (Dask, Prefect, Airflow, Parsl)
- Infer data dependencies from function arguments
- Build workflow schema from code structure

**Implementation:**
```python
class PythonWorkflowAnalyzer:
    """Analyze Python workflow code to extract structure."""
    
    def analyze_python_workflow(self, script_path: str) -> WorkflowSchema:
        """
        Use AST parsing to extract workflow structure from Python code.
        
        Supports:
        - Dask delayed/futures
        - Parsl apps
        - Prefect tasks
        - Custom function decorators
        """
```

#### C. Generic Schema Adapters
- Plugin architecture for adding new schema formats
- Schema format auto-detection
- Validation and error reporting
- Schema conversion utilities

**Technical Considerations:**
- Use `xml.etree.ElementTree` for Pegasus DAX parsing
- Use Python `ast` module for code analysis
- Maintain schema versioning for compatibility
- Document schema mapping rules clearly

---

### Priority 3: User-Defined Workflow Input
**Critical Need:** Allow users to build workflow DAGs without pre-existing trace files or schemas, enabling manual workflow design and what-if analysis.

**Description:** Provide interactive and file-based methods for users to define workflow structure, enabling workflow design before execution or analysis of hypothetical workflows.

**Key Features:**

#### A. Interactive Terminal Dialog
- Step-by-step workflow builder in CLI
- Guide user through defining tasks, files, and dependencies
- Validate workflow structure as it's built
- Save completed workflow for reuse

**Implementation:**
```python
def interactive_workflow_builder():
    """
    Interactive CLI workflow builder.
    
    Workflow:
    1. Enter workflow name
    2. Define tasks (name, stage, parallelism)
    3. Define files (name, size estimate)
    4. Define dependencies (task -> file -> task)
    5. Add I/O estimates (volume, op_count)
    6. Validate and save
    """
```

**Example Dialog:**
```
Welcome to Workflow Builder!

Workflow name: my_analysis

Step 1: Define Tasks
--------------------
Task 1 name: preprocess
  Stage order: 1
  Parallelism: 4
  
Add another task? (y/n): y

Task 2 name: analysis
  Stage order: 2
  Parallelism: 1

Step 2: Define Data Flow
-------------------------
preprocess outputs:
  1. intermediate_data.h5 (estimated size: 10 GB)
  
analysis inputs:
  Select from: [intermediate_data.h5]
  Selected: intermediate_data.h5

[Workflow structure validated]
Save to: my_analysis_schema.json
```

#### B. CSV/JSON Input Files
- Support structured input formats
- Define workflow as data tables
- Import/export for Excel/spreadsheet editing

**CSV Format Option:**
```csv
# tasks.csv
task_name,stage_order,parallelism
preprocess,1,4
analysis,2,1
postprocess,3,1

# files.csv
file_name,producer_task,size_mb
intermediate_data.h5,preprocess,10000
results.h5,analysis,5000

# connections.csv
from_task,to_file,to_task,volume_mb,op_count
preprocess,intermediate_data.h5,,10000,5000
,intermediate_data.h5,analysis,10000,5000
```

**JSON Format Option:**
```json
{
  "workflow_name": "my_analysis",
  "tasks": [
    {
      "name": "preprocess",
      "stage_order": 1,
      "parallelism": 4,
      "outputs": ["intermediate_data.h5"]
    },
    {
      "name": "analysis", 
      "stage_order": 2,
      "parallelism": 1,
      "inputs": ["intermediate_data.h5"],
      "outputs": ["results.h5"]
    }
  ],
  "edges": [
    {
      "from": "preprocess",
      "to": "analysis",
      "via": "intermediate_data.h5",
      "volume_mb": 10000,
      "op_count": 5000
    }
  ]
}
```

**Implementation:**
```python
class UserDefinedWorkflowLoader:
    """Load workflows from user-provided definitions."""
    
    def load_from_csv(self, tasks_file: str, files_file: str, 
                      connections_file: str) -> WorkflowSchema:
        """Load workflow from CSV files."""
        
    def load_from_json(self, workflow_file: str) -> WorkflowSchema:
        """Load workflow from JSON definition."""
        
    def validate_workflow(self, schema: WorkflowSchema) -> bool:
        """Validate user-defined workflow for consistency."""
```

#### C. Workflow Templates
- Pre-built templates for common workflow patterns
- MapReduce, Pipeline, Fork-Join, etc.
- Customizable parameters

**CLI Integration:**
```
Main Menu:
  ...
  6. Build Custom Workflow
     a. Interactive builder
     b. Import from CSV
     c. Import from JSON
     d. Use template
  ...
```

**Technical Considerations:**
- Input validation (cycle detection, missing dependencies)
- Reasonable defaults for missing metrics
- Schema compatibility with existing system
- Export to standard format for reuse
- Template library with examples

**Use Cases:**
- Design workflows before implementation
- What-if analysis with hypothetical workflows
- Teaching/demonstration workflows
- Prototype testing
- Documentation and planning

---

### Priority 4: Bottleneck Detection Tool
Most immediately useful for understanding where workflows are slow and identifying optimization opportunities.

### Priority 5: Timeline/Gantt Chart Visualization
Complements existing Sankey diagram by showing temporal aspects of workflow execution.

### Priority 6: Parallel Efficiency Analysis
Analyzes load balance across parallel task instances (e.g., 12 parallel openmm instances).

---

## 1. Enhanced Task Filtering Options

### A. Pattern Matching
Support for advanced task selection patterns:

**Features:**
- Wildcard support: `openmm_*` for all openmm instances
- Regex patterns: `openmm_[0-5]` for instances 0-5
- Range notation: `openmm:0-5` for instances 0 through 5

**Use Cases:**
- "Show me only the first 3 instances of each task"
- "Analyze odd-numbered task instances"
- "Filter tasks matching a specific naming pattern"

**Implementation:**
```python
def parse_task_pattern(pattern: str, dag: nx.DiGraph) -> List[str]:
    """
    Parse task patterns and return matching task IDs.
    
    Supported formats:
    - openmm_* : All instances of openmm
    - openmm_[0-5] : Specific range using regex
    - openmm:0-5 : Range notation
    """
```

---

### B. Stage-Based Filtering
Filter tasks by workflow stage number:

**Features:**
- Select all tasks in specific stages: `stage:0,1`
- Range selection: `stage:0-2`
- Useful for phase-based analysis

**Implementation:**
```python
def filter_by_stage(workflow_name: str, stages: List[int]) -> List[str]:
    """
    Return all tasks in specified stages.
    
    Args:
        workflow_name: Name of workflow
        stages: List of stage indices (e.g., [0, 1, 2])
    """
```

---

## 2. New Analysis Tools

### A. Bottleneck Detection Tool ? (Priority 1)

**Description:**
Automatically identifies performance bottlenecks in workflow execution.

**Tool Contract:**
```python
def detect_bottlenecks(
    workflow_name: str,
    threshold: float = 0.8,
    metric: str = 'volume'
) -> dict:
    """
    Identifies performance bottlenecks in the workflow.
    
    Args:
        workflow_name: Name of workflow to analyze
        threshold: Percentile threshold for bottleneck detection (0.0-1.0)
        metric: Metric to analyze ('volume', 'op_count', 'rate', 'time')
    
    Returns:
        {
            'bottleneck_tasks': [
                {'task': 'openmm_5', 'value': 1234, 'percentile': 0.95}
            ],
            'bottleneck_files': [
                {'file': 'aggregated.h5', 'volume': 5678, 'readers': 3}
            ],
            'stage_utilization': {
                'stage_0': {'duration': 120, 'efficiency': 0.85}
            },
            'recommendations': [
                'Consider parallelizing aggregate task',
                'Optimize I/O for aggregated.h5'
            ]
        }
    """
```

**Features:**
- Tasks with longest execution times
- Files with highest I/O volume
- Stage utilization analysis
- Ranked list of optimization opportunities
- Automated recommendations

---

### B. Parallel Efficiency Analysis ? (Priority 3)

**Description:**
Analyzes how well parallel task instances perform and identifies load imbalances.

**Tool Contract:**
```python
def analyze_parallel_efficiency(
    workflow_name: str,
    task_name: str
) -> dict:
    """
    Analyzes parallel task performance and load balance.
    
    Args:
        workflow_name: Name of workflow
        task_name: Task to analyze (e.g., 'openmm')
    
    Returns:
        {
            'task_name': 'openmm',
            'parallelism': 12,
            'instances': [
                {'id': 'openmm_0', 'volume': 1000, 'ops': 500, 'time': 10},
                ...
            ],
            'statistics': {
                'mean_volume': 1050,
                'std_dev': 120,
                'coefficient_of_variation': 0.114
            },
            'load_balance': {
                'imbalance_factor': 1.15,
                'underutilized_instances': ['openmm_3', 'openmm_7'],
                'overutilized_instances': ['openmm_0', 'openmm_11']
            },
            'recommendations': [
                'Load imbalance detected: 15% variation',
                'Consider work stealing or dynamic scheduling'
            ]
        }
    """
```

**Features:**
- Load balance across instances
- Variance in execution time and I/O volume
- Identification of underutilized instances
- Coefficient of variation calculation
- Efficiency scores

---

### C. Data Reuse Pattern Analysis

**Description:**
Identifies data reuse patterns and opportunities for caching or optimization.

**Tool Contract:**
```python
def analyze_data_reuse(
    workflow_name: str,
    min_reuse_count: int = 2
) -> dict:
    """
    Identifies data reuse patterns and caching opportunities.
    
    Args:
        workflow_name: Name of workflow
        min_reuse_count: Minimum number of reads to flag as reused
    
    Returns:
        {
            'highly_reused_files': [
                {
                    'file': 'stage0000_task0000.h5',
                    'readers': ['aggregate_0', 'training_0', 'inference_0'],
                    'read_count': 15,
                    'total_volume': 5000000000
                }
            ],
            'single_use_files': [
                {'file': 'temp_data.h5', 'reader': 'openmm_5'}
            ],
            'caching_opportunities': [
                {
                    'file': 'aggregated.h5',
                    'potential_savings': '45% reduced I/O',
                    'cache_size_needed': '2.5 GB'
                }
            ],
            'access_patterns': {
                'sequential': 25,
                'random': 8,
                'broadcast': 3
            }
        }
    """
```

**Features:**
- Files read by multiple tasks
- Potential for caching
- Data access patterns (sequential, random, broadcast)
- Estimated performance impact
- Cache size recommendations

---

## 3. New Visualization Features

### A. Timeline/Gantt Chart View ? (Priority 2)

**Description:**
Interactive timeline showing task execution over time with parallel execution visualization.

**Tool Contract:**
```python
def generate_timeline(
    workflow_name: str,
    output_file: str = 'timeline.html',
    time_metric: str = 'cumulative'
) -> str:
    """
    Generates an interactive timeline/Gantt chart visualization.
    
    Args:
        workflow_name: Name of workflow
        output_file: HTML output filename
        time_metric: 'cumulative', 'wall_clock', or 'cpu_time'
    
    Returns:
        Path to generated HTML file
    """
```

**Features:**
- Show task execution over time (Gantt chart style)
- Visualize parallel execution and idle time
- Interactive zoom and pan
- Highlight critical path on timeline
- Color-code by stage or task type
- Show dependencies as arrows
- Display idle/wait time gaps

**Visualization Elements:**
- X-axis: Time
- Y-axis: Task instances
- Bar length: Task duration
- Bar color: Task type or stage
- Gaps: Idle time or waiting for dependencies

---

### B. Heatmap Visualization

**Description:**
Color-coded heatmap showing I/O intensity and resource usage patterns.

**Tool Contract:**
```python
def generate_heatmap(
    workflow_name: str,
    metric: str = 'volume',
    output_file: str = 'heatmap.html'
) -> str:
    """
    Generates an interactive heatmap visualization.
    
    Args:
        workflow_name: Name of workflow
        metric: 'volume', 'op_count', 'rate', 'time'
        output_file: HTML output filename
    
    Returns:
        Path to generated HTML file
    """
```

**Features:**
- I/O intensity heatmap per task/file
- Stage-by-stage resource usage
- Color-coded performance metrics (green=low, red=high)
- Matrix view: tasks ? files
- Interactive tooltips with exact values
- Downloadable as PNG/SVG

---

### C. Comparison Mode

**Description:**
Side-by-side comparison of two workflow runs or configurations.

**Tool Contract:**
```python
def compare_workflows(
    workflow_name_1: str,
    workflow_name_2: str,
    output_file: str = 'comparison.html'
) -> str:
    """
    Generates a comparison visualization of two workflows.
    
    Args:
        workflow_name_1: First workflow (baseline)
        workflow_name_2: Second workflow (comparison)
        output_file: HTML output filename
    
    Returns:
        Path to generated HTML file with comparison report
    """
```

**Features:**
- Compare two workflow runs side-by-side
- Show differences in performance metrics
- Highlight regressions (slower) in red
- Highlight improvements (faster) in green
- Delta calculations and percentages
- Statistical significance testing

---

## 4. Data Export & Integration

### A. Export Capabilities

**Tool Contract:**
```python
def export_workflow_data(
    workflow_name: str,
    format: str,
    output_file: str = None
) -> str:
    """
    Export workflow data in various formats for external analysis.
    
    Args:
        workflow_name: Name of workflow
        format: 'csv', 'json', 'graphml', 'parquet', 'dot'
        output_file: Output filename (auto-generated if None)
    
    Returns:
        Path to exported file
    """
```

**Supported Formats:**
- **CSV**: Node and edge data tables for spreadsheets
  - `nodes.csv`: task_id, type, stage, parallelism, volume, ops
  - `edges.csv`: source, target, volume, op_count, rate
- **JSON**: Complete graph structure with all metadata
- **GraphML**: For external graph analysis tools (Gephi, Cytoscape)
- **Parquet**: Columnar format for data science workflows (pandas, Arrow)
- **DOT**: GraphViz format for static visualizations

**Use Cases:**
- Import into Excel/Google Sheets for custom analysis
- Load into Jupyter notebooks
- Use with graph analysis tools
- Archive for long-term storage

---

### B. Query Interface

**Tool Contract:**
```python
def query_workflow(
    workflow_name: str,
    query: str
) -> dict:
    """
    SQL-like queries on workflow data.
    
    Args:
        workflow_name: Name of workflow
        query: Query string (SQL-like syntax)
    
    Returns:
        Query results as dictionary
    """
```

**Query Examples:**
```sql
-- Find high-volume tasks
SELECT tasks WHERE volume > 1GB

-- Find files read by multiple tasks
SELECT files WHERE read_count > 5

-- Find slow I/O operations
SELECT edges WHERE rate < 10 MB/s

-- Find tasks in critical path
SELECT tasks WHERE in_critical_path = true

-- Aggregate statistics
SELECT AVG(volume), MAX(op_count) FROM tasks WHERE stage = 0
```

**Features:**
- SQL-like syntax (SELECT, WHERE, ORDER BY, LIMIT)
- Aggregation functions (SUM, AVG, MIN, MAX, COUNT)
- Filtering and sorting
- Join operations across tasks/files/edges
- Return results as JSON or DataFrame

---

## 5. Interactive CLI Enhancements

### A. Task Selection Helper

**Features:**
- Show suggested common ranges after listing tasks
  ```
  Suggested ranges:
    1. Full workflow: openmm inference
    2. Initial stage: openmm aggregate
    3. ML pipeline: aggregate training
  ```
- Auto-complete task names (tab completion)
- Command history (up/down arrows)
- Save favorite filters for quick reuse

**Implementation:**
```python
def get_common_ranges(workflow_name: str) -> List[dict]:
    """
    Suggest common task ranges based on workflow structure.
    
    Returns list of:
    - {'name': 'Full workflow', 'start': 'openmm', 'end': 'inference'}
    """
```

---

### B. Batch Processing

**Features:**
- Generate multiple Sankey diagrams at once
- Batch analysis for all task pairs
- Automated report generation
- Scheduled/cron job support

**Tool Contract:**
```python
def batch_generate_diagrams(
    workflow_name: str,
    ranges: List[dict],
    output_dir: str = 'batch_output'
) -> dict:
    """
    Generate multiple visualizations in batch.
    
    Args:
        workflow_name: Name of workflow
        ranges: List of {'start': 'task1', 'end': 'task2'}
        output_dir: Directory for outputs
    
    Returns:
        Summary of generated files
    """
```

**CLI Menu Option:**
```
5. Batch Operations
   a. Generate all stage-to-stage diagrams
   b. Generate reports for all tasks
   c. Export all data formats
```

---

### C. Watch Mode

**Features:**
- Monitor `workflow_traces/` folder for new traces
- Auto-regenerate visualizations when data changes
- Real-time updates during workflow execution
- Desktop notifications on completion

**Tool Contract:**
```python
def watch_mode(
    workflow_name: str,
    auto_refresh: bool = True,
    interval: int = 5
) -> None:
    """
    Watch for workflow trace updates and auto-regenerate.
    
    Args:
        workflow_name: Workflow to monitor
        auto_refresh: Automatically regenerate visualizations
        interval: Check interval in seconds
    """
```

**CLI Usage:**
```bash
python interactive_cli.py --watch ddmd
# Monitors ddmd workflow and regenerates on changes
```

---

## 6. Advanced Analysis Features

### A. What-If Analysis

**Tool Contract:**
```python
def simulate_optimization(
    workflow_name: str,
    changes: dict
) -> dict:
    """
    Simulate workflow changes before implementation.
    
    Args:
        workflow_name: Name of workflow
        changes: Dictionary of proposed changes
            {
                'parallelism': {'openmm': 24},  # Increase from 12 to 24
                'storage_speed': 2.0,            # 2x faster I/O
                'task_duration': {'aggregate': 0.5}  # 50% faster
            }
    
    Returns:
        {
            'baseline': {'total_time': 120, 'total_volume': 5000},
            'simulated': {'total_time': 85, 'total_volume': 5000},
            'improvement': {'time_saved': 35, 'percent': 29.2},
            'recommendations': [...]
        }
    """
```

**Simulation Types:**
- Parallelism changes
- Storage/network speed improvements
- Task optimization effects
- Resource allocation changes

---

### B. Recommendation Engine

**Tool Contract:**
```python
def get_optimization_recommendations(
    workflow_name: str,
    max_recommendations: int = 5,
    optimization_goal: str = 'time'
) -> list:
    """
    AI-powered recommendations for workflow optimization.
    
    Args:
        workflow_name: Name of workflow
        max_recommendations: Maximum number of suggestions
        optimization_goal: 'time', 'cost', 'efficiency', 'throughput'
    
    Returns:
        [
            {
                'priority': 1,
                'type': 'parallelism',
                'suggestion': 'Increase openmm parallelism from 12 to 16',
                'expected_improvement': '15% faster',
                'estimated_effort': 'low',
                'rationale': 'Task is CPU-bound with good scalability'
            },
            ...
        ]
    """
```

**Recommendation Types:**
- Parallelism adjustments
- I/O optimization opportunities
- Task reordering suggestions
- Caching strategies
- Resource allocation

**Ranking Criteria:**
- Expected performance impact
- Implementation difficulty
- Cost-benefit ratio
- Risk assessment

---

### C. Anomaly Detection

**Tool Contract:**
```python
def detect_anomalies(
    workflow_name: str,
    sensitivity: float = 2.0
) -> dict:
    """
    Detect unusual patterns in workflow execution.
    
    Args:
        workflow_name: Name of workflow
        sensitivity: Standard deviations for outlier detection
    
    Returns:
        {
            'task_anomalies': [
                {
                    'task': 'openmm_7',
                    'metric': 'duration',
                    'expected': 10.5,
                    'actual': 25.3,
                    'severity': 'high',
                    'possible_causes': ['I/O contention', 'Node failure']
                }
            ],
            'io_anomalies': [
                {
                    'file': 'stage0005_task0003.h5',
                    'metric': 'rate',
                    'anomaly_type': 'slow_write',
                    'details': '90% slower than average'
                }
            ],
            'pattern_anomalies': [
                {
                    'pattern': 'Unexpected data dependency',
                    'description': 'training reads from inference output'
                }
            ]
        }
    """
```

**Detection Methods:**
- Statistical outlier detection (z-score, IQR)
- Pattern recognition
- Time-series analysis
- Comparative analysis with historical runs

---

## 7. Multi-Workflow Analysis

### A. Cross-Workflow Comparison

**Tool Contract:**
```python
def compare_workflow_types(
    workflow_names: List[str],
    output_file: str = 'cross_comparison.html'
) -> str:
    """
    Compare different workflow types (e.g., ddmd vs montage).
    
    Args:
        workflow_names: List of workflows to compare
        output_file: HTML report output
    
    Returns:
        Path to comparison report
    """
```

**Features:**
- Compare ddmd vs montage workflows
- Identify common patterns across workflows
- Performance benchmarking
- Resource utilization comparison
- Best practices identification

---

### B. Workflow Evolution Tracking

**Tool Contract:**
```python
def track_workflow_evolution(
    workflow_name: str,
    versions: List[str]
) -> dict:
    """
    Track how a workflow changes over time across versions.
    
    Args:
        workflow_name: Base workflow name
        versions: List of version identifiers
    
    Returns:
        Evolution analysis with trends and changes
    """
```

**Features:**
- Track workflow changes over time
- Version-to-version comparison
- Performance trends (improving/degrading)
- Structural changes (added/removed tasks)
- Automated changelog generation

---

## 8. Enhanced Critical Path Features

### A. Critical Path Variants

**Tool Contract:**
```python
def find_top_k_paths(
    workflow_name: str,
    start_task: str,
    end_task: str,
    k: int = 3,
    metric: str = 'volume'
) -> list:
    """
    Find top K longest paths between tasks.
    
    Args:
        workflow_name: Name of workflow
        start_task: Starting task
        end_task: Ending task
        k: Number of paths to return
        metric: Weight metric
    
    Returns:
        List of top K paths with weights and analysis
    """
```

**Features:**
- Multiple critical paths (top 3 longest)
- Critical path with different metrics (time vs volume vs ops)
- Path diversity analysis
- Alternative route identification

---

### B. Path Exploration

**Tool Contract:**
```python
def explore_paths(
    workflow_name: str,
    start: str,
    end: str,
    max_paths: int = 10
) -> dict:
    """
    Find and analyze all paths between two tasks.
    
    Args:
        workflow_name: Name of workflow
        start: Starting task
        end: Ending task
        max_paths: Maximum paths to enumerate
    
    Returns:
        {
            'path_count': 15,
            'paths': [
                {
                    'nodes': ['openmm_0', 'file1.h5', 'aggregate_0'],
                    'length': 2,
                    'weight': 1500,
                    'parallel_portions': ['openmm_0 to file1.h5'],
                    'sequential_portions': ['file1.h5 to aggregate_0']
                }
            ],
            'statistics': {
                'avg_path_length': 3.2,
                'longest_path_length': 5,
                'shortest_path_length': 2
            }
        }
    """
```

**Features:**
- All simple paths between tasks
- Path lengths and weights
- Parallel vs sequential portions identification
- Path redundancy analysis
- Fault tolerance assessment (multiple paths = redundancy)

---

## Implementation Priority

### Phase 1: Core Analysis Tools (1-2 weeks)
- ? Bottleneck Detection
- ? Parallel Efficiency Analysis
- ? Data Reuse Pattern Analysis

### Phase 2: New Visualizations (1-2 weeks)
- ? Timeline/Gantt Chart
- ? Heatmap Visualization
- Export Capabilities (CSV, JSON)

### Phase 3: Advanced Features (2-3 weeks)
- What-If Analysis
- Recommendation Engine
- Anomaly Detection

### Phase 4: Integration & UX (1 week)
- CLI Enhancements (auto-complete, history)
- Batch Processing
- Watch Mode

### Phase 5: Multi-Workflow Support (1-2 weeks)
- Cross-Workflow Comparison
- Workflow Evolution Tracking

---

## Notes

- All new tools should follow the existing MCP protocol
- Maintain backward compatibility with current API
- Add comprehensive tests for each new feature
- Update `spec.md` with new tool contracts
- Extend `FILTERING_GUIDE.md` for new filtering options
- Consider performance impact for large workflows
- Ensure all visualizations are accessible and responsive

---

## Questions for Implementation

Before implementing each feature, consider:

1. **Data Requirements**: What additional trace data is needed?
2. **Performance**: Will this scale to large workflows (1000+ tasks)?
3. **User Interface**: How will users interact with this feature?
4. **Output Format**: What's the most useful way to present results?
5. **Dependencies**: Are new libraries required?
6. **Testing**: How can we validate correctness?
7. **Documentation**: What examples and use cases should we document?

---

*This TODO list is a living document. Features can be added, removed, or reprioritized based on user feedback and evolving requirements.*
