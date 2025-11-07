# DFL Workflow System - Unified Architecture

## Executive Summary

The DFL Workflow System is a unified platform for scientific workflow analysis that consists of **two primary functions** built on a **shared graph construction foundation**:

1. **Function 1: Visualization & Analysis** - Interactive exploration and bottleneck identification
2. **Function 2: DPM Analysis & Optimization** - Storage configuration optimization and performance prediction

Both functions leverage the same robust Workflow Graph Builder to ensure consistency and maximize code reuse.

---

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DFL Workflow System                             │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │              SHARED FOUNDATION: Workflow Graph Builder           │ │
│  │                                                                  │ │
│  │  Input:                                                          │ │
│  │    • Workflow traces (BlockTrace + DatalifeTrace JSON)          │ │
│  │    • Workflow schema (task definitions, file patterns)          │ │
│  │                                                                  │ │
│  │  Core Components:                                               │ │
│  │    • data_parser.py  - Trace parsing & correlation             │ │
│  │    • graph_builder.py - DFL-DAG construction                    │ │
│  │       - Task Name Priority System (3-tier)                      │ │
│  │       - Adaptive Parallelism                                    │ │
│  │       - PID tracking (task PIDs, file read/write PIDs)         │ │
│  │       - On-demand file node creation                            │ │
│  │                                                                  │ │
│  │  Output: NetworkX DiGraph (Bipartite: Tasks ↔ Files)           │ │
│  │    Nodes: {type, pid/pids, stage_order, pos}                   │ │
│  │    Edges: {volume, op_count, rate}                             │ │
│  └───────────────────────┬──────────────────┬─────────────────────┘ │
│                          │                  │                        │
│              ┌───────────▼───────┐   ┌──────▼─────────────────┐    │
│              │   FUNCTION 1      │   │   FUNCTION 2           │    │
│              │   Visualization   │   │   DPM Analysis         │    │
│              │   & Analysis      │   │   & Optimization       │    │
│              └───────────────────┘   └────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Function 1: Visualization & Analysis

**Status:** ✅ **IMPLEMENTED (V1 Complete)**

### Purpose
Interactive exploration of workflow dataflow patterns, bottleneck identification, and critical path analysis.

### Pipeline
1. Load workflow using shared graph builder
2. Filter subgraphs by task/file selection
3. Calculate critical paths using GCPA (Generalized Critical Path Analysis)
4. Generate Sankey diagrams with Plotly
5. Export flow statistics and pattern analysis

### Key Features
- **Interactive Sankey Diagrams**
  - Edge widths proportional to volume/rate/op_count
  - Critical path highlighting (orange edges)
  - PID information on hover (task PIDs, file read/write PIDs)
  - Task range filtering (start_task to end_task)
  
- **Flow Statistics**
  - Total volume (producer/consumer)
  - Operation counts
  - Transfer rates
  - Per-stage breakdowns

- **Critical Path Analysis**
  - GCPA with selectable weight property
  - DFL Caterpillar Tree extension
  - Pattern identification (inter-task locality, data non-use)

### Components
```
src/dfl_mcp/
├── server.py                    # MCP server with 3 tools
├── analysis/
│   ├── sankey_utils.py         # Sankey generation & filtering
│   ├── metrics.py              # Flow statistics
│   ├── critical_path.py        # GCPA & pattern detection
│   └── task_ordering.py        # Topological ordering
```

### Output Examples
- `output/sankey_montage_full.html` - Full workflow Sankey (391 edges)
- `output/sankey_openmm_to_aggregate.html` - Filtered subgraph
- Summary text reports with aggregated metrics

### Example Results (V1)
- **DDMD workflow**: ~100 edges, 15 tasks
- **Montage workflow**: ~391 edges, 237 task instances (with Task Name Priority)

---

## Function 2: DPM Analysis & Optimization

**Status:** 🔨 **PLANNED (V2)**

### Purpose
Storage configuration optimization through performance prediction and data movement cost analysis.

### Pipeline
1. **Start with shared DFL-DAG** (from graph_builder)
2. **Load IOR Benchmark Data**
   - Parse raw IOR benchmark JSON files (`ior_utils.py`)
   - Create consolidated benchmark database (`updated_master_ior_df.csv`)
   - Benchmark dimensions: storage type, parallelism, file size, transfer size
   
