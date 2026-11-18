import argparse
import os
import subprocess
import sys


def run_subgraph_partitioning(num_nodes=40, local_parts=4, graph_dir="."):
    """
    Loops through each generated sub-graph file and runs gpmetis locally.
    """
    print(f"Starting hierarchical partitioning for {num_nodes} sub-graphs ({local_parts} local partitions each)...")

    for node_id in range(num_nodes):
        graph_filename = os.path.join(graph_dir, f"node_{node_id}.graph")

        if not os.path.exists(graph_filename):
            print(f"Warning: {graph_filename} not found, skipping.")
            continue

        # Construct the gpmetis command for the sub-graph
        cmd = ["gpmetis", graph_filename, str(local_parts)]

        print(f"-> Executing: {' '.join(cmd)}")
        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"   Successfully partitioned {graph_filename}")
        except subprocess.CalledProcessError as e:
            print(f"   Error partitioning {graph_filename}:")
            print(e.stderr)
        except FileNotFoundError:
            print("Error: 'gpmetis' executable not found in PATH. Make sure it's installed or added to your environment path.")
            sys.exit(1)

    print("Finished processing all sub-graphs.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run gpmetis on each parent node sub-graph file (node_<id>.graph)."
    )
    parser.add_argument(
        "-p", "--num-nodes",
        type=int,
        default=40,
        help="Number of top-level parent node sub-graphs (default: 40)",
    )
    parser.add_argument(
        "-q", "--local-parts",
        type=int,
        default=4,
        help="Number of local sub-partitions per node (default: 4)",
    )
    parser.add_argument(
        "-d", "--graph-dir",
        default=".",
        help="Directory containing node_<id>.graph files (default: current directory)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_subgraph_partitioning(
        num_nodes=args.num_nodes,
        local_parts=args.local_parts,
        graph_dir=args.graph_dir,
    )
