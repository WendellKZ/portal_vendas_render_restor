(function () {
  function onlyDigits(s) { return (s || '').replace(/\D+/g, ''); }
  function message(text, isError) {
    const area = document.querySelector('#messages') || document.body;
    const div = document.createElement('div');
    div.style.padding = '8px 12px';
    div.style.margin = '8px 0';
    div.style.borderRadius = '6px';
    div.style.background = isError ? '#ffebe9' : '#e6ffed';
    div.style.border = '1px solid ' + (isError ? '#ff8182' : '#34d058');
    div.textContent = text;
    area.prepend(div);
    setTimeout(() => div.remove(), 6000);
  }
  function fillIfExists(id, value) {
    const el = document.getElementById(id);
    if (el && value != null && value !== '') el.value = value;
  }
  function addButton() {
    const cnpjInput = document.getElementById('id_cnpj');
    if (!cnpjInput) return;
    if (document.getElementById('btn-cnpj-lookup')) return;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'btn-cnpj-lookup';
    btn.className = 'button';
    btn.style.marginLeft = '8px';
    btn.textContent = 'Buscar CNPJ';
    cnpjInput.insertAdjacentElement('afterend', btn);

    btn.addEventListener('click', async () => {
      const raw = cnpjInput.value;
      const cnpj = onlyDigits(raw);
      if (cnpj.length !== 14) { message('CNPJ inválido. Use 14 dígitos.', true); return; }
      btn.disabled = true; btn.textContent = 'Buscando...';
      try {
        const resp = await fetch(`/api/cnpj/lookup/?cnpj=${cnpj}`, { credentials: 'same-origin' });
        if (!resp.ok) { const err = await resp.json().catch(() => ({})); throw new Error(err.error || err.detail || 'Falha ao consultar CNPJ'); }
        const json = await resp.json();
        if (!json.ok) throw new Error(json.error || 'Falha na consulta');
        const d = json.data || {};
        fillIfExists('id_nome', d.nome_fantasia || d.razao_social);
        fillIfExists('id_cidade', d.municipio);
        fillIfExists('id_uf', d.uf);
        fillIfExists('id_cep', d.cep);
        fillIfExists('id_logradouro', d.logradouro);
        fillIfExists('id_numero', d.numero);
        fillIfExists('id_complemento', d.complemento);
        fillIfExists('id_bairro', d.bairro);
        message('Dados do CNPJ preenchidos com sucesso!');
      } catch (e) { console.error(e); message(String(e.message || e), true); }
      finally { btn.disabled = false; btn.textContent = 'Buscar CNPJ'; }
    });
  }
  document.addEventListener('DOMContentLoaded', addButton);
})();