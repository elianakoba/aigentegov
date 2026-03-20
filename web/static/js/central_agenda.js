document.addEventListener("DOMContentLoaded", () => {
  const hoje = new Date();
  const anoAtual = hoje.getFullYear();
  const mesAtual = hoje.getMonth() + 1;

  const filtros = {
    modo: "todos",
    ano: anoAtual,
    mes: mesAtual,
    id_servicoespecializado: null,
    id_profissional: null,
    id_departamento: null,
    id_pessoa: null,
  };

  let diaSelecionado = null;
  let slotSelecionado = null;
  let cidadaoSelecionado = null; // ⭐ cidadão do modal

  inicializarCampos();
  buscarAgenda();

  document.querySelectorAll(
    "#filtro-servico, #filtro-profissional, #filtro-unidade, #filtro-idpessoa, #filtro-modo, #filtro-ano, #filtro-mes"
  ).forEach(el => {
    el?.addEventListener("change", () => {
      atualizarFiltros();
      diaSelecionado = null;
      buscarAgenda();
    });
  });

  function inicializarCampos() {
    document.getElementById("filtro-ano").value ||= anoAtual;
    document.getElementById("filtro-mes").value ||= mesAtual;
  }

  function atualizarFiltros() {
    filtros.modo = valorOuPadrao("filtro-modo", "todos");
    filtros.ano = Number(valorOuPadrao("filtro-ano", anoAtual));
    filtros.mes = Number(valorOuPadrao("filtro-mes", mesAtual));
    filtros.id_servicoespecializado = normalizarInt("filtro-servico");
    filtros.id_profissional = normalizarInt("filtro-profissional");
    filtros.id_departamento = normalizarInt("filtro-unidade");
    filtros.id_pessoa = normalizarInt("filtro-idpessoa");
  }

  function valorOuPadrao(id, padrao) {
    return document.getElementById(id)?.value || padrao;
  }

  function normalizarInt(id) {
    const v = document.getElementById(id)?.value;
    return v ? Number(v) : null;
  }

  function montarQuery() {
    const p = new URLSearchParams();
    Object.entries(filtros).forEach(([k, v]) => v !== null && p.append(k, v));
    return p.toString();
  }

  function buscarAgenda(dia = null) {
    let url;
    if (dia !== null) {
      filtros.modo = "todos";
      diaSelecionado = dia;
      url = `/api/central_agenda/visao?${montarQuery()}&dia=${dia}`;
    } else {
      diaSelecionado = null;
      url = `/api/central_agenda/visao?${montarQuery()}`;
    }

    fetch(url)
      .then(r => r.json())
      .then(d => {
        renderCalendario(d.calendario);
        renderLista(d.horarios);
      });
  }

  // =====================================================
  // MODAL – AGENDAR
  // =====================================================

  function abrirModalAgendar(h) {
    slotSelecionado = h;
    cidadaoSelecionado = null;

    document.getElementById("modal-hora").textContent = h.hora;
    document.getElementById("modal-especialidade").textContent = h.especialidade;
    document.getElementById("modal-profissional").textContent = h.profissional;
    document.getElementById("modal-unidade").textContent = h.unidade;

    document.getElementById("busca-cidadao").value = "";
    document.getElementById("card-cidadao").classList.add("d-none");
    document.getElementById("btn-confirmar-agendamento").disabled = true;

    new bootstrap.Modal(
      document.getElementById("modalAgendar")
    ).show();
  }

  // =====================================================
  // BUSCAR CIDADÃO
  // =====================================================

  async function buscarCidadao() {
    const doc = document.getElementById("busca-cidadao").value.trim();
    if (!doc) return alert("Informe CPF ou registro.");

    try {
      const r = await fetch(`/api/cidadao/buscar?documento=${encodeURIComponent(doc)}`);
      if (!r.ok) throw new Error();

      const c = await r.json();
      cidadaoSelecionado = c;

      document.getElementById("cidadao-nome").textContent = c.nome || "";
      document.getElementById("cidadao-doc").textContent = c.documento || "";
      document.getElementById("cidadao-contato").textContent = c.contato || "";
      document.getElementById("cidadao-endereco").textContent = c.endereco || "";

      document.getElementById("card-cidadao").classList.remove("d-none");
      document.getElementById("btn-confirmar-agendamento").disabled = false;

    } catch {
      alert("Cidadão não encontrado.");
    }
  }

  document
    .getElementById("btn-buscar-cidadao")
    ?.addEventListener("click", buscarCidadao);

  // =====================================================
  // CONFIRMAR AGENDAMENTO
  // =====================================================

  async function confirmarAgendamento() {
    if (!slotSelecionado || !cidadaoSelecionado) return;

    await fetch("/api/central_agenda/agendar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id_departamentoservicoespecializado: slotSelecionado.id_departamentoservicoespecializado,
        dataagenda: slotSelecionado.data_iso,
        horaagenda: slotSelecionado.hora,
        id_pessoaagenteia: cidadaoSelecionado.id_pessoaagenteia,
      }),
    });

    bootstrap.Modal.getInstance(
      document.getElementById("modalAgendar")
    ).hide();

    buscarAgenda(diaSelecionado);
  }

  document
    .getElementById("btn-confirmar-agendamento")
    ?.addEventListener("click", confirmarAgendamento);

  // =====================================================
  // CANCELAR
  // =====================================================

  async function cancelarSlot(h) {
    if (!h.id) return alert("Agendamento inválido");
    if (!confirm("Confirma o cancelamento?")) return;

    await fetch("/api/central_agenda/cancelar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_agendaservicoespecializado: h.id }),
    });

    buscarAgenda(diaSelecionado);
  }

  // =====================================================
  // RENDER
  // =====================================================

  function renderCalendario(cal) {
    const c = document.getElementById("calendario");
    c.innerHTML = "";
    cal.forEach(d => {
      const el = document.createElement("div");
      el.className = "dia-calendario";
      if (d.qtd > 0) {
        el.classList.add("disponivel");
        el.onclick = () => buscarAgenda(d.dia);
      }
      el.innerHTML = `<strong>${d.dia}</strong><span>${d.qtd} vagas</span>`;
      c.appendChild(el);
    });
  }

  function renderLista(horarios) {
    const c = document.getElementById("lista-horarios");
    c.innerHTML = "";

    horarios.forEach(h => {
      const el = document.createElement("div");
      el.className = "linha-horario";

      el.innerHTML = `
        <span>${h.hora}</span>
        <span>${h.profissional}</span>
        <span>${h.especialidade}</span>
        <span>${h.unidade}</span>
        <span>
          ${
            h.disponivel
              ? `<button class="btn btn-primary btn-sm">Agendar</button>`
              : `<button class="btn btn-danger btn-sm">Cancelar</button>`
          }
        </span>
      `;

      el.querySelector("button").onclick = () =>
        h.disponivel ? abrirModalAgendar(h) : cancelarSlot(h);

      c.appendChild(el);
    });
  }
});
