// Initialize Particles.js
particlesJS("particles-js", {
    "particles": {
        "number": {
            "value": 80,
            "density": {
                "enable": true,
                "value_area": 800
            }
        },
        "color": {
            "value": "#a855f7"
        },
        "shape": {
            "type": "circle",
            "stroke": {
                "width": 0,
                "color": "#000000"
            },
            "polygon": {
                "nb_sides": 5
            }
        },
        "opacity": {
            "value": 0.5,
            "random": true,
            "anim": {
                "enable": false,
                "speed": 1,
                "opacity_min": 0.1,
                "sync": false
            }
        },
        "size": {
            "value": 3,
            "random": true,
            "anim": {
                "enable": true,
                "speed": 2,
                "size_min": 0.1,
                "sync": false
            }
        },
        "line_linked": {
            "enable": true,
            "distance": 150,
            "color": "#6366f1",
            "opacity": 0.2,
            "width": 1
        },
        "move": {
            "enable": true,
            "speed": 1,
            "direction": "none",
            "random": true,
            "straight": false,
            "out_mode": "out",
            "bounce": false,
            "attract": {
                "enable": false,
                "rotateX": 600,
                "rotateY": 1200
            }
        }
    },
    "interactivity": {
        "detect_on": "canvas",
        "events": {
            "onhover": {
                "enable": true,
                "mode": "grab"
            },
            "onclick": {
                "enable": true,
                "mode": "push"
            },
            "resize": true
        },
        "modes": {
            "grab": {
                "distance": 140,
                "line_linked": {
                    "opacity": 1
                }
            },
            "bubble": {
                "distance": 400,
                "size": 40,
                "duration": 2,
                "opacity": 8,
                "speed": 3
            },
            "repulse": {
                "distance": 200,
                "duration": 0.4
            },
            "push": {
                "particles_nb": 4
            },
            "remove": {
                "particles_nb": 2
            }
        }
    },
    "retina_detect": true
});

// Digital Clock
function updateClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    document.getElementById('digital-clock').textContent = `${hours}:${minutes}:${seconds}`;
}

setInterval(updateClock, 1000);
updateClock();

// Mobile Menu Toggle
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.querySelector('aside');

menuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('hidden');
    sidebar.classList.toggle('flex');
    sidebar.classList.toggle('w-full');
    sidebar.classList.toggle('fixed');
    sidebar.classList.toggle('inset-0');

    const icon = menuToggle.querySelector('i');
    if (sidebar.classList.contains('flex')) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-times');
    } else {
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
    }
});

// Close sidebar on mobile when a link is clicked
const navLinks = document.querySelectorAll('aside nav a');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth < 1024) {
            sidebar.classList.add('hidden');
            sidebar.classList.remove('flex', 'w-full', 'fixed', 'inset-0');
            menuToggle.querySelector('i').classList.remove('fa-times');
            menuToggle.querySelector('i').classList.add('fa-bars');
        }
    });
});

// Smooth Scroll for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Reveal animations on scroll
function reveal() {
    const reveals = document.querySelectorAll("section, .glass-card, .bot-card");
    for (let i = 0; i < reveals.length; i++) {
        const windowHeight = window.innerHeight;
        const elementTop = reveals[i].getBoundingClientRect().top;
        const elementVisible = 150;
        if (elementTop < windowHeight - elementVisible) {
            reveals[i].classList.add("active");
        }
    }
}

window.addEventListener("scroll", reveal);
reveal(); // Initial check

// Snowfall Generator
function createSnow() {
    const snowContainer = document.getElementById('snow-container');
    const snowCount = 50;

    for (let i = 0; i < snowCount; i++) {
        const snowflake = document.createElement('div');
        snowflake.className = 'snowflake';

        // Random properties
        const size = Math.random() * 4 + 2 + 'px';
        const left = Math.random() * 100 + '%';
        const duration = Math.random() * 10 + 10 + 's';
        const delay = Math.random() * 10 + 's';
        const opacity = Math.random() * 0.5 + 0.3;

        snowflake.style.width = size;
        snowflake.style.height = size;
        snowflake.style.left = left;
        snowflake.style.animationDuration = duration;
        snowflake.style.animationDelay = delay;
        snowflake.style.opacity = opacity;

        snowContainer.appendChild(snowflake);
    }
}

