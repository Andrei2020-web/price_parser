import asyncio
from bs4 import BeautifulSoup
import random
import lxml
import main

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
            title_sku = ''
            shop_addr = ''
            production_date = ''
            price_regular = ''
            price_primary = ''
            discount = ''
            enough = ''
            mass = 0

            # Кол-во повторов, чтобы получить html документ с товаром
            for i in range(main.number_of_attempts):
                # Пауза между запросами, помогает при блокировке запросов сайтом
                sleep_time = round(random.uniform(main.pause_between_requests_products['begin'],
                                                  main.pause_between_requests_products['end']), 2)
                print(f'засыпаю на {sleep_time} c.')
                await asyncio.sleep(sleep_time)
                html = await main.get_html(url, product_uri, headers)
                if html:
                    break
                else:
                    # Пауза между попытками
                    await asyncio.sleep(main.pause_between_attempts_to_get_html)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                try:
                    title_sku = soup.find('div', class_='col l12 detail-title').find('h1',
                                                                                     itemprop='name').getText(
                        strip=True).replace('\u00A0', '')
                    print(f'[+] Товар {title_sku}')
                except:
                    title_sku = 'Не удалось прочитать наименование товара'
                    print(
                        f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")

                shop_addr = store_id
                print(f'  -- В магазине {shop_addr}:')

                try:
                    production_date = soup.find(
                        'a', class_='extreme-fresh-link').get_text(
                        strip=True).replace('\u00A0', '')
                    title_sku += f'\n{production_date}'
                    print(f'  -- Дата производства: {production_date}')
                except:
                    production_date = ''
                    print(
                        f'Не удалось прочитать дату производства для товара {product_uri} в магазине {store_id}')
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
                                mass = int(cols[1].text.replace('\u00A0', '').replace(' г', ''))
                                mass_find = True
                                break
                    print(f'  -- Скидка {discount}')
                except:
                    mass = 0
                    print(
                        f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
                try:
                    price_regular = soup.find(
                        'span', class_='detail-price-old-price').find('span', class_='count').find(
                        'span').get_text(strip=True).replace('\u00A0', '').replace('₽', '')
                    if mass:
                        # Цена за килограмм
                        price_regular = f'{price_regular}\nЦена за кг {round(int(price_regular) * 1000 / mass, 2)}'
                    print(f'  -- Обычная цена: {price_regular}')
                except:
                    price_regular = ''
                    print(
                        f'Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}')
                try:
                    price_primary = soup.find(
                        'div', class_='detail-price-full-price').find('span',
                                                                      class_='count').get_text(
                        strip=True).replace('\u00A0', '').replace('₽', '')
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
                try:
                    discount = soup.find(
                        'div', class_='row', itemtype='https://schema.org/Product').find('span',
                                                                                         class_='badge-store__text badge-store__text_sale').get_text(
                        strip=True).replace('\u00A0', '')
                    print(f'  -- Скидка {discount}')
                except:
                    discount = ''
                    print(
                        f'Не удалось прочитать скидку для товара {product_uri} в магазине {store_id}')

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
