// The main script which starts the application's server.

// if (process.env.NODE_ENV !== 'production'){
//     require('dotenv').config()
// }

const express = require('express')
const app = express()
const mongoose = require('mongoose')
const bcrypt = require('bcrypt')

const redis_client = require('./modules/redis_client')

const usersDocs = require('./mongo_models/usersDocs')

async function start(){
    // Wait until we connect to databases: Redis and MongoDB. 
    // This must be here at the beginning of this function because otherwise we can get an error about not being able to connect 
    // to a database.
    // We can get this error not just in this script but in every other script which runs together in the same process, for example:
    //  - when importing the tables_docs_route module which uses Redis
    //  - when running `usersDocs.find()` in the `login_route.js` module
    await redis_client.connect()
    await mongoose.connect(`mongodb://${process.env.MONGO_DNS}/${process.env.MONGO_DATABASE}`)

    const methodOverride = require('method-override')
    const flash = require('express-flash')
    const session = require('express-session')
    const initializePassport = require('./modules/passport-config')
    const passport = require('passport')

    const homePageRouter = require('./routes/home_page_route')
    const tablesDocsRouter = require('./routes/tables_docs_route')
    const loginRouter = require('./routes/login_route')
    const dataLineageRouter = require('./routes/data_lineage_route')

    initializePassport(
        passport,
        async email => await usersDocs.findOne({email: email}),
        async id => await usersDocs.findById(id)
    )


    app.set('view engine', 'ejs')
    // allow for linking .css files from 'public' folder to .ejs files
    app.use(express.static('public'));
    // express.urldencoded() and express.json() allows us to get access to req.body while sending a post request
    app.use(express.urlencoded({extended: true, limit: '200mb'}))
    app.use(express.json({limit: '200mb'}))

    // this method override will allow us to use PUT method in 'form' html element
    app.use(methodOverride('_method'))
    // thanks to the flash we can access 'messages' variable inside ejs files
    app.use(flash())
    app.use(session({
        secret: process.env.SESSION_SECRET,
        resave: false,
        saveUninitialized: false,
        cookie: {_expires: 30 * 60 * 1000} // session expires after 30 minutes and user needs to log in again
    }))
    app.use(passport.initialize())
    app.use(passport.session())
    // we will be using docsRouter under /docs url
    app.use('/home', homePageRouter)
    app.use('/tables_docs', tablesDocsRouter)
    app.use('/data_lineage', dataLineageRouter)
    app.use('/', loginRouter)

    app.get('/', checkNotAuthenticated, (req, res) => {
        res.redirect('/login')
    })

    // Create one admin user with the designer role (so it can access and modify all the data)
    await createAdminUser()

    // we want to use port 80 because then we don't need to write a port number in the url,
    // so instead of writting url 'db_doc.com:port_number' we just need to write 'db_doc.com'
    // app.listen(80)
    app.listen(8080, '0.0.0.0')

    console.log('app started listening to requests')
}

// function for checking if user has logged in and is authenticated
function checkNotAuthenticated(req, res, next) {
    if (req.isAuthenticated()) {
        return res.redirect('/tables_docs/0/table')
    }

    next()
}

async function createAdminUser(){
    // Create one admin user with the designer role (so it can access and modify all the data) if it doesn't exist yet

    const existingUser = await usersDocs.findOne({ email: 'admin@admin.com' })

    if (existingUser) {
        return existingUser
    }

    const user = await usersDocs.create({
        email: 'admin@admin.com',
        password: await bcrypt.hash('admin', 10),
        role: 'designer'
    })

    return user
}

start().catch(err => {
    console.error('Failed to start server:', err)
    process.exit(1)
})