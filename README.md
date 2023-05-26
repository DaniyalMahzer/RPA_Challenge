# News Scraper

The News Scraper is a Python script designed to scrape news articles from the New York Times website based on specified search criteria. It utilizes the RPAframework to automate web browsing, data extraction, and file management tasks.

## Prerequisites

Before running the script, ensure that you have the following dependencies installed:

- Python 3.x
- RPAframework
- requests

You can install the required dependencies using pip:

# Configration

You can customize the search criteria by modifying the following parameters when creating the NewsScraper instance:

search_text: The phrase to search for in the news articles.
sections: A list of sections to filter the news articles (e.g., ["Politics", "Business", "Sports"]).
months: The number of months to consider for the news articles (defaults to 1 if set to 0).

These variables can be passed as work items.