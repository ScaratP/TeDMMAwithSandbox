document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.custom-zone-btn');
    const container = document.getElementById('sights-container');
    const loading = document.getElementById('loading');

    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            buttons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const zone = button.getAttribute('data-zone');
            fetchSights(zone);
        });
    });

    async function fetchSights(zone) {
        container.innerHTML = '';
        loading.classList.remove('d-none');

        try {
            const response = await fetch(`/api/sights/${zone}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center text-muted my-5">
                        <p class="mb-2">該區域目前無景點資料</p>
                        <small>請管理員執行 <code>python -m app.seed_data</code> 更新資料庫</small>
                    </div>`;
                return;
            }

            data.forEach((sight, index) => {
                const col = document.createElement('div');
                col.className = 'col-12 col-md-4 d-flex align-items-stretch';
                const mapUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(sight.address)}`;
                const fallbackHTML = `<div class="no-image-placeholder">無圖片</div>`;
                let imageContent = fallbackHTML;

                if (sight.photoURL && sight.photoURL.startsWith('http') && !sight.photoURL.includes('via.placeholder.com')) {
                    const safeFallback = fallbackHTML.replace(/"/g, '&quot;');
                    imageContent = `<img src="${sight.photoURL}" class="card-img-custom" alt="${sight.sightName}" onerror='this.outerHTML="${safeFallback}"'>`;
                }

                const collapseId = `collapseSight-${index}`;

                col.innerHTML = `
        <div class="custom-card w-100 p-3">
            <div class="card-body d-flex flex-column">
                <h5 class="mb-3" style="font-weight: 500;">${sight.sightName}</h5>
                <div class="mb-3">
                    <span class="custom-badge me-1">${sight.zone}</span>
                    <span class="custom-badge category">${sight.category}</span>
                </div>
                
                <button class="btn btn-outline-secondary btn-sm mb-3" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="false" aria-controls="${collapseId}">
                    詳細資訊
                </button>
                
                <div class="collapse" id="${collapseId}">
                    ${imageContent}
                    <p class="sight-desc mt-3 mb-3" style="display: block; -webkit-line-clamp: unset;">${sight.description}</p>
                </div>
                
                <div class="card-footer-custom mt-auto">
                    <span class="address-text">${sight.address}</span>
                    <a href="${mapUrl}" target="_blank" class="map-link">Google Maps</a>
                </div>
            </div>
        </div>
    `;
                container.appendChild(col);
            });
        } catch (error) {
            console.error('Error fetching sights:', error);
            container.innerHTML = `
                <div class="col-12 text-center my-5" style="color: #7B8B88;">
                    <p>發生錯誤，請確認 API 伺服器狀態</p>
                </div>`;
        } finally {
            loading.classList.add('d-none');
        }
    }

    // 將切換文字的函式掛載到 window，讓行內的 onclick 可以呼叫
    window.toggleText = function (btn) {
        const desc = btn.previousElementSibling;
        if (desc.classList.contains('expanded')) {
            desc.classList.remove('expanded');
            btn.textContent = '顯示更多';
        } else {
            desc.classList.add('expanded');
            btn.textContent = '收起內容';
        }
    };
});