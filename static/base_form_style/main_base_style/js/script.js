/*==================== SHOW NAVBAR ====================*/
const showMenu = (headerToggle, navbarId) => {
    const toggleBtn = document.getElementById(headerToggle),
        nav__menu = document.getElementById(navbarId);

    // Validate that variables exist
    if (toggleBtn && nav__menu) {
        toggleBtn.addEventListener('click', () => {
            // We add the show-menu class to the div tag with the nav__menu class
            nav__menu.classList.toggle('show-menu');
            // Change icon and rotate it
            toggleBtn.classList.toggle('bx-x');
            toggleBtn.querySelector('.nav__dropdown-icon').style.transform =
                nav__menu.classList.contains('show-menu') ? 'rotate(180deg)' : 'rotate(0deg)';
        });
    }
};

// dropdown click wise show
document.addEventListener("DOMContentLoaded", function () {
    // Your showMenu function
    showMenu('header-toggle', 'navbar');

    var dropdowns = document.querySelectorAll(".nav__dropdown");

    dropdowns.forEach(function (dropdown) {
        dropdown.addEventListener("click", function (event) {
            // Toggle the class "active" to show/hide the dropdown content
            this.classList.toggle("active");

            // Rotate the dropdown-icon
            this.querySelector('.nav__dropdown-icon').style.transform =
                this.classList.contains("active") ? 'rotate(180deg)' : 'rotate(0deg)';

            // Store the state in localStorage
            var state = this.classList.contains("active") ? "active" : "inactive";
            localStorage.setItem(this.id + "-state", state);

            // Prevent closing other dropdowns when one is clicked
            event.stopPropagation();
        });
    });
});

/*==================== LINK ACTIVE ====================*/

document.addEventListener("DOMContentLoaded", function () {
    const menuLinks = document.querySelectorAll(".nav__link");
    const menuLinkMenus = document.querySelectorAll(".nav__link__menu");

    window.setActiveLink = function () {
        const currentPath = window.location.pathname;
        menuLinks.forEach(link => {
            const parentDropdown = link.closest('.nav__dropdown');
            if (parentDropdown) {
                const parentMenu = parentDropdown.querySelector('.nav__link__menu');
                if (link.getAttribute("href") === currentPath) {
                    link.classList.add("active");
                    if (parentMenu) {
                        parentMenu.classList.add("active");
                    }
                } else {
                    link.classList.remove("active");
                }
            }
        });

        // Update nav__link__menu active state
        menuLinkMenus.forEach(menu => {
            const hasActiveLink = menu.nextElementSibling.querySelector('.nav__link.active') !== null;
            if (!hasActiveLink) {
                menu.classList.remove("active");
            }
        });
    }

    // Initial call to set the active link based on the current URL
    setActiveLink();

    // Event listener for clicks on menu links
    menuLinks.forEach(link => {
        link.addEventListener("click", function () {
            // Remove active class from all links
            menuLinks.forEach(link => link.classList.remove("active"));
            menuLinkMenus.forEach(menu => menu.classList.remove("active"));

            // Add active class to the clicked link
            link.classList.add("active");
            const parentDropdown = link.closest('.nav__dropdown');
            if (parentDropdown) {
                const parentMenu = parentDropdown.querySelector('.nav__link__menu');
                if (parentMenu) {
                    parentMenu.classList.add("active");
                }
            }

            // Store the active link's href in localStorage
            localStorage.setItem("activeLink", link.getAttribute("href"));
        });
    });

    // Check and set the active link based on localStorage on page load
    const activeLink = localStorage.getItem("aactiveLink");
    if (activeLink && activeLink !== window.location.pathname) {
        // Update the URL without reloading the page
        window.history.pushState(null, null, activeLink);
    }

    // Set the active link based on the current URL or localStorage
    setActiveLink();

    // Listen for URL changes and set the active link accordingly
    window.addEventListener("popstate", setActiveLink);

    // Listen for manual URL changes (such as typing in the URL bar)
    window.addEventListener("load", setActiveLink);
});

