# Task Filtering Input Format Guide

## Quick Start: List Tasks and Generate Sankey Diagram

The easiest workflow:

1. Select **Option 4: List Available Tasks**
2. View the unique task names (e.g., openmm, aggregate, training, inference)
3. Enter two task names separated by space: `openmm training`
4. Sankey diagram is automatically generated!

**Output file naming**: `sankey_<start_task>_to_<end_task>.html`

Example: `sankey_openmm_to_training.html`

---

## Input Formats by Menu Option

### Option 1: Generate Sankey Diagram (Full Control)

This menu provides step-by-step prompts:

**Task Range Filtering:**
```
Filter by task range (y/n): y
  Start task ID (e.g., openmm_0): openmm_0
  End task ID (e.g., aggregate_0): training_0
```

**Format**: 
- `<task_name>_<instance_index>` (e.g., `openmm_0`, `aggregate_0`)
- Instance index is always 0 for single-instance tasks
- For parallel tasks like openmm (parallelism: 12), use any index from 0-11

**What it does**: Includes ALL tasks between start and end in topological order

**Additional options**:
- Critical path highlighting (y/n)
- Metric selection (volume/op_count/rate)
- Custom output filename

---

### Option 2: Get Flow Summary Statistics

**Input format**: Mixed format with space or comma separation

```
Tasks: openmm aggregate_0 training
```

**Supported formats**:
1. **Task name only** (expands to all instances): `openmm`  `openmm_0` through `openmm_11`
2. **Specific instance**: `openmm_0`  just that one instance
3. **Mixed**: `openmm aggregate_0`  all openmm instances + aggregate instance 0

**Separators**: Both spaces and commas work
- `openmm aggregate training` 
- `openmm,aggregate,training` 
- `openmm, aggregate training` 

---

### Option 4: List Tasks & Quick Sankey (Recommended!)

**Workflow**:
1. Lists 4 unique task names with stage and parallelism info
2. Prompts for task range: `openmm training`
3. Automatically generates Sankey diagram

**Input format**: Two task names separated by space
```
Task range: openmm training
```

**Rules**:
- Use task names WITHOUT instance index (e.g., `openmm`, not `openmm_0`)
- Space-separated only
- Must be exactly two task names
- Press Enter to skip and return to main menu

**What it does**:
- Automatically uses `_0` instance as start/end boundaries
- Includes all task instances between them
- Saves with descriptive filename

**Examples**:
```
openmm training     sankey_openmm_to_training.html
aggregate inference sankey_aggregate_to_inference.html
openmm inference    sankey_openmm_to_inference.html (entire workflow)
```

---

## Task Naming Reference

### DDMD Workflow Tasks:
```
1. openmm      (stage 0, parallelism: 12)  instances: openmm_0 to openmm_11
2. aggregate   (stage 1, parallelism: 1)   instance:  aggregate_0
3. training    (stage 1, parallelism: 1)   instance:  training_0
4. inference   (stage 2, parallelism: 1)   instance:  inference_0
```

### Stage Order & Dependencies:
- **Stage 0**: openmm (12 parallel tasks)
- **Stage 1**: 
  - aggregate (depends on openmm)
  - training (depends on openmm AND aggregate)
- **Stage 2**: inference (depends on openmm)

**Important**: Tasks at the same stage may have different dependencies!

---

## Common Use Cases

### Visualize Full Workflow
**Option 4**:
```
Task range: openmm inference
```
Output: `sankey_openmm_to_inference.html`

### Visualize Specific Dataflow Path
**Option 4**:
```
Task range: openmm aggregate
```
Output: `sankey_openmm_to_aggregate.html` (13 tasks: all openmm + aggregate only)

**Note**: Only includes tasks on the direct dataflow path. Since `training` is not on the path from openmm to aggregate, it's excluded even though it's at the same stage.

### Analyze Specific Openmm Instances
**Option 2**:
```
Tasks: openmm_0 openmm_5 openmm_11
```

### Analyze All Openmm + Training
**Option 2**:
```
Tasks: openmm training
```
This expands to all 12 openmm instances + training_0

---

## Tips

 **DO**:
- Use Option 4 for quick Sankey generation
- Use task names without indices in Option 4
- Use specific indices when you need precise control

 **DON'T**:
- Mix task names with indices in Option 4 (e.g., `openmm_0 training`)
- Use commas in Option 4 (space-separated only)
- Use more than 2 task names in Option 4

---

## Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `Task 'xxx' not found` | Task name doesn't exist | Check spelling, use listed task names |
| `Please enter exactly two task names` | Wrong number of inputs | Enter exactly 2 space-separated names |
| `Start task comes after end task` | Wrong order | Swap them (check stage order) |