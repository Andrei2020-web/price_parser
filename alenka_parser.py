import asyncio
from bs4 import BeautifulSoup
import utils
import random
import lxml

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
}

stores_id = [
    'Алёнка',
]

url = 'https://www.alenka.ru'

# Список любимых товаров. Например: ['/product/konfety_stolichnye_krasnyy_oktyabr/',]
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
                enough = ''
                soup = BeautifulSoup(html[0], 'lxml')
                title_sku = await _get_title_sku(product_uri, soup, store_id)
                shop_addr = store_id
                print(f'  -- В магазине {shop_addr}:')
                production_date = await _get_production_date(product_uri, soup, store_id)
                if production_date:
                    title_sku += f'\n{production_date}'
                discount = await _get_discount(product_uri, soup, store_id)
                mass = await _get_mass(product_uri, soup, store_id)
                price_regular = await _get_price_regular(mass, product_uri, soup,
                                                         store_id)
                price_primary = await _get_price_primary(mass, product_uri, soup,
                                                         store_id)

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


async def _get_discount(product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '-': '', '%': ''}
        discount = int(utils.replace_all(soup.find(
            'div', class_='row', itemtype='https://schema.org/Product').find('span',
                                                                             class_='badge-store__text badge-store__text_sale').get_text(
            strip=True), dic))
        print(f'  -- Скидка {discount}')
    except:
        discount = ''
        print(
            f'Не удалось прочитать скидку для товара {product_uri} в магазине {store_id}')
    return discount


async def _get_price_primary(mass, product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '₽': ''}
        price_primary = utils.replace_all(soup.find(
            'div', class_='detail-price-full-price').find('span',
                                                          class_='count').get_text(
            strip=True), dic)
        if mass:
            # Цена за килограмм
            price_primary = f"{price_primary}\nЦена за кг {round(int(price_primary.split('/')[0]) * 1000 / mass, 2)}"
        else:
            price_primary = f"{price_primary}\nЦена за кг {round(int(price_primary.split('/')[0]) * 1000 / (float(price_primary.split('/')[1].replace(' кг', '')) * 1000), 2)}"
        print(f'  -- Цена со скидкой: {price_primary}')
    except:
        price_primary = ''
        print(
            f'Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id}')
    return price_primary


async def _get_price_regular(mass, product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '₽': ''}
        price_regular = utils.replace_all(soup.find(
            'span', class_='detail-price-old-price').find('span', class_='count').find(
            'span').get_text(strip=True), dic)
        if mass:
            # Цена за килограмм
            price_regular = f'{price_regular}\nЦена за кг {round(int(price_regular) * 1000 / mass, 2)}'
        print(f'  -- Обычная цена: {price_regular}')
    except:
        price_regular = ''
        print(
            f'Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}')
    return price_regular


async def _get_mass(product_uri, soup, store_id):
    try:
        table = soup.find('table', class_='detail-table')
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        mass_find = False
        for row in rows:
            if mass_find:
                break
            cols = row.find_all('td')
            for col in cols:
                if col.text == 'Масса:':
                    dic = {'\u00A0': '', ' г': ''}
                    mass = int(utils.replace_all(cols[1].text, dic))
                    mass_find = True
                    break
        print(f'  -- Масса {mass}')
    except:
        mass = 0
        print(
            f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
    return mass


async def _get_production_date(product_uri, soup, store_id):
    try:
        production_date = soup.find(
            'a', class_='extreme-fresh-link').get_text(
            strip=True).replace('\u00A0', '')
        print(f'  -- {production_date}')
    except:
        production_date = ''
        print(
            f'Не удалось прочитать дату производства для товара {product_uri} в магазине {store_id}')
    return production_date


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('div', class_='col l12 detail-title').find('h1',
                                                                         itemprop='name').getText(
            strip=True).replace('\u00A0', '')
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")
    return title_sku
