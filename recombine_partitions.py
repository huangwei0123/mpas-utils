import argparse
import os


def recombine_global_partition(num_nodes=40, local_parts=4, graph_dir=".", output_filename=None):
    """
    Recombines local sub-graph partition files back into a single global MPAS partition file.
    """
    print(f"Starting global partition recombination (num_nodes={num_nodes}, local_parts={local_parts})...")

    # Dictionary to store global vertex ID -> final reordered/hierarchical partition ID
    global_vertex_assignments = {}
    total_vertices_processed = 0

    for node_id in range(num_nodes):
        map_filename = os.path.join(graph_dir, f"node_{node_id}.map")
        part_filename = os.path.join(graph_dir, f"node_{node_id}.graph.part.{local_parts}")

        if not os.path.exists(map_filename) or not os.path.exists(part_filename):
            print(f"Warning: Missing map or partition file for node {node_id}, skipping.")
            continue

        # 1. Read global vertex IDs for this sub-graph
        with open(map_filename, "r") as mf:
            global_vertices = [int(line.strip()) for line in mf if line.strip()]

        # 2. Read local partition assignments (0-indexed)
        with open(part_filename, "r") as pf:
            local_assignments = [int(line.strip()) for line in pf if line.strip()]

        if len(global_vertices) != len(local_assignments):
            raise ValueError(
                f"Length mismatch in node {node_id}: "
                f"{len(global_vertices)} vertices vs {len(local_assignments)} partition tags."
            )

        # 3. Map local partitions to a globally unique hierarchical ID
        # Example: Node 0, local part 1 -> Global ID = (0 * local_parts) + local_part
        for global_v, local_part in zip(global_vertices, local_assignments):
            hierarchical_id = (node_id * local_parts) + local_part
            global_vertex_assignments[global_v] = hierarchical_id

        total_vertices_processed += len(global_vertices)

    # 4. Write out the final global partition file sorted by original vertex ID (1-based index)
    if output_filename is None:
        output_filename = f"global_hierarchical.part.{num_nodes * local_parts}"

    print(f"Writing unified partition file to {output_filename} ({total_vertices_processed} total vertices)...")

    with open(output_filename, "w") as out_f:
        for v in sorted(global_vertex_assignments.keys()):
            out_f.write(f"{global_vertex_assignments[v]}\n")

    print("Successfully generated global hierarchical partition file!")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Recombine local sub-graph partition files into a single global MPAS partition file."
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
        help="Directory containing node_<id>.map and node_<id>.graph.part.<q> files (default: current directory)",
    )
    parser.add_argument(
        "-o", "--out",
        default=None,
        help="Output global partition filename (default: global_hierarchical.part.<p*q>)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    recombine_global_partition(
        num_nodes=args.num_nodes,
        local_parts=args.local_parts,
        graph_dir=args.graph_dir,
        output_filename=args.out,
    )
