import asyncio
from bs4 import BeautifulSoup
import utils
import random
import lxml

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
}

# id магазинов. Например: ['г. Москва, ул Новокузнецкая, д 13 стр 1',]
stores_id = []

url = 'https://borisik.ru'

# Список любимых товаров. Например: ['/catalog/goods/bokovnik-nerki-kh-k-1kg/',]
products_uri = []


async def get_products():
    find_products_in_stores = {}

    for store_id in stores_id:
        find_products_in_store = []
        for product_uri in products_uri:
            # Кол-во повторов, чтобы получить html документ с товаром
            for i in range(utils.number_of_attempts):
                # Пауза между запросами, помогает при блокировке запросов сайтом
                sleep_time = round(random.uniform(utils.pause_between_requests_products['begin'],
                                                  utils.pause_between_requests_products['end']), 2)
                print(f'засыпаю на {sleep_time} c.')
                await asyncio.sleep(sleep_time)
                html = await utils.get_html(url, product_uri, headers)
                if html:
                    break
                else:
                    # Пауза между попытками
                    await asyncio.sleep(utils.pause_between_attempts_to_get_html)
            if html:
                price_primary = ''
                discount = ''
                soup = BeautifulSoup(html[0], 'lxml')
                title_sku = await _get_title_sku(product_uri, soup, store_id)
                shop_addr = store_id
                print(f'  -- В магазине {shop_addr}:')
                price_regular = await _get_price_regular(product_uri, soup,
                                                         store_id)
                enough = await _get_enough(product_uri, shop_addr, soup, store_id)

                find_products_in_store.append(
                    {
                        'title_sku': title_sku,
                        'shop_addr': shop_addr,
                        'price_regular': price_regular,
                        'price_primary': price_primary,
                        'discount': discount,
                        'enough': enough,
                        'url': url + product_uri
                    }
                )
        find_products_in_stores[store_id] = find_products_in_store
    return find_products_in_stores


async def _get_enough(product_uri, shop_addr, soup, store_id):
    try:
        store_list = soup.find('div',
                               class_='lstcnt lstadr storeblock storelist').find_all(
            'div', class_='adritm')
        for store in store_list:
            div_addres_store = store.find('div', class_='adr_c1').find(
                'span').get_text(
                strip=True).replace('\u00A0', '')
            if div_addres_store == shop_addr:
                enough = store.find_all('div', class_='adr_b2')[1].find(
                    'span').get_text(
                    strip=True).replace('\u00A0', '')
                print(f'  -- {enough}')
                break
    except:
        enough = ''
        print(
            f"Не удалось прочитать наличие товара {product_uri} в магазине {store_id}")
    return enough


async def _get_price_regular(product_uri, soup, store_id):
    try:
        price_regular = soup.find(
            'div', class_='prd_rtp prd_rtp1').get_text(
            strip=True).replace(
            '\u00A0', '')
        print(f'  -- Обычная цена {price_regular}:')
    except:
        price_regular = ''
        print(
            f'Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}')
    return price_regular


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('div', class_='prd_hdr').getText(
            strip=True).replace('\u00A0', '')
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")
    return title_sku
