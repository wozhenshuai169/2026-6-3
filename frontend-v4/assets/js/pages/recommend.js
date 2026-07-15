/**
 * Recommend — Route Recommendation Page
 */
(function(){
  'use strict';
  var A=window.Aurelian,api=A.api,ui=A.ui,st=A.state;
  var SCENIC_AREA_ID='lingshan_shengjing';
  var preferences={interests:[],timeLimit:60,physicalStrength:'medium',elderly:false,children:false,avoidCrowd:false};

  function init(){
    A.auth.guardRole('visitor', function(){
      loadScenicContext();
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
    });
  }

  function loadScenicContext(){
    var card=document.getElementById('scenic-context');
    var status=document.getElementById('map-status');
    api.get('/map/scenic-areas/current').then(function(r){
      if(!r.ok||!r.data||!r.data.current){
        status.className='status map-status-error';
        status.textContent='景区信息暂时无法获取';
        card.innerHTML='<div class="scenic-error"><strong>暂时无法读取景区信息</strong><p>请稍后重试，或先返回导览页继续使用其他功能。</p></div>';
        return;
      }

      var data=r.data;
      var current=data.current;
      var related=data.relatedScenicAreas||[];
      var pois=(data.pois||[]).slice(0,5);
      status.className='status';
      status.textContent='景区信息已更新';

      var relatedHtml=related.map(function(area){
        var closed=area.temporarilyClosed?'<span class="poi-warning">当前暂停开放</span>':'';
        return '<div class="related-area"><div><small>独立景区，不加入本路线</small><strong>'+
          ui.escapeHtml(area.scenicAreaName)+'</strong></div>'+closed+'</div>';
      }).join('');

      var poiHtml=pois.map(function(poi){
        return '<span class="live-poi-chip"><span class="material-icons">place</span>'+
          ui.escapeHtml(poi.name)+'</span>';
      }).join('');

      card.innerHTML='<div class="scenic-card-head"><div><small>当前主景区</small><h3>'+
        ui.escapeHtml(current.scenicAreaName)+'</h3></div><span class="verified-badge">景区资料</span></div>'+
        '<p class="scenic-address"><span class="material-icons">location_on</span>'+
        ui.escapeHtml(current.city+current.district+' · '+current.address)+'</p>'+
        '<div class="coordinate-grid"><div><small>所在区域</small><strong>'+ui.escapeHtml(current.district||'滨湖区')+'</strong></div><div><small>参观入口</small><strong>'+ui.escapeHtml(current.entranceLocation||current.address||'请以现场指引为准')+'</strong></div></div>'+
        '<div class="live-poi-list">'+poiHtml+'</div>'+relatedHtml+
        '<p class="source-note">开放情况和入口位置可能临时调整，请以景区现场指引为准。</p>';
    });
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
    var placeholder=document.getElementById('route-placeholder');
    if(placeholder) placeholder.classList.add('hidden');
    document.getElementById('result-area').classList.add('hidden');
    document.getElementById('loading-area').classList.remove('hidden');
    btn.disabled=true;
    btn.innerHTML='<div class="loading-spinner"></div> 正在安排...';

    api.post('/recommend/route',{
      roomId:st.get('roomId')||'demo',
      userId:st.get('userId')||'demo',
      scenicAreaId:SCENIC_AREA_ID,
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
      btn.innerHTML='<span class="material-icons text-[18px]">route</span> 查看推荐路线';

      if(r.ok&&r.data){
        showResult(r.data);
      }else{
        if(placeholder) placeholder.classList.remove('hidden');
        ui.toast('暂时无法安排路线，请稍后重试','error');
      }
    });
  }

  function showResult(data){
    document.getElementById('result-route-name').textContent=data.routeName||'灵山胜境推荐路线';
    document.getElementById('result-time').innerHTML='<span class="material-icons text-[14px]">schedule</span> 约'+(data.estimatedTime||0)+'分钟';
    document.getElementById('result-distance').innerHTML='<span class="material-icons text-[14px]">directions_walk</span> '+Number(data.distance||0).toFixed(2)+'公里';
    var difficultyLabels={low:'轻松',medium:'适中',high:'较多步行'};
    document.getElementById('result-difficulty').textContent='步行强度：'+(difficultyLabels[data.difficulty]||'适中');
    document.getElementById('result-source').textContent='园内步行路线';
    document.getElementById('result-score').textContent='已按你的偏好安排';

    var spotsEl=document.getElementById('result-spots');
    var spots=data.spots||[];
    spotsEl.innerHTML=spots.map(function(s,i){
      var isLast=i===spots.length-1;
      var closed=s.temporarilyClosed?
        '<span class="poi-warning">当前暂停开放</span>':'';
      return '<div class="relative"><div class="absolute -left-[29px] w-4 h-4 rounded-full bg-primary border-2 border-white"></div>'+
        '<div class="route-poi-card"><div class="route-poi-title"><span>'+(i+1)+'. '+
        ui.escapeHtml(s.spotName||s.spotId)+'</span>'+closed+'</div>'+
        '<div class="route-poi-meta"><span>建议停留约 '+Number(s.stayMinutes||0)+' 分钟</span></div>'+
        '<p>'+ui.escapeHtml(s.address||'具体位置请以园内指引为准')+'</p></div>'+
        (isLast?'':'<div class="h-4 border-l-2 border-orange-soft ml-[-21px]"></div>')+'</div>';
    }).join('');

    var legs=data.instructions||[];
    var evidence=document.getElementById('result-map-note');
    evidence.innerHTML='<div class="map-evidence-head"><strong>分段步行参考</strong><span>预计时间可能受现场人流影响</span></div>'+
      (legs.length?legs.map(function(leg){
        return '<div class="route-leg"><span>'+ui.escapeHtml(leg.fromSpot)+' → '+
          ui.escapeHtml(leg.toSpot)+'</span><strong>'+Number(leg.distanceMeters||0)+' 米 · 约 '+
          Number(leg.durationMinutes||0)+' 分钟</strong></div>';
      }).join(''):'<p>当前路线没有需要计算的相邻路段。</p>');

    document.getElementById('result-reason').innerHTML='<span class="material-icons text-[16px] text-primary align-text-bottom mr-1">lightbulb</span> '+ui.escapeHtml(data.reason||'该路线根据你的时间、兴趣和体力安排。');

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
