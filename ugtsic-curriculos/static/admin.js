(function(){
  const btn = document.getElementById('btnCarregar');
  const tokenInput = document.getElementById('token');
  const statusEl = document.getElementById('status');
  const linhas = document.getElementById('linhas');

  function setStatus(msg){ statusEl.textContent = msg || ''; }

  function linhaVazia(msg){
    linhas.innerHTML = `<tr><td colspan="9" class="muted">${msg}</td></tr>`;
  }

  function render(rows, token){
    if(!rows || rows.length === 0){
      linhaVazia('Nenhuma candidatura encontrada.');
      return;
    }
    linhas.innerHTML = rows.map(r => {
      const dt = (r.enviado_em || '').replace('T',' ').replace('Z','');
      const url = `/api/download/${r.id}?token=${encodeURIComponent(token)}`;
      return `
        <tr>
          <td>${r.id}</td>
          <td>${escapeHtml(r.nome || '')}</td>
          <td>${escapeHtml(r.email || '')}</td>
          <td>${escapeHtml(r.telefone || '')}</td>
          <td>${escapeHtml(r.cargo || '')}</td>
          <td><span class="pill">${escapeHtml(r.escolaridade || '')}</span></td>
          <td class="nowrap">${escapeHtml(dt)}</td>
          <td><a class="link" href="${url}" target="_blank" rel="noopener">Baixar</a></td>
          <td>${escapeHtml(r.ip || '')}</td>
        </tr>`;
    }).join('');
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>"']/g, m => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[m]));
  }

  btn.addEventListener('click', async () => {
    const token = tokenInput.value.trim();
    if(!token){ setStatus('Informe o token.'); return; }
    setStatus('Carregando…');
    linhaVazia('Carregando…');

    try{
      const res = await fetch(`/api/candidaturas?token=${encodeURIComponent(token)}`);
      if(res.status === 401){ setStatus('Token inválido.'); linhaVazia('Token inválido.'); return; }
      if(!res.ok){ setStatus('Erro ao buscar dados.'); linhaVazia('Erro ao buscar dados.'); return; }
      const data = await res.json();
      if(!data.ok){ setStatus('Falha na API.'); linhaVazia('Falha na API.'); return; }
      render(data.rows, token);
      setStatus(`Carregado: ${data.rows.length} registro(s).`);
    }catch(e){
      console.error(e);
      setStatus('Erro de rede.');
      linhaVazia('Erro de rede.');
    }
  });
})();
