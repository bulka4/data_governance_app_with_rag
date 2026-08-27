const mongoose = require('mongoose')

const nodeSchema = new mongoose.Schema(
    {
        // Node's value, e.g. table's name, script's name
        value: {
            type: String,
            required: true
        },
        // Node's type indicating whether it represents a table or a script
        type: {
            type: String,
            required: true
        },
        // LinkedTo indicates to which node this node is linked
        linkedTo: Array,
        // Script's content, if given node represents a script
        script: String,
        // x and y coordinates used to position node on the data lineage graph
        x: Number,
        y: Number
    }
)

const dataLineageSchema = new mongoose.Schema(
    {
        // A single document of this schema contains a data lineage data for one final table, i.e. showing how a single final table
        // is being created, where a final table is a table which is not used as a source for creating any other table.
        
        // Primary key
        dataLineageId: {
            type: Number,
            required: true
        },
        // Name of the given data lineage
        dataLineageName: {
            type: String,
            required: true
        },
        // Nodes which given data lineage graph conists of with data about which source tables and scripts are used to create
        // the final table which given document of this schema represents. 
        nodes: [nodeSchema]
    },
    {collection: 'dataLineageDocs'}
)

module.exports = mongoose.model('dataLineageDoc', dataLineageSchema)