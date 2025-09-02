
(function(){
  window.pvAuthBadge = function(){
    try{
      const tok = localStorage.getItem('pv_token');
      const badge = document.getElementById('pv-auth-badge');
      if (badge) badge.textContent = tok ? 'logado' : 'deslogado';
      const btn = document.getElementById('pv-logout');
      if (btn){ btn.onclick = () => { localStorage.removeItem('pv_token'); location.href = '/app/'; }; }
    }catch(e){}
  };
  window.pvGetToken = function(){ try{ return localStorage.getItem('pv_token'); }catch(e){ return null; } };
  window.pvAuthHeaders = function(token){ const h={}; if (token) h['Authorization']='Bearer '+token; return h; };
  window.pvFmt = function(v){ const n=Number(v||0); return n.toLocaleString('pt-BR',{style:'currency',currency:'BRL'}); };
  window.pvToast = function(msg){ alert(msg); };
  window.pvGetQS = function(sel){ const f=document.querySelector(sel); if(!f) return {}; const d=new FormData(f); const o={}; for(const [k,v] of d.entries()){ if(v) o[k]=v; } return o; };
})();
