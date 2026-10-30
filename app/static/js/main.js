document.addEventListener("DOMContentLoaded", () => {
  // Mobile nav toggle
  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", () => {
      links.classList.toggle("open");
      links.style.display = links.classList.contains("open") ? "flex" : "";
    });
  }

  // Auto-dismiss flash messages
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // Register page: toggle society name field for organiser sign-ups
  const roleInputs = document.querySelectorAll('input[name="account_type"]');
  const societyField = document.getElementById("society-field");
  if (roleInputs.length && societyField) {
    roleInputs.forEach((input) => {
      input.addEventListener("change", () => {
        societyField.style.display = input.value === "organiser" && input.checked ? "block" : "none";
      });
    });
  }
});
