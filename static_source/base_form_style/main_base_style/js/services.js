(function () {
  var grid = document.getElementById('servicesGrid');
  if (!grid) return;

  var ajaxUrl = grid.dataset.ajaxUrl;
  var detailsUrlTemplate = grid.dataset.detailsUrlTemplate; // e.g. ".../services/0/"

  function buildDetailsUrl(id) {
    return detailsUrlTemplate.replace('0', id);
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
  }

  function truncate(str, max) {
    if (!str) return '';
    return str.length > max ? str.slice(0, max).trim() + '…' : str;
  }

  function renderCards(items) {
    if (!items.length) {
      grid.innerHTML = '<div class="svcx-empty">No services found.</div>';
      return;
    }

    var html = items.map(function (item) {
      var img = item.image
        ? '<img src="' + item.image + '" alt="' + escapeHtml(item.title) + '">'
        : '';

      var bgStyle = item.image
        ? ' style="background-image:url(\'' + item.image + '\');"'
        : '';

      return (
        '<div class="svcx-card">' +
          '<div class="svcx-card-img"' + bgStyle + '>' + img + '</div>' +
          '<div class="svcx-card-body">' +
            '<h2>' + escapeHtml(item.title) + '</h2>' +
            '<p>' + escapeHtml(truncate(item.description, 140)) + '</p>' +
            '<div class="svcx-rule"></div>' +
            '<button type="button" class="svcx-details-btn" data-id="' + item.id + '">Details</button>' +
            '<div class="svcx-rule"></div>' +
          '</div>' +
        '</div>'
      );
    }).join('');

    grid.innerHTML = html;

    grid.querySelectorAll('.svcx-details-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        window.location.href = buildDetailsUrl(btn.dataset.id);
      });
    });
  }

  function loadServices() {
    grid.innerHTML = '<div class="svcx-loading">Loading…</div>';

    fetch(ajaxUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(function (data) {
        renderCards(data.results || []);
      })
      .catch(function () {
        grid.innerHTML = '<div class="svcx-empty">Could not load services. Please try again.</div>';
      });
  }

  loadServices();
})();