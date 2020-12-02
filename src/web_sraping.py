from html.parser import HTMLParser
import urllib.request
import copy
import pandas as pd

from src.utils import load_config
from src.settings import CONTAINER_TAG_NAME, CONTAINER_TAG_ATTR_NAME, CONTAINER_TAG_ATTR_VALUE, \
                         TAG_NAME_TO_SEARCH, TAG_ATTR_TO_SEARCH, TAG_ATTR_VALUE_PATTERN, \
                         TAG_FILTER_ATTR_NAME, TAG_FILTER_ATTR_VALUE, HAS_SUB_CONTAINER, SUB_CONTAINER_TAG_NAME, \
                         SUB_CONTAINER_TAG_ATTR_NAME, SUB_CONTAINER_TAG_ATTR_VALUE, \
                         PRODUCT_INFORMATION_CONFIG, \
                         PRODUCT_INFORMATION_TAG_NAME, PRODUCT_INFORMATION_ATTR_NAME, PRODUCT_INFORMATION_ATTR_VALUE, \
                         MAIN_URL_COLLECTION_NEEDED, MAIN_SOURCE_URL, MAIN_URLS_TO_SCRAP_CONFIG, \
                         PRODUCT_SUB_URL_COLL_NEEDED, SUB_SOURCE_URL_BEGINNING, PRODUCT_SUB_URLS_TO_SCRAP_CONFIG, \
                         PRODUCT_SCRAPING_CONFIG, RESULT_FILE, MAIN_CATEG_COL, SUB_CATEG_COL


class ScrapingDoneException(Exception):
    """ScrapingDoneException is a custom Exception class that is to signal when we can exit processing the HTML source.
    The main goal is to save performance by not going through the whole HTML source."""
    pass


