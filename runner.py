import csv
import logging
import requests

from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG, filename='logs.log')


CHROME_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
        'image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-GB,en;q=0.7',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Chromium";v="112", "Brave";v="112", "Not:A-Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': "macOS",
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
}
RESULT_FILE = 'reviews.csv'


def process_page(url):
    response = requests.get(url, headers=CHROME_HEADERS, timeout=180)
    logging.debug(response)
    soup = BeautifulSoup(response.text, 'html.parser')
    product_name = soup.find('a', {'data-hook': 'product-link'}).string
    reviews = soup.find_all('div', {'data-hook': 'review'})
    with open(RESULT_FILE, 'a', encoding='utf-8') as file_:
        csv_writer = csv.writer(file_)
        for review in reviews:
            try:
                rating = review.find('i', {'data-hook': 'review-star-rating'}).find('span')\
                    .string.replace(' out of 5 stars', '')
            except AttributeError:
                # this exception occures when all original customers reviews are parsed and
                # current review is a review from 'From other countries' section
                # so, return with no-next-page flag
                return False
            title = review.find('a', {'data-hook': 'review-title'}).find('span').string
            location_and_date = review.find('span', {'data-hook': 'review-date'}).string
            options = review.find('a', {'data-hook': 'format-strip'})
            options = ' | '.join(options.contents[::2]) if options else None
            verified_purchase = bool(review.find('span', {'data-hook': 'avp-badge'}))
            text = review.find('span', {'data-hook': 'review-body'})
            text = text.find('span', recursive=False) if text else None
            text = text.text if text else None
            helpful_count = review.find('span', {'data-hook': 'helpful-vote-statement'})
            helpful_count = helpful_count.string if helpful_count else None
            if options is None:
                logging.warning('Options for "%s" review are ommitted', title)
            if text is None:
                logging.warning('Review text for "%s" review is ommitted', title)
            logging.debug('Got review with title "%s"', title)
            csv_writer.writerow([product_name, rating, title, location_and_date,
                                 options, verified_purchase, text, helpful_count])
    next_page_available = soup.find(id='cm_cr-pagination_bar').find('li', class_='a-last').find('a')
    return next_page_available


def parse_reviews(base_url: str):
    with open(RESULT_FILE, 'w', encoding='utf-8') as file_:
        csv_writer = csv.writer(file_)
        csv_writer.writerow(['product_name', 'rating', 'title', 'location_and_date',
                             'options', 'verified_purchase', 'text', 'helpful_count'])
    page_number = 1
    next_page_available = True
    while next_page_available:
        url = f'{base_url}?pageNumber={page_number}'
        logging.debug('Going to %s ...', url)
        next_page_available = process_page(url)
        page_number += 1


if __name__ == '__main__':
    parse_reviews(
        'https://www.amazon.com/Introducing-Kindle-Scribe-the-first-Kindle-for-reading-and-writing'
        '/product-reviews/B09BS26B8B/'
    )
