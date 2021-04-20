const bodyparser = require("body-parser");
const cors = require("cors");
const errorhandler = require("errorhandler");
const morgan = require("morgan");
const express = require("express");

const path = require('path');

const app  = express();
const PORT = process.env.PORT || 4000;

app.use(bodyparser.json());
app.use(errorhandler());
app.use(cors());
app.use(morgan('dev')); // Developer mode

// Hooking up the router to serve requests to the database:
const apiRouter = require("./api/api.js");
app.use('/api', apiRouter);

// Serving the user with the login window on boot:
app.get('/', function(req,res) {
    res.sendFile(path.join(__dirname + '/templates/login.html'));
});
  
app.use(express.static('./'));

app.listen(PORT, ()=>{
    console.log('Listening on port: ' + PORT);
    console.log('http://localhost:' + PORT + '/');
});

module.exports = app;