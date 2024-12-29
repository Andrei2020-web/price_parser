import aiohttp
import asyncio
import spar_parser
import lenta_parser
import perekrestok_parser
import pyaterochka_parser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

pause_between_requests_products = {'begin': 5, 'end': 7}
pause_between_requests_promos = {'begin': 2, 'end': 3}
pause_between_attempts_to_get_html = 30
number_of_attempts = 3

lenta_cookies = None
perekrestok_cookies = None


async def get_html(url, product_uri, headers=None, any_parameters=None):
    try:
        chrom_driver_lenta = None
        chrom_driver_spar = None
        chrom_driver_perekrestok = None
        chrom_driver_pyaterochka = None

        # Если это Спар
        if url == spar_parser.url:
            chrom_driver_spar = await _create_a_Chrome_driver()
            return await _get_spar_html(chrom_driver_spar, product_uri, url)

        # Если это Лента
        elif url == lenta_parser.url:
            chrom_driver_lenta = await _create_a_Chrome_driver()
            return await _get_lenta_html(chrom_driver_lenta, product_uri, url, any_parameters)

        # Если это Перекрёсток
        elif url == perekrestok_parser.url:
            chrom_driver_perekrestok = await _create_a_Chrome_driver()
            return await _get_perekrestok_html(chrom_driver_perekrestok, product_uri, url,
                                               any_parameters)
        # Если это Пятёрочка
        elif url == pyaterochka_parser.url:
            chrom_driver_pyaterochka = await _create_a_Chrome_driver()
            return await _get_pyaterochka_html(chrom_driver_pyaterochka, product_uri, url)
        # Асинхронные запросы через aiohttp для остальных магазинов
        else:
            async with aiohttp.ClientSession() as session:
                response = await session.get(url + product_uri,
                                             headers=headers)
                if response.status == 200:
                    return await response.text(), headers
                else:
                    print(
                        f'Не удалось выполнить запрос, ошибка {response.status}, url: {url + product_uri}')
                    return None
    except Exception as e:
        print(f'Не удалось получить html! {e}')
        return None
    finally:
        if chrom_driver_spar:
            await _close_a_Chrome_driver(chrom_driver_spar)
        if chrom_driver_lenta:
            await _close_a_Chrome_driver(chrom_driver_lenta)
        if chrom_driver_perekrestok:
            await _close_a_Chrome_driver(chrom_driver_perekrestok)
        if chrom_driver_pyaterochka:
            await _close_a_Chrome_driver(chrom_driver_pyaterochka)


async def _get_spar_html(chrom_driver_spar, product_uri, url):
    await _exec_request(chrom_driver_spar, product_uri, url)
    return chrom_driver_spar.page_source


async def _get_lenta_html(chrom_driver_lenta, product_uri, url, any_parameters):
    global lenta_cookies
    # Сначала открываем карточку с товаром
    await _exec_request(chrom_driver_lenta, product_uri, url)
    # Ждём пока не появится кнопка смены адреса магазина
    button_address_text = await _get_change_store_button_text(chrom_driver_lenta)
    # Проверяем текущий адрес магазина и если не подходит меняем его
    if button_address_text.text != any_parameters['store_id']:
        # Находим саму кнопку
        button_address = await _get_change_store_button(chrom_driver_lenta)
        button_address.click()
        # Ждём появления поля для ввода адреса магазина
        addressQueryInput = await _get_addressQueryInput(chrom_driver_lenta)
        # Пишем адрес нужного нам магазина
        await _input_store_adress(addressQueryInput, any_parameters)
        # Далее ждём когда станет активной и нажимаем кнопку забрать отсюда
        await _press_button_zabrat(chrom_driver_lenta)
        # Необходимо обновить, т.к. не изменяется остаток товара в магазине
        chrom_driver_lenta.refresh()
        # Далее ждём когда подгрузится остаток по товару в данном магазине
        await _get_change_store_button_text(chrom_driver_lenta)
        # Сохраняем печеньки
        lenta_cookies = chrom_driver_lenta.get_cookies()
        return chrom_driver_lenta.page_source
    # Если мы в нужном магазине ленты, тогда просто получаем данные страницы
    return chrom_driver_lenta.page_source


async def _get_perekrestok_html(chrom_driver_perekrestok, product_uri, url, any_parameters):
    global perekrestok_cookies
    # Сначала открываем карточку с товаром
    await _exec_request(chrom_driver_perekrestok, product_uri, url)
    # Ждём пока не появится кнопка смены адреса магазина
    button_address_text = await _get_change_store_button_text(chrom_driver_perekrestok)
    # Проверяем текущий адрес магазина и если не подходит меняем его
    if button_address_text.text != any_parameters['store_id']:
        # Находим саму кнопку
        button_address = await _get_change_store_button(chrom_driver_perekrestok)
        button_address.click()
        # Находим кнопку самовывоза
        button_pickup = await _get_pickup_button(chrom_driver_perekrestok)
        button_pickup.click()
        # Находим кнопку отображения магазинов списком
        button_list_of_stores = await _get_list_of_stores_button(chrom_driver_perekrestok)
        button_list_of_stores.click()
        # Находим нужный магазин и кликаем по нему
        store = await _get_store_from_list(chrom_driver_perekrestok,
                                           any_parameters['store_id'])
        store.click()
        # Нажимаем кнопку подтвердить
        await _press_button_zabrat(chrom_driver_perekrestok)
        # Далее ждём когда подгрузится остаток по товару в данном магазине
        await _get_change_store_button_text(chrom_driver_perekrestok)
        # Сохраняем печеньки
        perekrestok_cookies = chrom_driver_perekrestok.get_cookies()
        return chrom_driver_perekrestok.page_source
    # Если мы в нужном магазине, тогда просто получаем данные страницы
    return chrom_driver_perekrestok.page_source


