const sql = require('mssql');

class SQLConnector {
    // Class for connecting into the SQL Server. We use here:
    //  - ODBC Driver 17 for SQL Server

    constructor(server, database, user, password){
        this.config = {
            database: database,
            server: server,
            user: user,
            password: password,
            options: {
                encrypt: true,
                trustServerCertificate: true
            },
            connectionTimeout: 10000,
            requestTimeout: 60000
        }
    }

    async createPool(){
        // console.log('Creating a pool for the SQL server')
        this.pool = await sql.connect(this.config)
        // console.log('Finished creating a pool for the SQL server')
    }

    async read_query(query){
        if (this.pool == undefined) await this.createPool()
        const result = await this.pool.request().query(query)
        return result
    }
}

module.exports = SQLConnector