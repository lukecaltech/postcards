document.addEventListener("DOMContentLoaded", () => {
    // Create modal elements dynamically
    const modal = document.createElement("div");
    modal.id = "zoom-modal";
    
    const modalImg = document.createElement("img");
    modal.appendChild(modalImg);
    
    // Create Close Button
    const closeBtn = document.createElement("div");
    closeBtn.id = "zoom-close";
    closeBtn.innerHTML = "&times;"; // HTML entity for 'X'
    modal.appendChild(closeBtn);

    closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        modal.classList.remove("active");
    });
    closeBtn.addEventListener("mousedown", (e) => e.stopPropagation());
    
    // Create Slider Controls
    const controls = document.createElement("div");
    controls.id = "zoom-controls";
    
    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "20"; // 20% width
    slider.max = "300"; // 300% width
    slider.value = "100";
    slider.id = "zoom-slider";
    
    controls.appendChild(slider);
    modal.appendChild(controls);
    document.body.appendChild(modal);

    // Update image scale when slider moves
    slider.addEventListener("input", (e) => {
        modalImg.style.maxWidth = "none";
        modalImg.style.maxHeight = "none";
        modalImg.style.width = `${e.target.value}%`;
    });

    // Prevent clicks/drags on controls from triggering other behaviors
    controls.addEventListener("mousedown", (e) => e.stopPropagation());
    controls.addEventListener("click", (e) => e.stopPropagation());

    // --- Drag to Pan Logic ---
    let isDragging = false;
    let startX, startY, scrollLeft, scrollTop;

    modalImg.addEventListener("mousedown", (e) => {
        e.preventDefault(); // Prevent native browser image drag
        e.stopPropagation();
        isDragging = true;
        modalImg.style.cursor = "grabbing";
        
        startX = e.pageX - modal.offsetLeft;
        startY = e.pageY - modal.offsetTop;
        scrollLeft = modal.scrollLeft;
        scrollTop = modal.scrollTop;
    });

    modal.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        e.preventDefault();
        
        const x = e.pageX - modal.offsetLeft;
        const y = e.pageY - modal.offsetTop;
        const walkX = x - startX;
        const walkY = y - startY;
        
        modal.scrollLeft = scrollLeft - walkX;
        modal.scrollTop = scrollTop - walkY;
    });

    modal.addEventListener("mouseup", () => {
        isDragging = false;
        modalImg.style.cursor = "grab";
    });

    modal.addEventListener("mouseleave", () => {
        isDragging = false;
        modalImg.style.cursor = "grab";
    });

    // Don't close modal when clicking the image
    modalImg.addEventListener("click", (e) => {
        e.stopPropagation();
    });

    // Close modal ONLY when clicking the dark background
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.classList.remove("active");
        }
    });

    // Attach click listeners to all postcard images on the detail pages
    const images = document.querySelectorAll(".postcard-view img");
    images.forEach(img => {
        img.addEventListener("click", () => {
            modalImg.src = img.src;
            
            // Reset slider and size to nicely fit the screen initially
            slider.value = "100"; 
            modalImg.style.width = "100%";
            modalImg.style.maxWidth = "90vw";
            modalImg.style.maxHeight = "90vh";
            modalImg.style.objectFit = "contain";
            modalImg.style.cursor = "grab";
            
            modal.classList.add("active");
        });
    });

    // Hover logic: Highlight bounding boxes when hovering over tags
    const tags = document.querySelectorAll('.tag[data-box]');
    tags.forEach(tag => {
        tag.addEventListener('mouseenter', () => {
            const boxIds = tag.getAttribute('data-box').split(',');
            boxIds.forEach(id => {
                if (!id) return;
                const box = document.querySelector(`.box-${id}`);
                if(box) box.classList.add('highlight');
            });
        });
        
        tag.addEventListener('mouseleave', () => {
            const boxIds = tag.getAttribute('data-box').split(',');
            boxIds.forEach(id => {
                if (!id) return;
                const box = document.querySelector(`.box-${id}`);
                if(box) box.classList.remove('highlight');
            });
        });
    });
});
