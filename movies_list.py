import requests
from requests.exceptions import RequestException
from lxml import etree
import re
import copy
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pymongo

# browser = webdriver.Chrome()


client = pymongo.MongoClient('localhost', 27017)
db = client['movies']
collection = db['list']

chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)
wait = WebDriverWait(browser, 10)


def get_page(url):

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


def parse_page(response):
    re_response = copy.copy(response)
    response = etree.HTML(str(response))
    title = response.xpath('//p[@class="title g-clear"]/span[@class="s1"]/text()')
    star = response.xpath('//p[@class="star"]/text()')
    img = response.xpath('//div[@class="cover g-playicon"]/img/@src')
    href = response.xpath('//li[@class="item"]/a[@class="js-tongjic"]/@href')
    re_response = re_response.replace("<span class='s2'>", '<span class="s2">None')
    re_response = etree.HTML(re_response)
    score = re_response.xpath('//p[@class="title g-clear"]/span[@class="s2"]//text()')
    add = 'http://www.yn-dove.cn'

    for item in range(len(title)):          
        yield {
            'title': title[item],
            'score': score[item],
            'star': star[item],
            'img': img[item],
            'href': add+href[item].replace('.', '', 1)
        }


def page_numbers(url):

    try:
        browser.get(url)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body > section'))
        )
        pages = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#js-ew-page > a:nth-child(8)'))
        )
        return pages.text
    except TimeoutException:
        return page_numbers(url)


def next_page_url():

    response = requests.get('http://www.yn-dove.cn/movie.php?m=list.php?cat=all&pageno=1').text
    response = etree.HTML(response)
    url_list = response.xpath('//dd[@class="item g-clear js-listfilter-content" and @style="margin: 0;"]//a/@href')
    return url_list


def write(item):
    titles = set()
    if item['title'] in titles:
        print('Already existed.')
    else:
        titles.add(item['title'])
        return collection.insert(item)


def main():

    for url in next_page_url():
        url = 'http://www.yn-dove.cn/movie.php'+url
        pages = page_numbers(url)
      # print(url,'\t',pages)
        pages = int(pages)
        for page in range(1, pages+1):
            re_url = url.replace('pageno=1', 'pageno={}')
            reurl = re_url.format(page)
            response = get_page(reurl)
            for item in parse_page(response):
                write(item)


if __name__ == "__main__":
    main()
