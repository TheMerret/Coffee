import sys
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets, uic


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('main.ui', self)
        self.con = sqlite3.connect('coffee.sqlite')
        self.setupUi()

    def setupUi(self):
        self.display_table()

    def get_db_data(self):
        cur = self.con.cursor()
        data = cur.execute("""SELECT Name, VarietyName, RoastLevels.RoastLevel, 
        GrindLevels.GrindLevel, TasteDescription, Price, PackingVolume, PackingVolumeUnit FROM 
        Coffee INNER JOIN RoastLevels ON Coffee.RoastLevel = RoastLevels.ID INNER JOIN 
        GrindLevels ON Coffee.GrindLevel = GrindLevels.ID """)
        data = [i[:-3] + (f'{i[-3]} руб', f'{i[-2]} {i[-1]}') for i in data]
        return data

    def display_table(self):
        header = ['Название', 'Название сорта', 'Степень обжарки', 'Степень помола',
                  'Описание вкуса', 'Цена', 'Объем упаковки']
        self.tableCoffee: QtWidgets.QTableWidget
        self.tableCoffee.setColumnCount(len(header))
        self.tableCoffee.setRowCount(0)
        self.tableCoffee.setHorizontalHeaderLabels(header)
        data = self.get_db_data()
        for row_ind, row in enumerate(data):
            self.tableCoffee.setRowCount(
                self.tableCoffee.rowCount() + 1)
            for col_ind, col in enumerate(row):
                self.tableCoffee.setItem(row_ind, col_ind, QtWidgets.QTableWidgetItem(col))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
