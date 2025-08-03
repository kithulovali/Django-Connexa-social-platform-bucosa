document.addEventListener('DOMContentLoaded', function() {
    const mainNav = document.getElementById('mainNav');
    const navLinks = document.querySelectorAll('#mainNav .nav-link');
    const toggleLeaf = document.getElementById('toggleLeaf'); // The leaf icon that acts as a toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Function to check if it's a mobile view based on CSS media query
    function isMobileView() {
        return window.matchMedia("(max-width: 767.98px)").matches;
    }

    // Function to set the active link based on the current view
    function setActiveLinkBasedOnView() {
        // Clear all active classes first
        navLinks.forEach(l => l.classList.remove('active'));

        if (isMobileView()) {
            // Mobile view: activate 'list' link
            const mobileDefaultLink = document.querySelector('#mainNav .nav-link[data-link-id="list"]');
            if (mobileDefaultLink) {
                mobileDefaultLink.classList.add('active');
            }
        } else {
            // Desktop view: activate 'home' link
            const desktopHomeLink = document.querySelector('#mainNav .nav-link[data-link-id="home"]');
            if (desktopHomeLink) {
                desktopHomeLink.classList.add('active');
            }
        }
    }

    // Set initial active link on DOMContentLoaded
    setActiveLinkBasedOnView();

    // Handle clicks on regular navigation links (excluding the toggle)
    navLinks.forEach(link => {
        if (link !== toggleLeaf) { // Exclude the toggle button from regular active state logic
            link.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent default link behavior

                // Remove 'active' class from all links that are not the toggle
                navLinks.forEach(l => {
                    if (l !== toggleLeaf) { // Only remove active from non-toggle links
                        l.classList.remove('active');
                    }
                });

                // Add 'active' class to the clicked content link
                this.classList.add('active');

                // If in mobile view and hidden links are currently shown, hide them after a content link is clicked
                if (isMobileView() && mainNav.classList.contains('show-all-links')) {
                    mainNav.classList.remove('show-all-links');
                    toggleLeaf.classList.remove('active'); // Deactivate toggle icon
                }
            });
        }
    });

    // Handle click on the toggle (leaf) button
    if (toggleLeaf) {
        toggleLeaf.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default link behavior
            if (isMobileView()) { // Only toggle if in mobile view
                mainNav.classList.toggle('show-all-links'); // Toggle visibility of hidden links
                this.classList.toggle('active'); // Toggle active state of the leaf icon itself
            }
        });
    }

    // Handle window resize to adjust navigation behavior
    window.addEventListener('resize', function() {
        // When resizing, always ensure mobile-specific classes are removed and toggle is reset
        mainNav.classList.remove('show-all-links');
        toggleLeaf.classList.remove('active');
        setActiveLinkBasedOnView(); // Re-evaluate and set active link based on new view
    });

    // --- Friend Suggestions JavaScript ---
    document.querySelectorAll('.follow-btn').forEach(button => {
        button.addEventListener('click', function() {
            if (this.textContent === 'FOLLOW') {
                this.textContent = 'FOLLOWING';
                this.classList.add('disabled');
                this.disabled = true;
                this.style.backgroundColor = '#cccccc'; /* Change to disabled color */
            }
        });
    });

    document.querySelectorAll('.close-btn').forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.friend-card');
            if (card) {
                card.remove(); // Remove the card from the DOM
            }
        });
    });

    // --- More Posts Button JavaScript ---
    const recentPostsSection = document.getElementById('recentPostsSection');
    const morePostsBtn = document.getElementById('morePostsBtn');

    if (morePostsBtn && recentPostsSection) {
        morePostsBtn.addEventListener('click', function() {
            // Toggle the 'show-all-posts' class on the recent posts section
            recentPostsSection.classList.toggle('show-all-posts');

            // Change button text and icon based on state
            if (recentPostsSection.classList.contains('show-all-posts')) {
                morePostsBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Show Less';
            } else {
                morePostsBtn.innerHTML = '<i class="fas fa-chevron-down"></i> More Posts';
            }
        });
    }

    // --- More Events Button JavaScript ---
    const upcomingEventsSection = document.getElementById('upcomingEventsSection');
    const moreEventsBtn = document.getElementById('moreEventsBtn');

    if (moreEventsBtn && upcomingEventsSection) {
        moreEventsBtn.addEventListener('click', function() {
            // Toggle the 'show-all-events' class on the upcoming events section
            upcomingEventsSection.classList.toggle('show-all-events');

            // Change button text and icon based on state
            if (upcomingEventsSection.classList.contains('show-all-events')) {
                moreEventsBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Show Less';
            } else {
                moreEventsBtn.innerHTML = '<i class="fas fa-chevron-down"></i> More Events';
            }
        });
    }

    // --- Dark Mode Toggle JavaScript ---
    // Function to apply the theme based on localStorage or default to light
    function applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            body.classList.add('dark-mode');
            darkModeToggle.querySelector('i').classList.remove('fa-moon');
            darkModeToggle.querySelector('i').classList.add('fa-sun');
        } else {
            body.classList.remove('dark-mode');
            darkModeToggle.querySelector('i').classList.remove('fa-sun');
            darkModeToggle.querySelector('i').classList.add('fa-moon');
        }
    }

    // Apply theme on initial load
    applyTheme();

    // Event listener for the dark mode toggle button
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode'); // Toggle the dark-mode class on the body

            // Update local storage and button icon
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
                this.querySelector('i').classList.remove('fa-moon');
                this.querySelector('i').classList.add('fa-sun');
            } else {
                localStorage.setItem('theme', 'light');
                this.querySelector('i').classList.remove('fa-sun');
                this.querySelector('i').classList.add('fa-moon');
            }
        });
    }
});
