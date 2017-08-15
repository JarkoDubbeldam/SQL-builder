# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 14:33:44 2017

@author: jdubbeldam
"""
from json import loads

class Universe:
    """
    The Universe is a context for the Query class. It contains the information
    of the available Database tables and their relation to eachother. This
    information is stored in a JSON file.
    """

    def __init__(self, filename):
        """
        Reads the JSON and separates the information in a presets dictionary and
        a graph dictionary. The latter contains the information of the nodes in
        the universe/graph, including relational information.
        """
        with open(filename, encoding='utf-8') as file:
            json = loads(str(file.read()))
        self.presets = json['presets']
        self.tables = json['graph']
        self.connections = self.get_edges()

    def get_edges(self):
        """
        Creates a dictionary with for each node a list of nodes that join on
        that node.
        """

        edges = {}
        for table in self.tables:
            edges[table] = []
            try:
                edges[table] += [connected_tables
                                 for connected_tables in self.tables[table]['Joins']]
            except AttributeError:
                pass
        for node in edges:
            for connected_node in edges[node]:
                if node not in edges[connected_node]:
                    edges[connected_node].append(node)
        return edges

    def shortest_path(self, start, end, path_argument=None):
        """
        Calculates the shortest path in a graph, using the dictionary created
        in getEgdes. Adapted from https://www.python.org/doc/essays/graphs/.
        """
        if path_argument is None:
            old_path = []
        else:
            old_path = path_argument
        path = old_path + [start]
        if start == end:
            return path
        if start not in self.connections:
            return None
        shortest = None
        for node in self.connections[start]:
            if node not in path:
                newpath = self.shortest_path(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def join_paths(self, nodes):
        """
        Extension of shortest_path to work with multiple nodes to be connected.
        The nodes are sorted based on the priority, which is taken from the JSON.
        shortest_path is called on the first two nodes, then iteratively on each
        additional node and one of the existing nodes returned by shortest_path,
        selecting the one that takes the fewest steps.
        """
        sorted_nodes = sorted([[self.tables[node]['Priority'][0], node] for node in nodes])
        paths = []

        paths.append(self.shortest_path(sorted_nodes[0][1], sorted_nodes[1][1]))
        for next_node_index in range(len(sorted_nodes) - 2):
            shortest = None
            flat_paths = [item for sublist in paths for item in sublist]
            old_path = len(flat_paths)
            for connected_path in flat_paths:
                newpath = self.shortest_path(connected_path,
                                             sorted_nodes[next_node_index+2][1],
                                             flat_paths)
                if newpath:
                    if not shortest or len(newpath[old_path:]) < len(shortest):
                        shortest = newpath[old_path:]
            paths.append(shortest)
        return paths


class Query(Universe):
    """
    Query contains the functions that allow us to build an SQL query based on
    a universe object. It maintains lists with the names of activated tables
    and, if applicable, which of their columns in a dictionary. Implicit tables
    are tables that are called, only to bridge joins from one table to another.
    Since they are not explicitly called, we don't want their columns in the query.
    how_to_join is a dictionary that allows setting joins (left, right, inner, full)
    other than the defaults imported from the JSON.
    """
    core = 'select\n\n{columns}\n\nfrom {joins}\n\nwhere {where}'

    def __init__(self, filename):
        super().__init__(filename)
        self.active_tables = []
        self.active_columns = {}
        self.active_presets = []
        self.implicit_tables = []
        self.how_to_join = {}
        self.where = []
        self.tables_added_by_preset = []

    def add_tables(self, tablename, add_or_remove=True):
        """
        Toggles active setting of given tablename. GUI ensures that only valid names
        will be given.
        """
        if add_or_remove:
            if tablename not in self.active_tables:
                self.active_tables.append(tablename)
                self.active_columns[tablename] = []
        else:
            self.active_tables.remove(tablename)

    def add_columns(self, table, column, add_or_remove=True):
        """
        Toggles active setting for given columnname from table. GUI ensures that
        only valid names will be given.
        """
        if add_or_remove:
            if column not in self.active_columns[table]:
                self.active_columns[table].append(column)
        else:
            self.active_columns[table].remove(column)

    def add_where(self, string):
        """
        Adds any string to a list to be input as where statement. This could be
        vulnerable for SQL injection, but the scope of this project is in-house
        usage, and the generated SQL query isn't directly passed to the server.
        """
        self.where.append(string)

    def add_preset(self, preset):
        """
        Presets are predefined where-statements. They add the relevant table to
        the list of activated tables and add a where statement. For simplicity,
        when added, a preset can't be disabled.
        """
        relevant_preset = self.presets[preset]
        table_to_add = relevant_preset['table'][0]
        if table_to_add not in self.active_tables:
            self.add_tables(table_to_add, True)
            self.tables_added_by_preset.append(table_to_add)
        self.add_where(relevant_preset['where'][0])
        self.active_presets.append(preset)


    def find_joins(self):
        """
        Calls the join_paths function from Universe class. Figures out which joins
        are needed and which tables need to be implicitly added. Returns a list
        of tuples with tablenames to be joined.
        """
        tags = [self.tables[table]['tag'][0]
                for table in self.active_tables]
        join_paths = self.join_paths(tags)
        join_sets = [(table1, table2)
                     for join_edge in join_paths
                     for table1, table2 in zip(join_edge[:-1], join_edge[1:])]
        for sublist in join_paths:
            for item in sublist:
                if item not in self.active_tables:
                    self.add_tables(item)
                    self.implicit_tables.append(item)
        return join_sets

    def generate_join_statement(self, table_tuple):
        """
        Creates the join statement for a given tuple of tablenames. The second
        entry in the tuple is always the table that is joined. Since the string
        is stored in a dictionary with one specific combination of the two table
        names, the try statement checks which way around it needs to be. how contains
        the default way to join. Unless otherwise specified, this is used to generate
        the join string.
        """
        added_table = table_tuple[1]
        try:
            on_string, how = self.tables[table_tuple[0]]['Joins'][table_tuple[1]]
        except TypeError:
            table_tuple = (table_tuple[1], table_tuple[0])
            on_string, how = self.tables[table_tuple[0]]['Joins'][table_tuple[1]]


        if table_tuple not in self.how_to_join:
            self.how_to_join[table_tuple] = how

        join_string = (self.how_to_join[table_tuple]
                       + ' join '
                       + self.tables[added_table]['DBHandle'][0]
                       + ' '
                       +  self.tables[added_table]['tag'][0]
                       + '\n')
        return join_string + on_string

    def generate_select_statement(self, table):
        """
        Creates the column specification. If no columns of an active table are
        specified, it assumes all the columns are wanted.
        """
        if not self.active_columns[table]:
            self.active_columns[table] = ['*']
        return ',\n'.join([(self.tables[table]['tag'][0]
                            + '.'
                            + i)
                           for i in self.active_columns[table]])


    def compile_query(self):
        """
        Handles compilation of the query. If there are more than one activated
        table, joins need to be handled. First the required joins are found, then
        the strings that handle this are generated. The column statement is created.
        If there is no where statement specified, '1=1' is added. The relevent
        statements are added into the core query and returned.
        """
        if len(self.active_tables) == 1:
            base_table = self.active_tables[0]
            join_statement = []
        else:
            joins = self.find_joins()
            base_table = joins[0][0]
            join_statement = [self.generate_join_statement(i) for i in joins]
        join_statement = ([self.tables[base_table]['DBHandle'][0]
                           + ' '
                           + self.tables[base_table]['tag'][0]]
                          + join_statement)
        completed_join_statement = '\n\n'.join(join_statement)


        column_statement = [self.generate_select_statement(table)
                            for table in self.active_tables
                            if table not in self.implicit_tables]



        completed_column_statement = ',\n'.join(column_statement)


        if self.where:
            where_statement = '\nand '.join(self.where)
        else:
            where_statement = '1 = 1'

        query = Query.core.replace('{columns}', completed_column_statement)
        query = query.replace('{joins}', completed_join_statement)
        query = query.replace('{where}', where_statement)

        return query

def main():
    """
    Creates an example query
    """
    file = 'example.JSON'
    query = Query(file)
    query.addTables('table1')
    query.addTables('table2')
    query.addTables('table3')
    print(query.compileQuery())

if __name__ == "__main__":
    main()
