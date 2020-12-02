
# constant for the config file
CONFIG_FILE = '../config/config.yml'

# config name constants for web_scraping
CONTAINER_TAG_NAME = 'container_tag_name'
CONTAINER_TAG_ATTR_NAME = 'container_tag_attr_name'
CONTAINER_TAG_ATTR_VALUE = 'container_tag_attr_value'
TAG_NAME_TO_SEARCH = 'tag_name_to_search'
TAG_ATTR_TO_SEARCH = 'tag_attr_to_search'
TAG_ATTR_VALUE_PATTERN = 'tag_attr_value_pattern'
TAG_FILTER_ATTR_NAME = 'tag_filter_attr_name'
TAG_FILTER_ATTR_VALUE = 'tag_filter_attr_value'
HAS_SUB_CONTAINER = 'has_sub_container'
SUB_CONTAINER_TAG_NAME = 'sub_container_tag_name'
SUB_CONTAINER_TAG_ATTR_NAME = 'sub_container_tag_attr_name'
SUB_CONTAINER_TAG_ATTR_VALUE = 'sub_container_tag_attr_value'

# config name constants for web_scraping, specifically for product scraping
PRODUCT_SCRAPING_CONFIG = 'product_scraping'
PRODUCT_INFORMATION_CONFIG = 'product_information'
PRODUCT_INFORMATION_TAG_NAME = 'tag_name'
PRODUCT_INFORMATION_ATTR_NAME = 'attr_name'
PRODUCT_INFORMATION_ATTR_VALUE = 'attr_value'

# constants for controller
MAIN_URL_COLLECTION_NEEDED = 'main_url_collection_needed'
MAIN_SOURCE_URL = 'main_source_url'
MAIN_URLS_TO_SCRAP_CONFIG = 'main_urls_to_scrap'
PRODUCT_SUB_URL_COLL_NEEDED = 'product_sub_url_coll_needed'
SUB_SOURCE_URL_BEGINNING = 'sub_source_url_beginning'
PRODUCT_SUB_URLS_TO_SCRAP_CONFIG = 'product_sub_urls_to_scrap'

# constants for data management
RESULT_FILE = '../files/result.csv'
MAIN_CATEG_COL = 'main_categ'
SUB_CATEG_COL = 'sub_categ'

REPORT_FILE_MAIN = '../files/main_categ_dist_report.png'
REPORT_FILE_SUB = '../files/sub_categ_dist_report.png'
