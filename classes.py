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
            self.json = loads(str(file.read()))
        self.presets = self.json['presets']
        self.json = self.json['graph']
        self.tables = self.json.keys()
        self.connections = self.getEdges()

    def getEdges(self):
        """
        Creates a dictionary with for each node a list of nodes that join on
        that node.
        """
        edges = {}
        for i in self.tables:
            edges[i] = []
            try:
                edges[i] += [j for j in self.json[i]['Joins'].keys()]
            except AttributeError:
                pass
        for i in edges.keys():
            for j in edges[i]:
                if not i in edges[j]:
                  edges[j].append(i)
        return edges

    def shortestPath(self, start, end, path = []):
        """
        Calculates the shortest path in a graph, using the dictionary created
        in getEgdes. Adapted from https://www.python.org/doc/essays/graphs/.
        """
        path = path + [start]
        if start == end:
            return path
        if not start in self.connections.keys():
            return None
        shortest = None
        for node in self.connections[start]:
            if node not in path:
                newpath = self.shortestPath(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def joinPaths(self, nodes):
        """
        Extension of shortestPath to work with multiple nodes to be connected.
        The nodes are sorted based on the priority, which is taken from the JSON.
        shortestPath is called on the first two nodes, then iteratively on each
        additional node and one of the existing nodes returned by shortestPath,
        selecting the one that takes the fewest steps.
        """
        sorted_nodes = sorted([[self.json[i]['Priority'][0], i] for i in nodes])
        paths = []

        paths.append(self.shortestPath(sorted_nodes[0][1], sorted_nodes[1][1]))
        for i in range(len(sorted_nodes) - 2):
            shortest = None
            flat_paths = [item for sublist in paths for item in sublist]
            old_path = len(flat_paths)
            for j in flat_paths:
                newpath = self.shortestPath(j, sorted_nodes[i+2][1], flat_paths)
                if newpath:
                    if not shortest or len(newpath[old_path:]) < len(shortest):
                        shortest = newpath[old_path:]
            paths.append(shortest)
        return paths    


class Query:
    """
    Query contains the functions that allow us to build an SQL query based on
    a universe object. It maintains lists with the names of activated tables
    and, if applicable, which of their columns in a dictionary. Implicit tables
    are tables that are called, only to bridge joins from one table to another.
    Since they are not explicitly called, we don't want their columns in the query.
    how_to_join is a dictionary that allows setting joins (left, right, inner, full)
    other than the defaults imported from the JSON.
    """

    def __init__(self, universum):
        self.core = 'select\n\n{columns}\n\nfrom {joins}\n\n where {where}'

        self.graph = universum
        self.active_tables = []
        self.active_columns = {}
        self.implicit_tables = []
        self.join_strings = {}
        for i in self.graph.tables:
            self.join_strings[i] = self.graph.json[i]['Joins']
        self.how_to_join = {}

    def addTables(self, tablename):
        """
        Sets given tablename to active. GUI ensures that only valid names
        will be given.
        """
        if not tablename in self.active_tables:
            self.active_tables.append(tablename)
            self.active_columns[tablename] = []

    def addColumns(self, table, column):
        """
        Sets given columnname from table to active. GUI ensures that only valid names
        will be given.
        """
        if not column in self.active_columns[table]:
            self.active_columns[table].append(column)

    def addWhere(self, string):
        """
        Adds any string to a list to be input as where statement. This could be
        vulnerable for SQL injection, but the scope of this project is in-house
        usage, and the generated SQL query isn't directly passed to the server.
        If no where statements have been given yet, the list is created.
        """
        try:
            self.where.append(string)
        except AttributeError:
            self.where = [string]

    def findJoins(self):
        """
        Calls the joinPaths function from Universe class. Figures out which joins
        are needed and which tables need to be implicitly added. Returns a list
        of tuples with tablenames to be joined.
        """
        tags = [self.graph.json[i]['tag'][0] for i in self.active_tables]
        join_paths = self.graph.joinPaths(tags)
        join_sets = []
        for i in join_paths:
            for j, k in zip(i[:-1], i[1:]):
                join_sets.append((j, k))
        for sublist in join_paths:
            for item in sublist:
                if not item in self.active_tables:
                    self.addTables(item)
                    self.implicit_tables.append(item)
        return join_sets

    def joinStatement(self, table_tuple):
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
            on_string, how = self.graph.json[table_tuple[0]]['Joins'][table_tuple[1]]
        except (KeyError, TypeError) as error:
            table_tuple = (table_tuple[1], table_tuple[0])
            on_string, how = self.graph.json[table_tuple[0]]['Joins'][table_tuple[1]]


        if not table_tuple in self.how_to_join.keys():
            self.how_to_join[table_tuple] = how

        join_string = self.how_to_join[table_tuple] + ' join ' + self.graph.json[added_table]['DBHandle'][0] + ' ' +  self.graph.json[added_table]['tag'][0] + '\n'
        return join_string + on_string     

    def selectStatement(self, table):
        """
        Creates the column specification. If no columns of an active table are 
        specified, it assumes all the columns are wanted.
        """
        if not self.active_columns[table]:
            self.active_columns[table] = ['*']
        return ',\n'.join([self.graph.json[table]['tag'][0] + '.' + i for i in self.active_columns[table]])


    def compileQuery(self):
        """
        Handles compilation of the query. If there are more than one activated
        table, joins need to be handled. First the required joins are found, then
        the strings that handle this are generated. The column statement is created.
        If there is no where statement specified, '1=1' is added. The relevent
        statements are added into the core query and returned.
        """
        if len(self.active_tables) == 1:
            base_table = self.active_tables[0]
            self.join_statement = []
        else:
            joins = self.findJoins()
            base_table = joins[0][0]
            self.join_statement = [self.joinStatement(i) for i in joins]
        self.join_statement = [self.graph.json[base_table]['DBHandle'][0] + ' ' + self.graph.json[base_table]['tag'][0]] + self.join_statement
        self.join_statement = '\n\n'.join(self.join_statement)


        self.column_statement = []
        for i in self.active_tables:
            if i not in self.implicit_tables:
                self.column_statement.append(self.selectStatement(i))


        self.column_statement = ',\n'.join(self.column_statement)


        try:
            self.where_statement = '\nand '.join(self.where)
        except AttributeError:
            self.where_statement = '1 = 1'

        return self.core.replace('{columns}', self.column_statement).replace('{joins}', self.join_statement).replace('{where}', self.where_statement)



if __name__ == "__main__":
    graph = Universe('example.JSON')
    query = Query(graph)
    query.addTables('table1')
    query.addTables('table2')
    query.addTables('table3')
    print(query.compileQuery())
