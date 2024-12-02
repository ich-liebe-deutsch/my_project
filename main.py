import sqlite3
import sys
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QTextBrowser, QLineEdit, QLabel, \
    QCheckBox, QMessageBox

from pioneer_sdk import Pioneer, VideoStream

pioneer_mini = Pioneer()  # дрон
con = sqlite3.connect("pioneer.sqlite")  # бд
cur = con.cursor()


class Welcome(QMainWindow):  # вход/регистрация
    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 500)
        self.setWindowTitle("Pioneer Control Panel v0.1 BETA - Вход не выполнен")
        self.register = SignUp()
        self.login = LogIn()

        self.sign_up = QPushButton('Зарегистрироваться', self)
        self.sign_up.move(75, 400)
        self.sign_up.resize(150, 33)
        self.sign_up.clicked.connect(self.signing_up)  # кнопка зарегистрироваться

        self.pixmap = QPixmap('mini.jpg')
        self.image = QLabel(self)
        self.image.move(60, 40)
        self.image.resize(450, 350)
        self.image.setPixmap(self.pixmap)

        self.log_in = QPushButton('Войти', self)
        self.log_in.move(275, 400)
        self.log_in.resize(150, 33)
        self.log_in.clicked.connect(self.logging_in)  # кнопка входа

    def signing_up(self):  # открытие окна регистрации
        self.register.show()
        window.close()

    def logging_in(self):  # открытие окна входа в сущ. пользователя
        self.login.show()
        window.close()


class SignUp(QWidget):  # регистрация
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Регистрация аккаунта лётчика-испытателя')
        self.setFixedSize(450, 235)
        self.state = 0
        self.panel = Panel()

        self.sign_up = QPushButton('Зарегистрироваться', self)
        self.sign_up.move(30, 180)
        self.sign_up.resize(175, 33)
        self.sign_up.clicked.connect(self.req_check)

        self.license_read = QPushButton('Лицензионное соглашение', self)
        self.license_read.move(240, 180)
        self.license_read.resize(175, 33)
        self.license_read.clicked.connect(self.license)

        self.username_label = QLabel("Имя пользователя:", self)
        self.username_label.move(75, 27)
        self.username = QLineEdit(self)
        self.username.move(200, 25)
        self.username.resize(200, 25)

        self.password_label = QLabel("Пароль:", self)
        self.password_label.move(75, 72)
        self.password_req1 = QLabel("(пароль 8 символдан кыскарак булмаска тиеш,", self)
        self.password_req1.move(75, 95)
        self.password_req1.setFont(QFont('Arial', 5))
        self.password_req2 = QLabel("ике регистры да булырга тиеш һәм бик гади булмаска тиеш)", self)
        self.password_req2.move(75, 100)
        self.password_req2.setFont(QFont('Arial', 5))
        self.password = QLineEdit(self)
        self.password.move(200, 70)
        self.password.resize(200, 25)

        self.key_label = QLabel("Ключ продукта:", self)
        self.key_label.move(75, 117)
        self.key = QLineEdit(self)
        self.key.move(200, 115)
        self.key.resize(200, 25)

        self.no_key = QCheckBox("Продолжить без ключа продукта", self)
        self.no_key.move(75, 150)
        self.no_key.stateChanged.connect(lambda state: self.skip_key(state))

    def license(self):  # открытие лицензионного соглашения
        self.license = License()
        self.license.show()

    def skip_key(self, state):  # пропуск ключа
        self.state = state
        if self.state == 2:  # если галка есть
            QMessageBox.information(self, "Ограничение функций",
                                    "Без ключа продукта, некоторые функции панели будут ограничены/недоступны.")
            self.key.clear()
            self.key.setDisabled(True)
            self.key.setText('False')
        elif self.state == 0:  # если (передумали и купили ключ как сигма) галку сняли
            self.key.setDisabled(False)

    def req_check(self):  # общая проверка
        try:
            if not self.username.text() or not self.password.text():  # если хотя бы 1 из полей не заполнено
                raise UsernamePasswordEmpty
            elif not self.key.text() and self.state == 0:
                raise NoKeyWithoutCheck
            self.check_password(self.password.text())  # проверка пароля
            find_key = cur.execute(
                f"""SELECT id FROM keys
                WHERE key = '{self.key.text()}'""").fetchall()
            find_user = cur.execute(
                f"""SELECT id FROM users
                WHERE username = '{self.username.text()}'""").fetchall()
            if not find_key and self.state == 0:
                raise KeyNotFound
            if find_user:
                raise UserExists
        except UsernamePasswordEmpty:
            QMessageBox.critical(self, "Ошибка регистрации",
                                 "Имя пользователя или пароль не заполнены")
            return 0
        except NoKeyWithoutCheck:
            QMessageBox.critical(self, "Ошибка регистрации",
                                 "Ключ продукта не заполнен")
            return 0
        except PasswordRulesError:
            QMessageBox.critical(self, "Ошибка регистрации",
                                 "Пароль не соответствует требованиям")
            return 0
        except KeyNotFound:
            QMessageBox.critical(self, "Ошибка регистрации",
                                 "Ключ продукта не найден в базе данных")
            return 0
        except UserExists:
            QMessageBox.critical(self, "Ошибка регистрации",
                                 "Пользователь с таким именем уже существует")
            return 0
        cur.execute(
            f"""INSERT INTO users(username,password,key_id)
            VALUES('{self.username.text()}','{self.password.text()}','{self.key.text()}')""")
        cur.execute("""UPDATE users SET logged_in='False'""")
        cur.execute(
            f"""UPDATE users SET logged_in='True' 
            WHERE username='{self.username.text()}'""")
        con.commit()
        self.panel.show()
        self.close()

    def check_password(self, password):  # проверка соответствия требованиям пароля
        if len(password) < 8 or password.islower() or password.isupper() or (not set(password) & set('1234567890')):
            raise PasswordRulesError
        for symb in password:
            if symb.isalpha():
                break
        else:
            raise PasswordRulesError