async def _input_store_adress(addressQueryInput, any_parameters):
    addressQueryInput.send_keys(any_parameters['store_id'])
    await asyncio.sleep(2)
    addressQueryInput.click()
    addressQueryInput.send_keys(Keys.DOWN)
    addressQueryInput.send_keys(Keys.TAB)


async def _press_button_zabrat(chrom_driver):
    button_zabrat = WebDriverWait(chrom_driver, timeout=50).until(
        EC.any_of(
            # Лента
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/p-dynamicdialog/div/div/div[2]/lu-popup-base/div/div/lu-address-edit-popup/lu-pickup-select/lu-pickup-select-b2c/div/div[1]/div[2]/button[1]')),
            # Перекрёсток
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/div[8]/div[2]/div/div/div/div/div[2]/div/div[4]/div/div/div/button')),
        )
    )
    button_zabrat.click()
    await asyncio.sleep(2)


async def _get_addressQueryInput(chrom_driver_lenta):
    return WebDriverWait(chrom_driver_lenta, timeout=50).until(
        EC.element_to_be_clickable((By.ID, 'addressQueryInput')))


async def _get_change_store_button(chrom_driver_lenta):
    return WebDriverWait(chrom_driver_lenta, timeout=50).until(
        EC.any_of(
            # Лента
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'p-element p-button p-button-pure p-button--no-padding p-button--no-border selected-store p-component')),
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'p-button p-button-pure p-button--no-padding p-button--no-border info ng-star-inserted')),
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'p-button p-button-pure p-button--no-padding p-button--no-border info')),
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/lnt-root/div/lu-layout/lnt-header/lu-header/header/div/div[2]/lnt-header-address/lu-address-switch/div[3]/lu-address-switch-select-b2c/lu-address-switch-select-empty-b2c/div/button')),
            # Перекрёсток
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'sc-eCstlR izpZKH delivery-button__location')),
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/div[1]/div/header/div[1]/div[1]/div/div[3]/button')),
        )
    )


async def _get_change_store_button_text(chrom_driver):
    return WebDriverWait(chrom_driver, timeout=50).until(
        EC.any_of(
            # Лента
            EC.element_to_be_clickable((By.CLASS_NAME, 'street-name')),
            EC.element_to_be_clickable((By.CLASS_NAME, 'address-text')),
            # Перекрёсток
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//*[@id="header-container"]/div[1]/div/div[3]/button/span[2]/div/div[2]')),
        )
    )


async def _get_pickup_button(chrom_driver):
    return WebDriverWait(chrom_driver, timeout=50).until(
        EC.any_of(
            EC.element_to_be_clickable((By.CLASS_NAME, 'sc-laRQdt daXvfR')),
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/div[8]/div[2]/div/div/div/div/div[2]/div/div[2]/div[2]/button')),
        )
    )


async def _get_list_of_stores_button(chrom_driver):
    return WebDriverWait(chrom_driver, timeout=50).until(
        EC.any_of(
            EC.element_to_be_clickable((By.CLASS_NAME, 'sc-laRQdt fCKTLm')),
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/div[8]/div[2]/div/div/div/div/div[1]/div[2]/div[2]/button')),
        )
    )


async def _get_store_from_list(chrom_driver, store_id):
    return WebDriverWait(chrom_driver, timeout=50).until(
        EC.any_of(
            EC.element_to_be_clickable((By.XPATH, f"//*[text()='{store_id}']")),
        )
    )


async def _create_a_Chrome_driver():
    chrome_options = await _get_Crome_options()
    await _add_experimental_options(chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


async def _exec_request(driver, product_uri, url):
    driver.maximize_window()
    if url == spar_parser.url or url == pyaterochka_parser.url:
        driver.minimize_window()

    driver.get(url + product_uri)

    if url == lenta_parser.url and lenta_cookies:
        for cookie in lenta_cookies:
            driver.add_cookie(cookie)
        driver.refresh()
    if url == perekrestok_parser.url and perekrestok_cookies:
        for cookie in perekrestok_cookies:
            driver.add_cookie(cookie)
        driver.refresh()


async def _add_experimental_options(chrome_options):
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,  # disable all notice
        "profile.default_content_setting_values.media_stream_mic": 2,  # disable microphone
        "profile.default_content_setting_values.media_stream_camera": 2,  # disable camera
        "profile.default_content_setting_values.geolocation": 2,  # disable geolocations
    })


async def _get_Crome_options():
    chrome_options = webdriver.ChromeOptions()
    return chrome_options


async def _close_a_Chrome_driver(driver):
    driver.close()
    driver.quit()


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text

async def _get_pyaterochka_html(chrom_driver_pyaterochka, product_uri, url):
    # Сначала открываем карточку с товаром
    await _exec_request(chrom_driver_pyaterochka, product_uri, url)
    # Ждём пока не появится заголовок
    await _get_title_text(chrom_driver_pyaterochka)
    return chrom_driver_pyaterochka.page_source

async def _get_title_text(chrom_driver):
    return WebDriverWait(chrom_driver, timeout=50).until(
        EC.any_of(
            EC.element_to_be_clickable((By.CLASS_NAME, 'chakra-text ypBDwsIV- css-0')),
            EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div[2]/div[3]/div[2]/div[2]/div[1]/div[1]/h1')),

        )
    )