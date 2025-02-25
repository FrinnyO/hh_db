from abc import ABC, abstractmethod

import psycopg2

from src.logger import general_logger


class BaseDBManager(ABC):

    @abstractmethod
    def get_companies_and_vacancies_count(self):
        pass

    @abstractmethod
    def get_all_vacancies(self):
        pass

    @abstractmethod
    def get_avg_salary(self):
        pass

    @abstractmethod
    def get_vacancies_with_higher_salary(self):
        pass

    @abstractmethod
    def get_vacancies_with_keyword(self, keyword):
        pass


class DBManager(BaseDBManager):
    """Класс для работы с PostGreSQL"""

    password: str
    user_name: str
    database_name: str

    def __init__(self, user_name, password, database_name="hh_vacancies"):
        self.__params = {"host": "localhost", "user": user_name, "password": password}
        self.__database_name = database_name

    def create_database(self) -> None:
        """Создание PostGreSQL базы данных"""
        conn = psycopg2.connect(dbname="postgres", **self.__params)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {self.__database_name}")
        cur.execute(f"CREATE DATABASE {self.__database_name}")

        conn.close()

        general_logger.info(f"Создана база данных {self.__database_name}")

        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)

        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE employers (
                    employer_id SERIAL,
                    employer_name VARCHAR(255) NOT NULL,
                    CONSTRAINT pk_employers_employer_id PRIMARY KEY (employer_id)
                )
            """
            )
        general_logger.info("Создана таблица employers")

        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE vacancies (
                    vacancy_id SERIAL,
                    vacancy_name VARCHAR(255),
                    from_salary INTEGER,
                    to_salary INTEGER,
                    url TEXT,
                    employer_id INTEGER REFERENCES employers(employer_id)
                )
            """
            )
        general_logger.info("Создана таблица vacancies")
        conn.commit()
        conn.close()

    def fill_up_tables(self, companies: list, vacancies: list) -> None:
        """Заполнение таблиц в PostGreSQL"""
        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)

        with conn.cursor() as cur:
            for employer in companies:
                cur.execute(
                    f"""
                    INSERT INTO employers (employer_name) VALUES ('{employer}')
                """
                )
            general_logger.info("Успешно добавлены данные в таблицу employers")
            for vacancy in vacancies:
                cur.execute(
                    f"""
                    INSERT INTO vacancies (vacancy_name, from_salary, to_salary, url, employer_id)
                    VALUES (%s, %s, %s, %s, (SELECT employer_id from employers e
                    WHERE employer_name = '{vacancy['employer']}'))
                    """,
                    (vacancy["name"], vacancy["salary"]["from"], vacancy["salary"]["to"], vacancy["url"]),
                )
            general_logger.info("Успешно добавлены данные в таблицу vacancies")
        conn.commit()
        conn.close()

    def get_companies_and_vacancies_count(self) -> None:
        """Группировка вакансий по их работодателю"""
        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                """
                       SELECT employer_name, COUNT(*) from vacancies
                       JOIN employers e USING(employer_id)
                        GROUP BY employer_name
                        ORDER BY COUNT(*) DESC
                   """
            )
            companies = cur.fetchall()
        conn.close()
        for row in companies:
            print(f"Company: {row[0]}. Open vacancies: {row[1]}")

    def get_all_vacancies(self) -> None:
        """Получение всех вакансий с указанием названия их компании"""
        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                """
                       SELECT employer_name, vacancy_name,  from_salary, to_salary, url from vacancies v
                       JOIN employers e USING(employer_id)
                       ORDER BY employer_name
                   """
            )
            vacancies = cur.fetchall()
        conn.close()
        self.__print_vacancies_with_companies(vacancies)

    def get_avg_salary(self) -> None:
        """Получение средней заработной платы среди вакансий"""
        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                """
                       SELECT ROUND(AVG(from_salary)), ROUND(AVG(to_salary)) FROM vacancies;
                   """
            )
            avg_salaries = cur.fetchall()
        conn.close()
        avg_salary = round((avg_salaries[0][0] + avg_salaries[0][1]) / 2)
        print(f"Average salary: {avg_salary} RUB")

    def get_vacancies_with_higher_salary(self) -> None:
        """Получение вакансий с зарплатой выше средней"""
        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                """
                       SELECT employer_name, vacancy_name,  from_salary, to_salary, url FROM vacancies v
                        JOIN employers e
                        USING(employer_id)
                        WHERE from_salary > (SELECT (ROUND(AVG(from_salary)) + ROUND(AVG(to_salary))) / 2
                        FROM vacancies)
                        OR
                        to_salary > (SELECT (ROUND(AVG(from_salary)) + ROUND(AVG(to_salary))) / 2
                        FROM vacancies)
                        ORDER BY employer_name;
                   """
            )
            bigger_than_avg_salaries = cur.fetchall()
        conn.close()
        self.__print_vacancies_with_companies(bigger_than_avg_salaries)

    def get_vacancies_with_keyword(self, keyword: str) -> None:
        """Поиск вакансий по ключевым словам"""
        conn = psycopg2.connect(dbname=self.__database_name, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                       SELECT employer_name, vacancy_name,  from_salary, to_salary, url FROM vacancies v
                        JOIN employers e
                        USING(employer_id)
                        WHERE LOWER(vacancy_name) LIKE '%{keyword.lower()}%'
                        ORDER BY employer_name;
                   """
            )
            keyword_vacancies = cur.fetchall()
        conn.close()
        self.__print_vacancies_with_companies(keyword_vacancies)

    @staticmethod
    def __print_vacancies_with_companies(vacancies: list) -> None:
        """Вывод вакансий в консоль в читаемом формате"""
        for index, vacancy in enumerate(vacancies, 1):
            if vacancy[2] is None:
                salary = f"До {vacancy[3]} руб."
            elif vacancy[3] is None:
                salary = f"От {vacancy[2]} руб."
            else:
                salary = f"От {vacancy[2]} до {vacancy[3]} руб."
            print(
                f"""Vacancy # {index}
                    Company: {vacancy[0]}. Vacancy: {vacancy[1]}
                    Salary: {salary}
                    Link: {vacancy[4]}"""
            )