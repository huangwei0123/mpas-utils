import numpy as np
import netCDF4 as nc_file

def analyse_partitions(part_path, nc=160, output_nc="partition_analysis.nc"):
    print(f"Loading partition from {part_path}")

    with open(part_path, 'r') as f:
        partitions = np.array([int(line.strip()) for line in f if line.strip()])

    nic = np.zeros((nc,), dtype=int)
    pic = np.zeros((nc, len(partitions)), dtype=int)

    for id in range(len(partitions)):
        ic = partitions[id]
        pic[ic][nic[ic]] = id
        nic[ic] += 1

    print('nic = ', nic)
    print(f'min: {np.min(partitions)}, max: {np.max(partitions)}')
    print(f'Sum of nic: {np.sum(nic)} | Total partitions elements: {len(partitions)}')

    # --- Trim and Save to NetCDF ---
    max_nic = int(np.max(nic))
    pic_trimmed = pic[:, :max_nic]

    with nc_file.Dataset(output_nc, 'w', format='NETCDF4') as ds:
        ds.createDimension('n_partitions', nc)
        ds.createDimension('max_cells_per_partition', max_nic)
        ds.createDimension('total_cells', len(partitions))

        v_nic = ds.createVariable('nic', 'i4', ('n_partitions',))
        v_nic[:] = nic

        v_pic = ds.createVariable('pic', 'i4', ('n_partitions', 'max_cells_per_partition'))
        v_pic[:] = pic_trimmed

        v_parts = ds.createVariable('partition_assignment', 'i4', ('total_cells',))
        v_parts[:] = partitions

    print(f"Saved processed output to {output_nc} with shape {pic_trimmed.shape}")

if __name__ == "__main__":
    partition_file = "../data/x1.655362.graph.info.part.160"
    nc = 160
    analyse_partitions(partition_file, nc=nc)
