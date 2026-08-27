const createDataLineageDocs = require('./functions/data_lineage_docs')
const { createTablesDocs, clear_collection } = require('./functions/tables_docs')
const tablesDocs = require('./mongo_models/tablesDocs')
    
// ----------------------------------------------------------------------
// Parameters
// ----------------------------------------------------------------------
// DNS name of the SQL server for which to extract metadata and name of the database used to connect to that server (it can be any database)
mongo_dns = process.env.MONGO_DNS // 'mongo-db'
mongo_database = process.env.MONGO_DATABASE // 'my_doc'
sql_server_dns = process.env.SQL_SERVER_DNS // 'ms-sql'
sql_database = process.env.SQL_DATABASE // 'master'
sql_user = process.env.SQL_USER
sql_password = process.env.SQL_PASSWORD

main()

async function main(){
    // ----------------------------------------------------------------------
    // Prepare data lineage data (populate the dataLineageDocs MongoDB collection)
    // ----------------------------------------------------------------------
    await createDataLineageDocs(mongo_dns, mongo_database, sql_server_dns, sql_database, sql_user, sql_password)


    // ----------------------------------------------------------------------
    // Prepare documents about tables (populate the tablesDocs MongoDB collection)
    // ----------------------------------------------------------------------
    await clear_collection(mongo_dns, mongo_database, tablesDocs)
    await createTablesDocs(mongo_dns, mongo_database, sql_server_dns, sql_database, sql_user, sql_password)

    console.log('done')
}