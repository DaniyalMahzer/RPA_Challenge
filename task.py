import os

from RPA.Robocorp.WorkItems import WorkItems

from scrapper import NewsScraper
from variables import search, sections, months


env = os.environ.get('stage')
if env == 'cloud':
    print('Processing with workitems.')
    wi = WorkItems()
    wi.get_input_work_item()
    payload = wi.get_work_item_payload()
    sections = payload.get('sections')
    months = payload.get('months', 0)
    search_phrase = payload.get('search', '')
else:
    print('processing with local variables.')
scraper = NewsScraper(search, sections, months)
scraper.start()
