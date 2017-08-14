# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 10:46:28 2017

@author: jdubbeldam
"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QFileDialog,
                             QRadioButton, QPushButton, QCheckBox, QDialog, QTextEdit,
                             QButtonGroup, QLineEdit, QApplication)
from classes import Universe, Query


#Global constants defining the amount of vertical space between those specific items.
PUSHBUTTONHEIGHT = 50
RADIOBUTTONHEIGHT = 20
CHECKBOXHEIGHT = 20

class CreateQueryInterface(QMainWindow):
    """
    This class provides a GUI to the Query class imported from classes.py.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        Handles generating the main interface. This consists of a column of
        buttons, which get enabled when they become relevant, and a textbox
        from where the output from compile_query can be copied.
        """
        self.universe_button = QPushButton('Select universe', self)
        self.universe_button.move(50, 50)
        self.universe_button.clicked.connect(self.pick_universe)
        self.table_button = QPushButton('Select tables', self)
        self.table_button.move(50, 100)
        self.table_button.clicked.connect(self.pick_tables)
        self.table_button.setEnabled(False)
        self.column_button = QPushButton('Select columns', self)
        self.column_button.move(50, 150)
        self.column_button.clicked.connect(self.pick_table_for_columns)
        self.column_button.setEnabled(False)
        self.join_button = QPushButton('Specify joins', self)
        self.join_button.move(50, 200)
        self.join_button.clicked.connect(self.specify_joins)
        self.join_button.setEnabled(False)
        self.where_button = QPushButton('Specify wheres', self)
        self.where_button.move(50, 250)
        self.where_button.clicked.connect(self.specify_where)
        self.where_button.setEnabled(False)
        self.preset_button = QPushButton('Presets', self)
        self.preset_button.move(50, 300)
        self.preset_button.clicked.connect(self.select_presets)
        self.preset_button.setEnabled(False)
        self.compile_button = QPushButton('Compile', self)
        self.compile_button.move(50, 350)
        self.compile_button.clicked.connect(self.print_query)
        self.compile_button.setEnabled(False)
        self.output = QTextEdit(self)
        self.output.move(200, 50)
        self.output.resize(250, 400)
        self.output.setReadOnly(True)
        self.resize(500, 500)
        self.center()
        self.raise_()
        self.activateWindow()

        self.available_tables = []
        self.activated_tables = []
        self.activated_columns = {}
        self.join_settings = {}
        self.where = []
        self.activated_presets = {}
        self.added_by_preset = {}

        self.show()

    def center(self):
        """
        Handles the position of the main window.
        """
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height())/2)


    def pick_universe(self):
        """
        Creates a filedialog to select a JSON file to serve as context (Universe).
        These files have their extension changed to .uni to make filtering easier.
        The generated files will be in one specific directory, so this location
        is hardcoded.
        When a JSON is selected, instances of the imported classes are created
        to serve as a reference. Relevant buttons are activated.
        """
        self.universe_file = QFileDialog.getOpenFileName(
            None,
            'Select universe',
            'R:/NL/Database Marketing/R library/SQL builder/Poging 4/Universes',
            'Universes (*.uni)')[0]
        self.universe = Universe(self.universe_file)
        self.query = Query(self.universe)
        self.available_tables = self.query.graph.tables
        self.table_button.setEnabled(True)
        self.preset_button.setEnabled(True)
        self.universe_button.setEnabled(False)

        for preset in self.universe.presets:
            self.activated_presets[preset] = False


    def pick_tables(self):
        """
        Creates a dialog where tables can be activated. self.activated_tables
        contains a list of tables already activated; the checked state is imported
        from there. If the table has been activated by a preset, its button will
        be disabled, to prevent messing with the preset.
        """
        dialog2 = QDialog()
        buttons = []
        for index, table in zip(range(len(self.available_tables)), self.available_tables):
            buttons.append(QCheckBox(dialog2))
            buttons[index].setText(table)
            buttons[index].move(10, 10 + index * CHECKBOXHEIGHT)
            buttons[index].clicked[bool].connect(self.activate_table)
            buttons[index].setChecked(table in self.activated_tables)
            try:
                buttons[index].setEnabled(not self.added_by_preset[table])
            except KeyError:
                pass

        dialog2.setWindowTitle('Pick tables')
        dialog2.exec_()

    def activate_table(self, pressed):
        """
        When a checkbox created by pick_tables is changed, the related table is
        added or removed from self.activated_tables. This also activates more
        relevant buttons in the main window.
        """
        source = self.sender()
        if pressed:
            self.activated_tables.append(source.text())
            self.activated_columns[source.text()] = []
            self.added_by_preset[source.text()] = False
        else:
            new_tables = [table
                          for table in self.activated_tables
                          if not table == source.text()]
            self.activated_tables = new_tables
            self.activated_columns[source.text()] = None

        self.column_button.setEnabled(True)
        self.compile_button.setEnabled(True)
        if len(self.activated_tables) > 1:
            self.join_button.setEnabled(True)


    def pick_table_for_columns(self):
        """
        Selecting columns goes in two steps, first the table is selected, then
        another dialog is displayed with checkboxes for the columns. This method
        handles the table selection.
        """
        dialog3 = QDialog()

        buttons = []
        tables = self.activated_tables
        for index, table in zip(range(len(tables)), tables):
            buttons.append(QPushButton(table, dialog3))
            buttons[index].move(10, 10 + index * PUSHBUTTONHEIGHT)
            buttons[index].clicked.connect(self.pick_columns)
        dialog3.setWindowTitle('Select tables')
        dialog3.exec_()

    def pick_columns(self):
        """
        When a table is selected, its name is stored in an attribute so it can
        be called in subsequent functions. This method enumerates all columns
        available in the selected table and creates checkboxes.
        """
        source = self.sender()
        self.selected_table = source.text()
        dialog = QDialog()

        buttons = []
        columns = self.query.graph.json[self.selected_table]['Columns']
        for index, column in zip(range(len(columns)),
                                 sorted(columns)):
            buttons.append(QCheckBox(dialog))
            buttons[index].setText(column)
            buttons[index].move(10 + 200 * (index//15), 10 + index%15 * CHECKBOXHEIGHT)
            buttons[index].clicked[bool].connect(self.activate_columns)
            buttons[index].setChecked(column in self.activated_columns[self.selected_table])

        dialog.setWindowTitle('Pick columns')
        dialog.exec_()

    def activate_columns(self, pressed):
        """
        When a checkbox created by pick_columns is changed, it is added or removed
        from the dictionary of activated columns. Enables another button.
        """
        source = self.sender()
        if pressed:
            self.activated_columns[self.selected_table].append(source.text())
        else:
            new_columns = [column
                           for column in self.activated_columns[self.selected_table]
                           if not column == source.text()]
            self.activated_columns[self.selected_table] = new_columns

        self.where_button.setEnabled(True)

    def specify_joins(self):
        """
        Dialog to set the way tables are joined. First the required joins are
        computed by creating a Query instance, adding the activated tables to
        it and calling the find_joins method. Each of the joins gets a button
        which creates another dialog.
        """
        self.query = Query(self.universe)
        for table in self.activated_tables:
            self.query.add_tables(table)

        joins = self.query.find_joins()

        dialog = QDialog()
        options = []
        for index, join in zip(range(len(joins)), joins):
            options.append(QPushButton(join[0] + ' on ' + join[1], dialog))
            options[index].move(10, 10 + index * PUSHBUTTONHEIGHT)
            options[index].clicked.connect(self.pick_join_settings)
            options[index].joinTag = join
        dialog.setWindowTitle('Select a join')
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
            how = self.query.graph.json[table_tuple[0]]['Joins'][table_tuple[1]][1]
        except TypeError:
            table_tuple = (table_tuple[1], table_tuple[0])
            how = self.query.graph.json[table_tuple[0]]['Joins'][table_tuple[1]][1]

        self.selected_join = table_tuple
        try:
            how = self.join_settings[table_tuple]
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
            buttongroup.addButton(buttons[index])
        dialog.setWindowTitle('Pick a join type')
        dialog.exec_()

    def adjust_join_settings(self):
        """
        Sets the join setting to the selected radiobutton.
        """
        source = self.sender()
        self.join_settings[self.selected_join] = source.text()

    def specify_where(self):
        """
        Series of dialogs to set where-statements. Where-statements can be
        configured on columns, so there first is a dialog to select one of the
        activated tables, and then one to select one of the activated columns.
        """
        dialog3 = QDialog()

        buttons = []
        for index, table in zip(range(len(self.activated_tables)),
                                self.activated_tables):
            buttons.append(QPushButton(table, dialog3))
            buttons[index].move(10, 10 + index * PUSHBUTTONHEIGHT)
            buttons[index].clicked.connect(self.pick_column_for_where)
        dialog3.setWindowTitle('Select a table')
        dialog3.exec_()

    def pick_column_for_where(self):
        """
        After a table has been selected, this enumerates the activated columns
        and allows column selection.
        """
        source = self.sender()
        self.selected_table = source.text()
        self.dialog2 = QDialog()

        buttons = []
        columns = self.activated_columns[self.selected_table]
        for index, column in zip(range(len(columns)),
                                 sorted(columns)):
            buttons.append(QPushButton(self.dialog2))
            buttons[index].setText(column)
            buttons[index].move(10 + 200 * (index//15), 10 + index%15 * PUSHBUTTONHEIGHT)
            buttons[index].clicked.connect(self.specify_where_text)

        self.dialog2.setWindowTitle('Select a columns')
        self.dialog2.exec_()

    def specify_where_text(self):
        """
        Creates a line-edit dialog where "table.column = " is already filled in.
        This is (very) vulnerable to SQL-injection, but 1) this is for internal
        use only and 2) the generated SQL is printed, not sent to the database.
        """
        source = self.sender()
        selected_column = source.text()

        self.dialog = QDialog()

        self.where_editor = QLineEdit(self.dialog)
        self.where_editor.setText(self.selected_table + '.' + selected_column + ' = ')
        self.where_editor.move(20, 20)
        self.where_editor.resize(360, 20)
        confirm = QPushButton('Confirm', self.dialog)
        confirm.move(20, 60)
        confirm.clicked.connect(self.submit_where_text)
        self.dialog.setWindowTitle('Specify where statement')
        self.dialog.resize(400, 100)
        self.dialog.exec_()

    def submit_where_text(self):
        """
        Handles the submit button, stores the where-string and closes the dialogs.
        """
        self.where.append(self.where_editor.text())
        self.dialog.close()
        self.dialog2.close()

    def select_presets(self):
        """
        Presets are predefined where-statements that can be added in a few clicks.
        They add the relevant table to the list of activated tables and add
        a where statement. For simplicity, when added, a preset can't be disabled.
        """
        presets = self.universe.presets.keys()

        dialog = QDialog()

        buttons = []
        for index, preset in zip(range(len(presets)), presets):
            buttons.append(QCheckBox(dialog))
            buttons[index].setText(preset)
            buttons[index].setEnabled(not self.activated_presets[preset])
            buttons[index].setChecked(self.activated_presets[preset])
            buttons[index].clicked[bool].connect(self.activate_preset)
            buttons[index].move(10, 10 + index * CHECKBOXHEIGHT)

        dialog.setWindowTitle('Select presets')
        dialog.exec_()

    def activate_preset(self, pressed):
        """
        Activates preset. Enables buttons similar to activating a table, as this
        also activates presets. Keeps track of tables added by presets.
        """
        source = self.sender()
        source.setEnabled(False)
        self.activated_presets[source.text()] = pressed
        relevant_preset = self.universe.presets[source.text()]
        required_table = relevant_preset['table'][0]

        if required_table not in self.activated_tables:
            self.activated_tables.append(required_table)
            self.activated_columns[required_table] = []
        self.added_by_preset[required_table] = True
        self.where.append(relevant_preset['where'][0])
        self.column_button.setEnabled(True)
        self.compile_button.setEnabled(True)
        if len(self.activated_tables) > 1:
            self.join_button.setEnabled(True)

    def print_query(self):
        """
        Compiles the query. The activated elements are added to the query and
        the compile_query method is called. The result is printed in the Textdisplay.
        """
        query = Query(self.universe)

        for table in self.activated_tables:
            query.add_tables(table)

        for table in self.activated_columns:
            for column in self.activated_columns[table]:
                query.add_columns(table, column)

        query.how_to_join = self.join_settings
        if self.where:
            query.where = self.where
        outputquery = query.compile_query()
        self.output.setText(outputquery)

def main():
    app = QApplication([])
    interface = CreateQueryInterface()
    sys.exit(app.exec_())
    print(interface)

if __name__ == '__main__':
    main()
