// notification toast variables
//const notificationToast = document.querySelector('[data-toast]');
//const toastCloseBtn = document.querySelector('[data-toast-close]');

// notification toast eventListener
//toastCloseBtn.addEventListener('click', function () {
//    notificationToast.classList.add('closed');
//});





// mobile menu variables
const mobileMenuOpenBtn = document.querySelectorAll('[data-mobile-menu-open-btn]');
const mobileMenu = document.querySelectorAll('[data-mobile-menu]');
const mobileMenuCloseBtn = document.querySelectorAll('[data-mobile-menu-close-btn]');
const overlay = document.querySelector('[data-overlay]');

for (let i = 0; i < mobileMenuOpenBtn.length; i++) {

    // mobile menu function
    const mobileMenuCloseFunc = function () {
        mobileMenu[i].classList.remove('active');
        overlay.classList.remove('active');
    }

    mobileMenuOpenBtn[i].addEventListener('click', function () {
        mobileMenu[i].classList.add('active');
        overlay.classList.add('active');
    });

    mobileMenuCloseBtn[i].addEventListener('click', mobileMenuCloseFunc);
    overlay.addEventListener('click', mobileMenuCloseFunc);

}





// accordion variables
const accordionBtn = document.querySelectorAll('[data-accordion-btn]');
const accordion = document.querySelectorAll('[data-accordion]');

for (let i = 0; i < accordionBtn.length; i++) {

    accordionBtn[i].addEventListener('click', function () {

        const clickedBtn = this.nextElementSibling.classList.contains('active');

        for (let i = 0; i < accordion.length; i++) {

            if (clickedBtn) break;

            if (accordion[i].classList.contains('active')) {

                accordion[i].classList.remove('active');
                accordionBtn[i].classList.remove('active');

            }

        }

        this.nextElementSibling.classList.toggle('active');
        this.classList.toggle('active');

    });

}



/// #section selection js. example: #bookus, #home etc
document.addEventListener("DOMContentLoaded", function () {

    const navLinks = document.querySelectorAll(".nav-link");
    const sections = document.querySelectorAll("section");

    /* =========================
       CLICK NAV LINK
    ========================== */
    navLinks.forEach(link => {
        link.addEventListener("click", function (e) {

            const targetId = this.getAttribute("href");
            if (!targetId.startsWith("#")) return;

            e.preventDefault();

            const targetSection = document.querySelector(targetId);
            if (!targetSection) return;

            // update active immediately
            navLinks.forEach(l => l.classList.remove("active"));
            this.classList.add("active");

            // smooth scroll
            targetSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

            // update URL hash (important)
            history.pushState(null, "", targetId);
        });
    });

    /* =========================
       PAGE LOAD WITH HASH
    ========================== */
    if (window.location.hash) {
        const target = document.querySelector(window.location.hash);

        if (target) {
            setTimeout(() => {
                target.scrollIntoView({ behavior: "smooth" });

                navLinks.forEach(l => l.classList.remove("active"));
                const activeLink = document.querySelector(
                    `.nav-link[href="${window.location.hash}"]`
                );
                if (activeLink) activeLink.classList.add("active");
            }, 150);
        }
    }

    /* =========================
       SCROLL SPY (auto active)
    ========================== */
    window.addEventListener("scroll", () => {
        let current = "";

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            if (pageYOffset >= sectionTop) {
                current = section.getAttribute("id");
            }
        });

        navLinks.forEach(link => {
            link.classList.remove("active");
            if (link.getAttribute("href") === `#${current}`) {
                link.classList.add("active");
            }
        });
    });

});


/*==========================================================================
  BACK TO TOP BUTTON
==========================================================================*/
document.addEventListener("DOMContentLoaded", function () {
  const backToTopBtn = document.getElementById("backToTopBtn");

  if (backToTopBtn) {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 400) {
        backToTopBtn.classList.add("show");
      } else {
        backToTopBtn.classList.remove("show");
      }
    });

    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /*==========================================================================
    SCROLL REVEAL ANIMATION (IntersectionObserver)
  ==========================================================================*/
  const revealEls = document.querySelectorAll("[data-reveal]");

  if (revealEls.length && "IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -60px 0px" });

    revealEls.forEach(el => revealObserver.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add("in-view"));
  }
});

window.addEventListener("scroll", () => {
    const header = document.querySelector("header");

    header.classList.toggle(
        "scrolled",
        window.scrollY > window.innerHeight * 0.1
    );
});