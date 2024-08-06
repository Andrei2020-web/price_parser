import asyncio
from bs4 import BeautifulSoup
from nested_lookup import nested_lookup
import datetime
import random
import json
import lxml
import main

# id магазинов. Например: [1453, 1413]
stores_id = []

url = 'https://www.lenta.com'

# Акции
promotions_uri = '/goods-actions/main/'

# Список любимых товаров. Например: ['/product/mango-prochie-tovary-speloe-egipet-ves-662614/',]
products_uri = []


async def _get_crazy_promo(lenta_store_id, soup, promos):
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


async def _get_goods_actions_promo(lenta_store_id, soup, promos):
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
            await _get_crazy_promo(lenta_store_id, soup, promos)
            # Акция Выгодные предложения
            await _get_goods_actions_promo(lenta_store_id, soup, promos)

        find_promotions_in_stores[lenta_store_id] = promos

    return find_promotions_in_stores


async def get_products():
    find_products_in_stores = {}

    for store_id in stores_id:
        find_products_in_store = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cookie': f'ShouldSetDeliveryOptions=False; DontShowCookieNotification=False; CityCookie=msk; StoreSubDomainCookie={store_id}; CitySubDomainCookie=msk; Store={store_id}; IsNextSiteAvailable=True; DeliveryOptions=Pickup',
        }
        for product_uri in products_uri:
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
                json_next_data = json.loads(
                    soup.find_all('script', attrs={'id': ["__NEXT_DATA__", "ng-state"]})[0].string)

                title_sku = await _get_title_sku(product_uri, soup, store_id)
                shop_addr = await _get_shop_addr(product_uri, soup, store_id)
                mass = await _get_mass(json_next_data, product_uri, store_id)
                validityStartDate = await _getvalidityStartDay(json_next_data, product_uri,
                                                               store_id)
                validityEndDate = await _get_validityEndDate(json_next_data, product_uri, store_id)
                price_regular = await _get_price_regular(json_next_data, mass,
                                                         product_uri, store_id)
                price_primary = await _get_price_primary(json_next_data, mass,
                                                         product_uri, store_id, validityEndDate,
                                                         validityStartDate)
                discount = await _get_discount(json_next_data, product_uri, store_id)
                enough = await _get_enough(json_next_data, product_uri, store_id)

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


async def _get_enough(json_next_data, product_uri, store_id):
    try:
        enough = nested_lookup(
            key='count',
            document=json_next_data)[0]
        print(f'  -- {enough}')
    except:
        enough = 'Не удалось прочитать наличие товара'
        print(
            f"Не удалось прочитать наличие товара {product_uri} в магазине {store_id}")
    return enough


async def _get_discount(json_next_data, product_uri, store_id):
    try:
        discount = int(nested_lookup(
            key='title',
            document=json_next_data)[0].replace('-', '').replace('%', ''))
        print(
            f'  -- Скидка {discount}')
    except:
        discount = ''
        print(
            f"Не удалось прочитать скидку для товара {product_uri} в магазине {store_id}")
    return discount


async def _get_price_primary(json_next_data, mass, product_uri, store_id,
                             validityEndDate, validityStartDate):
    try:
        price_primary = str(nested_lookup(
            key='cost',
            document=json_next_data)[0])[0:-2]
        if mass:
            # Цена за килограмм
            price_primary = f'{price_primary}\nЦена за кг {round(int(price_primary) * 1000 / mass, 2)}'
            # Инфа по актуальности цен
            if validityStartDate:
                price_primary = f'{price_primary}\nс {validityStartDate} по {validityEndDate}'
        print(f'  -- Цена по карте: -- {price_primary}')
    except:
        price_primary = ''
        print(
            f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id}")
    return price_primary


async def _get_price_regular(json_next_data, mass, product_uri, store_id):
    try:
        price_regular = str(nested_lookup(
            key='costRegular',
            document=json_next_data)[0])[0:-2]
        if mass:
            # Цена за килограмм
            price_regular = f'{price_regular}\nЦена за кг {round(int(price_regular) * 1000 / mass, 2)}'
        print(f'  -- Обычная цена -- {price_regular}:')
    except:
        price_regular = ''
        print(
            f"Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id}")
    return price_regular


async def _get_validityEndDate(json_next_data, product_uri, store_id):
    try:
        validityEndDateTimeStr = nested_lookup(
            key='validityEndDate',
            document=json_next_data)[0]
        validityEndMonth = datetime.datetime.strptime(validityEndDateTimeStr,
                                                      "%Y-%m-%dT%H:%M:%SZ").month
        validityEndDay = datetime.datetime.strptime(validityEndDateTimeStr,
                                                    "%Y-%m-%dT%H:%M:%SZ").day
        validityEndDate = str(validityEndDay) + '.' + str(validityEndMonth)
        print(
            f'  -- Скидка актуальна по {validityEndDate}')
    except:
        validityEndDate = ''
        print(
            f"Не удалось прочитать по какую дату актуальна скидка для товара {product_uri} в магазине {store_id}")
    return validityEndDate


async def _getvalidityStartDay(json_next_data, product_uri, store_id):
    try:
        validityStartDateTimeStr = nested_lookup(
            key='validityStartDate',
            document=json_next_data)[0]
        validityStartMonth = datetime.datetime.strptime(validityStartDateTimeStr,
                                                        "%Y-%m-%dT%H:%M:%SZ").month
        validityStartDay = datetime.datetime.strptime(validityStartDateTimeStr,
                                                      "%Y-%m-%dT%H:%M:%SZ").day
        validityStartDate = str(validityStartDay) + '.' + str(validityStartMonth)
        print(
            f'  -- Скидка актуальна с {validityStartDate}')
    except:
        validityStartDate = ''
        print(
            f"Не удалось прочитать с какой даты актуальна скидка для товара {product_uri} в магазине {store_id}")
    return validityStartDate


async def _get_mass(json_next_data, product_uri, store_id):
    try:
        mass = int(nested_lookup(
            key='package',
            document=json_next_data)[0].replace(' ', '').replace('г', '').replace('мл', ''))
    except:
        mass = 0
        print(
            f'Не удалось прочитать массу для товара {product_uri} в магазине {store_id}')
    return mass


async def _get_shop_addr(product_uri, soup, store_id):
    try:
        shop_addr = soup.find('span',
                              class_='Address_street__Ewkm4').get_text(
            strip=True)
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
