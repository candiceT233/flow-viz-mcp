#!/usr/bin/env python3
"""
Interactive CLI for DFL Visualization MCP Server

This script provides a user-friendly command-line interface to interact with
the DFL Visualization MCP server without needing an MCP client application.
"""

import sys
import os
from src.dfl_mcp.server import DFLVisualizationMCP
from src.dfl_mcp.analysis.task_ordering import get_topological_task_order, get_unique_task_names


def print_banner():
    """Print the welcome banner."""
    print("\n" + "="*70)
    print("  DFL Visualization Interactive CLI")
    print("="*70)


def print_menu():
    """Print the main menu."""
    print("\nMain Menu:")
    print("  1. Generate Sankey Diagram")
    print("  2. Get Flow Summary Statistics")
    print("  3. Analyze Critical Path")
    print("  4. List Available Tasks (in a workflow)")
    print("  5. Adjust Sankey Canvas Size")
    print("  6. Switch Workflow")
    print("  0. Exit")


def get_user_choice(prompt, options=None):
    """Get validated user input."""
    while True:
        choice = input(prompt).strip()
        if options is None or choice in options:
            return choice
        print(f"[ERROR] Invalid choice. Please choose from: {', '.join(options)}")


def get_optional_input(prompt, default=""):
    """Get optional user input with a default value."""
    value = input(f"{prompt} (press Enter to skip): ").strip()
    return value if value else default


def expand_task_names(task_input_list, dag):
    """
    Expand task names to specific task instances.
    
    Args:
        task_input_list: List of task names or task instances (e.g., ['openmm', 'aggregate_0'])
        dag: The workflow DAG
        
    Returns:
        List of specific task instance IDs (e.g., ['openmm_0', 'openmm_1', ..., 'aggregate_0'])
    """
    expanded_tasks = []
    
    for task_input in task_input_list:
        task_input = task_input.strip()
        
        # Check if it's already a specific instance (contains underscore and number)
        if '_' in task_input:
            parts = task_input.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                # It's already a specific instance
                expanded_tasks.append(task_input)
                continue
        
        # It's a task name without instance - expand to all instances
        task_name = task_input
        instances_found = []
        
        for node, data in dag.nodes(data=True):
            if data.get('type') == 'task' and data.get('task_name') == task_name:
                instances_found.append(node)
        
        if instances_found:
            # Sort by instance number
            instances_found.sort(key=lambda x: int(x.rsplit('_', 1)[1]) if '_' in x else 0)
            expanded_tasks.extend(instances_found)
        else:
            print(f"[WARNING] Task '{task_name}' not found in workflow, skipping...")
    
    return expanded_tasks


