import asyncio
from bs4 import BeautifulSoup
import random
import lxml
import main

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
}

url = 'https://www.perekrestok.ru'

# Список любимых товаров. Например: ['/cat/153/p/mango-egipet-4088772',]
products_uri = []


async def get_products():
    products = []
    products_in_store = {'Перекрёсток': products}
    for product_uri in products_uri:
        title_sku = ''
        promotion = ''
        shop_addr = ''
        price_regular = ''
        price_primary = ''
        discount = ''
        enough = ''

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
                await asyncio.sleep(main.number_of_attempts)
        if html:
            soup = BeautifulSoup(html, 'lxml')
            shop_addr = 'Перекрёсток'
            try:
                title_sku = soup.find('h1',
                                      class_='sc-fubCzh ibFUIH product__title').getText(
                    strip=True).replace('\u00A0', '')
                print(f'[+] Товар {title_sku}')
            except:
                title_sku = 'Не удалось прочитать наименование товара'
                print(
                    f"Не удалось прочитать наименование товара {product_uri} в магазине перекрёсток")
            try:
                promotion = soup.find('div', class_='sc-kYrlTI kRDKSf').find(
                    'span').get_text(strip=True).replace('\u00A0', '')
                print(f'  -- акция {promotion}')
            except:
                promotion = ''
                print(
                    f"Не удалось прочитать акцию товара {product_uri} в магазине перекрёсток")
            if promotion:
                title_sku += f' АКЦИЯ {promotion}'
            try:
                price_wrapper = soup.find('div', class_='Flex-brknwi-0 jRbnzW')
                price_old_wrapper = price_wrapper.find('div', class_='price-old-wrapper')
                price_regular = price_old_wrapper.find('div',
                                                       class_='price-old').contents[
                    -1].strip().replace('\u00A0', '').replace('₽', '')
                print(f'  -- Обычная цена {price_regular}:')
            except:
                print(
                    f"Не удалось прочитать обычную цену для товара {product_uri} в магазине перекрёсток")
            try:
                price_wrapper = soup.find('div', class_='Flex-brknwi-0 jRbnzW')
                price_primary = price_wrapper.find(
                    'div', class_='price-new').contents[-1].strip().replace('\u00A0', '').replace(
                    '₽', '')
                print(f'  -- Цена по карте: {price_primary}')

            except:
                print(
                    f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине перекрёсток")
            try:
                discount = soup.find('div', class_='sc-jGVbWl NgirP').find(
                    'span').get_text(strip=True).replace('\u00A0', '')
                print(f'  -- Скидка {discount}')
            except:
                print(
                    f"Не удалось прочитать скидку для товара {product_uri} в магазине перекрёсток")

            products.append({'title_sku': title_sku,
                             'shop_addr': shop_addr,
                             'price_regular': price_regular,
                             'price_primary': price_primary,
                             'discount': discount,
                             'enough': enough,
                             'url': url + product_uri})

    return products_in_store
