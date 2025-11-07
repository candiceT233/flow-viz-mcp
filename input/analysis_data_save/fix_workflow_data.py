#!/usr/bin/env python3
"""
Script to fix workflow data by comparing it with a template file.
Updates taskName, stageOrder, and prevTask columns in the workflow data
to match the template when they differ for the same taskPID.
"""

import pandas as pd
import os

def main():
    # File paths
    template_file = "pyflex_240f_workflow_data_fixed_template.csv"
    workflow_file = "pyflex_240f_workflow_data.csv"
    output_file = "pyflex_240f_workflow_data_fixed.csv"
    
    print(f"Reading template file: {template_file}")
    template_df = pd.read_csv(template_file)
    
    print(f"Reading workflow file: {workflow_file}")
    wf_df = pd.read_csv(workflow_file)
    
    print(f"Template dataframe shape: {template_df.shape}")
    print(f"Workflow dataframe shape: {wf_df.shape}")
    
    # Get unique taskPID values from both dataframes
    template_taskpids = set(template_df['taskPID'].unique())
    wf_taskpids = set(wf_df['taskPID'].unique())
    
    print(f"Unique taskPID in template: {len(template_taskpids)}")
    print(f"Unique taskPID in workflow: {len(wf_taskpids)}")
    
    # Check if they have the same taskPID values
    if template_taskpids != wf_taskpids:
        print("Warning: taskPID values are not identical between template and workflow files!")
        print(f"TaskPIDs in template but not in workflow: {template_taskpids - wf_taskpids}")
        print(f"TaskPIDs in workflow but not in template: {wf_taskpids - template_taskpids}")
    
    # Columns to compare and potentially update
    columns_to_compare = ['taskName', 'stageOrder', 'prevTask']
    
    # Create a copy of the workflow dataframe to modify
    wf_df_fixed = wf_df.copy()
    
    # Track changes
    total_changes = 0
    changes_by_column = {col: 0 for col in columns_to_compare}
    
    # Group template by taskPID and get the first occurrence of each column value
    template_grouped = template_df.groupby('taskPID').agg({
        'taskName': 'first',
        'stageOrder': 'first', 
        'prevTask': 'first'
    }).reset_index()
    
    print("\nProcessing each taskPID...")
    
    # Process each taskPID
    for taskpid in wf_taskpids:
        # Get template values for this taskPID
        template_row = template_grouped[template_grouped['taskPID'] == taskpid]
        
        if template_row.empty:
            print(f"Warning: taskPID {taskpid} not found in template, skipping...")
            continue
            
        template_values = template_row.iloc[0]
        
        # Get workflow rows for this taskPID
        wf_mask = wf_df_fixed['taskPID'] == taskpid
        wf_rows = wf_df_fixed[wf_mask]
        
        if wf_rows.empty:
            continue
            
        # Check if any of the columns differ from template
        needs_update = False
        for col in columns_to_compare:
            if wf_rows[col].iloc[0] != template_values[col]:
                needs_update = True
                break
        
        if needs_update:
            print(f"Updating taskPID {taskpid}")
            print(f"  Template: taskName={template_values['taskName']}, stageOrder={template_values['stageOrder']}, prevTask={template_values['prevTask']}")
            print(f"  Current: taskName={wf_rows['taskName'].iloc[0]}, stageOrder={wf_rows['stageOrder'].iloc[0]}, prevTask={wf_rows['prevTask'].iloc[0]}")
            
            # Update all rows with this taskPID
            for col in columns_to_compare:
                if wf_rows[col].iloc[0] != template_values[col]:
                    wf_df_fixed.loc[wf_mask, col] = template_values[col]
                    changes_by_column[col] += 1
                    total_changes += 1
    
    print(f"\nSummary of changes:")
    print(f"Total rows updated: {total_changes}")
    for col, count in changes_by_column.items():
        print(f"  {col}: {count} updates")
    
    # Save the fixed workflow data
    print(f"\nSaving fixed workflow data to: {output_file}")
    wf_df_fixed.to_csv(output_file, index=False)
    
    print("Done!")

if __name__ == "__main__":
    main()
