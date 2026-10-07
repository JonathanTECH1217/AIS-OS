console.log('hello', 1 + 1, { a: [1, 2] });
var f = new Float32Array(3); f[1] = 2.5;
console.log('typed', Array.from(f));
async function g() { return 'async ok'; }
g().then(function (v) { console.log(v); document.getElementById('out').textContent += '\n' + 'LOG ' + v; });
