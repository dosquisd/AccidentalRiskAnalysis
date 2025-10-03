import scienceplots  # noqa: F401
import matplotlib.pyplot as plt


def configure_scienceplots():
    plt.style.use(["science", "nature"])
    plt.rcParams.update(
        {
            "font.size": 12,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "axes.labelsize": 12,
            "legend.fontsize": 12,
        }
    )
