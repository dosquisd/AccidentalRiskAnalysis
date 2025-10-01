import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def filter_resampled_data(df: pd.DataFrame, col: str) -> pd.DataFrame:
    interest_columns = list(filter(lambda df_col: df_col.startswith(col), df.columns))
    columns = list(map(lambda df_col: df_col.split("_")[1].replace("-", " ").strip(), interest_columns))
    new_df = pd.DataFrame()
    for i in range(len(interest_columns)):
        new_df[columns[i]] = df[interest_columns[i]]

    return new_df


df = pd.read_csv("resample_data.csv", parse_dates=["FECHA_OCURRENCIA"], index_col="FECHA_OCURRENCIA")

# Boxplots by gravity
gravity_df = filter_resampled_data(df, "GRAVEDAD")
gravity_type = []
gravity_type_count = []
gravity_datetime = []
for col in gravity_df.columns:
    sub_df = gravity_df[[col]]
    for (date, row) in sub_df.iterrows():
        gravity_type.append(col)
        gravity_type_count.append(row)
        gravity_datetime.append(date)

gravity_plot_df = pd.DataFrame({"date": gravity_datetime, "type": gravity_type, "count": gravity_type_count})

print(gravity_plot_df)

# gravity_plot_df["count"] = pd.to_numeric(gravity_plot_df["count"])
gravity_plot_df["count"] = gravity_plot_df["count"].astype(float)

fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(gravity_plot_df, x="type", y="count", ax=ax)

# gravity_df.boxplot()
plt.show()

# print(gravity_df.head())
