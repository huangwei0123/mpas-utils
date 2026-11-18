#!/bin/bash

set -x

numpart=256
numnodes=16
subgroup=16

global_metis_graph_file="../data/x1.655362.graph.info"
part_file=${global_metis_graph_file}.part.${numnodes}

gpmetis ${global_metis_graph_file} ${numnodes}

python two_layer_partition.py \
  --graph ${global_metis_graph_file} \
  --part ${part_file} \
  --num-nodes ${numnodes}

# -d, --out-dir OUT_DIR
#                       Output directory for node_<id>.graph and node_<id>.map files (default: current directory)

python run_sub-partitioning.py \
  --num-nodes ${numnodes} \
  --local-parts ${subgroup}

# -d, --graph-dir GRAPH_DIR
#                       Directory containing node_<id>.graph files (default: current directory)

python recombine_partitions.py \
  --num-nodes ${numnodes} \
  --local-parts ${subgroup}

# -d, --graph-dir GRAPH_DIR    Directory containing node_<id>.map and node_<id>.graph.part.<q> files (default: current directory)
# -o, --out OUT         Output global partition filename (default: global_hierarchical.part.<p*q>)

