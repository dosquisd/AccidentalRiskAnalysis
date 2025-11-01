from typing import Union

import geopandas as gpd
import pandas as pd

from utils.constants import RAW_DATA_DIR

original_data_file = (
    RAW_DATA_DIR
    / "accidente-de-trafico-en-bogota-entre-2007-y-2017-geopoint.csv"
)


def load_raw_data(
    as_geopandas: bool = False,
) -> Union[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Loads the raw traffic accident data from a CSV file.

    Args:
        as_geopandas (bool): If True, returns a GeoDataFrame. If False, returns a DataFrame.

    Returns:
        Union[pd.DataFrame, gpd.GeoDataFrame]: The loaded data as a DataFrame or GeoDataFrame.
    """
    df = pd.read_csv(original_data_file, sep=";")

    # Parse geo points
    geopoints = df["Geo Point"].str.split(",", expand=True).astype(float)
    geopoints.columns = ["latitude", "longitude"]

    # Combine dataframes
    df = pd.concat([df, geopoints], axis=1)

    if not as_geopandas:
        return df

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",  # WGS84
    )

    return gdf
