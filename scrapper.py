import datetime
import re
import os
import shutil
import time

from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from RPA.Archive import Archive
from RPA.HTTP import HTTP
from SeleniumLibrary.errors import ElementNotFound
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.by import By

TEMP = f"{os.getcwd()}/temp"
OUTPUT = f"{os.getcwd()}/output"


class NewsScraper:

    def __init__(self, search, sections, months):
        self.browser = Selenium()
        self.base_url = 'https://www.nytimes.com/'
        self.news_list = []
        self.search = search
        self.sections = sections
        self.months = months
        self.files = Files()
        self.archive = Archive()
        self.request = HTTP()

    @staticmethod
    def create_directories():
        if not os.path.exists(TEMP):
            os.mkdir(TEMP)
        if not os.path.exists(OUTPUT):
            os.mkdir(OUTPUT)
        for path in [OUTPUT, TEMP]:
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

    def start(self):
        print('Started process.')
        self.create_directories()
        self.browser.open_available_browser(self.base_url, maximized=True)

        self.search_news()
        self.apply_section_filters()
        self.apply_date_filter()
        self.get_news()
        self.finish()

    def search_news(self):
        print(f'Searching with phrase: {self.search}')
        self.browser.click_element_if_visible('//button[contains(@class, "css-tkwi90")]')
        self.browser.input_text_when_element_is_visible('//input[@data-testid="search-input"]', self.search)
        self.browser.press_keys('//input[@data-testid="search-input"]', 'RETURN')

    def apply_section_filters(self):
        if self.sections:
            self.browser.click_element_when_clickable('//label[text()="Section"]')
            for section in self.sections:
                try:
                    self.browser.click_element_if_visible(f'//span[text()="{section}"]//..//input')
                except AssertionError and ElementNotFound:
                    pass

    def apply_date_filter(self):
        to_date = datetime.datetime.now()
        from_date = to_date - relativedelta(months=self.months)
        to_date = to_date.strftime('%m/%d/%Y')
        from_date = from_date.strftime('%m/%d/%Y')

        print(f'Setting date range from {from_date} to {to_date}.')
        self.browser.click_element_when_visible('//button[@data-testid="search-date-dropdown-a"]')
        self.browser.click_element_when_visible('//button[@aria-label="Specific Dates"]')
        self.browser.input_text_when_element_is_visible('//input[@data-testid="DateRange-startDate"]', from_date)
        self.browser.press_keys('//input[@data-testid="DateRange-endDate"]', to_date)
        self.browser.press_keys('//input[@data-testid="DateRange-endDate"]', 'RETURN')

    def get_news(self):
        show_more = True
        while show_more:
            try:
                self.browser.find_element('//button[contains(text(),"Show More")]')
                self.browser.scroll_element_into_view('//button[contains(text(),"Show More")]')
                time.sleep(1)
                self.browser.click_element_when_visible('//button[contains(text(),"Show More")]')
            except AssertionError:
                show_more = False
            except ElementNotFound:
                show_more = False

        for news_element in self.browser.find_elements('//li[@data-testid="search-bodega-result"]'):
            news = {}
            title = news_element.find_element(By.XPATH, './/h4[contains(@class,"css-2fgx4k")]').text
            news['title'] = title
            print(f'Reading news with title {title}')

            date = news_element.find_element(By.XPATH, './/span[@data-testid="todays-date"]').text
            news['date'] = date

            try:
                description = news_element.find_element(By.XPATH, './/p[@class="css-16nhkrn"]').text
            except Exception as e:
                print(f'error = {str(e)}')
                print(f'Description not found for {title}')
                description = ''
            news['description'] = description
            try:
                image = news_element.find_element(By.XPATH, './/img')
            except Exception as e:
                print(f'error = {str(e)}')
                print(f'Image not found for {title}')
                image = None
            if image:
                download_url = image.get_attribute('src')
                file_name = f'{title}.png'
                file_path = f'{TEMP}/{file_name}'
                self.request.download(download_url, file_path)
            else:
                file_name = ''
            news['file_name'] = file_name
            self.parse_title_and_description(news)

            self.news_list.append(news)

    def parse_title_and_description(self, news):
        news['contains_any_amount_of_money'] = False
        title_description = news['title'] + news['description']
        pattern = r'\\$\d+\.?\d*|\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b\d+\s+dollars\b|\b\d+\s+USD\b'
        match = re.search(pattern, title_description)
        if match:
            news['contains_any_amount_of_money'] = True

        count = title_description.count(self.search)
        news['count'] = count

    def finish(self):
        self.files.create_workbook(f'{OUTPUT}/nytimes.xlsx', 'xlsx')
        if self.news_list:
            for news in self.news_list:
                self.files.append_rows_to_worksheet(news, header=True)
            self.files.save_workbook()
            self.files.close_workbook()
            self.archive.archive_folder_with_zip(f'{TEMP}', f'{OUTPUT}/news_images.zip', recursive=True)
        else:
            print('no record found.')
        print('Process Completed.')
