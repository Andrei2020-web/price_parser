import asyncio
from bs4 import BeautifulSoup
from nested_lookup import nested_lookup
import utils
import random
import json
import lxml

url = 'https://www.lenta.com'

# id магазинов. Например: ['Москва, Красная пресня ул., 23, к. Б, стр. 1',]
stores_id = []

# Список любимых товаров. Например: ['/product/mango-prochie-tovary-speloe-egipet-ves-662614/',]
products_uri = []


async def get_products():
    find_products_in_stores = {}

    for store_id in stores_id:
        find_products_in_store = []
        for product_uri in products_uri:
            # Кол-во повторов, чтобы получить html документ с товаром
            for i in range(utils.number_of_attempts):
                # Пауза между запросами
                sleep_time = round(random.uniform(utils.pause_between_requests_products['begin'],
                                                  utils.pause_between_requests_products['end']), 2)
                print(f'засыпаю на {sleep_time} c.')
                await asyncio.sleep(sleep_time)
                html = await utils.get_html(url, product_uri,
                                            any_parameters={'store_id': store_id})
                if html:
                    break
                else:
                    # Пауза между попытками
                    await asyncio.sleep(utils.pause_between_attempts_to_get_html)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                json_next_data = json.loads(
                    soup.find_all('script', attrs={'id': ["__NEXT_DATA__", "ng-state"]})[0].string)

                title_sku = await _get_title_sku(product_uri, soup, store_id)
                shop_addr = await _get_shop_addr(product_uri, soup, store_id)
                mass = await _get_mass(json_next_data, product_uri, store_id)
                price_regular = await _get_price_regular(soup, mass,
                                                         product_uri, store_id)
                price_primary = await _get_price_primary(soup, mass,
                                                         product_uri, store_id)
                discount = await _get_discount(soup, product_uri, store_id)
                enough = await _get_enough(soup, product_uri, store_id)

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


async def _get_enough(soup, product_uri, store_id):
    try:
        enough = soup.find('span', class_='count').contents[
            -1].strip().replace('\u00A0', '')
        print(f'  -- {enough}')
    except:
        enough = 'Не удалось прочитать наличие товара'
        print(
            f"Не удалось прочитать наличие товара {product_uri} в магазине {store_id}")
    return enough


async def _get_discount(soup, product_uri, store_id):
    try:
        dic = {'\u00A0': '', '-': '', '%': ''}
        discount = int(
            utils.replace_all(soup.find('span', class_='discount-badge ng-star-inserted').contents[
                                  -1].strip(), dic))
        print(
            f'  -- Скидка {discount}')
    except:
        discount = ''
        print(
            f"Не удалось прочитать скидку для товара {product_uri} в магазине {store_id}")
    return discount


async def _get_price_primary(soup, mass, product_uri, store_id):
    try:
        dic = {'\u00A0': '', '₽': '', '/': '', 'шт': '', ' ': ''}
        price_primary = utils.replace_all(soup.find_all(attrs={
            'class': ['main-price title-28-20 __accent', 'main-price title-28-20']})[
                                              0].string.strip(), dic)[0:-3]
        if mass:
            # Цена за килограмм
            price_primary = f'{price_primary}\nЦена за кг {round(int(price_primary) * 1000 / mass, 2)}'
        print(f'  -- Цена по карте: -- {price_primary}')
    except:
        price_primary = ''
        print(
            f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id}")
    return price_primary


async def _get_price_regular(soup, mass, product_uri, store_id):
    try:
        price_regular = soup.find_all(
            attrs={"class": ['old-price-product text-decoration-none ng-star-inserted',
                             'old-price-product ng-star-inserted']})[0]
        if price_regular.attrs['class'][0] == 'main-price':
            price_regular = price_regular.string
        elif price_regular.attrs['class'][0] == 'old-price-product':
            price_regular = price_regular.find('span').contents[-1]
        dic = {'\u00A0': '', '₽': '', '/': '', 'шт': '', ' ': ''}
        price_regular = utils.replace_all(price_regular.strip(), dic)[0:-3]
        if mass:
            # Цена за килограмм
            price_regular = f'{price_regular}\nЦена за кг {round(int(price_regular) * 1000 / mass, 2)}'
        print(f'  -- Обычная цена -- {price_regular}:')
    except:
        price_regular = ''
        print(
            f"Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}")
    return price_regular


async def _get_mass(json_next_data, product_uri, store_id):
    try:
        dic = {' ': '', 'г': '', 'мл': ''}
        mass = int(utils.replace_all(nested_lookup(
            key='package',
            document=json_next_data)[0], dic))
    except:
        mass = 0
        print(
            f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
    return mass


async def _get_shop_addr(product_uri, soup, store_id):
    try:
        shop_addr = soup.find_all('div', attrs={'class': ["address-text", "street-name"]})[
            0].get_text(
            strip=True).replace('\u00A0', '')
        print(f'  -- В магазине лента {shop_addr}:')
    except:
        shop_addr = 'Не удалось прочитать адрес магазина'
        print(
            f"Не удалось прочитать адрес для товара {product_uri} в магазине {store_id}")
    return shop_addr


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('title').string
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")
    return title_sku
