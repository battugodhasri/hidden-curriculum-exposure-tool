document.addEventListener('DOMContentLoaded', () => {
    // Flash messages auto-dismiss
    setTimeout(() => {
        const flashes = document.querySelectorAll('.flash');
        flashes.forEach(f => {
            f.style.transition = "opacity 0.5s ease";
            f.style.opacity = "0";
            setTimeout(() => f.remove(), 500);
        });
    }, 4000);

    // Active nav logic
    const path = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if(item.getAttribute('href') === path) {
            item.classList.add('active');
        }
    });
});

function generatePDF() {
    const element = document.getElementById('report-content');
    const opt = {
        margin:       1,
        filename:     'Hidden_Curriculum_Report.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(element).save();
}
