const mongoose = require('mongoose')

// Collection to store data about application users, used for authentication
const userSchema = new mongoose.Schema({
    // User email and password
    email: String,
    password: String,
    // User role: newUser, viewer or designer
    role: {
        type: String,
        default: 'newUser'
    }
}, 
{collection: 'usersDocs'})

module.exports = mongoose.model('usersDocs', userSchema)