import numpy as np
import matplotlib.pyplot as plt
import xarray as dg # or xarray

def plot_spherical_partitions(nc_mesh_path, part_path):
    print("Loading MPAS mesh coordinates...")
    # Open the MPAS grid/mesh file (usually an initial condition or grid file, e.g., x1.655362.nc)
    ds = dg.open_dataset(nc_mesh_path)
    
    # Extract cell center coordinates (lat/lon in radians or degrees depending on file)
    # MPAS grids typically store latCell and lonCell in radians
    lat_cell = ds.latCell.values  # radians
    lon_cell = ds.lonCell.values  # radians
    
    print("Loading partition assignments...")
    with open(part_path, 'r') as f:
        partitions = np.array([int(line.strip()) for line in f if line.strip()])
        
    if len(lat_cell) != len(partitions):
        print(f"Warning: Mesh cell count ({len(lat_cell)}) does not match partition count ({len(partitions)}).")
        print("Ensure you are pointing to the correct corresponding NetCDF grid file.")
        
    print("Converting spherical coordinates to 3D Cartesian coordinates...")
    # Convert lat/lon to 3D Cartesian coordinates (R = 1.0)
    # lat: [-pi/2, pi/2], lon: [0, 2pi] or [-pi, pi]
    x = np.cos(lat_cell) * np.cos(lon_cell)
    y = np.cos(lat_cell) * np.sin(lon_cell)
    z = np.sin(lat_cell)
    
    print("Generating 3D spherical plot...")
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(projection='3d')
    
    # Scatter plot on the sphere surface, colored by partition ID (0 to 159)
    # Using a discrete or qualitative colormap like 'tab20' or 'viridis'
    scatter = ax.scatter(x, y, z, c=partitions, cmap='tab20', s=0.5, edgecolor='none')
    
    ax.set_title(f"MPAS Mesh Partitioning on Sphere (160 Processors)", fontsize=14)
    ax.set_axis_off()  # Hide axis grids for a clean globe view
    
    # Add a colorbar indicating processor ranks
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.5, pad=0.05)
    cbar.set_label("Processor Rank (0 - 159)")
    
    output_filename = "mpas_gloabl_heirarchical_160.png"
   #output_filename = "mpas_partition_sphere_160.png"
    print(f"Saving plot to {output_filename}...")
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    # Replace with your actual MPAS NetCDF grid/mesh filename (e.g., x1.655362.nc)
    netcdf_mesh_file = "../data/x1.655362.grid.nc"
   #partition_file = "../data/x1.655362.graph.info.part.48"
    partition_file = "global_hierarchical.part.160"
   #partition_file = "../data/x1.655362.graph.info.part.160"
    
    plot_spherical_partitions(netcdf_mesh_file, partition_file)
