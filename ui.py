# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 10:46:28 2017

@author: jdubbeldam
"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QFileDialog, QDialog,
                             QRadioButton, QPushButton, QCheckBox, QTextEdit,
                             QButtonGroup, QLineEdit, QApplication)
from classes import Query


#Global constants defining the amount of vertical space between those specific items.
PUSHBUTTONHEIGHT = 40
RADIOBUTTONHEIGHT = 20
CHECKBOXHEIGHT = 20

class CreateQueryInterface(QMainWindow):
    """
    This class provides a GUI to the Query class imported from classes.py.
    """

    def __init__(self):
        super().__init__()
        self.select_universe()
        self.init_ui()

    def init_ui(self):
        """
        Handles generating the main interface. This consists of a column of
        buttons, which get enabled when they become relevant, and a textbox
        from where the output from compile_query can be copied.
        """
        table_button = QPushButton('Select tables', self)
        table_button.move(50, 50)
        table_button.clicked.connect(self.pick_tables)
        table_button.setEnabled(True)
        self.column_button = QPushButton('Select columns', self)
        self.column_button.move(50, 100)
        self.column_button.clicked.connect(self.pick_table_for_columns)
        self.column_button.setEnabled(False)
        self.join_button = QPushButton('Specify joins', self)
        self.join_button.move(50, 150)
        self.join_button.clicked.connect(self.specify_joins)
        self.join_button.setEnabled(False)
        self.where_button = QPushButton('Specify wheres', self)
        self.where_button.move(50, 200)
        self.where_button.clicked.connect(self.specify_where)
        self.where_button.setEnabled(False)
        preset_button = QPushButton('Presets', self)
        preset_button.move(50, 250)
        preset_button.clicked.connect(self.select_presets)
        preset_button.setEnabled(True)
        self.compile_button = QPushButton('Compile', self)
        self.compile_button.move(50, 300)
        self.compile_button.clicked.connect(self.print_query)
        self.compile_button.setEnabled(False)
        reset_button = QPushButton('Reset', self)
        reset_button.move(50, 450)
        reset_button.clicked.connect(self.reset)
        self.output = QTextEdit(self)
        self.output.move(200, 50)
        self.output.resize(400, 400)
        self.output.setReadOnly(True)
        self.resize(650, 500)
        self.setWindowTitle('SQL Builder')
        self.center()
        self.raise_()
        self.activateWindow()
        self.show()

    def center(self):
        """
        Handles the position of the main window.
        """
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height())/2)

    def select_universe(self):
        """
        Upon initialization creates a filedialog to select a JSON file to serve as
        context (Universe). These files have their extension changed to .uni to make
        filtering easier. The generated files will be in one specific directory, so
        this location is hardcoded.
        """
        try:
            self.query = Query(filename=QFileDialog.getOpenFileName(
                None,
                'Select universe',
                'R:/NL/Database Marketing/R library/SQL builder/Universes',
                'Universes (*.uni)')[0])
        except FileNotFoundError:
            sys.exit()

    def pick_tables(self):
        """
        Creates a dialog where tables can be activated. self.active_tables
        contains a list of tables already activated; the checked state is imported
        from there. If the table has been activated by a preset, its button will
        be disabled, to prevent messing with the preset.
        """
        dialog = QDialog()
        buttons = []
        for index, table in zip(range(len(self.query.tables)), self.query.tables):
            buttons.append(QCheckBox(dialog))
            buttons[index].setText(table)
            buttons[index].move(10, 10 + index * CHECKBOXHEIGHT)
            buttons[index].clicked[bool].connect(self.activate_table)
            buttons[index].setChecked(table in self.query.active_tables)
            try:
                buttons[index].setEnabled(table not in self.query.tables_added_by_preset)
            except KeyError:
                pass

        dialog.setWindowTitle('Pick tables')
        dialog.exec_()

    def activate_table(self, pressed):
        """
        When a checkbox created by pick_tables is changed, the related table is
        added or removed from self.active_tables. This also activates more
        relevant buttons in the main window.
        """
        source = self.sender()
        if pressed:
            self.query.add_tables(source.text())
        else:
            self.query.remove_tables(source.text())
        self.column_button.setEnabled(True)
        self.compile_button.setEnabled(True)
        if len(self.query.active_tables) > 1:
            self.join_button.setEnabled(True)


    def pick_table_for_columns(self):
        """
        Selecting columns goes in two steps, first the table is selected, then
        another dialog is displayed with checkboxes for the columns. This method
        handles the table selection.
        """
        dialog = QDialog()

        buttons = []
        tables = self.query.active_tables
        for index, table in zip(range(len(tables)), tables):
            buttons.append(QPushButton(table, dialog))
            buttons[index].move(10, 10 + index * PUSHBUTTONHEIGHT)
            buttons[index].clicked.connect(self.pick_columns)
        dialog.setWindowTitle('Select tables')
        dialog.exec_()

    def pick_columns(self):
        """
        When a table is selected, its name is stored in an attribute so it can
        be called in subsequent functions. This method enumerates all columns
        available in the selected table and creates checkboxes.
        """
        source = self.sender()
        selected_table = source.text()
        dialog = QDialog()

        buttons = []
        columns = self.query.tables[selected_table]['Columns']
        maximal_name_length = max([len(column) for column in columns])
        for index, column in zip(range(len(columns)), sorted(columns)):
            buttons.append(QCheckBox(dialog))
            buttons[index].setText(column)
            buttons[index].move(10 + (CHECKBOXHEIGHT + 6 * maximal_name_length) * (index//45),
                                10 + index%45 * CHECKBOXHEIGHT)
            buttons[index].clicked[bool].connect(self.activate_columns)
            buttons[index].selected_table = selected_table
            buttons[index].setChecked(column in self.query.active_columns[selected_table])

        dialog.setWindowTitle('Pick columns')
        dialog.resize(20 + (CHECKBOXHEIGHT + 6 * maximal_name_length) * (len(columns)//45 + 1),
                      20 + min(len(columns), 45) * CHECKBOXHEIGHT)
        dialog.exec_()

    def activate_columns(self, pressed):
        """
        When a checkbox created by pick_columns is changed, it is added or removed
        from the dictionary of activated columns. Enables another button.
        """

        source = self.sender()
        selected_table = source.selected_table
        if pressed:
            self.query.add_columns(selected_table, source.text())
            self.where_button.setEnabled(True)
        else:
            self.query.remove_columns(selected_table, source.text())

    def specify_joins(self):
        """
        Dialog to set the way tables are joined. First the required joins are
        computed by calling the find_joins method. Each of the joins gets a button
        which creates another dialog.
        """
        joins = self.query.find_joins()

        dialog = QDialog()
        options = []
        max_join_string = max([len(join[0] + ' on ' + join[1]) for join in joins])
        for index, join in zip(range(len(joins)), joins):
            options.append(QPushButton(join[0] + ' on ' + join[1], dialog))
            options[index].move(10, 10 + index * PUSHBUTTONHEIGHT)
            options[index].clicked.connect(self.pick_join_settings)
            options[index].joinTag = join
        dialog.setWindowTitle('Select a join')
        dialog.resize(20 + 6 * max_join_string, 20 + PUSHBUTTONHEIGHT * len(joins))
        dialog.exec_()

    def pick_join_settings(self):
        """
        Given a join, the default join setting is imported from the Universe.
        Then the join_settings dictionary is checked to see if another join has
        already been set or not. If not, the default is used. The four options
        are shown as radiobuttons with the current setting activated.
        """
        source = self.sender()

        table_tuple = source.joinTag
        try:
            how = self.query.tables[table_tuple[0]]['Joins'][table_tuple[1]][1]
        except TypeError:
            table_tuple = (table_tuple[1], table_tuple[0])
            how = self.query.tables[table_tuple[0]]['Joins'][table_tuple[1]][1]

        selected_join = table_tuple
        try:
            how = self.query.how_to_join[table_tuple]
        except KeyError:
            pass

        dialog = QDialog()
        buttongroup = QButtonGroup(dialog)
        buttons = []
        for index, setting in zip(range(4), ['inner', 'left', 'right', 'full']):
            buttons.append(QRadioButton(dialog))
            buttons[index].setText(setting)
            buttons[index].setChecked(setting == how)
            buttons[index].move(20, 20 + index * RADIOBUTTONHEIGHT)
            buttons[index].clicked.connect(self.adjust_join_settings)
            buttons[index].selected_join = selected_join
            buttongroup.addButton(buttons[index])
        dialog.setWindowTitle('Pick a join type')
        dialog.exec_()

    def adjust_join_settings(self):
        """
        Sets the join setting to the selected radiobutton.
        """
        source = self.sender()
        selected_join = source.selected_join
        self.query.how_to_join[selected_join] = source.text()

    def specify_where(self):
        """
        Series of dialogs to set where-statements. Where-statements can be
        configured on columns, so there first is a dialog to select one of the
        activated tables, and then one to select one of the activated columns.
        """
        dialog3 = QDialog()
        tables = self.query.active_tables
        buttons = []
        for index, table in zip(range(len(tables)), tables):
            buttons.append(QPushButton(table, dialog3))
            buttons[index].move(10, 10 + index * PUSHBUTTONHEIGHT)
            buttons[index].clicked.connect(self.pick_column_for_where)
            buttons[index].setEnabled(len(self.query.active_columns[table]))
        dialog3.setWindowTitle('Select a table')
        dialog3.exec_()

    def pick_column_for_where(self):
        """
        After a table has been selected, this enumerates the activated columns
        and allows column selection.
        """
        source = self.sender()
        selected_table = source.text()
        dialog = QDialog()

        buttons = []
        columns = self.query.active_columns[selected_table]
        maximal_name_length = max([len(column) for column in columns])
        for index, column in zip(range(len(columns)), sorted(columns)):
            buttons.append(QPushButton(dialog))
            buttons[index].setText(column)
            buttons[index].move(10 + 6 * maximal_name_length * (index//45),
                                10 + index%45 * PUSHBUTTONHEIGHT)
            buttons[index].clicked.connect(self.specify_where_text)
            buttons[index].selected_table = selected_table
            buttons[index].parent_dialog = dialog

        dialog.setWindowTitle('Select a column')
        dialog.resize(20 + (CHECKBOXHEIGHT + 6 * maximal_name_length) * (len(columns)//45 + 1),
                      20 + min(len(columns), 45) * CHECKBOXHEIGHT)
        dialog.exec_()

    def specify_where_text(self):
        """
        Creates a line-edit dialog where "table.column = " is already filled in.
        This is (very) vulnerable to SQL-injection, but 1) this is for internal
        use only and 2) the generated SQL is printed, not sent to the database.
        """
        source = self.sender()
        selected_column = source.text()
        selected_table = source.selected_table
        dialog = QDialog()

        where_editor = QLineEdit(dialog)
        try:
            where_editor.setText(self.query.where[(selected_table, selected_column)])
        except KeyError:
            where_editor.setText(selected_table + '.' + selected_column + ' = ')
        where_editor.move(20, 20)
        where_editor.resize(6 * len(where_editor.text()) + 200, 20)
        confirm_button = QPushButton('Confirm', dialog)
        confirm_button.move(20, 60)
        confirm_button.clicked.connect(self.submit_where_text)
        confirm_button.selected_column = selected_column
        confirm_button.selected_table = selected_table
        confirm_button.linked_editor = where_editor
        confirm_button.parent_dialog = [dialog, source.parent_dialog]
        dialog.setWindowTitle('Specify where statement')
        dialog.resize(6 * len(where_editor.text()) + 240, 100)
        dialog.exec_()

    def submit_where_text(self):
        """
        Handles the submit button, stores the where-string and closes the dialogs.
        """
        source = self.sender()
        editor = source.linked_editor
        selected_table = source.selected_table
        selected_column = source.selected_column
        self.query.add_where(editor.text(), selected_table, selected_column)
        for dialog in source.parent_dialog:
            dialog.close()


    def select_presets(self):
        """
        Presets are predefined where-statements that can be added in a few clicks.
        They add the relevant table to the list of activated tables and add
        a where statement. For simplicity, when added, a preset can't be disabled.
        """
        presets = self.query.presets.keys()

        dialog = QDialog()

        buttons = []
        for index, preset in zip(range(len(presets)), presets):
            buttons.append(QCheckBox(dialog))
            buttons[index].setText(preset)
            buttons[index].setEnabled(preset not in self.query.active_presets)
            buttons[index].setChecked(preset in self.query.active_presets)
            buttons[index].clicked[bool].connect(self.activate_preset)
            buttons[index].move(10, 10 + index * CHECKBOXHEIGHT)

        dialog.setWindowTitle('Select presets')
        dialog.exec_()

    def activate_preset(self):
        """
        Activates preset. Enables buttons similar to activating a table, as this
        also activates presets. Keeps track of tables added by presets.
        """
        source = self.sender()
        source.setEnabled(False)
        self.query.add_preset(source.text())
        self.column_button.setEnabled(True)
        self.compile_button.setEnabled(True)
        if len(self.query.active_tables) > 1:
            self.join_button.setEnabled(True)

    def print_query(self):
        """
        Compiles the query. The activated elements are added to the query and
        the compile_query method is called. The result is printed in the Textdisplay.
        """
        self.output.setText(self.query.compile_query())

    def reset(self):
        """
        Resets the interface, opening another Universe selection dialog and clears
        the output.
        """
        self.select_universe()
        self.output.clear()


def main():
    """
    Deploys the app
    """
    app = QApplication([])
    interface = CreateQueryInterface()
    sys.exit(app.exec_())
    print(interface)

if __name__ == '__main__':
    main()
