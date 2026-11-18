#!/bin/bash

#robinson platecarree hammer aitoff 3d
#projection=mollweide
#projection=hammer
#projection=robinson
projection=aitoff

numpart=2048
numnodes=16
subgroup=128

datadir="../MPAS-Model/data"

python plot_global_hierarchical.py \
  -m ${datadir}/x1.655362.grid.nc \
  -i ${datadir}/x1.655362.graph.info.part.${numpart} \
  -o mpas_direct_group_${projection}_${numpart}_s${subgroup}.png \
  -n ${numpart} \
  -p ${numnodes} \
  -q ${subgroup} \
  -t "MPAS Direct Grouping" \
  --proj ${projection}

exit 0

python plot_global_hierarchical.py \
  -m ${datadir}/x1.655362.grid.nc \
  -i global_hierarchical.part.${numpart} \
  -o mpas_global_hierarchical_${projection}_${numpart}_s${subgroup}.png \
  -n ${numpart} \
  -p ${numnodes} \
  -q ${subgroup} \
  -t "MPAS Hierarchical Partitioning" \
  --proj ${projection}

python plot_global_hierarchical.py \
  -m ${datadir}/x1.655362.grid.nc \
  -i ${datadir}/x1.655362.graph.info.part.${numpart} \
  -o mpas_direct_partition_${projection}_${numpart}_s${subgroup}.png \
  -n ${numpart} \
  -p ${numpart} \
  -q 1 \
  -t "MPAS Direct Partitioning" \
  --proj ${projection}
