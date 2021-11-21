import sys
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from design.mainDesign import Ui_MainWindow
from design.addEditCoffeeFormDesign import Ui_Dialog


class AddEditDialog(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent, table_updater, db_con):
        super(AddEditDialog, self).__init__(parent)
        self.con = db_con
        self.variants = {}
        self.is_edit_mode = True
        self.table_updater = table_updater
        self.setupUi(self)

    def setupUi(self, Dialog):
        super().setupUi(Dialog)
        self.set_variants()
        self.comboBoxMode.currentTextChanged.connect(self.set_dialog_type)
        self.comboBoxMode.currentTextChanged.emit(self.comboBoxMode.currentText())
        self.spinBoxID.valueChanged.connect(self.update_edit_data)
        prev = self.spinBoxID.value()
        self.spinBoxID.valueChanged.emit(prev)
        self.btnAddEdit.clicked.connect(self.add_edit_item)

    def set_variants(self):
        cur = self.con.cursor()
        grind_levels = cur.execute("""SELECT ID, GrindLevel FROM GrindLevels""").fetchall()
        self.variants['grind_levels'] = [{'id': id_, 'level': level} for id_, level in grind_levels]
        self.comboBoxGrindLevel.addItems([i for _, i in grind_levels])
        roast_levels = cur.execute("""SELECT ID, RoastLevel FROM RoastLevels""").fetchall()
        self.variants['roast_levels'] = [{'id': id_, 'level': level} for id_, level in roast_levels]
        self.comboBoxRoastLevel.addItems([i for _, i in roast_levels])

    def clear_current_data(self):
        self.lineEditName.clear()
        self.lineEditVarietyName.clear()
        self.comboBoxRoastLevel.setCurrentIndex(0)
        self.comboBoxGrindLevel.setCurrentIndex(0)
        self.lineEditTasteDescription.clear()
        self.spinBoxPrice.setValue(self.spinBoxPrice.minimum())
        self.spinBoxPackingVolume.setValue(self.spinBoxPackingVolume.minimum())

    def set_item_data(self, id_):
        cur = self.con.cursor()
        item_data = cur.execute("""SELECT * FROM Coffee WHERE ID = ? """, (id_,)).fetchone()
        (_, name, variety_name, roast_level, grind_level,
         taste_desc, price, packing_volume, _) = item_data
        roast_level = [i for i in self.variants['roast_levels']
                       if i['id'] == roast_level][0]['level']
        grind_level = [i for i in self.variants['grind_levels']
                       if i['id'] == grind_level][0]['level']
        self.lineEditName.setText(name)
        self.lineEditVarietyName.setText(variety_name)
        self.comboBoxRoastLevel.setCurrentText(roast_level)
        self.comboBoxGrindLevel.setCurrentText(grind_level)
        self.lineEditTasteDescription.setText(taste_desc)
        self.spinBoxPrice.setValue(price)
        self.spinBoxPackingVolume.setValue(packing_volume)

    def update_edit_data(self, id_):
        if not self.is_edit_mode:
            return
        self.set_item_data(id_)

    def set_dialog_type(self, cur_mode):
        cur = self.con.cursor()
        ids = cur.execute("""SELECT ID FROM Coffee""")
        ids = [i for i, in ids]
        if not ids:
            ids = [0]
            self.comboBoxMode.setCurrentText('Добавление')
            cur_mode = 'Добавление'
        min_id, max_id = min(ids), max(ids)
        self.clear_current_data()
        if cur_mode == 'Изменение':
            self.spinBoxID.setRange(min_id, max_id)
            self.spinBoxID.setValue(min_id)
            self.set_item_data(self.spinBoxID.value())
            self.btnAddEdit.setText('Изменить')
            self.is_edit_mode = True
        elif cur_mode == 'Добавление':
            self.is_edit_mode = False
            self.spinBoxID.setRange(max_id + 1, 2147483647)
            self.btnAddEdit.setText('Добавить')

    def add_edit_item(self):
        try:
            if self.is_edit_mode:
                self.edit_item()
            else:
                self.add_item()
        except ValueError:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Введите данные')
            return
        except sqlite3.IntegrityError:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Кофе с таким названием уже существует')
            return
        reply = QtWidgets.QMessageBox.question(self, 'Подтвердить',
                                               f'Вы уверены, что хотите '
                                               f'{"изменить" if self.is_edit_mode else "добавить"}'
                                               f' элемент?')
        if reply == QtWidgets.QMessageBox.Yes:
            self.con.commit()
            self.table_updater()

    def get_new_values(self):
        name = self.lineEditName.text()
        variety_name = self.lineEditVarietyName.text()
        roast_level = self.comboBoxRoastLevel.currentText()
        roast_level = [i for i in self.variants['roast_levels']
                       if i['level'] == roast_level][0]['id']
        grind_level = self.comboBoxGrindLevel.currentText()
        grind_level = [i for i in self.variants['grind_levels']
                       if i['level'] == grind_level][0]['id']
        taste_desc = self.lineEditTasteDescription.text()
        price = self.spinBoxPrice.value()
        volume = self.spinBoxPackingVolume.value()
        if '' in (name, variety_name, taste_desc):
            raise ValueError('Empty values')
        values = {'Name': name, 'VarietyName': variety_name, 'RoastLevel': roast_level, 'GrindLevel':
            grind_level, 'TasteDescription': taste_desc, 'Price': price,
                  'PackingVolume': volume}
        return values

    def edit_item(self):
        current_id = self.spinBoxID.value()
        cur = self.con.cursor()
        query = "UPDATE Coffee SET"
        new_values = self.get_new_values()
        for key, value in new_values.items():
            query += f' {key} = "{value}",'
        query = query[:-1]
        query += ' '
        query += f"WHERE ID = {current_id}"
        cur.execute(query)

    def add_item(self):
        current_id = self.spinBoxID.value()
        cur = self.con.cursor()
        new_values = self.get_new_values()
        query = f"INSERT INTO Coffee(\"ID\", " \
                f"{', '.join(chr(34) + str(i) + chr(34) for i in new_values.keys())}) "
        query += f"VALUES({str(current_id)}, " \
                 f"{', '.join(chr(34) + str(i) + chr(34) for i in new_values.values())})"
        cur.execute(query)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.con = sqlite3.connect('data/coffee.sqlite')
        self.setupUi(self)

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.setWindowIcon(QtGui.QIcon('coffee.svg'))
        self.actionAddEdit.triggered.connect(self.show_add_edit_dialog)
        self.tableCoffee.mouseDoubleClickEvent = self.tableMouseDoubleClickEvent
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
        self.tableCoffee.setColumnCount(len(header))
        self.tableCoffee.setRowCount(0)
        self.tableCoffee.setHorizontalHeaderLabels(header)
        data = self.get_db_data()
        for row_ind, row in enumerate(data):
            self.tableCoffee.setRowCount(
                self.tableCoffee.rowCount() + 1)
            for col_ind, col in enumerate(row):
                self.tableCoffee.setItem(row_ind, col_ind, QtWidgets.QTableWidgetItem(col))

    def show_add_edit_dialog(self):
        dialog = AddEditDialog(self, self.display_table, self.con)
        dialog.exec()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete):
            rows = [i.row() for i in self.tableCoffee.selectionModel().selectedRows()]
            if not rows:
                return
            reply = QtWidgets.QMessageBox.question(self, 'Подтвердить', f'Вы уверены,'
                                                                        f' что хотите удалить'
                                                                        f' строки в количестве'
                                                                        f' {len(rows)}?')
            if reply == QtWidgets.QMessageBox.Yes:
                self.remove_entries(rows)

    def tableMouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        item = self.tableCoffee.itemAt(a0.pos())
        dialog = AddEditDialog(self, self.display_table, self.con)
        if item is not None:
            name = self.tableCoffee.item(item.row(), 0).text()
            cur = self.con.cursor()
            item_id, = cur.execute("""SELECT ID FROM Coffee WHERE Name = ?""", (name,)).fetchone()
            dialog.comboBoxMode.setCurrentText('Изменение')
            dialog.spinBoxID.setValue(item_id)
        else:
            dialog.comboBoxMode.setCurrentText('Добавление')
        dialog.exec()

    def remove_entries(self, rows):
        cur = self.con.cursor()
        for row in rows:
            name = self.tableCoffee.item(row, 0).text()
            cur.execute("""DELETE FROM Coffee WHERE Name = ?""", (name,))
        self.con.commit()
        self.display_table()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
