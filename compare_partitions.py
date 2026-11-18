import os

def parse_metis_graph(graph_path):
    """Reads a METIS graph file and returns vertex count and adjacency list."""
    adj_list = []
    with open(graph_path, 'r') as f:
        line = f.readline()
        while line.startswith('%'):
            line = f.readline()
        header = line.strip().split()
        num_vertices = int(header[0])
        
        for line in f:
            if line.startswith('%'):
                continue
            if line.strip():
                adj_list.append([int(x) for x in line.strip().split()])
    return num_vertices, adj_list

def parse_partition_file(part_path):
    """Reads a METIS partition file into a list of integer rank assignments."""
    with open(part_path, 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]

def evaluate_partition(adj_list, partition):
    """Calculates total cut edges, boundary vertices, and partition sizes."""
    num_vertices = len(adj_list)
    total_cut_edges = 0
    boundary_vertices = set()
    
    part_sizes = {}
    for p in partition:
        part_sizes[p] = part_sizes.get(p, 0) + 1

    for u_idx in range(num_vertices):
        u_part = partition[u_idx]
        is_boundary = False
        for v_1based in adj_list[u_idx]:
            v_idx = v_1based - 1  # convert to 0-indexed
            v_part = partition[v_idx]
            if u_part != v_part:
                total_cut_edges += 1
                is_boundary = True
        if is_boundary:
            boundary_vertices.add(u_idx)
            
    # Since METIS graphs are undirected, each cut edge is visited twice
    total_cut_edges = total_cut_edges // 2
    return total_cut_edges, len(boundary_vertices), part_sizes

def compare_partitions(graph_path, flat_part_path, hier_part_path):
    print("Parsing graph and partition files...")
    num_vertices, adj_list = parse_metis_graph(graph_path)
    
    flat_part = parse_partition_file(flat_part_path)
    hier_part = parse_partition_file(hier_part_path)
    
    print(f"Evaluating Flat Partition ({flat_part_path})...")
    flat_cuts, flat_boundary_count, flat_sizes = evaluate_partition(adj_list, flat_part)
    
    print(f"Evaluating Hierarchical Partition ({hier_part_path})...")
    hier_cuts, hier_boundary_count, hier_sizes = evaluate_partition(adj_list, hier_part)
    
    print("\n" + "="*56)
    print(f"{'METRIC':<28} | {'FLAT':<12} | {'HIERARCHICAL':<12}")
    print("="*56)
    print(f"{'Total Edge-Cuts':<28} | {flat_cuts:<12} | {hier_cuts:<12}")
    print(f"{'Boundary (Halo) Vertices':<28} | {flat_boundary_count:<12} | {hier_boundary_count:<12}")
    print(f"{'Max Partition Size':<28} | {max(flat_sizes.values()):<12} | {max(hier_sizes.values()):<12}")
    print(f"{'Min Partition Size':<28} | {min(flat_sizes.values()):<12} | {min(hier_sizes.values()):<12}")
    print("="*56)
    
    # Calculate percentage difference in edge cuts
    diff_pct = ((hier_cuts - flat_cuts) / flat_cuts) * 100
    print(f"Edge-cut overhead of hierarchical partitioning: {diff_pct:+.2f}%")

if __name__ == "__main__":
    # Ensure you have generated the flat 160-part file for comparison:
    # gpmetis data/x1.655362.graph.info 160
    graph_file = "../data/x1.655362.graph.info"
    flat_partition = "../data/x1.655362.graph.info.part.160"
    hier_partition = "global_hierarchical.part.160"
    
    if os.path.exists(flat_partition) and os.path.exists(hier_partition):
        compare_partitions(graph_file, flat_partition, hier_partition)
    else:
        print("Error: Missing one or both partition files. Make sure both 'part.160' and 'global_hierarchical.part.160' exist.")
