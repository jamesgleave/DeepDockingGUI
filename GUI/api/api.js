// This is where we maintain the database:
const express = require('express');
const apiRouter = express.Router();

module.exports = apiRouter;
// NOTE: The database is not protected against SQL injections.
//      But the purpose behind the app is to demonstrate my 
//      JavaScript knowledge.

// example of setup: See "C:\Users\jyaac\Documents\codecademy_projects\Back-End App with JS\capstone-x-press-publishing\api\api.js"
// const sqlite3 = require('sqlite3');

// const seriesRouter = express.Router();
// const db = new sqlite3.Database(process.env.TEST_DATABASE ||  './database.sqlite');

// module.exports = seriesRouter;

// // checks to see if any fields are missing 
// const validateFields = (req, res, next) => {
//     if (!(req.body.series.name && req.body.series.description)){
//         res.sendStatus(400);
//     } else {
//         next();
//     }
// };

// seriesRouter.param('seriesId', (req, res, next, id) => {
//     db.get(`
//         SELECT * FROM Series
//         WHERE Series.id = ${id};`,
//         (err, row) => {
//             if (err){
//                 next(err);
//             } else if (row){
//                 req.series = row;
//                 next();
//             } else {
//                 res.sendStatus(404);
//             }
//         }
//     );
// });

// seriesRouter.get('/', (req, res, next) => {
//     db.all(`SELECT * FROM Series`, (err, rows) => {
//         if (err){
//             next(err);
//         } else {
//             res.status(200).json({series: rows});
//         }
//     });
// });

// seriesRouter.get('/:seriesId', (req, res, next)=>{
//     res.status(200).json({series: req.series});
// });

// seriesRouter.post('/', validateFields, (req, res, next) => {
//     db.run(`
//         INSERT INTO Series (name, description) 
//         VALUES ('${req.body.series.name}', '${req.body.series.description}');`, 
//         function(err) {
//             if (err){
//                 next(err);
//             } else {
//                 db.get(`
//                     SELECT * FROM Series 
//                     WHERE Series.id = ${this.lastID}`,
//                     function (err, row) {
//                         res.status(201).json({series : row});
//                     } 
//                 );
//             }
//         }
//     );
// });

// seriesRouter.put('/:seriesId', validateFields, (req, res, next) => {
//     db.run(`
//         UPDATE Series 
//         SET name = '${req.body.series.name}', 
//             description = '${req.body.series.description}'
//         WHERE Series.id = ${req.params.seriesId};`, 
//         function(err){
//             if (err) {
//                 next(err);
//             } else {
//                 db.get(`SELECT * FROM Series WHERE Series.id = ${req.params.seriesId};`, 
//                     function(err, row){
//                         res.status(200).json({series: row});
//                     }
//                 )
//             }

//         }
//     );
// });

// const issuesRouter = require('./issues.js');
// seriesRouter.use('/:seriesId/issues', issuesRouter);

// seriesRouter.delete('/:seriesId', (req, res, next) =>{
//     // Check to insure there are no related issues in the database
//     db.get(`
//         SELECT * FROM Issue
//         WHERE Issue.series_id = ${req.params.seriesId};`, 
//         (err, row) =>{
//             if (err){
//                 next(err);
//             } else if (row) {
//                 res.sendStatus(400);
//             } else {
//                 db.run(`
//                     DELETE FROM Series 
//                     WHERE Series.id = ${req.params.seriesId};`, 
//                     function(err) {
//                         res.sendStatus(204);
//                     }  
//                 );
//             }
//         }
//     );
// });

// // IMPORTANT if you want to connect that router to the database:
// apiRouter.use('/series', seriesRouter); 