function navigateTo(url) {
    localStorage.setItem("activeLink", url);
    window.history.pushState(null, null, url);
    setActiveLink(); // Update active link before changing location
    location.href = url; // Trigger page load after setting active link
}

/*==================== LINK ACTIVE END ====================*/


// Date picker
$(document).ready(function () {
    $(".datepicker").datepicker({
        dateFormat: 'yy-mm-dd',
        changeYear: true,
        changeMonth: true
    });
});


// circle loader
function circleloaderstart() {
    document.getElementById('circleloader').style.display = 'grid';
}

function circleloaderstop() {
    setTimeout(function () {
        document.getElementById('circleloader').style.display = 'none';
    }, 1100);
}

// line loader
function lineloaderstart() {
    document.getElementById('line_loader').style.display = 'flex';
}

function lineloaderstop() {
    setTimeout(function () {
        document.getElementById('line_loader').style.display = 'none';
    }, 1100);
}

// tab panel click open loader
$(document).ready(function () {
    // When a nav-link is clicked
    $('.nav-link').on('click', function () {
        // Check if it is the active link
        if ($(this).hasClass('active')) {
            lineloaderstart();
            setTimeout(lineloaderstop, 1100); // Hide after 5 seconds
        }
    });
});

//tab content show hide #example: type,uom,category,supplier,manufecturer etc setup tab  
document.addEventListener("DOMContentLoaded", function () {
    // Attach a click event listener to each tab link
    var tabLinks = document.querySelectorAll('.nav-link');

    tabLinks.forEach(function (tabLink) {
        tabLink.addEventListener('click', function (event) {
            // Prevent the default behavior of the anchor tag
            event.preventDefault();

            // Get the target tab and its content
            var tabId = this.getAttribute('href').substring(1);
            var tabContent = document.getElementById(tabId);

            // Hide all tabs and their contents
            hideAllTabs();

            // Show the clicked tab and its content
            this.classList.add('active');
            tabContent.classList.add('show', 'active');

            // Store the active tab in localStorage
            localStorage.setItem('activeTab', tabId);
        });
    });

    // Load the active tab from localStorage on page load
    var activeTabId = localStorage.getItem('activeTab');
    if (activeTabId) {
        var activeTabLink = document.querySelector(`.nav-link[href="#${activeTabId}"]`);
        if (activeTabLink) {
            activeTabLink.click();
        }
    }
});

function hideAllTabs() {
    // Hide all tabs and their contents
    var allTabs = document.querySelectorAll('.nav-link');
    var allContents = document.querySelectorAll('.tab-pane');

    allTabs.forEach(function (tab) {
        tab.classList.remove('active');
    });

    allContents.forEach(function (content) {
        content.classList.remove('show', 'active');
    });
}



// notification toast variables
const notificationToast = document.querySelector('[data-toast]');
const toastCloseBtn = document.querySelector('[data-toast-close]');

// notification toast eventListener
if (toastCloseBtn) {
    toastCloseBtn.addEventListener('click', function () {
        notificationToast.classList.add('closed');  // Hide the toast when close button is clicked

        // Show the toast again after 10 seconds (adjust as needed)
        setTimeout(() => {
            notificationToast.classList.remove('closed');  // Remove 'closed' class to show the toast again
        }, 1000); // Show the toast again after 10 seconds
    });
}

//////////////////////////////// jarvis assistant command scrpt start ////////////////////////////////
// document.addEventListener("DOMContentLoaded", function () {
//     const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
//     recognition.lang = 'en-US';
//     recognition.continuous = true;
//     recognition.interimResults = false;

//     let isActivated = false;
//     let voiceCommands = [];

//     // 🔁 Fetch the voice command list from server
//     fetch('/static/jarvis_assistant/voice_commands.json')
//         .then(res => res.json())
//         .then(data => {
//             voiceCommands = data;
//             //recognition.start();
//         });

//     // console.log("🚀 Auto starting voice recognition...");
//     //recognition.start();