class BasicWebScraper(HTMLParser):
    """BasicWebScraper extends from the HTMLParser class from the basic library.
    A BasicWebScraper object takes care of basic web scraping and it is to be extended to further specific classes
    to collect URLs or product information.
    """

    def __init__(self, url, config):
        super(BasicWebScraper, self).__init__()
        self.config = load_config(config)
        self.source_url = url
        self.inside_container = False
        self.inside_sub_container = False
        self.cont_tag_counter = 0
        self.sub_cont_tag_counter = 0

    def get_source_url(self):
        """Returns the source URL that we are scraping."""
        return self.source_url

    def set_inside_container(self, value):
        """Sets the inside_container variable."""
        self.inside_container = value

    def is_inside_container(self):
        """Returns True if we are inside the container tag element. Otherwise False."""
        return self.inside_container

    def set_inside_sub_container(self, value):
        """Sets the inside_sub_container variable, or if the the config does not have a sub-container, it sets the
        original inside_container variable. Then there is no need to use the inside_sub_container, but for simpler
        coding we will use this method."""
        if self.config.get(HAS_SUB_CONTAINER):
            self.inside_sub_container = value
        else:
            self.inside_container = value

    def is_inside_sub_container(self):
        """Returns True if we are inside the sub-container element. Otherwise False.
        Also returns True if we do not have a sub-container, but we are in the container element."""
        if self.config.get(HAS_SUB_CONTAINER):
            return self.inside_sub_container
        else:
            return self.inside_container

    def increase_cont_tag_counter(self):
        """Increases the cont_tag_counter variable by 1.
        The cont_tag_counter variable is needed to know when to exit the process. If a container tag is DIV for example,
        we cannot just exit the process at the next DIV ending tag. So, when we are inside the container, we count
        the same DIV starting tags and make sure we exit the process only when we have had the ending tag for them.
        """
        self.cont_tag_counter += 1

    def decrease_cont_tag_counter(self):
        """Decreases the cont_tag_counter variable by 1. More info on variable at increase_cont_tag_counter()."""
        self.cont_tag_counter -= 1

    def get_cont_tag_counter(self):
        """Returns the value of the cont_tag_counter variable. More info on variable at increase_cont_tag_counter()."""
        return self.cont_tag_counter

    def increase_sub_cont_tag_counter(self):
        """Increases the sub_cont_tag_counter variable by 1.
        The sub_cont_tag_counter variable is needed to know when we exit the sub-container, meaning when we have
        finished collected data for the given product. The theory is the same of for the cont_tag_counter.
        """
        self.sub_cont_tag_counter += 1

    def decrease_sub_cont_tag_counter(self):
        """Decreases the sub_cont_tag_counter variable by 1. More info on variable at
        increase_sub_cont_tag_counter()."""
        self.sub_cont_tag_counter -= 1

    def get_sub_cont_tag_counter(self):
        """Returns the value of the sub_cont_tag_counter variable. More info on variable at
        increase_sub_cont_tag_counter()."""
        return self.sub_cont_tag_counter

    def exit_sub_container(self):
        """Method to be executed when we exit a sub-container. To be implemented in sub-classes."""
        pass

    def handle_starttag(self, tag, attrs):
        """Overrides method from HTMLParser. This is called when we find a starting tag.
        This method takes care of finding the (sub)container tag.
        """
        # if this tag is equal to the container tag, first we check if we are already inside the container or not
        # if we are already inside, then we increase the cont_tag_counter. more info at increase_cont_tag_counter()
        # if we are not in the container yet, we check the attributes and they match,
        # we set the inside_container variable to True, so that we will know it later
        if tag == self.config.get(CONTAINER_TAG_NAME):
            if self.is_inside_container():
                self.increase_cont_tag_counter()
                if not self.config.get(HAS_SUB_CONTAINER):
                    return
            else:
                for attr in attrs:
                    if attr[0] == self.config.get(CONTAINER_TAG_ATTR_NAME) and \
                            attr[1].strip() == self.config.get(CONTAINER_TAG_ATTR_VALUE):
                        self.set_inside_container(True)
                        return
        # if the config has sub-container setup, then:
        # if this tag is equal to the sub-container tag, first we check if we are already inside or not
        # if we are already inside, we increase the sub_cont_tag_counter. more info at increase_sub_cont_tag_counter()
        # if we are not in the sub-container yet, we check the attributes and they match,
        # we set the inside_sub_container variable to True, so that we will know it later
        if self.config.get(HAS_SUB_CONTAINER):
            if tag == self.config.get(SUB_CONTAINER_TAG_NAME):
                if self.is_inside_sub_container():
                    self.increase_sub_cont_tag_counter()
                    return
                for attr in attrs:
                    if attr[0] == self.config.get(SUB_CONTAINER_TAG_ATTR_NAME) and \
                            attr[1].strip() == self.config.get(SUB_CONTAINER_TAG_ATTR_VALUE):
                        self.set_inside_sub_container(True)

    def handle_endtag(self, tag):
        """Overrides method from HTMLParser. This is called when we find an ending tag.
        This method takes care of tracing the ending tags with the same name as the container tag. This is required
        to know when we leave the container element so that we can exit the process. Upon exiting the main container
        element, we throw a ScrapingDoneException exception to signal the end of the process.
        Also, this method takes care of tracing the ending tags of sub-containers as well, if any.
        This is required to know when we have finished collecting the data for one given sub-container. Upon exiting
        the sub-container we execute the exit_sub_container() method to perform any operation that we may want.
        """
        # if the config has sub-container setup, then:
        # if we are inside the sub-container and we find a tag with the same tag name, we finish collection data for
        # the given product
        if self.config.get(HAS_SUB_CONTAINER):
            if self.is_inside_sub_container():
                if tag == self.config.get(SUB_CONTAINER_TAG_NAME):
                    if self.get_sub_cont_tag_counter() == 0:
                        self.set_inside_sub_container(False)
                        self.exit_sub_container()  # to be implemented in sub-classes. here it does nothing
                    else:
                        self.decrease_sub_cont_tag_counter()
        # if we are inside the container and we find a tag with the same tag name, we decide whether to exit the process
        # or just to decrease the cont_tag_counter variable as the ending tag is not for our container tag
        if self.is_inside_container():
            if tag == self.config.get(CONTAINER_TAG_NAME):
                if self.get_cont_tag_counter() == 0:
                    if not self.config.get(HAS_SUB_CONTAINER):
                        self.exit_sub_container()  # to be implemented in sub-classes. here it does nothing
                    raise ScrapingDoneException()
                else:
                    self.decrease_cont_tag_counter()

    def get_html_by_url(self, url):
        """Returns the HTML source of a web page located at the given URL."""
        with urllib.request.urlopen(url) as response:
            html_source = response.read().decode('utf-8')
        return html_source


