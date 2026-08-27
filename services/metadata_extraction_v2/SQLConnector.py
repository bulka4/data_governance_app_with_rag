import pandas as pd
import sqlalchemy as sa

class SQLConnector:
    def __init__(
        self
        ,server
        ,database
        ,username = None
        ,password = None
        ,driver = 'SQL Server Native Client 11.0'
    ):
        
        if username == None and password == None:
            connection_url = f'mssql://@{server}/{database}?driver={driver}'
        else:
            connection_url = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}'
        
        self.engine = sa.create_engine(connection_url, fast_executemany=True)
        
    def read_query(self, query):
        "saving result of a sql query in a dataframe"
        
        with self.engine.connect() as con:
            df = pd.read_sql(sql = sa.text(query), con = con)
        
        return df
    
    def read_sql_file(self, file_path):
        "saving a result of a sql query from a file to a dataframe"
        
        with open(file_path, 'r') as query:
            with self.engine.connect() as con:
                df = pd.read_sql(sql = sa.text(query.read()), con = con)
                
        return df
        
    def execute_sql_file(self, file_path):
        "executing sql file"
        
        with open(file_path, 'r') as file:
            con = self.engine.raw_connection()
            with con.cursor() as cursor:
                cursor.execute(file.read())
            
            con.commit()
            con.close()
            
    def execute_query(self, query):
        "executing sql query"
        con = self.engine.raw_connection()
        with con.cursor() as cursor:
            cursor.execute(query)

        con.commit()
        con.close()
    
    def to_sql(
        self
        ,dataframe
        ,sql_table_name
        ,sql_schema_name
        ,if_exists
    ):
        """
        Inserting data from a dataframe into a sql database.
        Argument sql_table_name is a name of a SQL table to which we will insert the data.
        Argument sql_schema_name is a name of a SQL schema in thich that table will be placed.
        """
        
        col_count = len(dataframe.columns)
        max_params = 1000
        chunksize =  max_params // col_count
        
        
        # if schema doesnt exist then create it
        with self.engine.connect() as con:
            if sql_schema_name not in con.dialect.get_schema_names(con):
                con.execute(sqlalchemy.schema.CreateSchema(sql_schema_name))
        
            dataframe.to_sql(
                name = sql_table_name
                ,schema = sql_schema_name
                ,con = con
                ,index = False
                ,if_exists = if_exists
                ,chunksize = chunksize
                ,method = "multi"
            )