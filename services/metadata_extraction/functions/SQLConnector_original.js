const sql = require('mssql/msnodesqlv8')

class SQLConnector {
    // Class for connecting into the SQL Server. We use here:
    //  - ODBC Driver 17 for SQL Server

    constructor(server, database, user, password){
        this.config = {
            database: database,
            server: server,
            driver: 'msnodesqlv8',
            user: user,
            password: password,
            options: {
                driver: 'ODBC Driver 18 for SQL Server',
                trustServerCertificate: true
            },
            requestTimeout: 60000 // max time for how long we will wait for a server's response (in miliseconds)
        }
    }

    async createPool(){
        console.log('Creating a pool for the SQL server')
        this.pool = await sql.connect(this.config)
        console.log('Finished creating a pool for the SQL server')
    }

    async read_query(query){
        if (this.pool == undefined) await this.createPool()
        const result = await this.pool.request().query(query)
        return result
    }
}

module.exports = SQLConnector