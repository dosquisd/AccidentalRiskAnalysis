import geopandas as gpd
import pandas as pd

from utils.constants import DAY_OF_WEEK_MAP, PROCESSED_DATA_DIR


def load_processed_original_data(
    *,
    as_geopandas: bool = False,
    date_as_index: bool = False,
    parse_dates: bool = False,
) -> pd.DataFrame:
    """
    Loads the processed traffic accident data from a CSV file.

    Args:
        as_geopandas (bool): If True, returns a GeoDataFrame. If False, returns a DataFrame.
        date_as_index (bool): If True, sets 'FECHA_OCURRENCIA' as the index.
        parse_dates (bool): If True, parses 'FECHA_OCURRENCIA' as datetime.

    Returns:
        Union[pd.DataFrame, gpd.GeoDataFrame]: The loaded data as a DataFrame or GeoDataFrame.
    """
    data_path = PROCESSED_DATA_DIR / "dataset.csv"
    df = pd.read_csv(
        data_path,
        parse_dates=["FECHA_OCURRENCIA"] if parse_dates else None,
        index_col="FECHA_OCURRENCIA" if date_as_index else None,
    )

    if not as_geopandas:
        return df

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",  # WGS84
    )
    return gdf


def resample_data(
    *,
    df: pd.DataFrame = None,
    freq: str = "1W",
    multi_index: bool = False,
) -> pd.DataFrame:
    """
    Resamples the traffic accident data to a specified frequency, aggregating counts and categories.

    Args:
        df (pd.DataFrame): The DataFrame to resample. If None, loads the default processed data.
        freq (str): The resampling frequency (e.g., '1D' for daily, '1W' for weekly).
        multi_index (bool): If True, returns a DataFrame with MultiIndex columns.

    Returns:
        pd.DataFrame: The resampled DataFrame with aggregated counts and categories.
    """
    if df is None:
        df = load_processed_original_data(date_as_index=True, parse_dates=True)

    if df.index.dtype != "datetime64[ns]":
        raise ValueError("The DataFrame index must be of datetime type.")

    # Map day of week numbers to names
    df["DIA_SEMANA_OCURRENCIA"] = df["DIA_SEMANA_OCURRENCIA"].map(
        DAY_OF_WEEK_MAP
    )

    # Resample and aggregate
    resampled_df = df.resample(freq).agg(
        {
            "OBJECTID": "count",
            "GRAVEDAD": lambda x: x.value_counts().to_dict(),
            "CLASE": lambda x: x.value_counts().to_dict(),
            "LOCALIDAD": lambda x: x.value_counts().to_dict(),
            "DIA_SEMANA_OCURRENCIA": lambda x: x.value_counts().to_dict(),
        }
    )

    resampled_df.rename(columns={"OBJECTID": "TOTAL_ACCIDENTES"}, inplace=True)

    # Expand dictionary columns into separate columns
    dict_columns = ["GRAVEDAD", "CLASE", "LOCALIDAD", "DIA_SEMANA_OCURRENCIA"]
    if multi_index:
        expanded = (
            pd.concat(
                [resampled_df[col].apply(pd.Series) for col in dict_columns],
                axis=1,
                keys=dict_columns,
            )
            .fillna(0)
            .astype(int)
        )

        resampled_df = pd.concat(
            [resampled_df.drop(columns=dict_columns), expanded], axis=1
        )

        resampled_df.columns = pd.MultiIndex.from_tuples(
            [
                col if isinstance(col, tuple) else (col, "")
                for col in resampled_df.columns
            ]
        )

        return resampled_df

    for col in dict_columns:
        expanded_cols = resampled_df[col].apply(pd.Series).fillna(0).astype(int)
        expanded_cols.columns = [
            f"{col}-{str(c).replace(' ', '_')}" for c in expanded_cols.columns
        ]
        resampled_df = pd.concat(
            [resampled_df.drop(columns=[col]), expanded_cols], axis=1
        )

    return resampled_df
