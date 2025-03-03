document.addEventListener("DOMContentLoaded", function(){
    // File selection and preview for Color Matcher and Color Blindness
    document.getElementById('sampleInput').addEventListener('change', function() {
      previewImage(this.files[0], 'samplePreview');
    });
    document.getElementById('userInput').addEventListener('change', function() {
      previewImage(this.files[0], 'userPreview');
    });
    document.getElementById('cbInput').addEventListener('change', function() {
      previewImage(this.files[0], 'cbInputPreview');
    });
    
    // Click on preview boxes to trigger file selection
    document.getElementById('refBox').addEventListener('click', () => {
      document.getElementById('sampleInput').click();
    });
    document.getElementById('userBox').addEventListener('click', () => {
      document.getElementById('userInput').click();
    });
    document.getElementById('pickerContainer').addEventListener('click', () => {
      document.getElementById('colorInput').click();
    });
    document.getElementById('cbInputBox').addEventListener('click', () => {
      document.getElementById('cbInput').click();
    });
    
    // Tab Navigation
    window.showFacility = function(facility) {
      const tabs = document.querySelectorAll('.tab-btn');
      const sections = {
        matcher: document.getElementById('matcherSection'),
        picker: document.getElementById('pickerSection'),
        blindness: document.getElementById('blindnessSection'),
        completePalette: document.getElementById('completePaletteSection')
      };
      tabs.forEach(btn => btn.classList.remove('active'));
      Object.values(sections).forEach(sec => sec.style.display = 'none');
      if(facility === 'matcher') {
        sections.matcher.style.display = 'block';
        tabs[0].classList.add('active');
      } else if(facility === 'picker') {
        sections.picker.style.display = 'block';
        tabs[1].classList.add('active');
      } else if(facility === 'blindness') {
        sections.blindness.style.display = 'block';
        tabs[2].classList.add('active');
      } else if(facility === 'completePalette') {
        sections.completePalette.style.display = 'block';
        tabs[3].classList.add('active');
        generateCompletePalette();
      }
    };
    
    // Color Matcher Processing
    window.processImages = function() {
      const sampleInput = document.getElementById('sampleInput');
      const userInput = document.getElementById('userInput');
      if (!sampleInput.files[0] || !userInput.files[0]) {
        alert('Please add both images.');
        return;
      }
      const formData = new FormData();
      formData.append('sample', sampleInput.files[0]);
      formData.append('user', userInput.files[0]);
      document.getElementById('loading').style.display = 'block';
      fetch('/process', {
        method: 'POST',
        headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        document.getElementById('loading').style.display = 'none';
        if (data.error) { 
          alert(data.error); 
        } else {
          const userImg = document.getElementById('userPreview');
          userImg.src = data.result_img;
          userImg.classList.remove('empty');
          userImg.classList.add('loaded');
          document.getElementById('downloadLink').href = data.result_img;
          document.getElementById('downloadLink').style.display = 'inline-block';
        }
      })
      .catch(err => {
        document.getElementById('loading').style.display = 'none';
        console.error(err);
        alert('Error processing images.');
      });
    };
    
    window.resetMatcher = function() {
      ['samplePreview', 'userPreview'].forEach(id => {
        const img = document.getElementById(id);
        img.src = '';
        img.classList.remove('loaded');
        img.parentElement.classList.add('empty');
      });
      document.getElementById('sampleInput').value = '';
      document.getElementById('userInput').value = '';
      document.getElementById('downloadLink').style.display = 'none';
    };
    
    // Color Picker Functions
    document.getElementById('colorInput').addEventListener('change', function(){
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(e){
        const imgObj = new Image();
        imgObj.onload = function(){
          const container = document.getElementById('pickerContainer');
          const containerW = container.clientWidth;
          const containerH = container.clientHeight;
          const canvas = document.getElementById('pickerCanvas');
          canvas.width = containerW;
          canvas.height = containerH;
          canvas.style.display = 'block';
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#fff';
          ctx.fillRect(0, 0, containerW, containerH);
          let scale = Math.min(containerW / imgObj.naturalWidth, containerH / imgObj.naturalHeight);
          const imgDrawW = imgObj.naturalWidth * scale;
          const imgDrawH = imgObj.naturalHeight * scale;
          const imgOffsetX = (containerW - imgDrawW) / 2;
          const imgOffsetY = (containerH - imgDrawH) / 2;
          ctx.drawImage(imgObj, 0, 0, imgObj.naturalWidth, imgObj.naturalHeight, imgOffsetX, imgOffsetY, imgDrawW, imgDrawH);
          generatePalette(ctx, imgDrawW, imgDrawH);
        };
        imgObj.src = e.target.result;
        document.getElementById('pickerContainer').classList.remove('empty');
      };
      reader.readAsDataURL(file);
    });
    
    // Palette Generation for Color Picker
    window.generatePalette = function(ctx, width, height) {
      const container = document.getElementById('paletteContainer');
      container.innerHTML = '';
      let uniqueColors = new Set();
      const swatchSize = 50;
      for (let y = 0; y < height; y += swatchSize) {
        for (let x = 0; x < width; x += swatchSize) {
          const cellW = Math.min(swatchSize, width - x);
          const cellH = Math.min(swatchSize, height - y);
          const data = ctx.getImageData(x, y, cellW, cellH).data;
          let rSum = 0, gSum = 0, bSum = 0, count = 0;
          for (let i = 0; i < data.length; i += 4) {
            rSum += data[i];
            gSum += data[i+1];
            bSum += data[i+2];
            count++;
          }
          const avgR = Math.round(rSum / count);
          const avgG = Math.round(gSum / count);
          const avgB = Math.round(bSum / count);
          const hex = "#" + ((1 << 24) + (avgR << 16) + (avgG << 8) + avgB).toString(16).slice(1).toUpperCase();
          if (!uniqueColors.has(hex)) {
            uniqueColors.add(hex);
            const item = document.createElement('div');
            item.className = 'palette-item';
            item.innerHTML = `<div class="palette-swatch" style="background-color: ${hex};"></div><div class="palette-text">${hex}</div>`;
            item.addEventListener('click', () => zoomColor(hex));
            container.appendChild(item);
          }
        }
      }
    };
    
    window.resetPicker = function() {
      const canvas = document.getElementById('pickerCanvas');
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      document.getElementById('paletteContainer').innerHTML = '';
      document.getElementById('globalColorDisplay').textContent = 'Hover over image to see color';
      document.getElementById('pickerContainer').classList.add('empty');
      document.getElementById('colorInput').value = '';
    };
    
    // Color Blindness Functions
    window.simulateCB = function() {
      const cbInput = document.getElementById('cbInput');
      const deficiency = document.getElementById('deficiencySelect').value;
      if (!cbInput.files[0]) { alert('Please add an image.'); return; }
      const formData = new FormData();
      formData.append('cbImage', cbInput.files[0]);
      formData.append('deficiency', deficiency);
      fetch('/simulate_cb', {
        method: 'POST',
        headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.error) { 
          alert(data.error); 
        } else {
          const resultEl = document.getElementById('cbResultPreview');
          resultEl.src = data.simulated_img;
          resultEl.classList.remove('empty');
          resultEl.classList.add('loaded');
          document.getElementById('cbDownloadLink').href = data.simulated_img;
          document.getElementById('cbDownloadLink').style.display = 'inline-block';
        }
      })
      .catch(err => { console.error(err); alert('Error during simulation.'); });
    };
    
    window.resetBlindness = function() {
      ['cbInputPreview', 'cbResultPreview'].forEach(id => {
        const img = document.getElementById(id);
        img.src = '';
        img.classList.remove('loaded');
        img.parentElement.classList.add('empty');
      });
      document.getElementById('cbInput').value = '';
      document.getElementById('cbDownloadLink').style.display = 'none';
    };
    
    // Complete Palette Functions (Scrollable 5x5 Grid with Click-to-Zoom)
    window.generateCompletePalette = function() {
      const resolution = parseInt(document.getElementById('resolutionSlider').value);
      const grid = document.getElementById('completePaletteGrid');
      grid.innerHTML = '';
      const frag = document.createDocumentFragment();
      const step = resolution > 1 ? Math.round(255 / (resolution - 1)) : 255;
      for (let r = 0; r < resolution; r++) {
        for (let g = 0; g < resolution; g++) {
          for (let b = 0; b < resolution; b++) {
            const R = Math.round(r * step);
            const G = Math.round(g * step);
            const B = Math.round(b * step);
            const hex = "#" + ((1 << 24) + (R << 16) + (G << 8) + B).toString(16).slice(1).toUpperCase();
            const card = document.createElement('div');
            card.className = 'color-card';
            card.style.cursor = 'pointer';
            card.innerHTML = `<div class="color-swatch" style="background-color: ${hex}; width:100%; height:100px; border-radius:4px;"></div><div class="color-hex">${hex}</div>`;
            card.addEventListener('click', () => zoomColor(hex));
            frag.appendChild(card);
          }
        }
      }
      grid.appendChild(frag);
    };
    
    window.updateResolutionValue = function(val) {
      document.getElementById('resolutionValue').textContent = val;
      generateCompletePalette();
    };
    
    // Zoom modal for clicking on a color in the palette
    window.zoomColor = function(hex) {
      document.getElementById('zoomColorSwatch').style.backgroundColor = hex;
      document.getElementById('zoomColorHex').textContent = hex;
      document.getElementById('zoomModal').style.display = 'flex';
    };
    
    window.closeZoomModal = function() {
      document.getElementById('zoomModal').style.display = 'none';
    };
    
    // Helper for image preview
    window.previewImage = function(file, imgId) {
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          const imgElem = document.getElementById(imgId);
          imgElem.src = e.target.result;
          imgElem.classList.add('loaded');
          imgElem.parentElement.classList.remove('empty');
        };
        reader.readAsDataURL(file);
      }
    };
});