class License(QWidget):  # лицензионное соглашение
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Лицензионное соглашение')
        self.setFixedSize(400, 400)
        self.license = QTextBrowser(self)
        self.license.resize(400, 400)
        self.license_text = open('license.txt', encoding='utf-8')  # лиц. соглашение здесь (юр. белиберда)
        self.license.setText(self.license_text.read())


class UserNotFound(Exception):  # пользователь не найден
    pass


class UsernamePasswordEmpty(Exception):  # имя/пароль пусто
    pass


class AccessDenied(Exception):  # неверный пароль
    pass


class NoKeyWithoutCheck(Exception):  # нет ключа (галка не выбрана)
    pass


class PasswordRulesError(Exception):  # несоответствие пароля требованиям
    pass


class KeyNotFound(Exception):  # ключ не существует (анти-пиратство)
    pass


class UserExists(Exception):  # пользователь уже существует
    pass


class LogIn(QWidget):  # вход в сущ. пользователя
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Вход в аккаунт лётчика-испытателя')
        self.setFixedSize(450, 175)
        self.panel = Panel()

        self.log_in = QPushButton('Войти', self)
        self.log_in.move(125, 115)
        self.log_in.resize(175, 33)
        self.log_in.clicked.connect(self.check_procedure)

        self.username_label = QLabel("Имя пользователя:", self)
        self.username_label.move(75, 27)
        self.username = QLineEdit(self)
        self.username.move(200, 25)
        self.username.resize(200, 25)

        self.password_label = QLabel("Пароль:", self)
        self.password_label.move(75, 72)
        self.password = QLineEdit(self)
        self.password.move(200, 70)
        self.password.resize(200, 25)

    def check_procedure(self):  # проверка
        try:
            if not self.username.text() or not self.password.text():  # если хотя бы 1 из полей не заполнено
                raise UsernamePasswordEmpty
        except UsernamePasswordEmpty:
            QMessageBox.critical(self, "Ошибка входа",
                                 "Имя пользователя или пароль не заполнены")
            return 0
        try:
            user = cur.execute(
                f"""SELECT id FROM users WHERE username = '{self.username.text()}'""").fetchall()  # поиск ид юзера
            passwd = cur.execute(
                f"""SELECT id FROM users WHERE username = '{self.username.text()}'
            AND password = '{self.password.text()}'""").fetchall()  # поиск ид пароля
            if not user:  # если пользователя нет в дб
                raise UserNotFound()
            if user != passwd:  # если ид не совпадают (простыми словами - если неверный пароль)
                raise AccessDenied()
        except UserNotFound:
            QMessageBox.critical(self, "Ошибка входа",
                                 "Пользователь не найден")
            return 0
        except AccessDenied:
            QMessageBox.critical(self, "Ошибка входа",
                                 "Неверный пароль")
            return 0
        cur.execute("""UPDATE users SET logged_in='False'""")
        con.commit()
        cur.execute(f"""UPDATE users SET logged_in='True' 
        WHERE username='{self.username.text()}'""")
        con.commit()
        self.panel.show()
        self.close()


