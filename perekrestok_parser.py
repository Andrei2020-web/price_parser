import asyncio
from bs4 import BeautifulSoup
import utils
import random
import lxml

url = 'https://www.perekrestok.ru'

# id магазинов. Например: ['ТЦ Атриум', ]
stores_id = []

# Список любимых товаров. Например: ['/cat/153/p/mango-egipet-4088772',]
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
                    await asyncio.sleep(utils.number_of_attempts)
            if html:
                shop_addr = store_id
                soup = BeautifulSoup(html, 'lxml')
                title_sku = await _get_title_sku(product_uri, soup, store_id)
                promotion = await _get_promotion(product_uri, soup, store_id)
                if promotion:
                    title_sku += f' АКЦИЯ {promotion}'
                mass = await _get_mass(product_uri, title_sku, store_id)
                price_regular = await _get_price_regular(product_uri, soup, store_id, mass)
                price_primary = await _get_price_primary(product_uri, soup, store_id, mass)
                discount = await _get_discount(product_uri, soup, store_id)
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


async def _get_discount(product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '-': '', '%': ''}
        discount = int(utils.replace_all(soup.find(attrs={
            'class': ['sc-hjWSTT hMdZRn',
                      'sc-httYss iSBbxs']}).find('span').get_text(strip=True), dic))
        print(f'  -- Скидка {discount}')
    except:
        discount = ''
        print(
            f"Не удалось прочитать скидку для товара {product_uri} в магазине {store_id}")
    return discount


async def _get_price_primary(product_uri, soup, store_id, mass):
    try:
        price_wrapper = soup.find('div', class_='Flex-brknwi-0 kVzitC panel-price-card')
        dic = {'\u00A0': '', '₽': ''}
        price_primary = utils.replace_all(price_wrapper.find(
            'div', class_='price-new').contents[-1].strip(), dic)
        price_primary = price_primary.split(',')[0]
        if mass and mass != 1:
            # Цена за килограмм
            price_primary = f'{price_primary}\nЦена за кг {round(int(price_primary) * 1000 / mass, 2)}'
        print(f'  -- Цена по карте: {price_primary}')
    except:
        price_primary = ''
        print(
            f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id}")
    return price_primary


async def _get_price_regular(product_uri, soup, store_id, mass):
    try:
        dic = {'\u00A0': '', '₽': ''}
        price_regular = soup.find('div', class_='Flex-brknwi-0 jRbnzW').find('div', class_='price-old').contents[-1].text
        price_regular = utils.replace_all(price_regular.split(',')[0], dic)
        if mass and mass != 1:
            # Цена за килограмм
            price_regular = f'{price_regular}\nЦена за кг {round(int(price_regular) * 1000 / mass, 2)}'
        print(f'  -- Обычная цена {price_regular}:')
    except:
        price_regular = ''
        print(
            f"Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}")
    return price_regular


async def _get_promotion(product_uri, soup, store_id):
    try:
        promotion = soup.find('div', class_='sc-kYrlTI kRDKSf').find(
            'span').get_text(strip=True).replace('\u00A0', '')
        print(f'  -- акция {promotion}')
    except:
        promotion = ''
        print(
            f"Не удалось прочитать акцию товара {product_uri} в магазине {store_id}")
    return promotion


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('h1',
                              class_='sc-fubCzh ibFUIH product__title').getText(
            strip=True).replace('\u00A0', '')
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")
    return title_sku


async def _get_enough(soup, product_uri, store_id):
    try:
        enough = soup.find('div', class_='price-card-balance-state').getText(
            strip=True).replace('\u00A0', '')
        print(f'  -- {enough}')
    except:
        enough = 'Не удалось прочитать наличие товара'
        print(
            f"Не удалось прочитать наличие товара {product_uri} в магазине {store_id}")
    return enough


async def _get_mass(product_uri, title_sku, store_id):
    try:
        dic = {' ': '', 'г': '', 'кг': '', 'мл': '', 'л': ''}
        mass = int(utils.replace_all(title_sku.split(',')[1], dic))
    except:
        mass = 0
        print(
            f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
    return mass
