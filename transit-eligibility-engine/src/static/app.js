document.addEventListener('DOMContentLoaded', function(){
  const form = document.getElementById('resolveForm');
  const address = document.getElementById('address');
  const results = document.getElementById('results');

  function render(resp){
    results.innerHTML = '';
    if(!resp || !resp.candidates || resp.candidates.length===0){
      results.innerHTML = '<div class="card">לא נמצאו מועמדים</div>';
      return;
    }

    const top = resp.top_candidate;
    // Determine eligibility from rationale (server returns boolean there)
    const isEligible = resp && resp.rationale && resp.rationale.is_eligible === true;
    // Top card: eligibility
    const topCard = document.createElement('div');
    topCard.className = 'card ' + (isEligible ? 'eligible' : 'not-eligible');
    if(isEligible){
      topCard.innerHTML = `<div><strong>✓ נמצאה זכאות לפרופיל גיאוגרפי (50% הנחה)</strong></div><div class="small">${top.locality_name} — ${top.locality_code}</div><div class="rationale">${resp.rationale && resp.rationale.reason ? resp.rationale.reason : ''}</div>`;
    } else {
      topCard.innerHTML = `<div><strong>לא נמצאה זכאות לפרופיל גיאוגרפי</strong></div><div class="small">${top.locality_name} — ${top.locality_code}</div><div class="rationale">${resp.rationale && resp.rationale.reason ? resp.rationale.reason : ''}</div>`;
    }
    results.appendChild(topCard);

    // Candidates list
    const tpl = document.getElementById('candidate-template');
    resp.candidates.forEach(c => {
      const node = tpl.content.cloneNode(true);
      node.querySelector('.candidate-name').textContent = c.locality_name;
      node.querySelector('.candidate-meta').textContent = c.locality_code;
      const btn = node.querySelector('.select-btn');
      btn.addEventListener('click', ()=>{
        address.value = c.locality_name;
        // re-query as chosen
      });
      results.appendChild(node);
    });

    // Developer JSON (hidden by default) with proper LTR styling
    if(window.location.search.indexOf('dev')!==-1){
      const pre = document.createElement('div');
      pre.className = 'card json-dev';
      pre.setAttribute('dir','ltr');
      pre.style.textAlign = 'left';
      pre.textContent = JSON.stringify(resp, null, 2);
      results.appendChild(pre);
    }
  }

  form.addEventListener('submit', async function(e){
    e.preventDefault();
    results.innerHTML = '<div class="card">טוען…</div>';
    try{
      const resp = await fetch('/resolve',{
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({address: address.value})
      });
      if(!resp.ok){
        const t = await resp.text();
        results.innerHTML = `<div class="card">שגיאה: ${resp.status} ${t}</div>`;
        return;
      }
      const data = await resp.json();
      render(data);
    }catch(err){
      results.innerHTML = `<div class="card">שגיאה: ${err.message}</div>`;
    }
  });

});
