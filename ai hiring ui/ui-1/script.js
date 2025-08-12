// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Navbar background change on scroll with parallax effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    const scrolled = window.scrollY;
    
    if (scrolled > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.8)';
        navbar.style.boxShadow = 'none';
    }
});

// Parallax effect for hero section
window.addEventListener('scroll', function() {
    const hero = document.querySelector('.hero');
    const scrolled = window.scrollY;
    hero.style.backgroundPosition = `center ${scrolled * 0.5}px`;
});

// Form submission handling with animation
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Add loading animation
        const submitButton = this.querySelector('.submit-button');
        const originalText = submitButton.textContent;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        submitButton.disabled = true;

        // Simulate form submission (replace with actual form submission)
        setTimeout(() => {
            submitButton.innerHTML = '<i class="fas fa-check"></i> Sent!';
            submitButton.style.background = '#4CAF50';
            
            // Reset form and button after 2 seconds
            setTimeout(() => {
                contactForm.reset();
                submitButton.innerHTML = originalText;
                submitButton.style.background = '';
                submitButton.disabled = false;
            }, 2000);
        }, 1500);
    });
}

// Enhanced feature cards animation
const featureCards = document.querySelectorAll('.feature-card');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0) scale(1)';
        }
    });
}, {
    threshold: 0.2,
    rootMargin: '0px'
});

featureCards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(50px) scale(0.95)';
    card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
    card.style.transitionDelay = `${index * 0.1}s`;
    observer.observe(card);
});

// Add floating animation to icons
featureCards.forEach(card => {
    const icon = card.querySelector('i');
    if (icon) {
        icon.style.transition = 'transform 0.3s ease';
        card.addEventListener('mouseenter', () => {
            icon.style.transform = 'translateY(-10px) scale(1.2)';
        });
        card.addEventListener('mouseleave', () => {
            icon.style.transform = 'translateY(0) scale(1)';
        });
    }
});

// Add text reveal animation
const revealElements = document.querySelectorAll('.hero-content h1, .hero-content p, .features h2, .about h2, .contact h2');
const textObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
        }
    });
}, {
    threshold: 0.1
});

revealElements.forEach(element => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    element.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
    textObserver.observe(element);
});

// Add CSS class for revealed elements
document.head.insertAdjacentHTML('beforeend', `
    <style>
        .revealed {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    </style>
`); 