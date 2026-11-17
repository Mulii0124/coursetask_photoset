/* ==========================================================================
   木離 QIANJINGJING — interaction layer
   Motion vocabulary:
     · page change  -> vertical curtain wipe (scaleY), never a fade
     · catalogue    -> outgoing image retracts upward, incoming unfolds from
                       the bottom edge
     · content      -> clip-path reveal (裁切进入), never a plain fade
   ========================================================================== */
(function () {
  'use strict';

  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) {
    return Array.prototype.slice.call((c || document).querySelectorAll(s));
  };

  /* ------------------------------------------------------------------
     1. Page curtain — wipe over the current page, then navigate.
     ------------------------------------------------------------------ */
  var curtain = $('.curtain');

  if (curtain) {
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { curtain.classList.add('is-open'); });
    });
    window.setTimeout(function () {
      if (curtain && curtain.parentNode) curtain.parentNode.removeChild(curtain);
    }, 1400);
  }

  document.addEventListener('click', function (e) {
    var node = e.target;
    if (!node || !node.closest) return;
    var a = node.closest('a');
    if (!a) return;

    var href = a.getAttribute('href');
    if (!href) return;
    if (href.charAt(0) === '#') return;                       /* in-page anchor */
    if (a.target === '_blank' || a.hasAttribute('download')) return;
    if (/^(https?:|mailto:|tel:|javascript:)/i.test(href)) return;

    if (!curtain) return;
    e.preventDefault();
    curtain.classList.remove('is-open');
    curtain.classList.add('is-closed');
    window.setTimeout(function () { window.location.href = href; }, 540);
  });

  /* ------------------------------------------------------------------
     2. Navigation state
     ------------------------------------------------------------------ */
  var nav = $('.nav');
  function navState() {
    if (!nav) return;
    nav.classList.toggle('is-stuck', window.pageYOffset > window.innerHeight - 80);
  }
  navState();

  var toggle = $('.nav__toggle');
  var links = $('.nav__links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    links.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a')) {
        links.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ------------------------------------------------------------------
     3. Clip-path reveals — content enters by being cut open.
        A reveal only fires once its image has actually decoded.

        NOTE: the clip must NOT live on the element we observe. A clipped
        target has an empty intersection rect, so IntersectionObserver would
        never report it as visible and the reveal would never arm. We
        therefore test the layout box (getBoundingClientRect is unaffected
        by clip-path) against the viewport on every scroll frame.
     ------------------------------------------------------------------ */
  function arm(el) {
    var imgs = $$('img', el);
    if (!imgs.length) return Promise.resolve();
    return Promise.all(imgs.map(function (im) {
      if (im.complete) return Promise.resolve();
      return new Promise(function (resolve) {
        im.addEventListener('load', resolve, { once: true });
        im.addEventListener('error', resolve, { once: true });
      });
    }));
  }

  var reveals = $$('[data-reveal]');

  function show(el) {
    arm(el).then(function () { el.classList.add('is-in'); });
  }

  function pumpReveals() {
    if (!reveals.length) return;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var next = [];
    for (var i = 0; i < reveals.length; i++) {
      var el = reveals[i];
      if (el.classList.contains('is-in')) continue;
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.92 && r.bottom > 0 && r.height > 0) {
        show(el);
      } else {
        next.push(el);
      }
    }
    reveals = next;
  }

  pumpReveals();

  /* ------------------------------------------------------------------
     4. Series catalogue — one image at a time.
        Outgoing frame retracts upward (origin top),
        incoming frame unfolds from the bottom edge (origin bottom).
     ------------------------------------------------------------------ */
  var items = $$('[data-series]');
  var slot = $('[data-slot]');

  if (slot && items.length) {
    var frameA = $('img[data-role="a"]', slot);
    var frameB = $('img[data-role="b"]', slot);
    var frames = { a: frameA, b: frameB };
    var cap = $('[data-cap]');
    var state = { slot: 'a', src: frameA ? frameA.getAttribute('src') : '' };
    var pending = null;

    function highlight(item) {
      items.forEach(function (el) {
        el.classList.toggle('is-active', el === item);
        el.setAttribute('aria-selected', el === item ? 'true' : 'false');
      });
    }

    function paintCap(item) {
      if (!cap) return;
      var cn = item.getAttribute('data-cap-cn') || '';
      var en = item.getAttribute('data-cap-en') || '';
      var no = item.getAttribute('data-cap-no') || '';
      cap.innerHTML = '';
      var b = document.createElement('b');
      b.textContent = cn;
      var s = document.createElement('span');
      s.textContent = no + ' / ' + en;
      cap.appendChild(b);
      cap.appendChild(s);
    }

    function setSeries(item) {
      if (!item) return;
      var src = item.getAttribute('data-src');
      if (!src) return;
      highlight(item);
      paintCap(item);
      if (src === state.src) return;

      var next = state.slot === 'a' ? 'b' : 'a';
      var cur = frames[state.slot];
      var inc = frames[next];
      if (!cur || !inc) return;

      if (pending) { window.clearTimeout(pending); pending = null; }

      if (inc.getAttribute('src') !== src) inc.setAttribute('src', src);
      inc.alt = item.getAttribute('data-alt') || '';

      var begin = function () {
        cur.classList.add('is-outgoing');
        inc.classList.add('is-incoming', 'is-active');
        void inc.offsetWidth;                       /* freeze the start state */
        requestAnimationFrame(function () {
          requestAnimationFrame(function () { inc.classList.remove('is-incoming'); });
        });
        window.setTimeout(function () {
          cur.classList.remove('is-outgoing', 'is-active');
        }, 940);
      };

      if (inc.complete && inc.naturalWidth > 0) {
        begin();
      } else {
        inc.addEventListener('load', begin, { once: true });
        inc.addEventListener('error', begin, { once: true });
      }

      state.slot = next;
      state.src = src;
    }

    var hoverTimer = null;
    items.forEach(function (item) {
      item.setAttribute('role', 'option');
      item.setAttribute('aria-selected', item.classList.contains('is-active') ? 'true' : 'false');
      item.addEventListener('mouseenter', function () {
        window.clearTimeout(hoverTimer);
        hoverTimer = window.setTimeout(function () { setSeries(item); }, 140);
      });
      item.addEventListener('focus', function () { setSeries(item); });
      item.addEventListener('click', function () { setSeries(item); });
    });

    if (items[0]) {
      highlight(items[0]);
      paintCap(items[0]);
    }
  }

  /* ------------------------------------------------------------------
     5. Contact helpers — copy to clipboard, and a real mail composer.
     ------------------------------------------------------------------ */
  $$('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy');
      var done = function () {
        btn.classList.add('is-done');
        window.setTimeout(function () { btn.classList.remove('is-done'); }, 2200);
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
        try { document.execCommand('copy'); done(); } catch (err) { /* ignore */ }
        document.body.removeChild(ta);
      }
    });
  });

  var composer = $('[data-composer]');
  if (composer) {
    composer.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = ($('[name="name"]', composer) || {}).value || '';
      var subject = ($('[name="subject"]', composer) || {}).value || '合作咨询';
      var message = ($('[name="message"]', composer) || {}).value || '';
      var to = composer.getAttribute('data-composer');
      var body = (name ? '来自 ' + name + '：\n\n' : '') + message;
      window.location.href = 'mailto:' + to +
        '?subject=' + encodeURIComponent(subject) +
        '&body=' + encodeURIComponent(body);
      var note = $('[data-composer-note]', composer);
      if (note) note.textContent = '已为你打开邮件客户端；若未打开，请复制上面的邮箱地址。';
    });
  }

  /* ------------------------------------------------------------------
     6. Year stamp
     ------------------------------------------------------------------ */
  $$('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ------------------------------------------------------------------
     7. Scroll bookkeeping
     ------------------------------------------------------------------ */
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      navState();
      pumpReveals();
      ticking = false;
    });
  }, { passive: true });

  window.addEventListener('resize', pumpReveals, { passive: true });
  window.addEventListener('load', pumpReveals);
})();
