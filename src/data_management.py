import pandas as pd
import matplotlib.pyplot as plt

from src.settings import RESULT_FILE, REPORT_FILE_MAIN

# It would be nice to have separate classes for data writing, reading, etc ...


class ReportCreater:
    """The ReportCreater class is responsible for creating reports based on the scraped product data."""

    @classmethod
    def create_product_distribution_report(cls):
        """Creates a chart report on the main category product distribution.
        How many products each main category has.
        """
        df = pd.read_csv(RESULT_FILE)
        df.main_categ.value_counts().plot(kind='bar', color='blue', figsize=(25, 25))
        plt.savefig(REPORT_FILE_MAIN)
        # plt.show()
