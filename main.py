from time import sleep

from src.comp_fetcher import HeadHunterCompanies
from src.db_manager import DBManager
from src.vac_fetcher import HeadHunterVacancies

MY_COMPANIES_LIST = [
    "Pooling",
    "Amigoweb",
    "Doubletapp",
    "InlyIT",
    "PUSK",
    "Digital Sail",
    "Skillline",
    "Mindbox",
    "SPRINTHOST",
    "Voximplant",
]


def initial_setup() -> list:
    """Настройка компаний для поиска"""
    print("Добро пожаловать в приложение для сохранения базы данных вакансий! Давайте начнем c настройки.\n")

    user_company_list = input(
        f"""Пожалуйста, введите названия компаний (через пробел), в которых вы хотели бы найти открытые вакансии
 или просто нажмите ENTER, чтобы использовать список компаний по умолчанию. (По умолчанию: {MY_COMPANIES_LIST}\n"""
    )
    if user_company_list:
        companies_list = user_company_list.split(",")
    else:
        companies_list = MY_COMPANIES_LIST
    return companies_list


def parsing_companies(companies_list: list) -> list:
    """Поиск компаний из заданного списка"""
    companies_parser = HeadHunterCompanies(companies_list)

    companies_parser.prepare_to_fetch()

    companies_parser.get_companies_info()

    companies_parser.get_companies_id()

    return companies_parser.id_list


def parsing_vacancies(companies_id_list: list) -> list:
    """Поиск вакансий по списку идентификаторов компаний"""
    vacancies_parser = HeadHunterVacancies()

    vacancies_parser.fetch_vacancies(companies_id_list)

    filtered_data = vacancies_parser.filter_data()

    return filtered_data


def setting_up_database(user_name: str, password: str) -> DBManager:
    """Подготовка базы данных для дальнейшей работы"""
    db_manager = DBManager(user_name, password)

    db_manager.create_database()

    return db_manager


def set_database_option(option_number: str, database: DBManager) -> bool:
    """Выбор одного из методов работы из класса DBManager"""
    app_status = True
    if option_number == "1":
        database.get_all_vacancies()
    elif option_number == "2":
        database.get_companies_and_vacancies_count()
    elif option_number == "3":
        database.get_avg_salary()
    elif option_number == "4":
        database.get_vacancies_with_higher_salary()
    elif option_number == "5":
        user_keyword = input("Пожалйста введите кодовое слово: \n")
        database.get_vacancies_with_keyword(user_keyword)
    elif option_number == "0":
        app_status = False
    else:
        print("Неверный ввод, пожалуйста попробуйте снова.\n")
    if app_status is True:
        print("\nВы можете продолжить работу или выйти из приложения\n")
    return app_status


def main() -> None:
    companies_list = initial_setup()

    print("Отлично! Теперь пришло время установить соединение с вашей базой данных PostgreSQL\n")

    user_name = input("Пожалуйста, введите свое имя пользователя PostgreSQL:: ")
    password = input("Пожалуйства введите свой пароль: ")
    db_manager = setting_up_database(user_name, password)
    sleep(1)

    print("Хорошо! Начинаю поиск на сайте HeadHunter...\n")
    sleep(2)

    companies_id = parsing_companies(companies_list)
    sleep(2)
    vacancies = parsing_vacancies(companies_id)
    sleep(2)

    db_manager.fill_up_tables(companies_list, vacancies)
    print("Поиск завершен, и ваша база данных готова! Теперь вы можете выбрать номер опции для работы с вакансиями.\n")
    sleep(2)
    running_app = True
    while running_app:
        user_choice = input(
            """
        1. Посмотреть все доступные вакансии и соответствующих работодателей.
        2. Посмотреть, сколько вакансий есть у каждого работодателя.
        3. Посмотреть среднюю зарплату по всем доступным вакансиям.
        4. Посмотреть вакансии с зарплатой выше средней.
        5. Посмотреть вакансии, отфильтрованные по ключевому слову.
        0. Выйти из приложения.\n"""
        )

        running_app = set_database_option(user_choice, db_manager)
        sleep(3)

    print("Завершение работы. Спасибо!")
    input("\n\n\nНажмите Enter для выхода.")


if __name__ == "__main__":
    main()