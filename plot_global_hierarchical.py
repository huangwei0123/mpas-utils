import argparse
import colorsys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import xarray as xr

try:
    import cartopy.crs as ccrs
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False


class MpasPartitionPlotter:
    """
    Loads an MPAS NetCDF grid and a partition assignment file, builds a
    two-layer hierarchical HSV-to-RGB color table (n = p * q), and plots
    the decomposition on a 3D sphere or 2D global map projection.
    """

    def __init__(self, nc_mesh_path, part_path, output_path="mpas_global_hierarchical.png",
                 n=None, p=None, q=None, proj="mollweide", title="MPAS"):
        self.nc_mesh_path = nc_mesh_path
        self.part_path = part_path
        self.output_path = output_path
        self.proj = proj.lower()
        self.title = title

        self.lat_cell = None
        self.lon_cell = None
        self.partitions = None

        self.n = n
        self.p = p
        self.q = q
        self.cmap = None

    def load_data(self):
        """Load cell center coordinates from NetCDF and rank assignments from the part file."""
        print(f"Loading MPAS mesh coordinates from {self.nc_mesh_path}...")
        with xr.open_dataset(self.nc_mesh_path) as ds:
            self.lat_cell = ds.latCell.values  # radians: [-pi/2, pi/2]
            self.lon_cell = ds.lonCell.values  # radians: [0, 2pi] or [-pi, pi]

        print(f"Loading partition assignments from {self.part_path}...")
        self.partitions = np.loadtxt(self.part_path, dtype=np.int32)

        if len(self.lat_cell) != len(self.partitions):
            raise ValueError(
                f"Mesh cell count ({len(self.lat_cell)}) does not match "
                f"partition count ({len(self.partitions)})."
            )

        self._resolve_hierarchy_dims()

    def _resolve_hierarchy_dims(self):
        """Infer or validate n, p, and q such that n = p * q."""
        inferred_n = int(self.partitions.max()) + 1
        if self.n is None:
            self.n = inferred_n

        if self.p is not None and self.q is not None:
            if self.p * self.q != self.n:
                raise ValueError(f"Invalid hierarchy: p ({self.p}) * q ({self.q}) != n ({self.n})")
        elif self.p is not None:
            if self.n % self.p != 0:
                raise ValueError(f"n ({self.n}) is not divisible by p ({self.p})")
            self.q = self.n // self.p
        elif self.q is not None:
            if self.n % self.q != 0:
                raise ValueError(f"n ({self.n}) is not divisible by q ({self.q})")
            self.p = self.n // self.q
        else:
            self.q = 1
            self.p = self.n

    def build_hierarchical_colormap(self):
        """
        Generate a ListedColormap of length n = p * q:
        - Parent group (p_idx = rank // q): maximally distinct Hue via golden ratio step.
        - Sub-group (q_idx = rank % q): same parent Hue, stepped Saturation & Value.
        """
        golden_ratio_conjugate = 0.61803398875
        sub_s4 = [0.45, 0.85, 0.90, 0.95]
        sub_v4 = [0.98, 0.95, 0.72, 0.48]

        colors = []
        for rank in range(self.n):
            p_idx = rank // self.q
            q_idx = rank % self.q

            h = (p_idx * golden_ratio_conjugate) % 1.0

            if self.q == 1:
                s, v = 0.85, 0.92
            elif self.q == 4:
                s, v = sub_s4[q_idx], sub_v4[q_idx]
            else:
                frac = q_idx / (self.q - 1)
                s = 0.45 + 0.50 * frac
                v = 0.98 - 0.50 * frac

            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            colors.append((r, g, b))

        self.cmap = ListedColormap(colors, name=f"hierarchical_p{self.p}_q{self.q}")
        return self.cmap

    def _wrapped_lon_rad(self):
        """Wrap longitude from [0, 2pi] into [-pi, pi] for 2D map projections."""
        return (self.lon_cell + np.pi) % (2.0 * np.pi) - np.pi

    def spherical_to_cartesian(self):
        """Convert (lat, lon) in radians to unit sphere 3D Cartesian coordinates."""
        x = np.cos(self.lat_cell) * np.cos(self.lon_cell)
        y = np.cos(self.lat_cell) * np.sin(self.lon_cell)
        z = np.sin(self.lat_cell)
        return x, y, z

    def plot(self, show=True, dpi=300):
        """Render and save the partition plot in the requested projection."""
        if self.partitions is None:
            self.load_data()
        if self.cmap is None:
            self.build_hierarchical_colormap()

        title = f"{self.title} [{self.proj.upper()}] (n={self.n}: p={self.p}, q={self.q})"
        print(f"Generating {self.proj} plot (n={self.n}, p={self.p}, q={self.q})...")

        if self.proj == "3d":
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(projection="3d")
            x, y, z = self.spherical_to_cartesian()
            scatter = ax.scatter(
                x, y, z,
                c=self.partitions,
                cmap=self.cmap,
                vmin=-0.5,
                vmax=self.n - 0.5,
                s=0.5,
                edgecolor="none",
            )
            ax.set_axis_off()

        elif self.proj in ("robinson", "platecarree"):
            if not HAS_CARTOPY:
                raise ImportError(
                    f"Projection '{self.proj}' requires cartopy. "
                    "Install it via `conda install -c conda-forge cartopy` or use `--proj mollweide`."
                )
            crs = ccrs.Robinson() if self.proj == "robinson" else ccrs.PlateCarree()
            fig = plt.figure(figsize=(14, 7))
            ax = fig.add_subplot(projection=crs)

            lon_deg = np.degrees(self._wrapped_lon_rad())
            lat_deg = np.degrees(self.lat_cell)

            scatter = ax.scatter(
                lon_deg, lat_deg,
                c=self.partitions,
                cmap=self.cmap,
                vmin=-0.5,
                vmax=self.n - 0.5,
                s=0.4,
                edgecolor="none",
                transform=ccrs.PlateCarree(),
            )
            ax.coastlines(linewidth=0.6, color="black")
            ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.5)

        elif self.proj in ("mollweide", "hammer", "aitoff"):
            fig = plt.figure(figsize=(14, 7))
            ax = fig.add_subplot(projection=self.proj)

            lon_rad = self._wrapped_lon_rad()
            scatter = ax.scatter(
                lon_rad, self.lat_cell,
                c=self.partitions,
                cmap=self.cmap,
                vmin=-0.5,
                vmax=self.n - 0.5,
                s=0.4,
                edgecolor="none",
            )
            ax.grid(True, linewidth=0.3, color="gray", alpha=0.5)
            ax.set_xticklabels([])
            ax.set_yticklabels([])

        else:
            raise ValueError(
                f"Unsupported projection '{self.proj}'. "
                "Choose from: mollweide, robinson, platecarree, hammer, aitoff, 3d."
            )

        ax.set_title(title, fontsize=13, pad=12)
        cbar = fig.colorbar(scatter, ax=ax, orientation="horizontal", shrink=0.6, pad=0.05)
        cbar.set_label(f"Processor Rank (0 - {self.n - 1})")

        print(f"Saving plot to {self.output_path}...")
        plt.savefig(self.output_path, dpi=dpi, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot hierarchical MPAS mesh partitions on 2D map projections or a 3D sphere."
    )
    parser.add_argument(
        "-m", "--mesh",
        default="../data/x1.655362.grid.nc",
        help="Input MPAS NetCDF grid/mesh file (default: ../data/x1.655362.grid.nc)",
    )
    parser.add_argument(
        "-i", "--part",
        default="global_hierarchical.part.160",
        help="Input partition assignment file (default: global_hierarchical.part.160)",
    )
    parser.add_argument(
        "-o", "--out",
        default="mpas_global_hierarchical_160.png",
        help="Output PNG image filename (default: mpas_global_hierarchical_160.png)",
    )
    parser.add_argument(
        "--proj",
        default="mollweide",
        choices=["mollweide", "robinson", "platecarree", "hammer", "aitoff", "3d"],
        help="Map projection (default: mollweide)",
    )
    parser.add_argument(
        "-t", "--title",
        default="MPAS Hierarchical Partitioning",
        help="Title header",
    )
    parser.add_argument("-n", type=int, default=160, help="Total number of partitions (n = p * q)")
    parser.add_argument("-p", type=int, default=40, help="Number of parent groups (p)")
    parser.add_argument("-q", type=int, default=4, help="Number of sub-groups per parent (q)")
    parser.add_argument("--no-show", action="store_true", help="Save image without opening interactive window")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    plotter = MpasPartitionPlotter(
        nc_mesh_path=args.mesh,
        part_path=args.part,
        output_path=args.out,
        n=args.n,
        p=args.p,
        q=args.q,
        proj=args.proj,
        title=args.title,
    )
    plotter.plot(show=not args.no_show)