//     const micIcon = document.getElementById("voice_assistant");
//     if (micIcon) {
//         micIcon.addEventListener("click", function () {
//             console.log("🎤 Microphone icon clicked. Re-starting recognition...");
//             recognition.start();
//             safeSpeak("Voice assistant reactivated. Say Jarvis.");
//         });
//     }

//     recognition.onresult = function (event) {
//         const command = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
//         console.log("🎙 Full Command Heard:", command);

//         if (!isActivated && command.includes("jarvis")) {
//             isActivated = true;
//             console.log("✅ Wake word 'Jarvis' detected!");
//             recognition.stop(); // prevent echo
//             safeSpeak("Yes, how can I help you?");
//             return;
//         }

//         if (isActivated) {
//             console.log("✅ Searching for matching command:", command);

//             const match = findBestMatch(command, voiceCommands);

//             if (match) {
//                 console.log("✅ Matched Command:", match.command_name);
//                 recognition.stop(); // stop listening while redirecting
//                 safeSpeak("Redirecting to " + match.command_name);
//                 setTimeout(() => {
//                     window.location.href = match.feature_page_link;
//                 }, 1000);
//             } else {
//                 safeSpeak("Sorry, I didn't understand that.");
//                 console.warn("⚠️ No match found.");
//             }

//             isActivated = false;
//         }
//     };

//     // recognition.onerror = function (event) {
//     //     console.error("🎤 Speech recognition error:", event.error);
//     //     safeSpeak("Microphone error occurred.");
//     // };

//     // recognition.onend = function () {
//     //     console.warn("🎤 Voice recognition ended. Restarting...");
//     //     setTimeout(() => recognition.start(), 500);
//     // };

//     // ✅ Fuzzy matching functions
//     function similarity(str1, str2) {
//         let longer = str1, shorter = str2;
//         if (str1.length < str2.length) {
//             longer = str2; shorter = str1;
//         }
//         const longerLength = longer.length;
//         if (longerLength === 0) return 1.0;
//         return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
//     }

//     function editDistance(s1, s2) {
//         s1 = s1.toLowerCase();
//         s2 = s2.toLowerCase();
//         const costs = [];
//         for (let i = 0; i <= s1.length; i++) {
//             let lastValue = i;
//             for (let j = 0; j <= s2.length; j++) {
//                 if (i === 0) {
//                     costs[j] = j;
//                 } else if (j > 0) {
//                     let newValue = costs[j - 1];
//                     if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
//                         newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
//                     }
//                     costs[j - 1] = lastValue;
//                     lastValue = newValue;
//                 }
//             }
//             if (i > 0) costs[s2.length] = lastValue;
//         }
//         return costs[s2.length];
//     }

//     function findBestMatch(inputCommand, commandList) {
//         let bestMatch = null;
//         let bestScore = 0;

//         for (const item of commandList) {
//             const score = similarity(inputCommand, item.command_name.toLowerCase());
//             if (score > 0.6 && score > bestScore) {
//                 bestScore = score;
//                 bestMatch = item;
//             }
//         }
//         return bestMatch;
//     }

//     // ✅ Safe TTS function that resumes recognition after speaking
//     function safeSpeak(text) {
//         const utterance = new SpeechSynthesisUtterance(text);
//         utterance.lang = 'en-US';

//         // Stop recognition before speaking to avoid echo and conflict
//         if (recognition) {
//             try {
//                 recognition.abort(); // safer than stop()
//             } catch (e) {
//                 console.warn("🔇 Recognition abort failed:", e.message);
//             }
//         }

//         utterance.onend = () => {
//             console.log("🔊 Finished speaking:", text);

//             // Restart recognition safely after speaking
//             try {
//                 recognition.start();
//             } catch (e) {
//                 console.warn("⚠️ Recognition start failed:", e.message);
//             }
//         };

//         speechSynthesis.speak(utterance);
//     }
// });















// document.addEventListener("DOMContentLoaded", function () {
//     const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
//     recognition.lang = 'en-US';
//     recognition.continuous = true;
//     recognition.interimResults = false;

