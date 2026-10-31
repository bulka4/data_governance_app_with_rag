// tablesDocs is the database documentation database
const tablesDocs = require('../mongo_models/tablesDocs')
const dataLineageDocs = require('../mongo_models/dataLineageDocs')

const redis_client = require('../modules/redis_client')
const kafka = require('../modules/kafka_producer')

const Fuse = require('fuse.js')
const express = require('express')

const router = express.Router()


router.get('/', checkAuthenticated, async (req, res) => {
    res.redirect('/tables_docs/0/table')
})



// get request for viewing tables descriptions
router.get('/:id/table', checkAuthenticated, async (req, res) => {
    const table_id = req.params.id

    if (req.user.role == 'newUser'){
        res.render('newUser')
    } else {
        // readOnly indicates if user can only read documentation without editing
        let readOnly
        if (req.user.role == 'viewer') readOnly = true
        else if (req.user.role == 'designer') readOnly = false

        const searchedQuery = if_undefined(req.query.searchedQuery, '')
        const alert = if_undefined(req.query.alert, '')

        // load data about tables from redis if it's saved there. If not then load it from mongodb and save in redis
        const tables_docs = await LoadData(tablesDocs, 'tables_docs')

        // find for which table documentation is actually being displayed
        const selected_doc = find_doc(tables_docs, table_id)

        // sort documents such that at the top are documents with table or column description
        // with a meaning the most similar to the searched query from search engine
        const sortedDocs = await sortDocs(searchedQuery, tables_docs)


        res.render('table', {
            docs: sortedDocs,
            // docs: tables_docs,
            selected_doc: selected_doc,
            searchedQuery: searchedQuery,
            alert: alert,
            readOnly: readOnly
        })
    }
})



// get request for viewing columns descriptions
router.get('/:id/columns', checkAuthenticated, async (req, res) => {
    const table_id = req.params.id

    if (req.user.role == 'newUser') res.render('newUser')
    else {
        // readOnly indicates if user can only read documentation without editing
        let readOnly
        if (req.user.role == 'viewer') readOnly = true
        else if (req.user.role == 'designer') readOnly = false

        // load data about tables from redis if it's saved there. If not then load it from mongodb and save in redis
        const tables_docs = await LoadData(tablesDocs, 'tables_docs')

        const searchedQuery = if_undefined(req.query.searchedQuery, '')
        const selected_doc = find_doc(tables_docs, table_id)
        const sortedDocs = await sortDocs(searchedQuery, tables_docs)

        res.render('columns', {
            docs: sortedDocs,
            // docs: tables_docs,
            selected_doc: selected_doc,
            searchedQuery: searchedQuery,
            readOnly: readOnly
        })
    }
})



// put request for saving table description
router.put('/:id/table', async (req, res) => {
    const table_id = req.params.id
    const table_doc = await tablesDocs.findOne({tableId: table_id})
    const data_lineage_docs = await dataLineageDocs.find()
    const searchedQuery = if_undefined(req.query.searchedQuery, '')

    // if there is too long word in a table description then show an alert
    for (let word of req.body.description.split(' ')){
        if (word.length > 50){
            if (searchedQuery != ''){
                res.redirect(`/tables_docs/${table_id}/table?searchedQuery=${searchedQuery}&alert=tooLongWord`)
                return
            }
            else {
                res.redirect(`/tables_docs/${table_id}/table?alert=tooLongWord`)
                return
            }
        }
    }

    table_doc.tableDescription = req.body.description
    
    await SaveData(tablesDocs, table_doc, 'tables_docs')
    
    // save table description in documents for data lineage graphs
    data_lineage_docs.forEach(doc => {
        const nodes = doc.nodes
        nodes.forEach(node => {
            if (node.type == 'table' & node.value == table_doc.tableName){
                node.tableDescription = req.body.description
            }
        })
    })
    await dataLineageDocs.create(data_lineage_docs)

    // Emit an event to Kafka about updated table description
    await kafka.connect();
    await kafka.publishTableDescriptionCreated(table_id);

    if (searchedQuery != '')
        res.redirect(`/tables_docs/${table_id}/table?searchedQuery=${searchedQuery}`)
    else
        res.redirect(`/tables_docs/${table_id}/table`)
})



// put request for saving columns description
router.put('/:id/columns', async (req, res) => {
    const table_id = req.params.id
    const doc = await tablesDocs.findOne({tableId: table_id})
    const searchedQuery = if_undefined(req.query.searchedQuery, '')

    for (let column of doc.columns){
        column.foreignKey = false
        column.primaryKey = false
    }

    let column
    let index
    for (let [key, value] of Object.entries(req.body)){
        index = key.slice(-1)
        column = doc.columns[index]

        if (key.slice(0, -2) == 'column_description'){
            column.columnDescription = value
        } else if (key.slice(0, -2) == 'foreignKey'){
            column.foreignKey = true
        } else if (key.slice(0, -2) == 'primaryKey'){
            column.primaryKey = true
        }
    }

    // await doc.save()
    await SaveData(tablesDocs, doc, 'tables_docs')

    if (searchedQuery != '')
        res.redirect(`/tables_docs/${table_id}/columns?searchedQuery=${searchedQuery}`)
    else
        res.redirect(`/tables_docs/${table_id}/columns`)
})