3. **DPM Edge Augmentation**
   - For each edge in DFL-DAG, estimate performance for all storage×parallelism configs
   - Use 4D interpolation (`workflow_interpolation.py`) on benchmark data
   - **ADD** (not replace) DPM attributes to existing edge data:
   ```python
   # Original edge attributes remain unchanged:
   G.edges['task_0', 'file_A.h5'] = {
       'volume': 1000000,
       'op_count': 500,
       'rate': 50000
   }
   
   # DPM ADDS new attributes for producer-consumer storage pairs:
   G.edges['task_0', 'file_A.h5']['dpm'] = {
       # Key: (producer_storage, consumer_storage, num_nodes, tasks_per_node)
       ('ssd', 'beegfs', 4, 2): {'estimated_time': 10.5, 'trMiB': 95.2},
       ('ssd', 'ssd', 4, 2): {'estimated_time': 8.2, 'trMiB': 122.0},
       ('tmpfs', 'tmpfs', 4, 2): {'estimated_time': 6.1, 'trMiB': 164.0},
       ('beegfs', 'ssd', 4, 2): {'estimated_time': 9.8, 'trMiB': 102.0},
       ('beegfs', 'beegfs', 4, 2): {'estimated_time': 10.2, 'trMiB': 98.0},
       ('tmpfs', 'ssd', 4, 2): {'estimated_time': 7.5, 'trMiB': 133.3},
       ('tmpfs', 'beegfs', 4, 2): {'estimated_time': 11.8, 'trMiB': 84.7},
       ('ssd', 'tmpfs', 4, 2): {'estimated_time': 7.1, 'trMiB': 140.8},
       ('beegfs', 'tmpfs', 4, 2): {'estimated_time': 9.3, 'trMiB': 107.5}
   }
   ```

4. **Data Movement Stage Insertion**
   - Analyze optimal storage per workflow stage
   - When storage changes between stages, insert artificial data movement tasks
   - Example transformation:
   ```
   Original:
   Task_A (stage 0) → File_X → Task_B (stage 1)
   
   Optimized (if best storage differs):
   Task_A (stage 0, SSD) → File_X (SSD) → 
   [Data_Movement_Stage_0_to_1] (SSD→BeeGFS, cost: 2.3s) → 
   File_X' (BeeGFS) → 
   Task_B (stage 1, BeeGFS)
   ```

5. **Configuration Ranking**
   - Calculate total workflow I/O time for each storage configuration
   - Account for data movement overhead
   - Rank ALL configurations in ascending order (fastest=rank 1, slower=higher rank)
   - Output all ranked configurations (not just optimal)

### Key Features
- **4D Performance Interpolation**
  - Dimensions: storage type, num_nodes, tasks_per_node, file size, transfer size
  - Estimates performance for untested configurations
  - Based on IOR benchmark profiles

- **Multi-Storage Optimization**
  - Considers heterogeneous storage (BeeGFS, SSD, tmpfs)
  - Per-stage producer-consumer storage pairs
  - Data movement cost modeling

- **Configuration Ranking**
  - All producer×consumer storage×parallelism combinations evaluated
  - Ranked in ascending order by total workflow I/O time
  - Detailed performance breakdowns for each configuration

### Components
```
workflow_analysis/
├── workflow_analyzer.py            # Main DPM orchestrator
├── workflow_interpolation.py       # 4D interpolation engine
├── workflow_dpm_calculator.py      # Configuration ranking
├── workflow_data_staging.py        # Data movement insertion

perf_profiles/
├── ior_utils.py                    # IOR benchmark parsing
└── concat_csv_files.py             # Benchmark consolidation
```

### Data Models (DPM-Specific)

```python
class DPMConfiguration(BaseModel):
    producer_storage: str           # 'beegfs', 'ssd', 'tmpfs'
    consumer_storage: str           # 'beegfs', 'ssd', 'tmpfs'
    num_nodes: int
    tasks_per_node: int
    estimated_time: float           # seconds
    throughput_MiB: float           # MiB/s

# Type alias: (producer_storage, consumer_storage, num_nodes, tasks_per_node)
StorageConfig = Tuple[str, str, int, int]

class DPMEdgeData(BaseModel):
    # Original DFL properties - UNCHANGED by DPM
    volume: int
    op_count: int
    rate: float
    
    # DPM augmentation - ADDED by DPM analysis
    dpm: Dict[StorageConfig, DPMConfiguration]

class DPMConfigurationResult(BaseModel):
    """Result for a single storage configuration"""
    rank: int                       # 1=fastest, higher=slower
    stage_assignments: Dict[int, Tuple[str, str]]  # {stage: (prod_storage, cons_storage)}
    total_io_time: float
    data_movement_overhead: float
    data_movement_stages: List[Dict]

class DPMResult(BaseModel):
    """Complete DPM analysis with all configurations"""
    workflow_name: str
    ranked_configurations: List[DPMConfigurationResult]  # Ascending order
    total_configurations_evaluated: int
```

