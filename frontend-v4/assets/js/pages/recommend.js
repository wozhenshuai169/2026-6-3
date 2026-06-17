/**
 * Recommend — Route Recommendation Page
 */
(function(){
  'use strict';
  var A=window.Aurelian,api=A.api,ui=A.ui,st=A.state;
  var preferences={interests:[],timeLimit:60,physicalStrength:'medium',elderly:false,children:false,avoidCrowd:false};

  function init(){
    A.auth.guard();

    // Tag toggle handlers
    bindTagGroup('interest-tags',function(active){
      preferences.interests=active;
    });
    bindTagGroup('time-options',function(active){
      preferences.timeLimit=parseInt(active[0])||60;
    },true);
    bindTagGroup('stamina-options',function(active){
      preferences.physicalStrength=active[0]||'medium';
    },true);
    bindTagGroup('companion-tags',function(active){
      preferences.elderly=active.indexOf('elderly')!==-1;
      preferences.children=active.indexOf('children')!==-1;
      preferences.avoidCrowd=active.indexOf('crowd')!==-1;
    });

    document.getElementById('btn-generate').addEventListener('click',generateRoute);
  }

  function bindTagGroup(containerId,callback,singleSelect){
    var container=document.getElementById(containerId);
    if(!container) return;
    var buttons=container.querySelectorAll('.tag-btn');
    var active=[];

    // Init active from tag-active class
    buttons.forEach(function(btn){
      if(btn.classList.contains('tag-active')) active.push(btn.getAttribute('data-val'));
    });

    buttons.forEach(function(btn){
      btn.addEventListener('click',function(){
        var val=this.getAttribute('data-val');
        if(singleSelect){
          buttons.forEach(function(b){b.classList.remove('tag-active');});
          this.classList.add('tag-active');
          callback([val]);
        }else{
          if(this.classList.contains('tag-active')){
            this.classList.remove('tag-active');
            active=active.filter(function(v){return v!==val;});
          }else{
            this.classList.add('tag-active');
            active.push(val);
          }
          callback(active);
        }
      });
    });
  }

  function generateRoute(){
    var btn=document.getElementById('btn-generate');
    document.getElementById('result-area').classList.add('hidden');
    document.getElementById('loading-area').classList.remove('hidden');
    btn.disabled=true;
    btn.innerHTML='<div class="loading-spinner"></div> 分析中...';

    api.post('/recommend/route',{
      roomId:st.get('roomId')||'demo',
      userId:st.get('userId')||'demo',
      preferences:{
        interest:preferences.interests,
        timeLimit:preferences.timeLimit,
        physicalStrength:preferences.physicalStrength,
        withChildren:preferences.children,
        withElderly:preferences.elderly,
        avoidCrowd:preferences.avoidCrowd
      }
    }).then(function(r){
      document.getElementById('loading-area').classList.add('hidden');
      btn.disabled=false;
      btn.innerHTML='<span class="material-symbols-outlined text-[18px]">route</span> 生成推荐路线';

      if(r.ok&&r.data){
        showResult(r.data);
      }else{
        ui.toast((r.error&&r.error.message)||'推荐失败，请重试','error');
      }
    });
  }

  function showResult(data){
    document.getElementById('result-route-name').textContent=data.routeName||'推荐路线';
    document.getElementById('result-time').innerHTML='<span class="material-symbols-outlined text-[14px]">schedule</span> 约'+(data.estimatedTime||0)+'分钟';
    document.getElementById('result-difficulty').textContent='难度：'+(data.difficulty||'medium');
    document.getElementById('result-score').textContent='★ '+(data.score||0).toFixed(1);

    // Timeline
    var spotsEl=document.getElementById('result-spots');
    var spots=data.spots||[];
    spotsEl.innerHTML=spots.map(function(s,i){
      var isLast=i===spots.length-1;
      return '<div class="relative"><div class="absolute -left-[29px] w-4 h-4 rounded-full bg-primary border-2 border-white"></div><div class="bg-background border border-border rounded-lg p-3 ml-3"><div class="text-sm font-medium">'+(i+1)+'. '+ui.escapeHtml(s.spotName||s.spotId)+'</div><div class="text-xs text-text-secondary mt-1">停留约 '+s.stayMinutes+' 分钟</div></div>'+(isLast?'':'<div class="h-4 border-l-2 border-orange-soft ml-[-21px]"></div>')+'</div>';
    }).join('');

    // Reason
    document.getElementById('result-reason').innerHTML='<span class="material-symbols-outlined text-[16px] text-primary align-text-bottom mr-1">lightbulb</span> '+ui.escapeHtml(data.reason||'该路线根据你的偏好生成。');

    // Matched
    var matched=data.matchedPreferences||[];
    var matchedEl=document.getElementById('result-matched');
    matchedEl.innerHTML=matched.length?matched.map(function(p){
      return '<span class="px-2 py-0.5 bg-[#FDF6F1] border border-primary/10 rounded-full text-xs text-primary">✓ '+ui.escapeHtml(p)+'</span>';
    }).join(''):'';

    document.getElementById('result-area').classList.remove('hidden');
    document.getElementById('result-area').scrollIntoView({behavior:'smooth'});
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
