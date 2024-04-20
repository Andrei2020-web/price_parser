import asyncio
from bs4 import BeautifulSoup
import json
import random
import lxml
import main

# id магазинов. Например: [1453, 1413]
stores_id = []

url = 'https://www.lenta.com'

# Акции
promotions_uri = '/goods-actions/main/'

# Список любимых товаров. Например: ['/product/mango-prochie-tovary-speloe-egipet-ves-662614/',]
products_uri = []


def _get_crazy_promo(lenta_store_id, soup, promos):
    try:
        crazy_promo_list_day = soup.find('div',
                                         class_='js-crazy-promo-slider crazy-promo-slider-container show-block')[
            'data-model']
        crazy_promo_list_day_json = json.loads(crazy_promo_list_day)
        for promo in crazy_promo_list_day_json['sliderItems']:
            try:
                title_promo = f'Акция скидка дня: {promo["title"]}'
            except:
                title_promo = 'Заголовок акции не найден.'
            try:
                date_promo = promo['actionDate']
            except:
                date_promo = 'Срок акции не найден.'
            try:
                promo_discount_label = promo['discount']
            except:
                promo_discount_label = ''
            try:
                promo_url = promo['url']
            except:
                promo_url = ''
            print(
                f'[+] {title_promo} {promo_discount_label} c {date_promo}')

            promos.append(
                {
                    'title_promo': title_promo,
                    'promo_discount_label': promo_discount_label,
                    'date_promo': date_promo,
                    'url': promo_url,
                }
            )
    except:
        print(f"Не удалось прочитать акцию в магазине {lenta_store_id}")


def _get_goods_actions_promo(lenta_store_id, soup, promos):
    try:
        all_actions_list = soup.find_all('div',
                                         class_='promotional-hub-block-carousel js-promotional-hub-block-carousel')
        for all_actions_list_item in all_actions_list:
            all_actions_list_item_json = json.loads(all_actions_list_item['data-model'])
            if all_actions_list_item_json['name'] == 'Выгодные предложения':
                for promo in all_actions_list_item_json['promotions']:
                    promo_discount_label = ''
                    try:
                        title_promo = f'Акция: {promo["description"]}'
                    except:
                        title_promo = 'Заголовок акции не найден.'
                    try:
                        date_promo = promo['showDates']
                    except:
                        date_promo = 'Срок акции не найден.'
                    try:
                        promo_url = promo['link']
                    except:
                        promo_url = ''
                    print(
                        f'[+] {title_promo} {promo_discount_label} c {date_promo}')

                    promos.append(
                        {
                            'title_promo': title_promo,
                            'promo_discount_label': promo_discount_label,
                            'date_promo': date_promo,
                            'url': promo_url,
                        }
                    )
    except:
        print(f"Не удалось прочитать акцию в магазине {lenta_store_id}")


async def get_promotions_in_stores():
    find_promotions_in_stores = {}

    for lenta_store_id in stores_id:
        promos = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cookie': f'CityCookie=msk; StoreSubDomainCookie={lenta_store_id}; CitySubDomainCookie=msk; Store={lenta_store_id}; DeliveryOptions=Pickup'
        }
        # Кол-во повторов, чтобы получить html документ с акциями
        for i in range(main.number_of_attempts):
            # Пауза между запросами, помогает при блокировке запросов сайтом
            sleep_time = round(random.uniform(main.pause_between_requests_promos['begin'],
                                              main.pause_between_requests_promos['end']), 2)
            print(f'засыпаю на {sleep_time} c.')
            await asyncio.sleep(sleep_time)
            html = await main.get_html(url, promotions_uri, headers)
            if html:
                break
            else:
                # Пауза между попытками
                await asyncio.sleep(main.pause_between_attempts_to_get_html)
        if html:
            soup = BeautifulSoup(html, 'lxml')
            # Акция cкидка дня
            _get_crazy_promo(lenta_store_id, soup, promos)
            # Акция Выгодные предложения
            _get_goods_actions_promo(lenta_store_id, soup, promos)

        find_promotions_in_stores[lenta_store_id] = promos

    return find_promotions_in_stores


async def get_products():
    find_products_in_stores = {}

    for store_id in stores_id:
        find_products_in_store = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cookie': f'CityCookie=msk; StoreSubDomainCookie={store_id}; CitySubDomainCookie=msk; Store={store_id}; DeliveryOptions=Pickup'
        }
        for product_uri in products_uri:

            title_sku = ''
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
                    await asyncio.sleep(main.pause_between_attempts_to_get_html)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                try:
                    title_sku = soup.find('h1',
                                          class_='Title_title__jcDAb Product_cardTitle__GhDos').getText(
                        strip=True).replace('\u00A0', '')
                    print(f'[+] Товар {title_sku}')
                except:
                    title_sku = 'Не удалось прочитать наименование товара'
                    print(
                        f"Не удалось прочитать наименование товара {product_uri} в магазине {store_id}")
                try:
                    shop_addr = soup.find('span',
                                          class_='Address_street__Ewkm4').get_text(
                        strip=True)
                    print(f'  -- В магазине лента {shop_addr}:')
                except:
                    shop_addr = 'Не удалось прочитать адрес магазина'
                    print(
                        f"Не удалось прочитать адрес для товара {product_uri} в магазине {store_id}")
                try:
                    price_regular = soup.find('p',
                                              class_='Price_secondaryPrice__ppVFT').get_text(
                        strip=True).replace(
                        '\u00A0', '').replace('обычная цена', '')
                    print(f'  -- Обычная цена {price_regular}:')
                except:
                    price_regular = ''
                    print(
                        f"Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}")
                try:
                    price_primary = soup.find('p',
                                              class_=['Price_mainPrice__T9yBp Price_red__b91DW',
                                                      'Price_mainPrice__T9yBp']).get_text(
                        strip=True).replace('\u00A0', '').replace('по карте', '')
                    print(f'  -- Цена по карте: {price_primary}')
                except:
                    price_primary = ''
                    print(
                        f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id}")
                try:
                    discount = soup.find('span',
                                         class_='Product_discountBadge__40fed Badge_badge__w952k Badge_badge_color_red__36Xhs Badge_badge_size_large__tNWP6 Badge_badge_number__mQzYy').get_text(
                        strip=True).replace('\u00A0', '')
                    print(
                        f'  -- Скидка {discount}')
                except:
                    print(
                        f"Не удалось прочитать скидку для товара {product_uri} в магазине {store_id}")
                try:
                    div = \
                        soup.find('span',
                                  class_=[
                                      'Badge_badge__w952k Badge_badge_color_greenSecondary__2cVlN Badge_badge_size_medium__feig9',
                                      'Badge_badge__w952k Badge_badge_color_orangeSecondary__l7hYO Badge_badge_size_medium__feig9',
                                      'Badge_badge__w952k Badge_badge_color_redSecondary__i_Xad Badge_badge_size_medium__feig9'])
                    if div:
                        enough = div.get_text(strip=True).replace('\u00A0', '')
                        print(f'  -- {enough}')
                except:
                    print(
                        f"Не удалось прочитать наличие товара {product_uri} в магазине {store_id}")

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
