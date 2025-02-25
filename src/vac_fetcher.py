from abc import ABC, abstractmethod

import requests

from src.logger import general_logger


class BaseVacancyParser(ABC):
    """Абстрактный класс для парсеров вакансий"""

    @abstractmethod
    def fetch_vacancies(self, employers_info):
        pass

    @abstractmethod
    def filter_data(self):
        pass


class HeadHunterVacancies(BaseVacancyParser):
    """Class-коннектор к hh.ru API для получения открытых вакансий нужных компаний"""

    def __init__(self):
        self.__url = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self.__params = {"text": "", "page": 0, "per_page": 100}
        self.vacancies = []

    @property
    def url(self):
        return self.__url

    @property
    def headers(self):
        return self.__headers

    @property
    def params(self):
        return self.__params

    def fetch_vacancies(self, employers_id: list) -> None:
        """Поиск вакансий на HeadHunter"""

        general_logger.info("Поиск вакансий")
        response = requests.get(
            self.__url,
            headers=self.__headers,
            params={"page": 0, "per_page": 100, "employer_id": employers_id},
        )
        if response.status_code == 200:
            vacancies = response.json()["items"]
            self.vacancies.extend(vacancies)
            general_logger.info("Вакансии успешно добавлены в список")

    def filter_data(self) -> list:
        """Выбор только полезной информацию из ответа api и возврат отфильтрованного списка с зарплатой в рублях"""
        filtered_data = []
        for vacancy in self.vacancies:
            try:
                if vacancy.get("salary").get("currency") == "RUR":
                    current_vacancy = dict()
                    current_vacancy["name"] = vacancy["name"]
                    current_vacancy["salary"] = vacancy.get("salary")
                    current_vacancy["url"] = vacancy["alternate_url"]
                    current_vacancy["experience"] = vacancy["experience"]["name"]
                    current_vacancy["employer"] = vacancy["employer"]["name"]
                    del current_vacancy["salary"]["gross"]
                    filtered_data.append(current_vacancy)
            except AttributeError:
                continue
        return filtered_data