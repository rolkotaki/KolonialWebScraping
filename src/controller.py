from src.web_sraping import WebScraperRunner
from src.data_management import ReportCreater


def main():
    """Main method which runs everything."""
    WebScraperRunner.run_web_scraping_and_save_data()
    ReportCreater.create_product_distribution_report()


if __name__ == "__main__":
    main()