def select_workflow(server):
    """Let user select a workflow."""
    workflows = server.available_workflows
    
    if not workflows:
        print("\n[ERROR] No workflows found in workflow_traces/")
        return None
    
    print("\nAvailable Workflows:")
    for i, workflow in enumerate(workflows, 1):
        print(f"  {i}. {workflow}")
    
    while True:
        choice = input(f"\nSelect workflow (1-{len(workflows)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(workflows):
                return workflows[idx]
        except ValueError:
            pass
        print(f"[ERROR] Invalid choice. Please enter a number between 1 and {len(workflows)}")


def list_tasks_menu(server, workflow_name):
    """List all unique task names in stage order and optionally generate Sankey diagram."""
    print(f"\nLoading tasks for workflow: {workflow_name}")
    try:
        dag = server._load_workflow(workflow_name)
        unique_tasks = get_unique_task_names(dag)
        
        print(f"\n[SUCCESS] Found {len(unique_tasks)} unique tasks in stage order:")
        for i, (task_name, stage_order, parallelism) in enumerate(unique_tasks, 1):
            print(f"  {i}. {task_name} (stage {stage_order}, parallelism: {parallelism})")
        
        print("\n" + "="*70)
        print("Generate Sankey diagram for a task range?")
        print("="*70)
        print("\nEnter two task names separated by space (e.g., 'openmm training')")
        print("  - First task = starting task (e.g., openmm)")
        print("  - Second task = ending task (e.g., training)")
        print("  - This will include ALL task instances between them")
        print("\nOr press Enter to return to main menu.")
        print("="*70)
        
        task_range_input = input("\nTask range: ").strip()
        
        if task_range_input:
            # Parse the input
            parts = task_range_input.split()
            if len(parts) == 2:
                start_task_name, end_task_name = parts[0], parts[1]
                
                # Find the first instance of each task
                start_task_id = f"{start_task_name}_0"
                end_task_id = f"{end_task_name}_0"
                
                # Verify these tasks exist
                task_names = [name for name, _, _ in unique_tasks]
                if start_task_name not in task_names:
                    print(f"\n[ERROR] Task '{start_task_name}' not found in workflow")
                    return
                if end_task_name not in task_names:
                    print(f"\n[ERROR] Task '{end_task_name}' not found in workflow")
                    return
                
                # Generate output filename
                output_file = f"sankey_{start_task_name}_to_{end_task_name}.html"
                
                print(f"\n[WORKING] Generating Sankey diagram from {start_task_name} to {end_task_name}...")
                try:
                    result = server.get_sankey_data(
                        workflow_name=workflow_name,
                        start_task_id=start_task_id,
                        end_task_id=end_task_id,
                        metric='volume',
                        output_file=output_file,
                        highlight_critical_path=True
                    )
                    print(f"\n[SUCCESS] {result}")
                except Exception as e:
                    print(f"\n[ERROR] {e}")
            else:
                print("\n[ERROR] Please enter exactly two task names separated by space")
        
    except Exception as e:
        print(f"\n[ERROR] Error loading tasks: {e}")


def generate_sankey_menu(server, workflow_name):
    """Interactive menu for generating Sankey diagrams."""
    print(f"\nGenerate Sankey Diagram for: {workflow_name}")
    print("\n[TIP] You can filter by task range or visualize the full workflow")
    
    # Ask about task filtering
    use_filter = get_user_choice("\nFilter by task range? (y/n, default=n): ", ["y", "n", "Y", "N", ""])
    if use_filter == "":
        use_filter = "n"
    
    start_task = None
    end_task = None
    
    if use_filter.lower() == "y":
        start_task = get_optional_input("  Start task ID (e.g., openmm_0)")
        end_task = get_optional_input("  End task ID (e.g., aggregate_0)")
        
        if not start_task:
            start_task = None
        if not end_task:
            end_task = None
    
    # Ask about critical path highlighting
    highlight = get_user_choice("\nHighlight critical path? (y/n, default=y): ", ["y", "n", "Y", "N", ""])
    highlight_critical_path = highlight.lower() != "n"
    
    # Ask about metric
    print("\nSelect metric for edge width:")
    print("  1. volume (default)")
    print("  2. op_count")
    print("  3. rate")
    metric_choice = get_user_choice("Metric (1-3, default=1): ", ["1", "2", "3", ""])
    
    metric_map = {"1": "volume", "2": "op_count", "3": "rate", "": "volume"}
    metric = metric_map[metric_choice]
    
    # Font size
    font_size = get_optional_input("\nFont size (default: 10)", "10")
    try:
        font_size = int(font_size)
    except ValueError:
        print("[WARNING] Invalid font size, using default of 10.")
        font_size = 10

    # Node padding
    node_pad = get_optional_input("\nNode padding (default: 15)", "15")
    try:
        node_pad = int(node_pad)
    except ValueError:
        print("[WARNING] Invalid node padding, using default of 15.")
        node_pad = 15

    # Transform link value
    transform_link_value = get_user_choice("\nTransform link value (log scale)? (y/n, default=y): ", ["y", "n", "Y", "N", ""]) 
    transform_link_value = transform_link_value.lower() != "n"

    # Output file
    output_file = get_optional_input("\nOutput filename (default: sankey.html)", "sankey.html")
    if not output_file.endswith(".html"):
        output_file += ".html"
    
    # Generate the diagram
    print(f"\n[WORKING] Generating Sankey diagram...")
    try:
        result = server.get_sankey_data(
            workflow_name=workflow_name,
            start_task_id=start_task,
            end_task_id=end_task,
            metric=metric,
            output_file=output_file,
            highlight_critical_path=highlight_critical_path,
            font_size=font_size,
            node_pad=node_pad,
            transform_link_value=transform_link_value
        )
        print(f"\n[SUCCESS] {result}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def flow_summary_menu(server, workflow_name):
    """Interactive menu for flow summary statistics."""
    print(f"\nGet Flow Summary Statistics for: {workflow_name}")
    
    # Ask about task filtering
    use_filter = get_user_choice("\nFilter by specific tasks? (y/n): ", ["y", "n", "Y", "N"])
    
    selected_tasks = []
    if use_filter.lower() == "y":
        print("\nEnter task names or specific instances:")
        print("  - Use task names for ALL instances: openmm aggregate")
        print("  - Use specific instances: openmm_0,openmm_1")
        print("  - Mix both (space or comma separated): openmm aggregate_0 training_0")
        tasks_input = input("\nTasks: ").strip()
        if tasks_input:
            # Support both space and comma separation
            tasks_input = tasks_input.replace(',', ' ')
            task_list = [t.strip() for t in tasks_input.split() if t.strip()]
            
            # Expand task names to instances
            dag = server._load_workflow(workflow_name)
            selected_tasks = expand_task_names(task_list, dag)
            
            if selected_tasks:
                print(f"\n[INFO] Expanded to {len(selected_tasks)} task instance(s): {', '.join(selected_tasks[:5])}")
                if len(selected_tasks) > 5:
                    print(f"       ... and {len(selected_tasks) - 5} more")
    
    # Output file
    output_file = get_optional_input("\nOutput filename (default: auto-generated)", None)
    
    # Generate summary
    print(f"\n[WORKING] Calculating summary statistics...")
    try:
        result = server.get_flow_summary_stats(
            workflow_name=workflow_name,
            selected_tasks=selected_tasks,
            output_file=output_file
        )

        if isinstance(result, dict):
            saved_path = result.get("output_file")
            summary_text = result.get("summary_text")
            print(f"\n[SUCCESS] Summary saved to {saved_path}")
        else:
            saved_path = output_file
            summary_text = None
            print(f"\n[SUCCESS] {result}")
        
        # Optionally display the content
        show_content = get_user_choice("\nDisplay summary content? (y/n): ", ["y", "n", "Y", "N"])
        if show_content.lower() == "y":
            if summary_text:
                print("\n" + "="*70)
                print(summary_text)
                print("="*70)
            elif saved_path:
                try:
                    with open(saved_path, 'r') as f:
                        print("\n" + "="*70)
                        print(f.read())
                        print("="*70)
                except Exception as e:
                    print(f"[ERROR] Could not read file: {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def critical_path_menu(server, workflow_name):
    """Interactive menu for critical path analysis."""
    print(f"\nAnalyze Critical Path for: {workflow_name}")
    
    # Ask about weight property
    print("\nSelect weight property:")
    print("  1. volume (default)")
    print("  2. op_count")
    print("  3. rate")
    weight_choice = get_user_choice("Weight property (1-3, default=1): ", ["1", "2", "3", ""])
    
    weight_map = {"1": "volume", "2": "op_count", "3": "rate", "": "volume"}
    weight_property = weight_map[weight_choice]
    
    # Analyze
    print(f"\n[WORKING] Analyzing critical path using '{weight_property}'...")
    try:
        result = server.analyze_critical_path(
            workflow_name=workflow_name,
            weight_property=weight_property
        )
        
        print(f"\n[SUCCESS] Critical Path Analysis Complete")
        print(f"\nTotal Critical Weight ({weight_property}): {result['total_critical_weight']:,.2f}")
        print(f"\nCritical Path Nodes ({len(result['critical_path_nodes'])} nodes):")
        for i, node in enumerate(result['critical_path_nodes'], 1):
            print(f"  {i}. {node}")
        
        if result['opportunities']:
            print(f"\nOptimization Opportunities ({len(result['opportunities'])} found):")
            for i, opp in enumerate(result['opportunities'], 1):
                print(f"\n  {i}. {opp.get('pattern_type', 'Unknown')}:")
                print(f"     Description: {opp.get('description', 'N/A')}")
                print(f"     Nodes: {opp.get('nodes', [])}")
        else:
            print("\n[INFO] No specific optimization opportunities identified.")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def adjust_sankey_canvas_menu(server):
    """Interactive menu for adjusting Sankey canvas size."""
    print("\nAdjust Sankey Canvas Size")
    print("-------------------------")
    
    if not server.last_sankey_params:
        print("[INFO] No Sankey diagram has been generated yet. Please generate one first.")
        return

    try:
        width = int(input("Enter new width (e.g., 1800): ").strip())
        height = int(input("Enter new height (e.g., 2000): ").strip())
        font_size = int(get_optional_input("Enter new font size (default: 10): ", "10"))
        node_pad = int(get_optional_input("Enter new node padding (default: 15): ", "15"))
        transform_link_value = get_user_choice("Transform link value (log scale)? (y/n, default=y): ", ["y", "n", "Y", "N", ""]) 
        transform_link_value = transform_link_value.lower() != "n"

        print(f"\n[WORKING] Adjusting Sankey canvas size to {width}x{height} with font size {font_size}...")
        result = server.adjust_sankey_canvas_size(width=width, height=height, font_size=font_size, node_pad=node_pad, transform_link_value=transform_link_value)
        print(f"\n[SUCCESS] {result}")
    except ValueError:
        print("[ERROR] Invalid input. Please enter integer values for width, height, font size and node padding.")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def main():
    """Main interactive loop."""
    print_banner()
    
    # Initialize server
    print("\n[WORKING] Initializing DFL Visualization server...")
    try:
        server = DFLVisualizationMCP()
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize server: {e}")
        sys.exit(1)
    
    # Select initial workflow
    workflow_name = select_workflow(server)
    if not workflow_name:
        print("\n[ERROR] No workflow selected. Exiting.")
        sys.exit(1)
    
    print(f"\n[SUCCESS] Selected workflow: {workflow_name}")
    
    # Main loop
    while True:
        print_menu()
        choice = get_user_choice("\nEnter your choice (0-6): ", ["0", "1", "2", "3", "4", "5", "6"])
        
        if choice == "0":
            print("\nGoodbye!")
            break
        elif choice == "1":
            generate_sankey_menu(server, workflow_name)
        elif choice == "2":
            flow_summary_menu(server, workflow_name)
        elif choice == "3":
            critical_path_menu(server, workflow_name)
        elif choice == "4":
            list_tasks_menu(server, workflow_name)
        elif choice == "5":
            adjust_sankey_canvas_menu(server)
        elif choice == "6":
            new_workflow = select_workflow(server)
            if new_workflow:
                workflow_name = new_workflow
                print(f"\n[SUCCESS] Switched to workflow: {workflow_name}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
