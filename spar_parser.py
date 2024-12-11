import asyncio
from bs4 import BeautifulSoup
import utils
import random
import lxml

url = 'https://myspar.ru'

stores_id = [
    'Спар',
]

# Список любимых товаров. Например: ['/catalog/frukty/mango-zheltoe/',]
products_uri = [

]


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
                await asyncio.sleep(sleep_time)
                print(f'засыпаю на {sleep_time} c.')
                html = await utils.get_html(url, product_uri)
                if html:
                    break
                else:
                    # Пауза между попытками
                    await asyncio.sleep(utils.pause_between_attempts_to_get_html)
            if html:
                enough = ''
                shop_addr = 'Спар'
                soup = BeautifulSoup(html, 'lxml')
                title_sku = await _get_title_sku(product_uri, soup, store_id)
                mass = await _get_mass(product_uri, soup, store_id)
                price_regular = await _get_price_regular(product_uri, soup, store_id, mass)
                price_primary = await _get_price_primary(product_uri, soup, store_id, mass)
                discount = await _get_discount(product_uri, soup, store_id)

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
        find_products_in_stores[store_id[0]] = find_products_in_store
    return find_products_in_stores


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('h1',
                              class_='catalog-element__title js-cut-text').getText(
            strip=True).replace('\u00A0', '')
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине спар {store_id[0]}")
    return title_sku


async def _get_price_regular(product_uri, soup, store_id, mass):
    try:
        dic = {'\u00A0': '', '₽': '', ',': '.', ' ': ''}
        price_regular = utils.replace_all(soup.find('span',
                                                    class_='prices__old').get_text(
            strip=True), dic)
        if mass:
            price_regular = f'{price_regular}\nЦена за кг {round(float(price_regular) * 1000 / mass, 2)}'
        print(f'  -- Обычная цена {price_regular}:')
    except:
        price_regular = ''
        print(
            f"Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id[0]}")
    return price_regular


async def _get_price_primary(product_uri, soup, store_id, mass):
    try:
        dic = {'\u00A0': '', '₽': '', ',': '.', ' ': ''}
        price_primary = utils.replace_all(soup.find('span',
                                                    class_='prices__cur js-item-price').get_text(
            strip=True), dic)
        if mass:
            price_primary = f'{price_primary}\nЦена за кг {round(float(price_primary) * 1000 / mass, 2)}'
        print(
            f'  -- Цена по карте: {price_primary}')
    except:
        price_primary = ''
        print(
            f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id[0]}")
    return price_primary


async def _get_discount(product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '−': '', '%': ''}
        discount = int(utils.replace_all(soup.find('span', class_='discount').get_text(
            strip=True), dic))
        print(
            f'  -- Скидка {discount}')
    except:
        discount = ''
        print(
            f"Не удалось прочитать скидку для товара {product_uri} в магазине {store_id[0]}")
    return discount


async def _get_mass(product_uri, soup, store_id):
    try:
        mass = float(
            soup.find('span', class_='element-props__title',
                      string='Вес нетто').find_next().find_next().get_text().replace('\u00A0',
                                                                                     '')) * 1000
    except:
        mass = 0
        print(
            f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
    return mass
