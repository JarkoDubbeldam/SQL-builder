# SQL-builder
Python GUI for building simple SQL queries.

This is a project I have been working on. This is one of my first experiences with Python and OOP as a whole. I have written a GUI that handles the inputs for these classes, but I will ask for a separate review for that, since the question would be rather bulky when including both.

The goal of this program is to create standard SQL (SQL server) queries for everyday use. The rationale behind this is that we regularly need similar queries, and would like to prevent common mistakes in them. The focus on this question is on the Python code however.

The information about the tables and their relation to each-other is provided by a JSON file, of which I have attached a mock-up version.

The code consists of three parts:

- A universe class which handles the JSON file and creates the context of the tables.

- A query class, which handles the specifications of which tables to include, which columns to take, how to join each table and optional where statements.

- A PyQT GUI that handles the inputs.
