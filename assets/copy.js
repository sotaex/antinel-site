/* 代码块复制按钮 —— 全站唯一的 JS，原生实现，无依赖 */
document.addEventListener('click', function (e) {
  var btn = e.target.closest('.copy');
  if (!btn) return;
  var pre = btn.parentNode.querySelector('code');
  if (!pre) return;
  var text = pre.innerText;
  var done = function () {
    var old = btn.textContent;
    btn.textContent = '已复制';
    btn.classList.add('done');
    setTimeout(function () { btn.textContent = old; btn.classList.remove('done'); }, 1600);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, fallback);
  } else {
    fallback();
  }
  function fallback() {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); } catch (err) { /* 静默失败 */ }
    document.body.removeChild(ta);
  }
});
