/**
 * Vision — Image Recognition Page V2
 */
(function(){
  'use strict';
  var A=window.Aurelian,api=A.api,ui=A.ui,st=A.state;
  var roomId=st.get('roomId'),userId=st.get('userId');

  function init(){
    A.auth.guardRole('visitor', function(){
      var uploadZone=document.getElementById('upload-zone');
      var fileInput=document.getElementById('file-input');
      var retryBtn=document.getElementById('retry-btn');
      if(uploadZone){
        uploadZone.addEventListener('click',function(){fileInput.click();});
        uploadZone.addEventListener('dragover',function(e){e.preventDefault();uploadZone.style.borderColor='#E07B3C';});
        uploadZone.addEventListener('dragleave',function(){uploadZone.style.borderColor='';});
        uploadZone.addEventListener('drop',function(e){e.preventDefault();uploadZone.style.borderColor='';handleFile(e.dataTransfer.files[0]);});
      }
      if(fileInput) fileInput.addEventListener('change',function(){handleFile(fileInput.files[0]);});
      if(retryBtn) retryBtn.addEventListener('click',resetPage);
    });
  }

  function handleFile(file){
    if(!file) return;
    if(!file.type.match(/image\/(jpeg|png|webp)/)){ui.toast('请上传 jpg/png/webp 图片','warning');return;}
    if(file.size>10*1024*1024){ui.toast('图片不能超过 10MB','warning');return;}
    document.getElementById('upload-zone').classList.add('hidden');
    var placeholder=document.getElementById('result-placeholder');
    if(placeholder) placeholder.classList.add('hidden');
    document.getElementById('result-area').classList.add('hidden');
    document.getElementById('error-area').classList.add('hidden');
    var reader=new FileReader();
    reader.onload=function(e){
      document.getElementById('preview-img').src=e.target.result;
      document.getElementById('preview-area').classList.remove('hidden');
    };
    reader.readAsDataURL(file);
    document.getElementById('loading-area').classList.remove('hidden');
    recognizeWithBase64(file);
  }

  function recognizeWithBase64(file){
    var reader=new FileReader();
    reader.onload=function(e){
      api.post('/vision/recognize',{
        roomId:roomId||'demo',userId:userId||'demo',
        imageUrl:e.target.result,
        currentSpotId:st.get('currentSpotId')||''
      }).then(function(r){
        document.getElementById('loading-area').classList.add('hidden');
        if(r.ok&&r.data) showResult(r.data);
        else showError((r.error&&r.error.message)||'识别失败');
      });
    };
    reader.readAsDataURL(file);
  }

  function showResult(data){
    var spot=data.recognizedSpot||{};
    document.getElementById('result-spot-name').textContent=spot.spotName||data.spotName||'未知景点';
    document.getElementById('result-confidence').textContent='置信度：'+((spot.confidence||data.confidence||0)*100).toFixed(0)+'%';
    document.getElementById('result-category').textContent=data.category||'spot';
    document.getElementById('result-description').textContent=data.description||'暂无讲解';
    var features=data.visualFeatures||[];
    document.getElementById('result-features').innerHTML=features.map(function(f){
      return '<span class="px-2 py-0.5 bg-surface border border-border rounded-full text-xs text-text-secondary">'+ui.escapeHtml(f)+'</span>';
    }).join('');
    var related=data.relatedSpots||[];
    if(related.length){
      document.getElementById('result-related').classList.remove('hidden');
      document.getElementById('related-list').innerHTML=related.map(function(s){
        return '<div class="flex items-center gap-2 p-2 border border-border rounded-lg"><span class="material-icons text-primary text-[18px]">location_on</span><span class="text-sm">'+ui.escapeHtml(s.spotName||s.spotId)+'</span></div>';
      }).join('');
    }else document.getElementById('result-related').classList.add('hidden');
    document.getElementById('result-area').classList.remove('hidden');
  }

  function showError(msg){
    document.getElementById('error-message').textContent=msg;
    document.getElementById('error-area').classList.remove('hidden');
  }

  function resetPage(){
    document.getElementById('upload-zone').classList.remove('hidden');
    document.getElementById('preview-area').classList.add('hidden');
    document.getElementById('result-area').classList.add('hidden');
    document.getElementById('error-area').classList.add('hidden');
    document.getElementById('loading-area').classList.add('hidden');
    document.getElementById('file-input').value='';
    var placeholder=document.getElementById('result-placeholder');
    if(placeholder) placeholder.classList.remove('hidden');
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