// Mist Generator
function createMist() {
    const mistContainer = document.getElementById('mist-container');
    for (let i = 0; i < 2; i++) {
        const mist = document.createElement('div');
        mist.className = 'mist';
        mist.style.top = i * 50 + '%';
        mist.style.opacity = 0.1 + (i * 0.1);
        mist.style.animationDuration = (60 + i * 20) + 's';
        mistContainer.appendChild(mist);
    }
}

// YouTube Content Integration
const YOUTUBE_LINKS = [
    "https://youtu.be/gfB1HbxyP3w",
    "https://youtu.be/vtqXdD2tGCg",
    "https://youtu.be/tqV2jH5YWFY"
];

async function fetchYouTubeMetadata(url) {
    try {
        // Using oEmbed API for metadata - YouTube's oEmbed allows CORS
        const oEmbedUrl = `https://www.youtube.com/oembed?url=${encodeURIComponent(url)}&format=json`;
        const response = await fetch(oEmbedUrl);
        if (!response.ok) throw new Error('Failed to fetch metadata');
        const data = await response.json();

        if (data) {
            const isPlaylist = url.includes('playlist');
            let videoId = "";
            let thumbUrl = data.thumbnail_url;

            if (isPlaylist) {
                // For playlists, oEmbed thumbnail usually points to the first video
                // We try to get a higher quality version if possible
                thumbUrl = thumbUrl.replace('hqdefault', 'maxresdefault');
            } else {
                // Extract video ID for high-res thumbnail
                const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
                const match = url.match(regExp);
                videoId = (match && match[2].length === 11) ? match[2] : null;

                if (videoId) {
                    thumbUrl = `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`;
                }
            }

            return {
                title: data.title,
                author: data.author_name,
                thumbnail: thumbUrl,
                url: url,
                isPlaylist: isPlaylist,
                // Duration is not available in oEmbed, so we use a stylized badge
                duration: isPlaylist ? "PLAYLIST" : "HD 4K"
            };
        }
    } catch (error) {
        console.error(`Error fetching YT data for ${url}:`, error);
        return null;
    }
}

async function renderYouTubeCards() {
    const container = document.getElementById('youtube-cards-container');
    if (!container) return;

    const metadataPromises = YOUTUBE_LINKS.map(url => fetchYouTubeMetadata(url));
    const results = await Promise.all(metadataPromises);

    // Filter out nulls and clear skeleton
    const validResults = results.filter(r => r !== null);
    if (validResults.length > 0) {
        container.innerHTML = '';
    } else {
        // Fallback or keep skeleton? Let's show error
        container.innerHTML = '<p class="text-gray-500 col-span-full text-center py-10">Failed to load YouTube content. Please check your connection.</p>';
        return;
    }

    validResults.forEach((data, index) => {
        const card = document.createElement('div');
        card.className = `yt-card group rounded-3xl overflow-hidden opacity-0 translate-y-10 transition-all duration-700 ${index === 0 ? 'featured' : ''}`;
        card.style.transitionDelay = `${index * 150}ms`;

        const badge = data.isPlaylist
            ? `<div class="playlist-badge"><i class="fas fa-list"></i> PLAYLIST</div>`
            : `<div class="duration-badge">${data.duration}</div>`;

        card.innerHTML = `
            <div class="thumb-container aspect-video relative">
                <img src="${data.thumbnail}" alt="${data.title}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" loading="lazy" onerror="this.src='https://i.ytimg.com/vi/${data.videoId || 'dQw4w9WgXcQ'}/hqdefault.jpg'">
                <div class="play-overlay">
                    <div class="play-btn">
                        <i class="fas fa-play"></i>
                    </div>
                </div>
                ${badge}
            </div>
            <div class="p-6">
                <h5 class="text-lg font-bold mb-2 group-hover:text-purple-400 transition-colors duration-300">${data.title}</h5>
                <div class="flex items-center space-x-2 text-xs text-gray-400 mb-6">
                    <i class="fab fa-youtube text-red-500"></i>
                    <span>${data.author}</span>
                </div>
                <a href="${data.url}" target="_blank" class="watch-btn inline-block px-6 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest">
                    Watch Now
                </a>
            </div>
        `;

        card.addEventListener('click', () => {
            window.open(data.url, '_blank');
        });

        container.appendChild(card);

        // Trigger entrance animation
        setTimeout(() => {
            card.classList.remove('opacity-0', 'translate-y-10');
        }, 100);
    });
}

// Initialize Effects
document.addEventListener('DOMContentLoaded', () => {
    createSnow();
    createMist();
    renderYouTubeCards();
});
