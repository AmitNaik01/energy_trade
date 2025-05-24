var sidebar = document.querySelector(".w3-sidebar");
var closeBtn = document.querySelector(".close-btn");
var openBtn = document.querySelector(".menu-btn");

openBtn.onclick = function() {
  sidebar.style.width = "100%"; // Open sidebar
  document.querySelector(".side-div-section24").classList.add("open-sidebar");
  sidebar.style.display = "block"; // Ensure the sidebar is displayed
}

closeBtn.onclick = function() {
  sidebar.style.width = "0"; // Close sidebar
  document.querySelector(".side-div-section24").classList.remove("open-sidebar");
  sidebar.style.display = "none"; // Hide the sidebar again
}