class Panel(QMainWindow):  # сама панель
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pioneer Control Panel v0.1 BETA')
        self.setFixedSize(200, 190)
        self.control = Control()
        self.info = Info()
        self.settings = Settings()

        self.title = QLabel('Здравствуйте!', self)
        self.title.move(60, 5)

        self.controls = QPushButton('Управление', self)
        self.controls.move(25, 35)
        self.controls.resize(150, 33)
        self.controls.clicked.connect(self.key_check)  # управление

        self.information = QPushButton('Информация', self)
        self.information.move(25, 85)
        self.information.resize(150, 33)
        self.information.clicked.connect(self.open_info)  # информация о дроне

        self.setting = QPushButton('Настройки', self)
        self.setting.move(25, 135)
        self.setting.resize(150, 33)
        self.setting.clicked.connect(self.open_settings)  # настройки

    def open_settings(self):
        self.settings.show()
        self.close()

    def open_info(self):
        if pioneer_mini.connected():
            self.info.show()
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка подключения",
                                 "Не удаётся подключиться к дрону")

    def key_check(self):
        if pioneer_mini.connected():
            stream = VideoStream()
            stream.start()
            self.control.show()
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка подключения",
                                 "Не удаётся подключиться к дрону")


class Control(QWidget):  # управление
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Управление')
        self.setFixedSize(400, 290)

        self.armed = QPushButton('Запуск', self)
        self.armed.move(35, 35)
        self.armed.clicked.connect(self.arming)

        self.disarmed = QPushButton('Отключить', self)
        self.disarmed.move(35, 75)
        self.disarmed.clicked.connect(self.disarming)

        self.lift = QPushButton('Взлёт', self)
        self.lift.move(35, 115)
        self.lift.clicked.connect(self.takeoff)

        self.land = QPushButton('Посадка', self)
        self.land.move(35, 155)
        self.land.clicked.connect(self.landing)

        self.fly = QPushButton('Лететь к точке', self)
        self.fly.move(35, 195)
        self.fly.clicked.connect(self.flying)

        self.x_label = QLabel('x:', self)
        self.x_label.move(35, 220)
        self.x = QLineEdit(self)
        self.x.move(30, 235)
        self.x.resize(20, 20)
        self.y_label = QLabel('y:', self)
        self.y_label.move(75, 220)
        self.y = QLineEdit(self)
        self.y.move(75, 235)
        self.y.resize(20, 20)
        self.z_label = QLabel('z:', self)
        self.z_label.move(115, 220)
        self.z = QLineEdit(self)
        self.z.move(115, 235)
        self.z.resize(20, 20)

    def arming(self):
        pioneer_mini.arm()

    def disarming(self):
        pioneer_mini.disarm()

    def takeoff(self):
        pioneer_mini.takeoff()

    def landing(self):
        pioneer_mini.land()

    def flying(self):
        pioneer_mini.go_to_local_point(int(self.x.text()), int(self.y.text()), int(self.z.text()), 0)


class Info(QWidget):  # информация о дроне
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Информация о дроне')
        self.setFixedSize(400, 290)

        self.connection_status = QLabel('Соединение: стабильно', self)
        self.connection_status.move(35, 35)

        status = pioneer_mini.get_battery_status()
        self.battery = QLabel(f"Заряд аккумулятора: {status}%", self)
        self.battery.move(35, 85)


class Settings(QWidget):  # настройки
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Настройки')
        self.setFixedSize(350, 200)

        username = cur.execute(
            "SELECT username FROM users WHERE logged_in='True'").fetchall()
        for elem in username:
            username = str(elem[0])
        self.username_label = QLabel(f"Имя пользователя: {username}", self)
        self.username_label.move(25, 25)
        self.password_label = QLabel('Пароль: ********', self)
        self.password_label.move(25, 75)
        key = cur.execute(
            f"""SELECT key_id FROM users 
            WHERE logged_in = 'True'""").fetchall()
        if key == [('False', )]:
            self.key_label = QLabel('Ключ продукта: Отсутствует', self)
            self.key_label.move(25, 125)
        else:
            full_key = cur.execute(
                f"SELECT key FROM keys WHERE id IN (SELECT key_id FROM users WHERE username = '{username}')")
            for elem in full_key:
                self.key_label = QLabel(f'Ключ продукта: {str(elem[0])}', self)
                self.key_label.move(25, 125)


if __name__ == '__main__':  # открытие окна входа/регистрации, очевидно
    app = QApplication(sys.argv)
    window = Welcome()
    window.show()
    sys.exit(app.exec())