class URLCollector(BasicWebScraper):
    """URLCollector extends from BasicWebScraper.
    As a BasicWebScraper object already takes cares of the web scraping, this class only specifies the process
    for collecting the URL list that we will have to scrap.
    """

    def __init__(self, url, config):
        super(URLCollector, self).__init__(url, config)
        self.url_list = []

    def add_url_to_list(self, url):
        """Adds the found URL to the list to be returned."""
        self.url_list.append(url)

    def get_url_list(self):
        """Returns the list of URLs that have been found."""
        return self.url_list

    def handle_starttag(self, tag, attrs):
        """"""
        """Overrides method from BasicWebScraper (and HTMLParser). This is called when we find a starting tag.
        The super of this method takes care of finding the (sub)container tag. 
        This overridden version also checks whether we have found the required tag(s) inside the (sub)container.
        If the required tag is found and all parameters match, we add the required value (URL) to the list to be returned.
        """
        tag_found = False
        # if we are inside the (sub)container and we are looking for the the current tag, then we check whether
        # we need to filter the tag or not. if the tag is one that we are looking for, we set the tag_found to True
        if self.is_inside_sub_container() and tag == self.config.get(TAG_NAME_TO_SEARCH):
            if self.config.get(TAG_FILTER_ATTR_NAME) is not None:
                for attr in attrs:
                    if attr[0] == self.config.get(TAG_FILTER_ATTR_NAME):
                        if attr[1].strip() == self.config.get(TAG_FILTER_ATTR_VALUE):
                            tag_found = True
                            break
            else:
                tag_found = True
        # if this is a tag that we are looking for, we check the attributes and add the required value (URL) to the list
        if tag_found:
            for attr in attrs:
                if attr[0] == self.config.get(TAG_ATTR_TO_SEARCH):
                    if self.config.get(TAG_ATTR_VALUE_PATTERN) is None:
                        self.add_url_to_list(attr[1].strip())
                    elif self.config.get(TAG_ATTR_VALUE_PATTERN) is not None and \
                            self.config.get(TAG_ATTR_VALUE_PATTERN) in attr[1].strip():
                        self.add_url_to_list(attr[1].strip())
        super(URLCollector, self).handle_starttag(tag, attrs)

    def get_urls_to_scrap(self):
        """Runs the feed() method of the HTMLParser class and when finished, returns the collected URL list."""
        if self.config is None:
            return []
        html_source = self.get_html_by_url(self.get_source_url())
        try:
            self.feed(html_source)
        except ScrapingDoneException:
            pass
        return self.get_url_list()


