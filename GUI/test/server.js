const assert = require('chai').assert;  // imports the assert function from chai
const app = require('../server.js');

describe('Server', function(){
    it('App should return hello', function(){
        assert.equal(app(), 'hello');
    });

    // Example tests if you ever actually make testing suites
    // describe('sayHello()' ,function(){
    //     it('sayHello should return hello', function(){
    //         // let result = app.sayHello();
    //         assert.equal(sayHelloResult, 'hello');
    //     });
    
    //     it('sayHello should return type string', function(){
    //         // let result = app.sayHello()
    //         assert.typeOf(sayHelloResult, 'string');
    //     });
    // });

    // describe('addNumbers()', function(){
    //     it('addNumbers should be above 5', function(){
    //         // let result = app.addNumbers(1,5);
    //         assert.isAbove(addNumbersResult, 5);
    //     });
    
    //     it('addNumbers should return type number', function(){
    //         // let result = app.addNumbers(1,1);
    //         assert.typeOf(addNumbersResult, 'number');
    //     });
    // });
});