import csv
import logging
import requests

from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG, filename='logs.log')


CHROME_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,'
        'image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
}
RESULT_FILE = 'reviews.csv'


def process_page(url):
    response = requests.get(url, headers=CHROME_HEADERS, timeout=180)
    logging.debug(response)
    soup = BeautifulSoup(response.text, 'html.parser')
    reviews = soup.find_all('div', {'data-hook': 'review'})
    with open(RESULT_FILE, 'a', encoding='utf-8') as file_:
        csv_writer = csv.writer(file_)
        for review in reviews:
            rating = review.find('i', {'data-hook': 'review-star-rating'}).find('span')\
                .string.replace(' out of 5 stars', '')
            title = review.find('a', {'data-hook': 'review-title'}).find('span').string
            location_and_date = review.find('span', {'data-hook': 'review-date'}).string
            option, setup, offer_type = review.find('a', {'data-hook': 'format-strip'})\
                .contents[::2]
            verified_purchase = bool(review.find('span', {'data-hook': 'avp-badge'}))
            text = review.find('span', {'data-hook': 'review-body'})\
                .find('span', recursive=False).text
            helpful_count = review.find('span', {'data-hook': 'helpful-vote-statement'})
            helpful_count = helpful_count.string if helpful_count else None
            logging.debug('Got review with title "%s"', title)
            csv_writer.writerow([rating, title, location_and_date, option, setup,
                                 offer_type, verified_purchase, text, helpful_count])
    next_page_available = soup.find(id='cm_cr-pagination_bar').find('li', class_='a-last').find('a')
    return next_page_available


def parse_reviews(base_url: str):
    with open(RESULT_FILE, 'w', encoding='utf-8') as file_:
        csv_writer = csv.writer(file_)
        csv_writer.writerow(['rating', 'title', 'location_and_date', 'option',
                             'setup', 'offer_type', 'verified_purchase',
                             'text', 'helpful_count'])
    page_number = 0
    next_page_available = True
    while next_page_available:
        page_number += 1
        url = f'{base_url}?ie=UTF8&pageNumber={page_number}'
        logging.debug('Going to %s ...', url)
        next_page_available = process_page(url)


if __name__ == '__main__':
    parse_reviews(
        'https://www.amazon.com/Introducing-Kindle-Scribe-the-first-Kindle-for-reading-and-writing'
        '/product-reviews/B09BS26B8B/'
    )
