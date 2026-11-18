import argparse
import os


class TwoLayerSubgraphExtractor:
    """
    Parses a global METIS graph and top-level partition file, then extracts
    per-node sub-graphs (node_<id>.graph) and global-to-local vertex maps
    (node_<id>.map) for second-layer partitioning.
    """

    def __init__(self, graph_path, part_path, num_nodes=None, out_dir="."):
        self.graph_path = graph_path
        self.part_path = part_path
        self.num_nodes = num_nodes
        self.out_dir = out_dir

        self.num_vertices = 0
        self.num_edges = 0
        self.adj_list = []
        self.vertex_assignments = []

    def parse_metis_graph(self):
        """Read a METIS graph file and populate headers and 1-based adjacency list."""
        self.adj_list = []
        with open(self.graph_path, "r") as f:
            line = f.readline()
            while line.startswith("%"):
                line = f.readline()

            header = line.strip().split()
            self.num_vertices = int(header[0])
            self.num_edges = int(header[1])

            for line in f:
                if line.startswith("%"):
                    continue
                self.adj_list.append([int(x) for x in line.strip().split()])

        if len(self.adj_list) != self.num_vertices:
            raise ValueError(
                f"Graph vertex count mismatch: header states {self.num_vertices}, "
                f"but read {len(self.adj_list)} adjacency lines."
            )

    def parse_partition_file(self):
        """Read the METIS partition output file (0-indexed assignments)."""
        with open(self.part_path, "r") as f:
            self.vertex_assignments = [int(line.strip()) for line in f if line.strip()]

        if self.num_vertices and len(self.vertex_assignments) != self.num_vertices:
            raise ValueError(
                f"Partition file length ({len(self.vertex_assignments)}) does not match "
                f"graph vertex count ({self.num_vertices})."
            )

        inferred_nodes = max(self.vertex_assignments) + 1
        if self.num_nodes is None:
            self.num_nodes = inferred_nodes
        elif inferred_nodes > self.num_nodes:
            raise ValueError(
                f"Partition file contains node ID {inferred_nodes - 1}, "
                f"which exceeds num_nodes ({self.num_nodes})."
            )

    def extract_subgraphs(self):
        """Build and write node_<id>.graph and node_<id>.map files for every parent node."""
        print("Reading global graph and partition files...")
        self.parse_metis_graph()
        self.parse_partition_file()

        os.makedirs(self.out_dir, exist_ok=True)

        # 1. Group global 1-based vertex IDs by their assigned parent node
        node_to_global_vertices = {i: [] for i in range(self.num_nodes)}
        for global_idx, node_id in enumerate(self.vertex_assignments):
            node_to_global_vertices[node_id].append(global_idx + 1)

        # 2. Create sub-graphs and mapping files for each node
        generated_count = 0
        for node_id, vertices in node_to_global_vertices.items():
            if not vertices:
                print(f"Warning: Node {node_id} has 0 assigned vertices, skipping.")
                continue

            # Global 1-based vertex ID -> Local 1-based vertex ID
            global_to_local = {
                global_v: local_idx + 1 for local_idx, global_v in enumerate(vertices)
            }

            sub_adj_list = []
            sub_edge_arcs = 0

            for global_v in vertices:
                neighbors = self.adj_list[global_v - 1]
                local_neighbors = []
                for nbr in neighbors:
                    if nbr in global_to_local:
                        local_neighbors.append(str(global_to_local[nbr]))
                        sub_edge_arcs += 1
                sub_adj_list.append(" ".join(local_neighbors))

            sub_edge_count = sub_edge_arcs // 2
            sub_graph_filename = os.path.join(self.out_dir, f"node_{node_id}.graph")

            with open(sub_graph_filename, "w") as sf:
                sf.write(f"{len(vertices)} {sub_edge_count}\n")
                for line in sub_adj_list:
                    sf.write(line + "\n")

            mapping_filename = os.path.join(self.out_dir, f"node_{node_id}.map")
            with open(mapping_filename, "w") as mf:
                for global_v in vertices:
                    mf.write(f"{global_v}\n")

            generated_count += 1

        print(f"Successfully generated {generated_count} sub-graphs and mapping files in '{self.out_dir}'.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract per-node METIS sub-graphs and vertex mapping files from a global partition."
    )
    parser.add_argument(
        "-g", "--graph",
        default="../data/x1.655362.graph.info",
        help="Input global METIS graph file (default: ../data/x1.655362.graph.info)",
    )
    parser.add_argument(
        "-i", "--part",
        default="../data/x1.655362.graph.info.part.40",
        help="Input top-level METIS partition file (default: ../data/x1.655362.graph.info.part.40)",
    )
    parser.add_argument(
        "-p", "--num-nodes",
        type=int,
        default=None,
        help="Number of top-level parent nodes (default: auto-detected from partition file)",
    )
    parser.add_argument(
        "-d", "--out-dir",
        default=".",
        help="Output directory for node_<id>.graph and node_<id>.map files (default: current directory)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    extractor = TwoLayerSubgraphExtractor(
        graph_path=args.graph,
        part_path=args.part,
        num_nodes=args.num_nodes,
        out_dir=args.out_dir,
    )
    extractor.extract_subgraphs()
