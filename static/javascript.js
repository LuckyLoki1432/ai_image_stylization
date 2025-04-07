document.addEventListener("DOMContentLoaded", function() {
    // Shared functionality
    const applyStyleBtn = document.getElementById("apply-style");
    if (applyStyleBtn) {
        applyStyleBtn.addEventListener("click", showLoading);
    }

    const downloadBtn = document.getElementById("download-btn");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", downloadImage);
    }

    // Home page option cards
    const optionCards = document.querySelectorAll(".option-card");
    optionCards.forEach(card => {
        card.addEventListener("click", function() {
            window.location = this.getAttribute("onclick").match(/'(.*?)'/)[1];
        });
    });
});

function showLoading() {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
        loadingDiv.style.opacity = '1';
    }
}

function downloadImage() {
    const editedImg = document.getElementById("edited-img");
    if (!editedImg || !editedImg.src) {
        alert("No image available for download!");
        return;
    }

    const link = document.createElement("a");
    link.href = editedImg.src;
    link.download = "styled_image.jpg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}