---

## Shared Foundation: Workflow Graph Builder

**Status:** ✅ **IMPLEMENTED**

### Core Components

#### 1. Data Parser (`data_parser.py`)
- Parses BlockTrace and DatalifeTrace JSON files
- Implements Task Name Priority System (3-tier)
- Correlates traces with optional datalife matching
- Approximates missing metrics (bytes = blocks × 4096)

#### 2. Graph Builder (`graph_builder.py`)
- Constructs bipartite DFL-DAG (Tasks ↔ Files)
- Implements Adaptive Parallelism (runtime PIDs vs schema)
- On-demand file node creation
- PID tracking for all nodes
- Node positioning for visualization

### Task Name Priority System

**3-Tier Priority Hierarchy:**
1. **Tier 1 (Highest):** Direct `task_name` from trace files
2. **Tier 2:** Schema pattern matching for write operations
3. **Tier 3:** Schema pattern matching for read operations

**Benefits:**
- Montage: 391 edges (vs 101 without priority)
- Handles runtime parallelism ≠ schema parallelism
- Works with incomplete datalife traces
- Maintains backward compatibility (DDMD)

### Graph Structure

**Nodes:**
```python
# Task node
{
    'type': 'task',
    'pid': 12345,
    'stage_order': 1,
    'pos': (1, 0)  # (x=stage*2-1, y=unique)
}

# File node
{
    'type': 'file',
    'write_pids': [12345, 12346],
    'read_pids': [12347, 12348, 12349],
    'pos': (2, 0)  # (x=producer_x+1, y=unique)
}
```

**Edges:**
```python
{
    # Original DFL properties (always present):
    'volume': 1000000,        # bytes
    'op_count': 500,          # number of I/O ops
    'rate': 50000,            # bytes/sec
    
    # DPM augmentation (ADDED by Function 2, does not modify above):
    'dpm': {
        ('ssd', 'beegfs', 4, 2): {'estimated_time': 10.5, 'trMiB': 95.2},
        ('tmpfs', 'tmpfs', 4, 2): {'estimated_time': 6.1, 'trMiB': 164.0},
        ('beegfs', 'ssd', 4, 2): {'estimated_time': 9.8, 'trMiB': 102.0},
        ('ssd', 'ssd', 4, 2): {'estimated_time': 8.2, 'trMiB': 122.0},
        ('beegfs', 'beegfs', 4, 2): {'estimated_time': 10.2, 'trMiB': 98.0},
        ('tmpfs', 'ssd', 4, 2): {'estimated_time': 7.5, 'trMiB': 133.3},
        ('tmpfs', 'beegfs', 4, 2): {'estimated_time': 11.8, 'trMiB': 84.7},
        ('ssd', 'tmpfs', 4, 2): {'estimated_time': 7.1, 'trMiB': 140.8},
        ('beegfs', 'tmpfs', 4, 2): {'estimated_time': 9.3, 'trMiB': 107.5}
    }
}
```

---

## Code Organization

### Current Structure (V1)
```
flow-viz-mcp/
├── src/dfl_mcp/
│   ├── server.py                   # MCP server (Function 1)
│   ├── data_parser.py             # SHARED
│   ├── graph_builder.py           # SHARED
│   ├── models.py                   # SHARED
│   └── analysis/                   # Function 1
│       ├── sankey_utils.py
│       ├── metrics.py
│       ├── critical_path.py
│       └── task_ordering.py
│
├── workflow_analysis/              # Function 2 (to be integrated)
│   ├── workflow_analyzer.py
│   ├── workflow_interpolation.py
│   ├── workflow_dpm_calculator.py
│   └── workflow_data_staging.py
│
├── perf_profiles/                  # Function 2 (benchmark data)
│   ├── ior_utils.py
│   └── concat_csv_files.py
│
├── input/                          # Benchmark data
│   ├── ior_data/                   # IOR benchmark results
│   ├── cp_data/                    # Copy operation data
│   └── updated_master_ior_df.csv  # Consolidated benchmarks
│
├── workflow_traces/                # Workflow trace data
│   ├── ddmd/
│   └── montage/
│
└── docs/
    ├── v1_spec.md                  # Function 1 spec
    └── spec.md                     # Unified architecture (this system)
```

