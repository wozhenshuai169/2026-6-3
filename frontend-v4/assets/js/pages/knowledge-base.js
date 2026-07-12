/**
 * Knowledge Base — Document Management
 */
(function () {
  'use strict';
  var A = window.Aurelian, api = A.api, ui = A.ui, comp = A.components, state = A.state;

  var docs = [];
  var currentPage = 1;
  var pageSize = 10;
  var activeFilter = 'all';
  var selectedFile = null;

  function init() {
    A.auth.guard(function(){
      bindEvents();
      fetchDocs();
    });
  }

  function bindEvents() {
    document.getElementById('btn-upload').addEventListener('click', openUploadModal);
    document.getElementById('upload-cancel').addEventListener('click', closeUploadModal);
    document.getElementById('upload-confirm').addEventListener('click', handleUpload);
    document.getElementById('search-input').addEventListener('input', ui.debounce(handleSearch, 300));

    // Drop zone
    var dz = document.getElementById('drop-zone');
    var fi = document.getElementById('file-input');
    if (dz && fi) {
      dz.addEventListener('click', function(){ fi.click(); });
      dz.addEventListener('dragover', function(e){ e.preventDefault(); dz.classList.add('border-primary'); });
      dz.addEventListener('dragleave', function(){ dz.classList.remove('border-primary'); });
      dz.addEventListener('drop', function(e){ e.preventDefault(); dz.classList.remove('border-primary'); handleFileSelect(e.dataTransfer.files[0]); });
      fi.addEventListener('change', function(){ handleFileSelect(fi.files[0]); });
    }

    // Modal backdrop click
    document.getElementById('upload-modal').addEventListener('click', function(e){ if (e.target === this) closeUploadModal(); });

    // Select all
    document.getElementById('select-all').addEventListener('change', function(){ /* can implement later */ });
  }

  function fetchDocs() {
    api.get('/kb/docs').then(function(r) {
      if (r.ok && r.data) {
        docs = (Array.isArray(r.data) ? r.data : (r.data.docs || []));
        var count = document.getElementById('kb-count');
        if (count) count.textContent = docs.length;
        renderFilterBar();
        renderTable();
        renderPagination();
      }
    });
  }

  function renderFilterBar() {
    var bar = document.getElementById('filter-bar');
    if (!bar) return;
    // Collect unique categories
    var cats = ['all'];
    docs.forEach(function(d) { var c = d.category || d.type || 'other'; if (cats.indexOf(c) === -1) cats.push(c); });
    var html = '';
    cats.forEach(function(c) {
      var label = c === 'all' ? '全部' : c;
      var isActive = activeFilter === c;
      html += '<button class="filter-pill whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-medium transition-colors ' + (isActive ? 'bg-primary text-white' : 'bg-white border border-outline text-on-surface-variant hover:border-primary') + '" data-cat="' + ui.escapeHtml(c) + '">' + ui.escapeHtml(label) + '</button>';
    });
    bar.innerHTML = html;
    bar.querySelectorAll('.filter-pill').forEach(function(btn) {
      btn.addEventListener('click', function() {
        activeFilter = btn.getAttribute('data-cat');
        currentPage = 1;
        renderFilterBar();
        renderTable();
        renderPagination();
      });
    });
  }

  function getFilteredDocs() {
    if (activeFilter === 'all') return docs;
    return docs.filter(function(d) { return (d.category || d.type || 'other') === activeFilter; });
  }

  function renderTable() {
    var tbody = document.getElementById('docs-table-body');
    if (!tbody) return;
    var filtered = getFilteredDocs();
    var start = (currentPage - 1) * pageSize;
    var page = filtered.slice(start, start + pageSize);

    if (page.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="py-16 text-center text-sm text-on-surface-variant">' + (docs.length === 0 ? '暂无文档，请上传第一份文档' : '没有匹配的文档') + '</div></td></tr>';
      return;
    }

    var html = '';
    page.forEach(function(d) {
      var name = d.originalName || d.title || d.docId || '未命名';
      var size = ui.formatFileSize(d.size || 0);
      var date = ui.formatDate(d.uploadedAt || d.updatedAt);
      var status = d.status || 'published';
      var statusBadge = comp.statusBadge(status);
      html += '<tr class="table-row border-b border-outline hover:bg-surface-container-low transition-colors">' +
        '<td class="px-4 py-3"><input type="checkbox" class="row-checkbox"></td>' +
        '<td class="px-4 py-3 font-medium">' + ui.escapeHtml(name) + '</td>' +
        '<td class="px-4 py-3 text-on-surface-variant text-xs">' + size + '</td>' +
        '<td class="px-4 py-3 text-on-surface-variant text-xs">' + date + '</td>' +
        '<td class="px-4 py-3">' + statusBadge + '</td>' +
        '<td class="px-4 py-3 row-actions opacity-0 transition-opacity"><div class="flex gap-1"><button class="p-1.5 hover:bg-surface-container rounded text-on-surface-variant" title="编辑"><span class="material-symbols-outlined text-[16px]">edit</span></button><button class="p-1.5 hover:bg-error-container rounded text-error" title="删除"><span class="material-symbols-outlined text-[16px]">delete</span></button></div></td>' +
        '</tr>';
    });
    tbody.innerHTML = html;
    // Wire edit/delete buttons
    tbody.querySelectorAll('.row-actions button').forEach(function(btn){
      var icon = btn.querySelector('.material-icons, .material-symbols-outlined');
      var action = icon ? icon.textContent.trim() : '';
      btn.addEventListener('click', function(e){
        e.stopPropagation();
        var row = btn.closest('tr');
        var docName = row ? row.querySelector('td:nth-child(2)').textContent.trim() : '';
        if (action === 'edit') ui.toast('编辑文档: ' + docName + ' · 功能开发中', 'info');
        else if (action === 'delete') ui.toast('删除文档: ' + docName + ' · 功能开发中', 'warning');
      });
    });
  }

  function renderPagination() {
    var info = document.getElementById('pagination-info');
    var controls = document.getElementById('pagination-controls');
    var filtered = getFilteredDocs();
    var totalPages = Math.ceil(filtered.length / pageSize);

    if (info) info.textContent = '共 ' + filtered.length + ' 条记录';
    if (!controls) return;
    if (totalPages <= 1) { controls.innerHTML = ''; return; }

    var html = '<button class="page-prev px-3 py-1 border border-outline rounded text-sm disabled:opacity-30" ' + (currentPage === 1 ? 'disabled' : '') + '>‹</button>';
    for (var i = 1; i <= totalPages; i++) {
      html += '<button class="page-num px-3 py-1 border rounded text-sm ' + (i === currentPage ? 'bg-primary text-white border-primary' : 'border-outline') + '">' + i + '</button>';
    }
    html += '<button class="page-next px-3 py-1 border border-outline rounded text-sm disabled:opacity-30" ' + (currentPage === totalPages ? 'disabled' : '') + '>›</button>';
    controls.innerHTML = html;

    controls.querySelector('.page-prev').addEventListener('click', function(){ if (currentPage > 1) { currentPage--; renderTable(); renderPagination(); } });
    controls.querySelector('.page-next').addEventListener('click', function(){ if (currentPage < totalPages) { currentPage++; renderTable(); renderPagination(); } });
    controls.querySelectorAll('.page-num').forEach(function(btn) {
      btn.addEventListener('click', function() { currentPage = parseInt(btn.textContent); renderTable(); renderPagination(); });
    });
  }

  function openUploadModal() {
    document.getElementById('upload-modal').classList.remove('hidden');
    selectedFile = null;
    document.getElementById('file-selected').classList.add('hidden');
    document.getElementById('upload-error').classList.add('hidden');
    document.getElementById('upload-confirm').disabled = true;
  }

  function closeUploadModal() {
    document.getElementById('upload-modal').classList.add('hidden');
  }

  function handleFileSelect(file) {
    if (!file) return;
    var allowed = ['.txt','.md','.json','.pdf'];
    var ext = '.' + file.name.split('.').pop().toLowerCase();
    if (allowed.indexOf(ext) === -1) {
      document.getElementById('upload-error').textContent = '不支持的文件格式: ' + ext;
      document.getElementById('upload-error').classList.remove('hidden');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      document.getElementById('upload-error').textContent = '文件超过 20MB 限制';
      document.getElementById('upload-error').classList.remove('hidden');
      return;
    }
    selectedFile = file;
    document.getElementById('upload-error').classList.add('hidden');
    document.getElementById('file-selected').textContent = '已选择: ' + file.name + ' (' + ui.formatFileSize(file.size) + ')';
    document.getElementById('file-selected').classList.remove('hidden');
    document.getElementById('upload-confirm').disabled = false;
  }

  function handleUpload() {
    if (!selectedFile) return;
    var btn = document.getElementById('upload-confirm');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span>上传中...';

    var fd = new FormData();
    fd.append('file', selectedFile);

    api.upload('/kb/upload', fd).then(function(r) {
      if (r.ok) {
        ui.toast('上传成功！', 'success');
        closeUploadModal();
        fetchDocs();
      } else {
        var msg = (r.error && r.error.message) || '上传失败';
        document.getElementById('upload-error').textContent = msg;
        document.getElementById('upload-error').classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = '确认上传';
      }
    });
  }

  function handleSearch() {
    var query = document.getElementById('search-input').value.trim();
    if (!query) { fetchDocs(); return; }
    api.post('/kb/test-query', { query: query, limit: 20 }).then(function(r) {
      if (r.ok && r.data && r.data.results) {
        docs = r.data.results.map(function(item) {
          return {
            docId: item.chunkId || item.title,
            originalName: item.title || item.chunkId,
            category: '搜索结果',
            size: 0,
            uploadedAt: new Date().toISOString(),
            status: 'published'
          };
        });
      } else {
        docs = [];
      }
      currentPage = 1;
      renderFilterBar();
      renderTable();
      renderPagination();
    });
  }

  // Boot
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
