import pandas as pd


def group_by_resample(df: pd.DataFrame, col: str) -> dict[str, pd.DataFrame]:
    unique_cols = original_df[col].unique().tolist()
    data = {}
    for unique_col in unique_cols:
        data[unique_col] = df[df[col] == unique_col].resample("1W").size()

    return data


# All df
df = pd.DataFrame()

# Read csv
original_df = pd.read_csv("./.csv", parse_dates=["FECHA_OCURRENCIA"]).set_index("FECHA_OCURRENCIA")

# Group by LOCALIDAD
localities = group_by_resample(original_df, "LOCALIDAD")
for locality, locality_df in localities.items():
    df[f"LOCALIDAD_{locality.replace(" ", "-")}"] = locality_df

# Group by GRAVEDAD
gravities = group_by_resample(original_df, "GRAVEDAD")
for gravity, gravity_df in gravities.items():
    df[f"GRAVEDAD_{gravity.replace(" ", "-")}"] = gravity_df

# Group by CLASE
classes = group_by_resample(original_df, "CLASE")
for class_i, class_df in gravities.items():
    df[f"CLASE_{class_i.replace(" ", "-")}"] = class_df

print(df.head())
df.to_csv("resample_data.csv")
