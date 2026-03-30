/* Rugby Manager Game — Frontend JS */

// Auto-scroll commentary feed to bottom
document.addEventListener('DOMContentLoaded', function() {
    const feed = document.querySelector('.commentary-feed');
    if (feed) {
        feed.scrollTop = feed.scrollHeight;
    }
});
