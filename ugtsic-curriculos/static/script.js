(function(){
  const form = document.getElementById('cvForm');
  const statusEl = document.getElementById('status');
  const arquivoInput = document.getElementById('arquivo');
  const submitBtn = form.querySelector('button[type="submit"]');

  function setStatus(msg, cls){
    statusEl.textContent = msg || '';
    statusEl.className = cls || '';
  }

  function addError(input, msg){
    input.classList.add('field-error');
    let hint = input.parentElement.querySelector('.error-msg');
    if(!hint){
      hint = document.createElement('div');
      hint.className = 'error-msg';
      input.parentElement.appendChild(hint);
    }
    hint.textContent = msg;
  }
  function clearError(input){
    input.classList.remove('field-error');
    const hint = input.parentElement.querySelector('.error-msg');
    if(hint) hint.remove();
  }
  function clearAllErrors(){
    form.querySelectorAll('.field-error').forEach(el => el.classList.remove('field-error'));
    form.querySelectorAll('.error-msg').forEach(el => el.remove());
  }

  function validateFile(){
    const f = arquivoInput.files && arquivoInput.files[0];
    if(!f){ addError(arquivoInput, 'Selecione um arquivo (.pdf, .doc, .docx) até 1MB'); return false; }
    const okExt = ['pdf','doc','docx'];
    const ext = (f.name.split('.').pop() || '').toLowerCase();
    if(!okExt.includes(ext)){ addError(arquivoInput, 'Extensão inválida. Use .pdf, .doc ou .docx'); return false; }
    if(f.size > 1 * 1024 * 1024){ addError(arquivoInput, 'Arquivo excede 1MB'); return false; }
    clearError(arquivoInput);
    return true;
  }

  // limpa erro ao digitar
  form.addEventListener('input', (e) => {
    if(e.target.matches('input, select, textarea')) clearError(e.target);
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAllErrors();
    setStatus('Enviando...', '');

  
    let ok = true;
    form.querySelectorAll('[required]').forEach((el) => {
      if(!el.value?.trim()){
        ok = false;
        addError(el, 'Campo obrigatório');
      }
    });
    if(!validateFile()) ok = false;

    if(!ok){
      setStatus('Preencha os campos obrigatórios corretamente.', 'error');
      return;
    }

    submitBtn.disabled = true;
    try{
      const fd = new FormData(form);
      const res = await fetch('/submit', { method: 'POST', body: fd });
      const data = await res.json();

      if(!res.ok || !data.ok){
        setStatus(data.error || 'Falha no envio.', 'error');
        submitBtn.disabled = false;
        return;
      }
      setStatus(data.mensagem || 'Candidatura enviada com sucesso!', 'success');
      form.reset();
    }catch(err){
      console.error(err);
      setStatus('Erro de rede. Tente novamente.', 'error');
    }finally{
      submitBtn.disabled = false;
    }
  });
})();
