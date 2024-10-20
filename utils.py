import aiohttp
import asyncio
import spar_parser
import lenta_parser
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

pause_between_requests_products = {'begin': 5, 'end': 7}
pause_between_requests_promos = {'begin': 2, 'end': 3}
pause_between_attempts_to_get_html = 30
number_of_attempts = 3

lenta_cookies = None


async def get_html(url, product_uri, headers=None, any_parameters=None):
    global lenta_cookies
    try:
        chrom_driver_lenta = None
        chrom_driver_spar = None
        # Если это Спар
        if url == spar_parser.url:
            chrom_driver_spar = await _create_a_Chrome_driver()
            await _exec_request(chrom_driver_spar, product_uri, url)
            await _wait_load_spar_page_with_sku_source(chrom_driver_spar)
            return chrom_driver_spar.page_source
        # Если это Лента
        elif url == lenta_parser.url:
            # Сначала открываем карточку с товаром
            chrom_driver_lenta = await _create_a_Chrome_driver()
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


async def _input_store_adress(addressQueryInput, any_parameters):
    addressQueryInput.send_keys(any_parameters['store_id'])
    await asyncio.sleep(2)
    addressQueryInput.click()
    addressQueryInput.send_keys(Keys.DOWN)
    addressQueryInput.send_keys(Keys.TAB)


async def _press_button_zabrat(chrom_driver_lenta):
    button_zabrat = WebDriverWait(chrom_driver_lenta, timeout=50).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '/html/body/p-dynamicdialog/div/div/div[2]/lu-popup-base/div/div/lu-address-edit-popup/lu-pickup-select/lu-pickup-select-b2c/div/div[1]/div[2]/button[1]')))
    button_zabrat.click()
    await asyncio.sleep(2)


async def _get_addressQueryInput(chrom_driver_lenta):
    return WebDriverWait(chrom_driver_lenta, timeout=50).until(
        EC.element_to_be_clickable((By.ID, 'addressQueryInput')))


async def _get_change_store_button(chrom_driver_lenta):
    return WebDriverWait(chrom_driver_lenta, timeout=50).until(
        EC.any_of(
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'p-element p-button p-button-pure p-button--no-padding p-button--no-border selected-store p-component')),
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'p-button p-button-pure p-button--no-padding p-button--no-border info ng-star-inserted')),
            EC.element_to_be_clickable((By.CLASS_NAME,
                                        'p-button p-button-pure p-button--no-padding p-button--no-border info')),
            EC.element_to_be_clickable((By.XPATH,
                                        '/html/body/lnt-root/div/lu-layout/lnt-header/lu-header/header/div/div[2]/lnt-header-address/lu-address-switch/div[3]/lu-address-switch-select-b2c/lu-address-switch-select-empty-b2c/div/button'))
        )
    )


async def _get_change_store_button_text(chrom_driver_lenta):
    return WebDriverWait(chrom_driver_lenta, timeout=50).until(
        EC.any_of(
            EC.element_to_be_clickable((By.CLASS_NAME, 'street-name')),
            EC.element_to_be_clickable((By.CLASS_NAME, 'address-text'))
        )
    )


async def _wait_load_spar_page_with_sku_source(chrom_driver_spar):
    WebDriverWait(chrom_driver_spar, timeout=3).until(
        EC.any_of(
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'catalog-element__title js-cut-text')),
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'prices__old')),
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'prices__cur js-item-price')),
        )
    )


async def _create_a_Chrome_driver():
    chrome_options = await _get_Crome_options()
    await _add_experimental_options(chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


async def _exec_request(driver, product_uri, url):
    driver.maximize_window()
    driver.get(url + product_uri)
    if url == lenta_parser.url and lenta_cookies:
        for cookie in lenta_cookies:
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
