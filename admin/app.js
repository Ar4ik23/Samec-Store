// ── Supabase config ─────────────────────────────────────────────────────────
// These are replaced at deploy time via Vercel env vars (public, safe to expose)
const SUPABASE_URL = window.SUPABASE_URL || 'REPLACE_SUPABASE_URL';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || 'REPLACE_SUPABASE_ANON_KEY';

const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ── State ────────────────────────────────────────────────────────────────────
let allProducts = [];
let deleteTargetId = null;

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupNav();
  loadProducts();
});

function setupNav() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      item.classList.add('active');
      document.getElementById('page-' + item.dataset.page).classList.add('active');
    });
  });
}

// ── Products ─────────────────────────────────────────────────────────────────
async function loadProducts() {
  const grid = document.getElementById('products-grid');
  grid.innerHTML = '<div class="loading">⏳ Загрузка...</div>';
  try {
    const { data, error } = await sb.from('products').select('*').order('created_at', { ascending: false });
    if (error) throw error;
    allProducts = data || [];
    renderProducts(allProducts);
  } catch (err) {
    grid.innerHTML = `<div class="empty">❌ Ошибка загрузки: ${err.message}</div>`;
  }
}

function renderProducts(products) {
  const grid = document.getElementById('products-grid');
  const count = document.getElementById('products-count');
  const active = products.filter(p => p.is_active).length;
  count.textContent = `${products.length} товаров · ${active} активных`;

  if (!products.length) {
    grid.innerHTML = '<div class="empty">📦 Нет товаров. Добавь первый!</div>';
    return;
  }

  grid.innerHTML = products.map(p => {
    const discount = p.price_official && p.price_ours
      ? Math.round((1 - p.price_ours / p.price_official) * 100)
      : null;
    const imgHtml = p.image_url
      ? `<img src="${p.image_url}" alt="${p.name}" />`
      : `<div class="card-image-placeholder">${p.emoji || '📦'}</div>`;

    return `
    <div class="product-card ${p.is_active ? '' : 'inactive'}" id="card-${p.id}">
      <div class="card-image">${imgHtml}</div>
      <div class="card-body">
        <div class="card-header">
          <div class="card-name">${p.emoji || ''} ${p.name}</div>
          <span class="card-badge ${p.is_active ? 'badge-active' : 'badge-inactive'}">
            ${p.is_active ? '● Активен' : '○ Скрыт'}
          </span>
        </div>
        <div class="card-desc">${p.description || 'Без описания'}</div>
        <div class="card-price">
          <span class="price-ours">${p.price_ours}₽</span>
          ${p.price_official ? `<span class="price-official">${p.price_official}₽</span>` : ''}
          ${discount ? `<span class="price-discount">−${discount}%</span>` : ''}
        </div>
        <div class="card-actions">
          <button class="btn-edit" onclick="editProduct(${p.id})">✏️ Изменить</button>
          <button class="btn-toggle" onclick="toggleProduct(${p.id}, ${p.is_active})">
            ${p.is_active ? '🙈 Скрыть' : '👁 Показать'}
          </button>
          <button class="btn-delete" onclick="askDelete(${p.id}, '${p.name.replace(/'/g, "\\'")}')">🗑</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

function filterProducts() {
  const query = document.getElementById('search').value.toLowerCase();
  const filter = document.getElementById('filter-active').value;
  const filtered = allProducts.filter(p => {
    const matchText = p.name.toLowerCase().includes(query);
    const matchFilter = filter === 'all' || (filter === 'active' && p.is_active) || (filter === 'inactive' && !p.is_active);
    return matchText && matchFilter;
  });
  renderProducts(filtered);
}

// ── Modal ────────────────────────────────────────────────────────────────────
function openModal(product = null) {
  document.getElementById('product-form').reset();
  document.getElementById('product-id').value = '';
  document.getElementById('product-image-url').value = '';
  document.getElementById('image-preview').style.display = 'none';
  document.getElementById('image-placeholder').style.display = 'flex';
  document.getElementById('product-active').checked = true;

  if (product) {
    document.getElementById('modal-title').textContent = 'Редактировать товар';
    document.getElementById('product-id').value = product.id;
    document.getElementById('product-name').value = product.name || '';
    document.getElementById('product-emoji').value = product.emoji || '';
    document.getElementById('product-price').value = product.price_ours || '';
    document.getElementById('product-price-official').value = product.price_official || '';
    document.getElementById('product-description').value = product.description || '';
    document.getElementById('product-tag').value = product.tag || 'technology';
    document.getElementById('product-active').checked = product.is_active;
    document.getElementById('product-image-url').value = product.image_url || '';
    if (product.image_url) {
      document.getElementById('image-preview').src = product.image_url;
      document.getElementById('image-preview').style.display = 'block';
      document.getElementById('image-placeholder').style.display = 'none';
    }
  } else {
    document.getElementById('modal-title').textContent = 'Добавить товар';
  }

  document.getElementById('modal-overlay').classList.add('open');
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modal-overlay')) return;
  document.getElementById('modal-overlay').classList.remove('open');
}

function editProduct(id) {
  const p = allProducts.find(p => p.id === id);
  if (p) openModal(p);
}

// ── Image preview & upload ────────────────────────────────────────────────────
function previewImage(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('image-preview').src = e.target.result;
    document.getElementById('image-preview').style.display = 'block';
    document.getElementById('image-placeholder').style.display = 'none';
  };
  reader.readAsDataURL(file);
}

async function uploadImage(file, productName) {
  const ext = file.name.split('.').pop();
  const filename = `${productName.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.${ext}`;
  const { data, error } = await sb.storage.from('product-images').upload(filename, file, { upsert: true });
  if (error) throw error;
  const { data: urlData } = sb.storage.from('product-images').getPublicUrl(filename);
  return urlData.publicUrl;
}

// ── Save product ──────────────────────────────────────────────────────────────
async function saveProduct(e) {
  e.preventDefault();
  const btn = document.getElementById('save-btn');
  btn.textContent = '⏳ Сохранение...';
  btn.disabled = true;

  try {
    const id = document.getElementById('product-id').value;
    const fileInput = document.getElementById('image-file');
    let imageUrl = document.getElementById('product-image-url').value;

    if (fileInput.files[0]) {
      const name = document.getElementById('product-name').value;
      imageUrl = await uploadImage(fileInput.files[0], name);
    }

    const payload = {
      name: document.getElementById('product-name').value.trim(),
      emoji: document.getElementById('product-emoji').value.trim(),
      price_ours: parseInt(document.getElementById('product-price').value),
      price_official: parseInt(document.getElementById('product-price-official').value) || null,
      description: document.getElementById('product-description').value.trim(),
      tag: document.getElementById('product-tag').value,
      is_active: document.getElementById('product-active').checked,
      image_url: imageUrl || null,
    };

    let error;
    if (id) {
      ({ error } = await sb.from('products').update(payload).eq('id', id));
    } else {
      ({ error } = await sb.from('products').insert(payload));
    }

    if (error) throw error;
    document.getElementById('modal-overlay').classList.remove('open');
    showToast(id ? '✅ Товар обновлён' : '✅ Товар добавлен', 'success');
    await loadProducts();
  } catch (err) {
    showToast('❌ Ошибка: ' + err.message, 'error');
  } finally {
    btn.textContent = '💾 Сохранить';
    btn.disabled = false;
  }
}

// ── Toggle active ─────────────────────────────────────────────────────────────
async function toggleProduct(id, currentState) {
  const { error } = await sb.from('products').update({ is_active: !currentState }).eq('id', id);
  if (error) { showToast('❌ Ошибка', 'error'); return; }
  showToast(currentState ? '🙈 Товар скрыт' : '👁 Товар активирован', 'success');
  await loadProducts();
}

// ── Delete ────────────────────────────────────────────────────────────────────
function askDelete(id, name) {
  deleteTargetId = id;
  document.getElementById('delete-name').textContent = `"${name}" будет удалён навсегда.`;
  document.getElementById('delete-overlay').classList.add('open');
}

function closeDelete() {
  deleteTargetId = null;
  document.getElementById('delete-overlay').classList.remove('open');
}

async function confirmDelete() {
  if (!deleteTargetId) return;
  const { error } = await sb.from('products').delete().eq('id', deleteTargetId);
  closeDelete();
  if (error) { showToast('❌ Ошибка удаления', 'error'); return; }
  showToast('🗑 Товар удалён', 'success');
  await loadProducts();
}

// ── Manual post trigger ───────────────────────────────────────────────────────
async function triggerPost() {
  showToast('▶ Публикация запущена через GitHub Actions...', 'success');
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast show ${type}`;
  setTimeout(() => { t.className = 'toast'; }, 3000);
}
