// Auto-dismiss flash messages after 4 seconds
document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => el.remove(), 4000);
});

// Password strength rules (register page)
const pwInput = document.getElementById('password');
const confirmInput = document.getElementById('confirmPassword');

if (pwInput) {
    const rules = {
        'r-len':   v => v.length >= 8,
        'r-upper': v => /[A-Z]/.test(v),
        'r-lower': v => /[a-z]/.test(v),
        'r-num':   v => /[0-9]/.test(v),
        'r-sym':   v => /[^A-Za-z0-9]/.test(v),
    };

    pwInput.addEventListener('input', () => {
        const val = pwInput.value;
        for (const [id, test] of Object.entries(rules)) {
            document.getElementById(id)?.classList.toggle('valid', test(val));
        }
    });
}

if (confirmInput) {
    confirmInput.addEventListener('input', () => {
        const err = document.getElementById('matchError');
        if (err) err.textContent = confirmInput.value !== pwInput.value ? 'Passwords do not match.' : '';
    });
}

// Block form submit if passwords don't match or rules not met
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', e => {
        const pw = document.getElementById('password').value;
        const confirm = document.getElementById('confirmPassword').value;
        const allValid = [
            pw.length >= 8,
            /[A-Z]/.test(pw),
            /[a-z]/.test(pw),
            /[0-9]/.test(pw),
            /[^A-Za-z0-9]/.test(pw),
        ].every(Boolean);

        if (!allValid) {
            e.preventDefault();
            alert('Password does not meet all requirements.');
            return;
        }
        if (pw !== confirm) {
            e.preventDefault();
            alert('Passwords do not match.');
        }
    });
}

// Futuristic Background Canvas Particles
const canvas = document.getElementById('bgCanvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    
    window.addEventListener('resize', resize);
    resize();

    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.size = Math.random() * 2;
            this.color = Math.random() > 0.5 ? '#00f3ff' : '#0096ba';
            this.alpha = Math.random() * 0.5 + 0.1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
        }
        draw() {
            ctx.globalAlpha = this.alpha;
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
            
            // Subtle glow
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
        }
    }

    // Create a network effect
    function connectParticles() {
        ctx.lineWidth = 0.5;
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 120) {
                    ctx.globalAlpha = 1 - (distance / 120);
                    ctx.strokeStyle = particles[i].color;
                    ctx.shadowBlur = 0;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }

    function initParticles() {
        particles = [];
        const count = Math.min(Math.floor(width * height / 15000), 100);
        for (let i = 0; i < count; i++) {
            particles.push(new Particle());
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        connectParticles();
        requestAnimationFrame(animate);
    }

    initParticles();
    animate();
}
