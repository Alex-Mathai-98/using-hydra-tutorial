#!/usr/bin/env python3
"""
Utilities for organizing and navigating experiments
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

class ExperimentOrganizer:
    def __init__(self, base_dir="./outputs"):
        self.base_dir = Path(base_dir)
        
    def create_experiment_index(self):
        """Create a searchable index of all experiments, including parameter sweep jobs"""
        experiments = []
        
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                # Check if this is a regular experiment directory
                info_file = exp_dir / "experiment_info.json"
                results_file = exp_dir / "results.json"
                
                if info_file.exists():
                    # Regular experiment (not a sweep parent directory)
                    experiment_info = self._extract_experiment_info(exp_dir, info_file, results_file)
                    experiments.append(experiment_info)
                else:
                    # Check for parameter sweep subdirectories (job_0, job_1, etc.)
                    job_dirs = [d for d in exp_dir.iterdir() if d.is_dir() and d.name.startswith('job_')]
                    
                    if job_dirs:
                        # This is a parameter sweep parent directory
                        for job_dir in sorted(job_dirs):
                            job_info_file = job_dir / "experiment_info.json"
                            job_results_file = job_dir / "results.json"
                            
                            if job_info_file.exists():
                                experiment_info = self._extract_experiment_info(job_dir, job_info_file, job_results_file)
                                # Add sweep information
                                experiment_info['sweep_parent'] = exp_dir.name
                                experiment_info['job_number'] = job_dir.name
                                experiments.append(experiment_info)
        
        df = pd.DataFrame(experiments)
        df.to_csv(self.base_dir / "experiment_index.csv", index=False)
        print(f"Created experiment index with {len(experiments)} experiments")
        return df
    
    def _extract_experiment_info(self, exp_dir, info_file, results_file):
        """Helper method to extract experiment information from a directory"""
        with open(info_file) as f:
            info = json.load(f)
        
        # Add results if available
        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)
            info.update(results)
        
        info['folder_name'] = exp_dir.name
        info['full_path'] = str(exp_dir)
        return info
    
    def find_experiments(self, **filters):
        """Find experiments matching criteria"""
        df = pd.read_csv(self.base_dir / "experiment_index.csv")
        
        for key, value in filters.items():
            if key in df.columns:
                df = df[df[key] == value]
        
        # Show sweep information if available
        display_cols = ['folder_name', 'model', 'dataset', 'lr', 'best_accuracy']
        if 'sweep_parent' in df.columns:
            display_cols.extend(['sweep_parent', 'job_number'])
        
        available_cols = [col for col in display_cols if col in df.columns]
        return df[available_cols]
    
    def cleanup_old_experiments(self, keep_days=30):
        """Remove experiments older than keep_days"""
        cutoff = datetime.now().timestamp() - (keep_days * 24 * 3600)
        removed = 0
        
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                if exp_dir.stat().st_mtime < cutoff:
                    # Check if it's a good experiment before deleting
                    results_file = exp_dir / "results.json"
                    if results_file.exists():
                        with open(results_file) as f:
                            results = json.load(f)
                        # Don't delete if accuracy is above threshold
                        if results.get('best_accuracy', 0) > 0.9:
                            print(f"Keeping high-performing experiment: {exp_dir.name}")
                            continue
                    
                    print(f"Removing old experiment: {exp_dir.name}")
                    shutil.rmtree(exp_dir)
                    removed += 1
        
        print(f"Removed {removed} old experiments")
    
    def analyze_sweep(self, sweep_name):
        """Analyze results from a parameter sweep"""
        df = pd.read_csv(self.base_dir / "experiment_index.csv")
        
        if 'sweep_parent' in df.columns:
            sweep_results = df[df['sweep_parent'] == sweep_name]
            
            if not sweep_results.empty:
                print(f"\nParameter Sweep Analysis: {sweep_name}")
                print("=" * 50)
                
                # Sort by performance
                if 'best_accuracy' in sweep_results.columns:
                    sweep_results = sweep_results.sort_values('best_accuracy', ascending=False)
                
                # Show key parameters and results
                display_cols = ['job_number', 'lr', 'batch_size', 'best_accuracy']
                available_cols = [col for col in display_cols if col in sweep_results.columns]
                print(sweep_results[available_cols].to_string(index=False))
                
                # Show best configuration
                if 'best_accuracy' in sweep_results.columns:
                    best_run = sweep_results.iloc[0]
                    print(f"\nBest configuration:")
                    print(f"  Job: {best_run['job_number']}")
                    print(f"  Accuracy: {best_run['best_accuracy']:.4f}")
                    print(f"  Path: {best_run['full_path']}")
                
                return sweep_results
            else:
                print(f"No sweep results found for: {sweep_name}")
                return pd.DataFrame()
        else:
            print("No parameter sweep data found in experiment index")
            return pd.DataFrame()

    def list_sweeps(self):
        """List all parameter sweeps"""
        df = pd.read_csv(self.base_dir / "experiment_index.csv")
        
        if 'sweep_parent' in df.columns:
            sweeps = df['sweep_parent'].dropna().unique()
            print(f"Found {len(sweeps)} parameter sweeps:")
            for sweep in sweeps:
                sweep_count = len(df[df['sweep_parent'] == sweep])
                print(f"  {sweep} ({sweep_count} jobs)")
            return sweeps
        else:
            print("No parameter sweep data found")
            return []
        """Create symbolic links for easy navigation"""
        shortcuts_dir = self.base_dir / "shortcuts"
        shortcuts_dir.mkdir(exist_ok=True)
        
        # Clear existing shortcuts
        for link in shortcuts_dir.iterdir():
            if link.is_symlink():
                link.unlink()
        
        # Create shortcuts for recent good experiments
        df = pd.read_csv(self.base_dir / "experiment_index.csv")
        if 'best_accuracy' in df.columns:
            top_experiments = df.nlargest(5, 'best_accuracy')
            
            for _, exp in top_experiments.iterrows():
                original_path = Path(exp['full_path'])
                shortcut_name = f"top_{exp['model']}_{exp['dataset']}_{exp['best_accuracy']:.3f}"
                shortcut_path = shortcuts_dir / shortcut_name
                
                if original_path.exists():
                    shortcut_path.symlink_to(original_path.resolve())
        
        print(f"Created shortcuts in {shortcuts_dir}")

# Command-line interface functions
def list_experiments():
    """List all experiments in a table"""
    organizer = ExperimentOrganizer()
    df = organizer.create_experiment_index()
    
    if not df.empty:
        # Show only key columns for readability
        display_cols = ['folder_name', 'model', 'dataset', 'lr', 'best_accuracy', 'timestamp']
        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].to_string(index=False))
    else:
        print("No experiments found")

def find_best_experiments(metric='best_accuracy', top_n=5):
    """Show top N experiments by metric"""
    organizer = ExperimentOrganizer()
    df = organizer.create_experiment_index()
    
    if metric in df.columns:
        top_experiments = df.nlargest(top_n, metric)
        print(f"\nTop {top_n} experiments by {metric}:")
        print(top_experiments[['folder_name', 'model', 'dataset', metric]].to_string(index=False))
    else:
        print(f"Metric '{metric}' not found")

def quick_cd(partial_name):
    """Generate cd command for partial experiment name match"""
    organizer = ExperimentOrganizer()
    df = organizer.create_experiment_index()
    
    matches = df[df['folder_name'].str.contains(partial_name, case=False)]
    
    if len(matches) == 1:
        path = matches.iloc[0]['full_path']
        print(f"cd {path}")
    elif len(matches) > 1:
        print("Multiple matches found:")
        print(matches[['folder_name', 'model', 'dataset']].to_string(index=False))
    else:
        print(f"No experiments found matching '{partial_name}'")

# CLI usage examples
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python experiment_organizer.py [list|find_best|cd|cleanup|shortcuts|sweeps|analyze_sweep]")
        sys.exit(1)
    
    command = sys.argv[1]
    organizer = ExperimentOrganizer()
    
    if command == "list":
        list_experiments()
    elif command == "find_best":
        find_best_experiments()
    elif command == "cd" and len(sys.argv) > 2:
        quick_cd(sys.argv[2])
    elif command == "cleanup":
        organizer.cleanup_old_experiments()
    elif command == "shortcuts":
        organizer.create_shortcuts()
    elif command == "sweeps":
        organizer.list_sweeps()
    elif command == "analyze_sweep" and len(sys.argv) > 2:
        organizer.analyze_sweep(sys.argv[2])
    else:
        print(f"Unknown command: {command}")

"""
Usage examples:

# List all experiments in a nice table (includes sweep jobs)
python experiment_organizer.py list

# Find top 5 experiments by accuracy
python experiment_organizer.py find_best

# Get cd command for experiment (copy-paste the output)
python experiment_organizer.py cd r50_c10

# List all parameter sweeps
python experiment_organizer.py sweeps

# Analyze a specific parameter sweep
python experiment_organizer.py analyze_sweep r18_c10_1215_1430

# Clean up old experiments
python experiment_organizer.py cleanup

# Create shortcuts to top experiments
python experiment_organizer.py shortcuts
"""