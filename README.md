#  price_parser
___
![python_version](https://img.shields.io/badge/python-3.11-orange)
![aiohttp_version](https://img.shields.io/badge/aiohttp-3.8-orange)
![beautifulsoup4_version](https://img.shields.io/badge/beautifulsoup4-4.12-orange)
![lxml_version](https://img.shields.io/badge/lxml-4.9-orange)
![xlwt_version](https://img.shields.io/badge/xlwt-1.3-orange)
![nested-lookup_version](https://img.shields.io/badge/nested_lookup-0.2-orange)
![auto-py-to-exe_version](https://img.shields.io/badge/auto_py_to_exe-2.43-orange)

Парсим цены на любимые товары и акции в магазинах.
Полученные данные сохраняем в файлы json и exl.

## Настройка перед запуском

Первое, что нужно сделать, это cклонировать репозиторий:

```sh
$ git clone https://github.com/Andrei2020-web/price_parser.git
$ cd price_parser
```

Создайте виртуальную среду для установки зависимостей и активируйте ее:

```sh
$ virtualenv venv
$ source venv/bin/activate
```

Затем установите зависимости:

```sh
(venv)$ pip install -r requirements.txt
```