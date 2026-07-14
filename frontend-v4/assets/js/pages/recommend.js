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

  function coordinateText(longitude,latitude){
    if(typeof longitude!=='number'||typeof latitude!=='number') return '坐标未返回';
    return longitude.toFixed(6)+', '+latitude.toFixed(6);
  }

  function loadScenicContext(){
    var card=document.getElementById('scenic-context');
    var status=document.getElementById('map-status');
    api.get('/map/scenic-areas/current').then(function(r){
      if(!r.ok||!r.data||!r.data.current){
        status.className='status map-status-error';
        status.textContent='高德地图连接失败';
        card.innerHTML='<div class="scenic-error"><strong>未取得真实地图数据</strong><p>'+
          ui.escapeHtml((r.error&&r.error.message)||'请确认后端网络和高德 Key。')+
          '</p><small>系统不会改用 Mock 数据。</small></div>';
        return;
      }

      var data=r.data;
      var current=data.current;
      var related=data.relatedScenicAreas||[];
      var pois=(data.pois||[]).slice(0,5);
      status.className='status';
      status.textContent='高德真实数据已连接';

      var relatedHtml=related.map(function(area){
        var closed=area.temporarilyClosed?'<span class="poi-warning">高德标注：暂停开放</span>':'';
        return '<div class="related-area"><div><small>独立景区，不加入本路线</small><strong>'+
          ui.escapeHtml(area.scenicAreaName)+'</strong></div><span>'+
          ui.escapeHtml(coordinateText(area.longitude,area.latitude))+'</span>'+closed+'</div>';
      }).join('');

      var poiHtml=pois.map(function(poi){
        return '<span class="live-poi-chip"><span class="material-icons">place</span>'+
          ui.escapeHtml(poi.name)+'</span>';
      }).join('');

      card.innerHTML='<div class="scenic-card-head"><div><small>当前主景区</small><h3>'+
        ui.escapeHtml(current.scenicAreaName)+'</h3></div><span class="verified-badge">高德已核验</span></div>'+
        '<p class="scenic-address"><span class="material-icons">location_on</span>'+
        ui.escapeHtml(current.city+current.district+' · '+current.address)+'</p>'+
        '<div class="coordinate-grid"><div><small>景区中心</small><strong>'+
        ui.escapeHtml(coordinateText(current.longitude,current.latitude))+'</strong></div><div><small>导航入口</small><strong>'+
        ui.escapeHtml(current.entranceLocation||'高德未返回')+'</strong></div></div>'+
        '<div class="live-poi-list">'+poiHtml+'</div>'+relatedHtml+
        '<p class="source-note">数据来源：'+ui.escapeHtml(data.dataSource||'高德地图 Web 服务')+
        '；Key 仅保存在后端。</p>';
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
    btn.innerHTML='<div class="loading-spinner"></div> 分析中...';

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
      btn.innerHTML='<span class="material-icons text-[18px]">route</span> 生成路线';

      if(r.ok&&r.data){
        showResult(r.data);
      }else{
        if(placeholder) placeholder.classList.remove('hidden');
        ui.toast((r.error&&r.error.message)||'推荐失败，请重试','error');
      }
    });
  }

  function showResult(data){
    document.getElementById('result-route-name').textContent=data.routeName||'灵山胜境推荐路线';
    document.getElementById('result-time').innerHTML='<span class="material-icons text-[14px]">schedule</span> 约'+(data.estimatedTime||0)+'分钟';
    document.getElementById('result-distance').innerHTML='<span class="material-icons text-[14px]">directions_walk</span> '+Number(data.distance||0).toFixed(2)+'公里';
    document.getElementById('result-difficulty').textContent='难度：'+(data.difficulty||'medium');
    document.getElementById('result-source').textContent=data.mapProvider==='amap'?'高德实时路线':'来源未确认';
    document.getElementById('result-score').textContent='★ '+Number(data.score||0).toFixed(1);

    var spotsEl=document.getElementById('result-spots');
    var spots=data.spots||[];
    spotsEl.innerHTML=spots.map(function(s,i){
      var isLast=i===spots.length-1;
      var coordinate=coordinateText(s.longitude,s.latitude);
      var amapName=s.amapPoiName&&s.amapPoiName!==s.spotName?
        '<div class="poi-amap-name">高德名称：'+ui.escapeHtml(s.amapPoiName)+'</div>':'';
      var closed=s.temporarilyClosed?
        '<span class="poi-warning">高德当前标注：暂停开放</span>':'';
      return '<div class="relative"><div class="absolute -left-[29px] w-4 h-4 rounded-full bg-primary border-2 border-white"></div>'+
        '<div class="route-poi-card"><div class="route-poi-title"><span>'+(i+1)+'. '+
        ui.escapeHtml(s.spotName||s.spotId)+'</span>'+closed+'</div>'+
        '<div class="route-poi-meta"><span>停留约 '+Number(s.stayMinutes||0)+' 分钟</span><span>'+
        ui.escapeHtml(coordinate)+'</span><span>POI '+ui.escapeHtml(s.poiId||'未返回')+'</span></div>'+
        amapName+'<p>'+ui.escapeHtml(s.address||'高德未返回详细地址')+'</p></div>'+
        (isLast?'':'<div class="h-4 border-l-2 border-orange-soft ml-[-21px]"></div>')+'</div>';
    }).join('');

    var legs=data.instructions||[];
    var evidence=document.getElementById('result-map-note');
    evidence.innerHTML='<div class="map-evidence-head"><strong>高德路线证据</strong><span>'+
      ui.escapeHtml(String((data.routePolyline||[]).length))+' 个折线坐标点</span></div>'+
      (legs.length?legs.map(function(leg){
        return '<div class="route-leg"><span>'+ui.escapeHtml(leg.fromSpot)+' → '+
          ui.escapeHtml(leg.toSpot)+'</span><strong>'+Number(leg.distanceMeters||0)+' 米 · 约 '+
          Number(leg.durationMinutes||0)+' 分钟</strong></div>';
      }).join(''):'<p>当前路线没有需要计算的相邻路段。</p>');

    document.getElementById('result-reason').innerHTML='<span class="material-icons text-[16px] text-primary align-text-bottom mr-1">lightbulb</span> '+ui.escapeHtml(data.reason||'该路线根据你的偏好生成。');

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
