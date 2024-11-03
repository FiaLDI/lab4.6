#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
import logging
import sys
from typing import List
import xml.etree.ElementTree as ET


# Класс пользовательского исключения в случае, если неверно
# введен номер года.
class IllegalCount(Exception):
    def __init__(self, count, message="Illegall count"):
        self.count = count
        self.message = message
        super(IllegalCount, self).__init__(message)

    def __str__(self):
        logging.info(f"{self.count} -> {self.message}")
        return f"{self.count} -> {self.message}"


class UnknownCommandError(Exception):
    def __init__(self, command, message="Unknown command"):
        self.command = command
        self.message = message
        super(UnknownCommandError, self).__init__(message)

    def __str__(self):
        return f"{self.command} -> {self.message}"


@dataclass(frozen=True)
class Product:
    name: str
    market: str
    count: int


@dataclass
class Staff:
    products: List[Product] = field(default_factory=lambda: [])

    def add(self, name: str, market: str, count: int) -> None:
        if count < 0:
            raise IllegalCount(count)
        self.products.append(Product(name=name, market=market, count=count))
        self.products.sort(key=lambda product: product.name)

    def __str__(self) -> str:
        # Заголовок таблицы.
        table = []
        line = "+-{}-+-{}-+-{}-+-{}-+".format("-" * 4, "-" * 30, "-" * 20, "-" * 10)
        table.append(line)
        table.append(
            "| {:^4} | {:^30} | {:^20} | {:^10} |".format(
                "№", "Название продукта", "Имя магазина", "Стоимость"
            )
        )
        table.append(line)
        # Вывести данные о всех продуктах.
        for idx, product in enumerate(self.products, 1):
            table.append(
                "| {:>4} | {:<30} | {:<20} | {:>10} |".format(
                    idx, product.name, product.market, product.count
                )
            )
        table.append(line)
        return "\n".join(table)

    def select(self, name: str) -> List[Product]:
        result: List[Product] = []
        for product in self.products:
            if product.name == name:
                result.append(product)
        return result

    def load(self, filename: str) -> None:
        with open(filename, "r", encoding="utf8") as fin:
            xml = fin.read()
        parser = ET.XMLParser(encoding="utf8")
        tree = ET.fromstring(xml, parser=parser)
        self.products = []
        for product_element in tree:
            name, market, count = None, None, None
            for element in product_element:
                if element.tag == "name":
                    name = element.text
                elif element.tag == "market":
                    market = element.text
                elif element.tag == "count":
                    count = int(element.text)
                if name is not None and market is not None and count is not None:
                    self.products.append(Product(name=name, market=market, count=count))

    def save(self, filename: str) -> None:
        root = ET.Element("products")
        for product in self.products:
            product_element = ET.Element("product")
            name_element = ET.SubElement(product_element, "name")
            name_element.text = product.name
            market_element = ET.SubElement(product_element, "market")
            market_element.text = product.market
            count_element = ET.SubElement(product_element, "count")
            count_element.text = str(product.count)
            root.append(product_element)
        tree = ET.ElementTree(root)
        with open(filename, "wb") as fout:
            tree.write(fout, encoding="utf8", xml_declaration=True)


if __name__ == "__main__":
    # Выполнить настройку логгера.
    logging.basicConfig(filename="products4.log", level=logging.INFO)
    # Список продуктов.
    staff = Staff()

    # Организовать бесконечный цикл запроса команд.
    while True:
        try:
            # Запросить команду из терминала.
            command = input(">>> ").lower()
            # Выполнить действие в соответствие с командой.
            if command == "exit":
                break
            elif command == "add":
                # Запросить данные о продукте.
                name = input("Название товара? ")
                market = input("Магазин? ")
                count = int(input("Стоимость? "))
                # Добавить продукт.
                staff.add(name, market, count)
                logging.info(
                    f"Добавлен продукт: {name}, {market}, "
                    f"стоимостью в {count} рублей."
                )
            elif command == "list":
                print(staff)
                logging.info("Отображен список продуктов.")
            elif command.startswith("select "):
                # Разбить команду на части для выделения имени продукта
                parts = command.split(maxsplit=1)
                selected = staff.select(parts[1])
                # Вывести результаты запроса.
                if selected:
                    for idx, product in enumerate(selected, 1):
                        print("{:>4}: {}".format(idx, product.name))
                    logging.info(
                        f"Найдено {len(selected)} продуктов со " f"названием {parts[1]}"
                    )
                else:
                    print("Продукты с заданным именем не найдены.")
                    logging.warning(f"Работники с именем {parts[1]} не найдены.")
            elif command.startswith("load "):
                # Разбить команду на части для имени файла.
                parts = command.split(maxsplit=1)
                # Загрузить данные из файла.
                staff.load(parts[1])
                logging.info(f"Загружены данные из файла {parts[1]}.")
            elif command.startswith("save "):
                # Разбить команду на части для имени файла.
                parts = command.split(maxsplit=1)
                # Сохранить данные в файл.
                staff.save(parts[1])
                logging.info(f"Сохранены данные в файл {parts[1]}.")
            elif command == "help":
                # Вывести справку о работе с программой.
                print("Список команд:\n")
                print("add - добавить продукт;")
                print("list - вывести список продуктов;")
                print("select <стаж> - запросить продукты с именем;")
                print("load <имя_файла> - загрузить данные из файла;")
                print("save <имя_файла> - сохранить данные в файл;")
                print("help - отобразить справку;")
                print("exit - завершить работу с программой.")
            else:
                raise UnknownCommandError(command)
        except Exception as exc:
            logging.error(f"Ошибка: {exc}")
            print(exc, file=sys.stderr)