class ProductScraper(BasicWebScraper):
    """ProductScraper extends from BasicWebScraper.
    As a BasicWebScraper object already takes cares of the web scraping, this class only specifies the process
    for collecting product information.
    """

    def __init__(self, url, config):
        super(ProductScraper, self).__init__(url, config)
        self.product_list = []
        self.current_product_dict = {}
        # self.empty_product_dict = {}
        self.data_to_be_collected = False
        self.item_to_be_collected = ''

    def set_data_to_be_collected(self, value, item):
        """Setting variables for data collection."""
        self.data_to_be_collected = value
        self.item_to_be_collected = item

    def get_item_to_be_collected(self):
        """Returns the name of the item that is to be collected."""
        return self.item_to_be_collected

    def is_data_to_be_collected(self):
        """Returns True if the current tag data should be collected."""
        return self.data_to_be_collected

    # def create_empty_product_dict(self):
    #     """Creates an empty"""
    #     for key in self.config.get(PRODUCT_INFORMATION_CONFIG):
    #         self.empty_product_dict[key] = ''

    def reset_current_product_dict(self):
        """Resets the current product dictionary to have empty values."""
        for key in self.config.get(PRODUCT_INFORMATION_CONFIG):
            self.current_product_dict[key] = ''

    def add_to_current_product_dict(self, key, value):
        """Adds a value to the current product dictionary."""
        self.current_product_dict[key] = value

    def get_current_product_dict(self):
        """Returns the current product dictionary."""
        return self.current_product_dict

    def exit_sub_container(self):
        """Method to be executed upon exiting the sub-container. Appends the current product dictionary to the list."""
        self.product_list.append(self.get_current_product_dict())
        self.product_list = copy.deepcopy(self.product_list)  # !!!!! - I lost a lot of time here, should have known, list is by reference
        self.reset_current_product_dict()

    def get_product_data_list(self):
        """Returns the whole product list for the (sub)category."""
        return self.product_list

    def handle_starttag(self, tag, attrs):
        """"""
        """Overrides method from BasicWebScraper (and HTMLParser). This is called when we find a starting tag.
        The super of this method takes care of finding the (sub)container tag.
        This overridden version also checks whether we have found any product information and if yes,
        we add the data to the current product dictionary that we will append to the product list upon exiting
        the (sub)container.
        """
        # if we are inside the (sub)container and we are looking for the the current tag, then we check whether
        # the tag has the required attribute or not. if the tag is one that we are looking for, we get the required
        # product data and save it into the current product dictionary
        if self.is_inside_sub_container():
            for product_info, setup in self.config.get(PRODUCT_INFORMATION_CONFIG).items():
                if tag == setup.get(PRODUCT_INFORMATION_TAG_NAME):
                    for attr in attrs:
                        if attr[0] == setup.get(PRODUCT_INFORMATION_ATTR_NAME):
                            if attr[1].strip() == setup.get(PRODUCT_INFORMATION_ATTR_VALUE):
                                self.set_data_to_be_collected(True, product_info)
                                break
        super(ProductScraper, self).handle_starttag(tag, attrs)

    def handle_data(self, data):
        """Overrides method from HTMLParser. If we get to a data, we check if the current data is to be collected or not.
        If yes, we add the data to the current product dictionary.
        """
        if self.is_data_to_be_collected():
            self.add_to_current_product_dict(self.get_item_to_be_collected(), data.strip())
        self.set_data_to_be_collected(False, '')

    def get_product_scraping_data(self):
        """Runs the feed() method of the HTMLParser class and when finished, returns the collected product information.
        """
        if self.config is None:
            return []
        # self.create_empty_product_dict()
        html_source = self.get_html_by_url(self.get_source_url())
        try:
            self.feed(html_source)
        except ScrapingDoneException:
            pass
        return self.get_product_data_list()


class WebScraperRunner:
    """WebScraperRunner manages the whole workflow of web scraping.
    # Should have more methods, better-organized, but I was running out of time ...
    """

    @classmethod
    def run_web_scraping_and_save_data(cls):
        """Runs the web scraping workflow, collects the product information data for each main and sub-category,
        and then it saves the whole list into a CSV file.
        # Improvement should be be save the currency and price separately, to have integer price fields, for example.
        # Many improvements could be done ...
        """
        product_df = pd.DataFrame()
        if load_config(MAIN_URL_COLLECTION_NEEDED):
            url = load_config(MAIN_SOURCE_URL)
            main_url_collector = URLCollector(url, MAIN_URLS_TO_SCRAP_CONFIG)
            main_url_list = main_url_collector.get_urls_to_scrap()
            print(main_url_list)

            if load_config(PRODUCT_SUB_URL_COLL_NEEDED):
                for main_url in main_url_list:
                    url = load_config(SUB_SOURCE_URL_BEGINNING) + main_url
                    sub_url_collector = URLCollector(url, PRODUCT_SUB_URLS_TO_SCRAP_CONFIG)
                    sub_url_list = sub_url_collector.get_urls_to_scrap()
                    print(sub_url_list)

                    for sub_url in sub_url_list:
                        url = load_config(SUB_SOURCE_URL_BEGINNING) + sub_url
                        product_scrapper = ProductScraper(url, PRODUCT_SCRAPING_CONFIG)
                        product_data = product_scrapper.get_product_scraping_data()
                        cur_product_df = pd.DataFrame(product_data)
                        cur_product_df.insert(0, MAIN_CATEG_COL, main_url.split('/')[2][main_url.split('/')[2].find('-')+1:])
                        cur_product_df.insert(1, SUB_CATEG_COL, sub_url.split('/')[3][sub_url.split('/')[3].find('-')+1:])
                        product_df = product_df.append(cur_product_df)
        print(len(product_df))
        print(product_df.head())
        product_df.to_csv(RESULT_FILE)
        return product_df