//     let isActivated = false;
//     let currentTargetField = null; // 👈 store current input field reference
//     let voiceCommands = [];

//     fetch('/static/jarvis_assistant/voice_commands.json')
//         .then(res => res.json())
//         .then(data => { voiceCommands = data; });

//     console.log("🚀 Starting voice recognition...");
//     recognition.start();

//     const micIcon = document.getElementById("voice_assistant");
//     if (micIcon) {
//         micIcon.addEventListener("click", function () {
//             console.log("🎤 Mic icon clicked");
//             recognition.start();
//             safeSpeak("Voice assistant reactivated. Say Jarvis.");
//         });
//     }

//     recognition.onresult = function (event) {
//         const command = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
//         console.log("🎙 Command:", command);

//         // Activation
//         if (!isActivated && command.includes("jarvis")) {
//             isActivated = true;
//             recognition.stop();
//             safeSpeak("Yes, how can I help you?");
//             return;
//         }

//         if (isActivated) {
//             // 🔹 Step 1: if we're waiting for value after "click"
//             if (currentTargetField) {
//                 currentTargetField.value = command;
//                 console.log(`✅ Voice value "${command}" set to field`);
//                 speak(`Value set to ${command}`);
//                 currentTargetField = null;
//                 isActivated = false;
//                 return;
//             }

//             // 🔹 Step 2: Try to detect "click" command to focus on a field
//             if (command.startsWith("click")) {
//                 const fieldLabel = command.replace("click", "").trim();
//                 const matchedField = findFieldByLabel(fieldLabel);

//                 if (matchedField) {
//                     matchedField.focus();
//                     currentTargetField = matchedField;
//                     speak("Say the value now.");
//                     return;
//                 } else {
//                     speak(`Sorry, I couldn't find ${fieldLabel}`);
//                 }
//             }

//             // Step 3: Try auto-fill form command
//             const fieldFilled = tryFillForm(command);
//             if (fieldFilled) {
//                 isActivated = false;
//                 return;
//             }

//             // Step 4: Try redirect
//             const match = findBestMatch(command, voiceCommands);
//             if (match) {
//                 recognition.stop();
//                 safeSpeak("Redirecting to " + match.command_name);
//                 setTimeout(() => {
//                     window.location.href = match.feature_page_link;
//                 }, 1000);
//                 return;
//             }

//             speak("Sorry, I didn't understand that.");
//             console.warn("⚠️ No match found.");
//             isActivated = false;
//         }
//     };

//     recognition.onerror = function (event) {
//         console.error("🎤 Error:", event.error);
//         safeSpeak("Microphone error occurred.");
//     };

//     recognition.onend = function () {
//         console.warn("🔁 Voice recognition ended. Restarting...");
//         setTimeout(() => recognition.start(), 500);
//     };

//     function safeSpeak(text) {
//         const utterance = new SpeechSynthesisUtterance(text);
//         utterance.lang = 'en-US';
//         try { recognition.abort(); } catch (e) { }
//         utterance.onend = () => {
//             try { recognition.start(); } catch (e) { }
//         };
//         speechSynthesis.speak(utterance);
//     }

//     function speak(text) {
//         const utterance = new SpeechSynthesisUtterance(text);
//         utterance.lang = 'en-US';
//         speechSynthesis.speak(utterance);
//     }

//     function findFieldByLabel(keyword) {
//         const allFields = document.querySelectorAll("input, textarea, select");
//         keyword = keyword.toLowerCase();

//         for (let field of allFields) {
//             const label = document.querySelector(`label[for='${field.id}']`);
//             const labelText = (label?.innerText || field.placeholder || field.name || "").toLowerCase().trim();
//             if (labelText.includes(keyword) || field.name?.toLowerCase().includes(keyword)) {
//                 return field;
//             }
//         }
//         return null;
//     }

//     let pendingField = null; // Remember the clicked field to fill next

//     function tryFillForm(command) {
//         const fields = document.querySelectorAll("input, textarea, select");