// post request for searching through tables and columns descriptions
// it redirects to the page with table description
router.post('/table/search', async (req, res) => {
    const searchedQuery = req.body.searchBar
    if (searchedQuery != '')
        res.redirect(`/tables_docs/${req.body.tableId}/table?searchedQuery=${searchedQuery}`)
    else
        res.redirect(`/tables_docs/${req.body.tableId}/table`)
})



// post request for searching through tables and columns descriptions
// it redirects to the page with columns description
router.post('/columns/search', async (req, res) => {
    const searchedQuery = req.body.searchBar
    if (searchedQuery != '')
        res.redirect(`/tables_docs/${req.body.tableId}/columns?searchedQuery=${searchedQuery}`)
    else
        res.redirect(`/tables_docs/${req.body.tableId}/columns`)
})



// sorting documents based on searched query typed in to search engine such that at the top there are
// the best matching documents. Matching is done based on:
// - how similar is a meaning of a table or column description to the searched query (semantic search)
// - tables and columns names (fuzzy match)
async function sortDocs(searchedQuery, docs) {
    // Sort documents from the 'docs' variable by their semantic similarity to the query given by the
    // 'searchedQuery' argument. Select the 200 most similar documents.
    
    if (searchedQuery === '') return docs

    // -------------------------
    // 1. Fuzzy matching
    // -------------------------
    const fuse = new Fuse(docs, {
        keys: ['tableName'],
        includeScore: true,
        threshold: 1,
        findAllMatches: true,
        ignoreLocation: true
    })

    const result = fuse.search(searchedQuery)

    // fuzzy_scores[tableId] = similarity score
    // Higher = better match
    const fuzzy_scores = {}

    result.forEach(x => {
        fuzzy_scores[x.item.tableId] = 1 - x.score
    })

    // Make sure every document has a fuzzy score
    docs.forEach(doc => {
        if (isNaN(fuzzy_scores[doc.tableId])) {
            fuzzy_scores[doc.tableId] = 0
        }
    })


    // -------------------------
    // 2. Semantic search
    // -------------------------

    // response.json() is a list of results where each result is an object with the following fields:
    //  - result.object_id is the tableId - ID of a table document from the database documentation database (the tablesDocs collection)
    //  - result.text_chunk - One text chunk from the table document
    //  - result.similarity_score is a similarity score for the given query 'searchedQuery' and the text chunk from the table document
    const response = await fetch(
        'http://semantic-search-rayservice-head:8000/search?' +
        new URLSearchParams({
            query: searchedQuery,
            // top_k: docs.length.toString()
            top_k: 200
        })
    )

    if (!response.ok) {
        throw new Error(
            `Semantic search failed: ${response.status} ${response.statusText}`
        )
    }

    const results = await response.json()

    // semantic_scores[tableId] is the maximum similarity score among all chunks belonging to the table document
    // given by the tableId.
    const semantic_scores = {}

    results.forEach(result => { 
        const tableId = result.object_id 
        const score = result.similarity_score 
        
        if ( 
            !Object.hasOwn(semantic_scores, tableId) 
            || score > semantic_scores[tableId] 
        ) { 
            semantic_scores[tableId] = score 
        }
    })

    // Make sure every document has a semantic score
    docs.forEach(doc => {
        if (isNaN(semantic_scores[doc.tableId])) {
            semantic_scores[doc.tableId] = 0
        }
    })


    // -------------------------
    // 3. Combine scores
    // -------------------------
    const similarity_scores = {}

    docs.forEach(doc => {
        similarity_scores[doc.tableId] =
            semantic_scores[doc.tableId] +
            fuzzy_scores[doc.tableId]
    })


    // -------------------------
    // 4. Sort documents
    // -------------------------
    const sortedDocs = [...docs].sort((a, b) => {
        return similarity_scores[b.tableId] - similarity_scores[a.tableId]
    })

    return sortedDocs
}



function find_doc(docs, tableId){
    let selected_doc
    docs.forEach(doc => {
        if (doc.tableId == tableId){
            selected_doc = doc
        }
    })

    return selected_doc
}



function if_undefined(x, y){
    if (x != undefined) return x
    else return y
}



// check if user is authenticated (if he has logged in)
function checkAuthenticated(req, res, next) {
    if (req.isAuthenticated()) {
        return next()
    }

    return res.redirect('/login')
}



async function LoadData(collection, redis_key){
    `This function loads data from the Redis for the key redis_key. If there is no data for that key in Redis
    then this function loads data from a MongoDB collection and saves it in redis for the key redis_key`

    let data = await redis_client.get(redis_key)
    if (data == null){
        data = await collection.find()

        // save data into redis
        redis_client.SETEX(redis_key, 2*60*60, JSON.stringify(data))
    } else {
        data = JSON.parse(data)
    }

    return data
}



async function SaveData(collection, document, redis_key){
    `When we are modifying a document (given by the argument 'document'), this function saves changes 
    in a MongoDB collection and also updates the whole collection data in Redis`

    await document.save()
    const data = await collection.find()
    redis_client.SETEX(redis_key, 2*60*60, JSON.stringify(data))
}



// function for reshaping 1d array into 2d array
Array.prototype.reshape = function(rows, cols) {
    var copy = this.slice(0); // Copy all elements.
    this.length = 0; // Clear out existing array.
  
    for (var r = 0; r < rows; r++) {
        var row = [];
        for (var c = 0; c < cols; c++) {
            var i = r * cols + c;
            if (i < copy.length) {
            row.push(copy[i]);
            }
        }
        this.push(row);
    }
}


module.exports = router