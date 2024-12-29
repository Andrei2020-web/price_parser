import asyncio
from bs4 import BeautifulSoup
import utils
import random
import lxml

url = 'https://www.5ka.ru'

stores_id = [
    'Пятёрочка',
]

# Список любимых товаров. Например: ['/product/3670111/maslo-slivochnoe-iz-vologdy-traditsionnoe--bzmzh',]
products_uri = [

]


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
                html = await utils.get_html(url, product_uri)
                if html:
                    break
                else:
                    # Пауза между попытками
                    await asyncio.sleep(utils.pause_between_attempts_to_get_html)
            if html:
                enough = ''
                soup = BeautifulSoup(html, 'lxml')
                title_sku = await _get_title_sku(product_uri, soup, store_id)
                shop_addr = store_id
                print(f'  -- В магазине {shop_addr}:')
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
            'div', class_='glk_dIAV- css-0').find('p',
                                                  class_='chakra-text HNH5GoH2- css-ykpbe9').get_text(
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
        price_primary = utils.replace_all(soup.find_all(attrs={
            'class': [
                'chakra-text DUXYWqnZ- D772ukru- css-6uvdux',
            ]
        })[0].string.strip(), dic)
        if mass and mass != 1:
            # Цена за килограмм
            price_primary = f"{price_primary}\nЦена за кг {round(int(price_primary.split('/')[0]) * 1000 / mass, 2)}"
        print(f'  -- Цена со скидкой: {price_primary}')
    except:
        price_primary = ''
        print(
            f'Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id}')
    return price_primary


async def _get_price_regular(mass, product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '₽': ''}
        price_regular = utils.replace_all(soup.find_all(attrs={
            'class': [
                'chakra-text VmUt9aCK- XoaYPJ0s- css-bx74j9',
            ]
        })[0].string.strip(), dic)
        if mass and mass != 1:
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
        dic = {' ': '', 'г': '', 'кг': '', 'мл': '', 'л': ''}
        mass = int(utils.replace_all(soup.find('p', class_='chakra-text wXbwqBFc- css-0').get_text(
            strip=True).replace('\u00A0', ''), dic))
    except:
        mass = 0
        print(
            f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
    return mass


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('h1', class_='chakra-text ypBDwsIV- css-0').getText(
            strip=True).replace('\u00A0', '')
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")
    return title_sku