### Proposed Integration (V2)
```
src/dfl_mcp/
├── server.py                       # Main MCP server
├── data_parser.py                 # SHARED
├── graph_builder.py               # SHARED
├── models.py                       # SHARED (augmented with DPM models)
├── analysis/                       # Function 1
│   └── ...
└── dpm/                            # Function 2 (NEW)
    ├── __init__.py
    ├── benchmark_loader.py         # IOR benchmark parsing
    ├── interpolation.py            # 4D interpolation
    ├── augmenter.py                # Edge augmentation
    ├── staging.py                  # Data movement insertion
    └── ranking.py                  # Configuration ranking
```

---

## Key Design Decisions

### 1. Shared Foundation
**Rationale:** Both functions need accurate workflow structure
**Benefit:** Single, well-tested implementation; consistency across functions

### 2. Function Separation
**Rationale:** Different concerns (visualization vs prediction)
**Benefit:** Functions can be used independently; clean separation

### 3. Edge Augmentation (not node)
**Rationale:** DPM is fundamentally about data transfer performance
**Benefit:** DPM data naturally belongs on edges (Task→File, File→Task)

### 4. Data Movement as Artificial Stages
**Rationale:** Storage changes incur real cost
**Benefit:** Accurately models cross-storage transfers in total time calculation

### 5. 4D Interpolation
**Rationale:** Can't benchmark all configurations
**Benefit:** Predicts performance for untested scenarios

---

## Implementation Status

### ✅ Completed (V1)
- [x] Shared graph builder with Task Name Priority
- [x] Adaptive parallelism
- [x] Function 1: Sankey visualization
- [x] Function 1: Flow statistics
- [x] Function 1: Critical path analysis
- [x] MCP server with 3 tools
- [x] Interactive CLI
- [x] Multi-workflow support

### 🔨 In Progress / Planned (V2)
- [ ] Integrate DPM components into unified codebase
- [ ] Function 2: IOR benchmark loader
- [ ] Function 2: 4D interpolation engine
- [ ] Function 2: Edge augmentation with DPM configs
- [ ] Function 2: Data movement stage insertion
- [ ] Function 2: Configuration ranking
- [ ] MCP tools for DPM analysis
- [ ] Combined visualization (show optimal storage on Sankey)

---

## Usage Examples

### Function 1: Visualization (Current)
```python
# Via MCP server
result = server.get_sankey_data(
    workflow_name='montage',
    start_task_id='mProject',
    end_task_id='mViewer',
    metric='volume',
    highlight_critical_path=True
)
# → generates output/sankey_mProject_to_mViewer.html
```