//         // STEP 1: If a field was previously clicked, fill it with the new command
//         if (pendingField) {
//             const value = command.replace(/\s+/g, '');  // Remove spaces like "1 2 3"
//             pendingField.value = value;
//             console.log(`✅ Voice value "${value}" set to field "${pendingField.name || pendingField.id}"`);
//             speak(`Value set to ${value}`);
//             pendingField = null;
//             return true;
//         }

//         // STEP 2: Handle "click [field name]" command
//         if (command.startsWith("click")) {
//             const fieldNameFromVoice = command.replace("click", "").toLowerCase().trim();

//             for (let field of fields) {
//                 const label = document.querySelector(`label[for='${field.id}']`);
//                 const keyText = (label?.innerText || field.placeholder || field.name || '').toLowerCase().trim();

//                 if (keyText.includes(fieldNameFromVoice)) {
//                     field.focus();
//                     pendingField = field;
//                     console.log(`🖱️ Focused on field: "${keyText}"`);
//                     speak(`Focused on ${keyText}`);
//                     return true;
//                 }
//             }

//             console.warn(`⚠️ No match found for field: ${fieldNameFromVoice}`);
//             return false;
//         }

//         // STEP 3: Normal form filling if no click happened
//         for (let field of fields) {
//             const label = document.querySelector(`label[for='${field.id}']`);
//             const keyText = (label?.innerText || field.placeholder || field.name || '').toLowerCase().trim();
//             const normalizedKey = keyText.replace(/[^a-z]/gi, ' ').toLowerCase();

//             if (normalizedKey && command.includes(normalizedKey.split(' ')[0])) {
//                 let value = command.toLowerCase()
//                     .replace(/set|is|to|number|no/gi, '')
//                     .replace(normalizedKey.split(' ')[0], '')
//                     .replace(/\s+/g, '');

//                 if (value) {
//                     field.value = value;
//                     console.log(`✅ Set "${keyText}": ${value}`);
//                     speak(`${keyText} set to ${value}`);
//                     return true;
//                 }
//             }
//         }

//         // STEP 4: Check for submit command
//         if (command.includes("submit")) {
//             const form = document.querySelector("form");
//             if (form) {
//                 form.submit();
//                 console.log("✅ Form submitted");
//                 speak("Form submitted");
//                 return true;
//             }
//         }

//         return false;
//     }

//     function similarity(str1, str2) {
//         let longer = str1, shorter = str2;
//         if (str1.length < str2.length) [longer, shorter] = [shorter, longer];
//         const longerLength = longer.length;
//         if (longerLength === 0) return 1.0;
//         return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
//     }

//     function editDistance(s1, s2) {
//         s1 = s1.toLowerCase(); s2 = s2.toLowerCase();
//         const costs = [];
//         for (let i = 0; i <= s1.length; i++) {
//             let lastValue = i;
//             for (let j = 0; j <= s2.length; j++) {
//                 if (i === 0) costs[j] = j;
//                 else if (j > 0) {
//                     let newValue = costs[j - 1];
//                     if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
//                         newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
//                     }
//                     costs[j - 1] = lastValue;
//                     lastValue = newValue;
//                 }
//             }
//             if (i > 0) costs[s2.length] = lastValue;
//         }
//         return costs[s2.length];
//     }

//     function findBestMatch(inputCommand, commandList) {
//         let bestMatch = null;
//         let bestScore = 0;
//         for (const item of commandList) {
//             const score = similarity(inputCommand, item.command_name.toLowerCase());
//             if (score > 0.6 && score > bestScore) {
//                 bestScore = score;
//                 bestMatch = item;
//             }
//         }
//         return bestMatch;
//     }
// });


//////////////////////////////// jarvis assistant command scrpt end ////////////////////////////////

//////////////////////////////// not use its always on in microphone ////////////////////////////////
//not use its always on in microphone
// recognition.onerror = function (event) {
//         console.error("🎤 Speech recognition error:", event.error);
//         speak("Microphone error occurred.");
//     };

//     recognition.onend = function () {
//         console.warn("🎤 Voice recognition ended. Restarting...");
//         recognition.start();
//     };