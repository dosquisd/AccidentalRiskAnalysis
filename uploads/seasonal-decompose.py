import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

DAY_OF_WEEK_MAP = {
    1: "Lunes",
    2: "Martes",
    3: "Miercoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
    7: "Domingo",
}


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
        df = pd.read_csv(
            ".csv",
            parse_dates=["FECHA_OCURRENCIA"] if True else None,
            index_col="FECHA_OCURRENCIA" if True else None,
        )

    if df.index.dtype != "datetime64[ns]":
        raise ValueError("The DataFrame index must be of datetime type.")

    # Map day of week numbers to names
    df["DIA_SEMANA_OCURRENCIA"] = df["DIA_SEMANA_OCURRENCIA"].map(DAY_OF_WEEK_MAP)

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


if __name__ == "__main__":
    model = "additive"
    df = resample_data(multi_index=True)
    historical = df["TOTAL_ACCIDENTES"]

    result = seasonal_decompose(historical, model=model)
    result.plot()
    plt.tight_layout()
    plt.suptitle("Original")
    plt.show()

    ewm_data = historical.ewm(alpha=0.12).mean()
    result = seasonal_decompose(ewm_data, model=model)
    result.plot()
    plt.tight_layout()
    plt.suptitle(r"EWM $\alpha=0.12$")
    plt.show()
