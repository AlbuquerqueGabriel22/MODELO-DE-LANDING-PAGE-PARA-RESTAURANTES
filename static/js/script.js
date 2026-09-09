document.addEventListener("DOMContentLoaded", () => {
  const slides = [...document.querySelectorAll(".hero-slide")];
  const dots = [...document.querySelectorAll(".slide-dot")];
  const revealItems = document.querySelectorAll(".reveal");
  const recipeItems = document.querySelectorAll(".recipes-list .recipe-story[data-category]");
  const recipeFilters = document.querySelectorAll(".recipe-filter");
  const filterEmpty = document.querySelector(".filter-empty");
  const rodizioSlider = document.querySelector(".rodizio-slider");
  let currentSlide = 0;
  let timer;

  const showSlide = (index) => {
    currentSlide = (index + slides.length) % slides.length;
    slides.forEach((slide, slideIndex) => slide.classList.toggle("is-active", slideIndex === currentSlide));
    dots.forEach((dot, dotIndex) => { dot.classList.toggle("is-active", dotIndex === currentSlide); dot.setAttribute("aria-current", dotIndex === currentSlide ? "true" : "false"); });
  };
  const restartTimer = () => { window.clearInterval(timer); timer = window.setInterval(() => showSlide(currentSlide + 1), 6500); };
  dots.forEach((dot, index) => dot.addEventListener("click", () => { showSlide(index); restartTimer(); }));
  showSlide(0);
  restartTimer();

  const revealObserver = new IntersectionObserver((entries, observer) => { entries.forEach((entry) => { if (entry.isIntersecting) { entry.target.classList.add("is-visible"); observer.unobserve(entry.target); } }); }, { threshold: 0.14 });
  revealItems.forEach((item) => revealObserver.observe(item));

  const recipeObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => entry.target.classList.toggle("is-visible", entry.isIntersecting));
  }, { threshold: 0.22 });
  recipeItems.forEach((item) => recipeObserver.observe(item));

  const applyRecipeFilter = (selectedCategory, selectedButton) => {
    let visibleItems = 0;
    recipeFilters.forEach((button) => {
      const isSelected = button === selectedButton;
      button.classList.toggle("is-active", isSelected);
      button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
    recipeItems.forEach((item) => {
      const shouldShow = selectedCategory !== "rodizios" && item.dataset.category === selectedCategory;
      item.hidden = !shouldShow;
      item.classList.toggle("is-filter-visible", shouldShow);
      if (shouldShow) {
        visibleItems += 1;
        item.classList.remove("is-visible");
        window.requestAnimationFrame(() => item.classList.add("is-visible"));
      }
    });
    if (rodizioSlider) rodizioSlider.hidden = selectedCategory !== "rodizios";
    if (selectedCategory === "rodizios") visibleItems = 1;
    if (filterEmpty) filterEmpty.hidden = visibleItems > 0;
  };

  recipeFilters.forEach((filterButton) => filterButton.addEventListener("click", () => {
    applyRecipeFilter(filterButton.dataset.filter, filterButton);
  }));
  const initialRecipeFilter = [...recipeFilters].find((button) => button.dataset.filter === "pratos");
  if (initialRecipeFilter) applyRecipeFilter("pratos", initialRecipeFilter);

  if (rodizioSlider) {
    rodizioSlider.querySelectorAll(".rodizio-gallery").forEach((gallery) => {
      const images = [...gallery.querySelectorAll(".rodizio-gallery-image")];
      const buttons = [...gallery.querySelectorAll(".rodizio-gallery-button")];
      const status = gallery.querySelector(".rodizio-gallery-status");
      let currentImage = 0;

      const showImage = (direction) => {
        currentImage = (currentImage + direction + images.length) % images.length;
        images.forEach((image, imageIndex) => image.classList.toggle("is-active", imageIndex === currentImage));
        if (status) status.innerHTML = `${String(currentImage + 1).padStart(2, "0")} <i>/ ${String(images.length).padStart(2, "0")}</i>`;
      };
      buttons.forEach((button) => button.addEventListener("click", () => {
        showImage(button.dataset.galleryDirection === "previous" ? -1 : 1);
      }));
    });
  }

  const restaurantSlider = document.querySelector(".restaurant-slider");
  if (restaurantSlider) {
    const restaurantSlides = [...restaurantSlider.querySelectorAll(".restaurant-preview-card")];
    const restaurantButtons = [...restaurantSlider.querySelectorAll(".restaurant-slider-button")];
    const restaurantStatus = restaurantSlider.querySelector(".restaurant-slider-status");
    let restaurantIndex = 0;
    let restaurantTimer;

    const showRestaurantSlide = (direction) => {
      const nextIndex = (restaurantIndex + direction + restaurantSlides.length) % restaurantSlides.length;
      if (nextIndex === restaurantIndex) return;
      const currentSlide = restaurantSlides[restaurantIndex];
      currentSlide.classList.remove("is-active");
      currentSlide.classList.add("is-leaving");
      restaurantSlides[nextIndex].classList.add("is-active");
      restaurantSlides[nextIndex].setAttribute("aria-hidden", "false");
      currentSlide.setAttribute("aria-hidden", "true");
      window.setTimeout(() => currentSlide.classList.remove("is-leaving"), 850);
      restaurantIndex = nextIndex;
      if (restaurantStatus) restaurantStatus.innerHTML = `${String(restaurantIndex + 1).padStart(2, "0")} <i>/ 04</i>`;
    };
    const restartRestaurantTimer = () => {
      window.clearInterval(restaurantTimer);
      restaurantTimer = window.setInterval(() => showRestaurantSlide(1), 5200);
    };
    restaurantButtons.forEach((button) => button.addEventListener("click", () => {
      showRestaurantSlide(button.dataset.sliderDirection === "previous" ? -1 : 1);
      restartRestaurantTimer();
    }));
    restartRestaurantTimer();
  }

  const reservationButtons = [...document.querySelectorAll(".table-btn")];
  if (reservationButtons.length) {
    const reservationStatus = document.getElementById("reservation-status");
    const mesasLivres = document.getElementById("mesas-livres");
    const mesasOcupadas = document.getElementById("mesas-ocupadas");
    const reservationModal = document.getElementById("reservation-modal");
    const closeModalButton = document.getElementById("close-modal");
    const stepType = document.getElementById("step-type");
    const stepForm = document.getElementById("step-form");
    const selectedTableNumber = document.getElementById("selected-table-number");
    const mesaIdInput = document.getElementById("mesa_id");
    const tipoInput = document.getElementById("tipo");
    const reservationDateInput = document.getElementById("data_reserva");
    const reservationForm = document.getElementById("reservation-form");

    const updateReservationSummary = () => {
      const total = reservationButtons.length;
      const livres = reservationButtons.filter((button) => button.dataset.disponivel === "true").length;
      const ocupadas = total - livres;

      if (mesasLivres) mesasLivres.textContent = String(livres);
      if (mesasOcupadas) mesasOcupadas.textContent = String(ocupadas);

      if (reservationStatus) {
        if (livres === 0) {
          reservationStatus.textContent = "Salão lotado";
        } else if (ocupadas === 0) {
          reservationStatus.textContent = "Todas as mesas disponíveis";
        } else {
          reservationStatus.textContent = "Algumas mesas ainda estão livres";
        }
      }
    };

    const setMesaState = (button, disponivel) => {
      button.dataset.disponivel = String(disponivel);
      button.classList.toggle("is-available", disponivel);
      button.classList.toggle("is-occupied", !disponivel);
      button.setAttribute("aria-label", `Mesa ${button.dataset.number} ${disponivel ? "disponível" : "reservada"}`);
      button.setAttribute("aria-pressed", String(!disponivel));

      const indicator = button.querySelector(".table-indicator");
      if (indicator) {
        indicator.textContent = disponivel ? "Disponível" : "Reservada";
      }

      if (!disponivel) {
        button.disabled = true;
      }

      updateReservationSummary();
    };

    const openReservationModal = (button) => {
      if (!reservationModal || !button) return;
      const mesaId = button.dataset.id;
      const mesaNumber = button.dataset.number;
      if (mesaIdInput) mesaIdInput.value = mesaId;
      if (selectedTableNumber) selectedTableNumber.textContent = mesaNumber;
      if (tipoInput) tipoInput.value = "";
      if (reservationDateInput) reservationDateInput.value = document.getElementById("reservation-date")?.value || reservationDateInput.value;
      reservationModal.hidden = false;
      stepType.hidden = false;
      stepForm.hidden = true;
      reservationForm.reset();
    };

    const closeReservationModal = () => {
      if (reservationModal) reservationModal.hidden = true;
      stepType.hidden = false;
      stepForm.hidden = true;
    };

    reservationButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.disponivel === "false") return;
        openReservationModal(button);
      });
    });

    closeModalButton?.addEventListener("click", closeReservationModal);
    reservationModal?.addEventListener("click", (event) => {
      if (event.target === reservationModal) closeReservationModal();
    });

    document.querySelectorAll(".experience-option").forEach((option) => {
      option.addEventListener("click", () => {
        const experience = option.dataset.experience;
        if (tipoInput) tipoInput.value = experience;
        stepType.hidden = true;
        stepForm.hidden = false;
      });
    });

    reservationForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(reservationForm);
      const mesaId = formData.get("mesa_id");

      try {
        const response = await fetch(`/reservas/${mesaId}/confirmar`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
          throw new Error(data.message || "Não foi possível confirmar a reserva.");
        }

        const reservaButton = document.querySelector(`.table-btn[data-id="${mesaId}"]`);
        if (reservaButton) {
          setMesaState(reservaButton, false);
        }

        closeReservationModal();
        window.location.href = data.redirect;
      } catch (error) {
        alert(error.message || "Erro ao confirmar reserva.");
      }
    });

    updateReservationSummary();
  }

  const adminMesaButtons = [...document.querySelectorAll(".admin-mesa-btn")];
  if (adminMesaButtons.length) {
    const adminTableDate = document.getElementById("admin-table-date");
    const adminTableModal = document.getElementById("admin-table-modal");
    const adminTableModalClose = document.getElementById("admin-table-modal-close");
    const adminTableDetails = document.getElementById("admin-table-details");

    const showTableDetails = (data) => {
      if (!adminTableDetails) return;
      if (!data.reservas.length) {
        adminTableDetails.innerHTML = `<strong>Mesa ${data.mesa}</strong><p>Livre em ${data.data}.</p>`;
      } else {
        adminTableDetails.innerHTML = `<strong>Mesa ${data.mesa} · ${data.data}</strong>${data.reservas.map((reserva) => `
          <div class="admin-table-reservation">
            <b>${reserva.nome}</b>
            <span>${reserva.horario} · ${reserva.pessoas} pessoa(s)</span>
            <span>${reserva.telefone} · ${reserva.email}</span>
          </div>`).join("")}`;
      }
      if (adminTableModal) adminTableModal.hidden = false;
    };

    const refreshAdminTableColors = async () => {
      if (!adminTableDate?.value) return;
      const response = await fetch(`/admin/mesas-disponiveis?data=${encodeURIComponent(adminTableDate.value)}`);
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || "Não foi possível atualizar as mesas.");
      data.mesas.forEach((mesa) => {
        const button = document.querySelector(`.admin-mesa-btn[data-mesa-id="${mesa.id}"]`);
        button?.classList.toggle("is-available", !mesa.tem_agendamento);
        button?.classList.toggle("is-occupied", mesa.tem_agendamento);
      });
    };

    adminMesaButtons.forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          const response = await fetch(`/admin/mesa/${button.dataset.mesaId}/reservas?data=${encodeURIComponent(adminTableDate.value)}`);
          const data = await response.json();
          if (!response.ok || !data.success) throw new Error(data.message || "Não foi possível consultar a mesa.");
          showTableDetails(data);
        } catch (error) {
          alert(error.message || "Erro ao consultar a mesa.");
        }
      });
    });

    adminTableDate?.addEventListener("change", async () => {
      try {
        await refreshAdminTableColors();
        if (adminTableModal) adminTableModal.hidden = true;
      } catch (error) {
        alert(error.message || "Erro ao atualizar as mesas.");
      }
    });

    adminTableModalClose?.addEventListener("click", () => {
      if (adminTableModal) adminTableModal.hidden = true;
    });
    adminTableModal?.addEventListener("click", (event) => {
      if (event.target === adminTableModal) adminTableModal.hidden = true;
    });
  }

  const adminCardapioForm = document.getElementById("admin-cardapio-form");
  if (adminCardapioForm) {
    const itemsList = document.querySelector(".admin-itens");

    const renderAdminItem = (item) => {
      const article = document.createElement("article");
      article.className = "admin-item";
      article.dataset.itemId = String(item.id);
      article.innerHTML = `
        <div>
          <span class="item-category">${item.categoria}</span>
          <h3>${item.titulo}</h3>
          <p>${item.descricao}</p>
        </div>
        <button type="button" class="delete-item" data-delete-id="${item.id}">Excluir</button>
      `;

      article.querySelector(".delete-item").addEventListener("click", async () => {
        try {
          const response = await fetch(`/admin/cardapio/${item.id}/delete`, { method: "POST" });
          const data = await response.json();

          if (!response.ok || !data.success) {
            throw new Error(data.message || "Não foi possível remover o item.");
          }

          article.remove();
        } catch (error) {
          alert(error.message || "Erro ao remover item do cardápio.");
        }
      });

      itemsList.appendChild(article);
    };

    adminCardapioForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const formData = new FormData(adminCardapioForm);

      try {
        const response = await fetch("/admin/cardapio", {
          method: "POST",
          body: formData,
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.message || "Não foi possível salvar o item.");
        }

        const item = {
          id: data.item.id,
          titulo: data.item.titulo,
          categoria: data.item.categoria,
          descricao: formData.get("descricao").toString(),
        };

        renderAdminItem(item);
        adminCardapioForm.reset();
      } catch (error) {
        alert(error.message || "Erro ao salvar item do cardápio.");
      }
    });

    document.querySelectorAll(".admin-item .delete-item").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = button.dataset.deleteId;
        const article = button.closest(".admin-item");

        try {
          const response = await fetch(`/admin/cardapio/${itemId}/delete`, { method: "POST" });
          const data = await response.json();

          if (!response.ok || !data.success) {
            throw new Error(data.message || "Não foi possível remover o item.");
          }

          article.remove();
        } catch (error) {
          alert(error.message || "Erro ao remover item do cardápio.");
        }
      });
    });
  }

  const adminReservaForm = document.getElementById("admin-reserva-form");
  const adminReservaDate = document.getElementById("admin-reserva-data");
  const adminReservaMesa = document.getElementById("admin-reserva-mesa");

  const updateAdminMesaOptions = async () => {
    if (!adminReservaDate || !adminReservaMesa || !adminReservaDate.value) return;
    const selectedMesa = adminReservaMesa.value;
    try {
      const response = await fetch(`/admin/mesas-disponiveis?data=${encodeURIComponent(adminReservaDate.value)}`);
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || "Não foi possível consultar as mesas.");

      adminReservaMesa.replaceChildren();
      data.mesas.filter((mesa) => mesa.disponivel).forEach((mesa) => {
        const option = document.createElement("option");
        option.value = String(mesa.id);
        option.textContent = `Mesa ${mesa.numero}`;
        adminReservaMesa.appendChild(option);
      });

      if (selectedMesa && [...adminReservaMesa.options].some((option) => option.value === selectedMesa)) {
        adminReservaMesa.value = selectedMesa;
      }
      if (!adminReservaMesa.options.length) {
        const option = document.createElement("option");
        option.textContent = "Nenhuma mesa disponível nesta data";
        option.disabled = true;
        option.selected = true;
        adminReservaMesa.appendChild(option);
      }
    } catch (error) {
      alert(error.message || "Erro ao consultar mesas disponíveis.");
    }
  };

  adminReservaDate?.addEventListener("change", updateAdminMesaOptions);
  updateAdminMesaOptions();

  adminReservaForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const response = await fetch("/admin/reservas", { method: "POST", body: new FormData(adminReservaForm) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || "Não foi possível adicionar a reserva.");
      window.location.reload();
    } catch (error) {
      alert(error.message || "Erro ao adicionar reserva.");
    }
  });

  document.querySelectorAll(".cancel-reservation").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!window.confirm("Cancelar este agendamento?")) return;
      try {
        const response = await fetch(`/admin/reservas/${button.dataset.reservaId}/cancelar`, { method: "POST" });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "Não foi possível cancelar a reserva.");
        button.closest(".admin-reserva")?.remove();
      } catch (error) {
        alert(error.message || "Erro ao cancelar reserva.");
      }
    });
  });
});