### Function 2: DPM Analysis (Planned)
```python
# Via DPM analyzer
result = dpm_analyzer.analyze_workflow(
    workflow_name='ddmd',
    benchmark_data='input/updated_master_ior_df.csv'
)
# → returns DPMResult with:
#   - ALL storage configurations ranked in ascending order
#   - Per-stage producer-consumer storage assignments for each config
#   - Data movement overhead per config
#   - Performance predictions per config

print(f"Workflow: {result.workflow_name}")
# Workflow: ddmd_4n_l

print(f"Total configs evaluated: {result.total_configurations_evaluated}")
# Total configs evaluated: 486

# =====================================================
# Rank 1 = fastest configuration
# =====================================================
config_1 = result.ranked_configurations[0]
print(f"Rank {config_1['rank']}: {config_1['total_io_time']}s")
# Rank 1: 145.3s

print("Stage assignments:")
for stage, (prod, cons) in config_1['stage_assignments'].items():
    print(f"  Stage {stage}: {prod} → {cons}")
# Stage assignments:
#   Stage 0: tmpfs → tmpfs
#   Stage 1: tmpfs → ssd
#   Stage 2: ssd → ssd
#   Stage 3: ssd → tmpfs

print(f"Data movement overhead: {config_1['data_movement_overhead']}s")
# Data movement overhead: 5.7s

print(f"Data movements: {len(config_1['data_movement_stages'])}")
for dm in config_1['data_movement_stages']:
    print(f"  Stage {dm['from_stage']}→{dm['to_stage']}: "
          f"{dm['source_storage']}→{dm['dest_storage']}, "
          f"{dm['file_size_mb']} MB, {dm['movement_time']}s")
# Data movements: 2
#   Stage 1→2: tmpfs→ssd, 1024.5 MB, 3.2s
#   Stage 2→3: ssd→tmpfs, 512.3 MB, 2.5s

# =====================================================
# Rank 2 = second fastest
# =====================================================
config_2 = result.ranked_configurations[1]
print(f"\nRank {config_2['rank']}: {config_2['total_io_time']}s")
# Rank 2: 152.8s

print("Stage assignments:")
for stage, (prod, cons) in config_2['stage_assignments'].items():
    print(f"  Stage {stage}: {prod} → {cons}")
# Stage assignments:
#   Stage 0: tmpfs → tmpfs
#   Stage 1: tmpfs → tmpfs
#   Stage 2: tmpfs → ssd
#   Stage 3: ssd → ssd

print(f"Data movement overhead: {config_2['data_movement_overhead']}s")
# Data movement overhead: 8.3s

# =====================================================
# Rank 3 = third fastest (all same storage)
# =====================================================
config_3 = result.ranked_configurations[2]
print(f"\nRank {config_3['rank']}: {config_3['total_io_time']}s")
# Rank 3: 158.1s

print("Stage assignments:")
for stage, (prod, cons) in config_3['stage_assignments'].items():
    print(f"  Stage {stage}: {prod} → {cons}")
# Stage assignments:
#   Stage 0: ssd → ssd
#   Stage 1: ssd → ssd
#   Stage 2: ssd → ssd
#   Stage 3: ssd → ssd

print(f"Data movement overhead: {config_3['data_movement_overhead']}s")
# Data movement overhead: 0.0s (no cross-storage movement)

print(f"Data movements: {len(config_3['data_movement_stages'])}")
# Data movements: 0

# =====================================================
# Rank 486 = slowest configuration
# =====================================================
config_486 = result.ranked_configurations[485]
print(f"\nRank {config_486['rank']}: {config_486['total_io_time']}s")
# Rank 486: 487.9s

print("Stage assignments:")
for stage, (prod, cons) in config_486['stage_assignments'].items():
    print(f"  Stage {stage}: {prod} → {cons}")
# Stage assignments:
#   Stage 0: beegfs → tmpfs
#   Stage 1: tmpfs → beegfs
#   Stage 2: beegfs → tmpfs
#   Stage 3: tmpfs → beegfs

print(f"Data movement overhead: {config_486['data_movement_overhead']}s")
# Data movement overhead: 125.3s (high cost of alternating storage)

print(f"Data movements: {len(config_486['data_movement_stages'])}")
# Data movements: 3
```

---

## Next Steps

### V2 Integration Roadmap

1. **Phase 1: Code Integration** (1-2 weeks)
   - Move `workflow_analysis/` → `src/dfl_mcp/dpm/`
   - Move `perf_profiles/` → `src/dfl_mcp/dpm/benchmarks/`
   - Update imports and dependencies

2. **Phase 2: Data Model Unification** (1 week)
   - Add DPM models to `models.py`
   - Define `DPMEdgeData`, `DPMConfiguration`, `DPMResult`
   - Update graph builder to support optional DPM augmentation

3. **Phase 3: DPM Pipeline Implementation** (2-3 weeks)
   - Implement `augment_dag_with_dpm()`
   - Implement `insert_data_movement_stages()`
   - Implement `rank_configurations()`
   - Add unit tests for each component

4. **Phase 4: MCP Tool Exposure** (1 week)
   - Add `run_dpm_analysis` MCP tool
   - Add `get_optimization_recommendations` MCP tool
   - Update server documentation

5. **Phase 5: Visualization Integration** (1 week)
   - Enhance Sankey to show optimal storage assignments
   - Color-code nodes/edges by storage type
   - Show data movement stages in visualization

---

## References

- **V1 Specification:** `docs/v1_spec.md` - Detailed Function 1 spec
- **Unified Specification:** `spec.md` - This architecture document
- **Session History:** `sessions/cursor-nov-4-2025.txt` - V1 implementation details
- **TODO List:** `docs/TODO.md` - Future enhancements
