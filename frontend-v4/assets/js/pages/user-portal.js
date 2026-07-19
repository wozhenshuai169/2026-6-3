/**
 * User Portal V2 — Voice + TTS + Digital Human States + Spot Card
 */
(function(){
  'use strict';
  var A=window.Aurelian,state=A.state,api=A.api,ui=A.ui,router=A.router,comp=A.components;

  var roomId=state.get('roomId'),userId=state.get('userId');
  var roomPollTimer,avatarPollTimer,members=[],currentSpotId=state.get('currentSpotId')||null,messages=[];
  var isTextMode=false,isRecording=false,recognition=null,recTimer=null,recSec=0;
  var lastAvatarStatus='idle',routeSpots=[],routeIndex=0,roomRouteId=state.get('routeId');
  var roomRequestPending=false,avatarRequestPending=false;
  var isSoloMode=!roomId;
  var lastNarrationId=null,roomNarrationPaused=false;
  var selectedVoice=state.get('narrationVoice')||'guide_female';
  var avatarSpeed=1.0;
  var selectedFeedbackScore=0;

  var els={};

  function init(){
    A.auth.guardRole('visitor', function(){
      cacheDom(); bindEvents(); loadAvatarSettings();
      initSpeechRecognition();
      if(roomId) startRoomMode();
      else showJoinOverlay();
    });
    window.addEventListener('pagehide',stopRoomMode);
    document.addEventListener('visibilitychange',function(){if(document.hidden)stopRoomMode();else if(roomId)startRoomMode();});
  }

  function cacheDom(){
    ['avatarContainer','avatarStatusLabel','roomJoinOverlay','roomCodeInput','roomJoinBtn','roomSoloBtn','roomJoinError',
     'memberListContainer','menuToggle','menuClose','functionOverlay',
     'fnKnowledge','fnMap','fnAi',
     'avatarMode','textMode','btnSwitchText','btnSwitchAvatar',
     'publicChatArea','publicChatInput','publicChatSend','narrationText',
     'btnVoice','spotChip','spotChipName','ttsPlayer','pageBody','visitorVoice','roomVoiceSelect',
     'feedbackTag','feedbackComment','feedbackSubmit'
    ].forEach(function(id){
      var camel=id.replace(/-([a-z])/g,function(m,c){return c.toUpperCase();});
      var kebab=id.replace(/([A-Z])/g,'-$1').toLowerCase();
      els[camel]=document.getElementById(id)||document.getElementById(kebab)||els[camel];
    });
  }

  function bindEvents(){
    syncVoiceSelectors();
    if(els.visitorVoice) els.visitorVoice.addEventListener('change',function(){setSelectedVoice(els.visitorVoice.value,true);});
    if(els.roomVoiceSelect) els.roomVoiceSelect.addEventListener('change',function(){setSelectedVoice(els.roomVoiceSelect.value,false);});
    if(els.menuToggle) els.menuToggle.addEventListener('click',function(){els.functionOverlay.classList.remove('hidden');});
    if(els.menuClose) els.menuClose.addEventListener('click',function(){els.functionOverlay.classList.add('hidden');});
    if(els.roomJoinBtn) els.roomJoinBtn.addEventListener('click',handleJoinRoom);
    if(els.roomSoloBtn) els.roomSoloBtn.addEventListener('click',startSoloMode);
    if(els.roomCodeInput) els.roomCodeInput.addEventListener('keydown',function(e){if(e.key==='Enter') handleJoinRoom();});
    if(els.fnKnowledge) els.fnKnowledge.addEventListener('click',function(){handleFunction('knowledge');});
    if(els.fnMap) els.fnMap.addEventListener('click',function(){handleFunction('map');});
    if(els.fnAi) els.fnAi.addEventListener('click',function(){handleFunction('assistant');});
    if(els.btnSwitchText) els.btnSwitchText.addEventListener('click',switchToTextMode);
    if(els.btnSwitchAvatar) els.btnSwitchAvatar.addEventListener('click',switchToAvatarMode);
    if(els.publicChatSend) els.publicChatSend.addEventListener('click',function(){sendPublicQuestion();});
    if(els.publicChatInput) els.publicChatInput.addEventListener('keydown',function(e){if(e.key==='Enter')sendPublicQuestion();});
    if(els.btnVoice){els.btnVoice.addEventListener('click',toggleRecording);updateVoiceBtn();}
    // Feedback stars
    document.querySelectorAll('.feedback-star').forEach(function(star){
      star.addEventListener('click', function(){
        selectedFeedbackScore=parseInt(this.getAttribute('data-score'));
        document.querySelectorAll('.feedback-star').forEach(function(s,i){s.style.color = i < selectedFeedbackScore ? '#F59E0B' : '#E8E8E4';});
      });
    });
    if(els.feedbackSubmit) els.feedbackSubmit.addEventListener('click',submitFeedback);
  }

  function loadAvatarSettings(){
    api.get('/avatar-settings').then(function(result){
      if(!result.ok||!result.data)return;
      avatarSpeed=Number(result.data.speed)||1.0;
      if(!state.get('narrationVoice'))setSelectedVoice(result.data.voice||'guide_female',false);
      else applyVoiceAvatar(selectedVoice);
    });
  }

  function submitFeedback(){
    if(!selectedFeedbackScore){ui.toast('请先选择星级','warning');return;}
    if(!roomId){ui.toast('加入导览房间后可以提交反馈','warning');return;}
    var tag=els.feedbackTag?els.feedbackTag.value:'';
    var comment=els.feedbackComment?els.feedbackComment.value.trim():'';
    els.feedbackSubmit.disabled=true;
    api.post('/feedback',{
      score:selectedFeedbackScore,
      roomId:roomId,
      userId:userId,
      scene:'public-tour',
      comment:comment,
      tags:tag?[tag]:[]
    }).then(function(r){
      els.feedbackSubmit.disabled=false;
      if(r.ok){
        ui.toast('感谢你的反馈','success');
        if(els.feedbackComment)els.feedbackComment.value='';
      }else ui.toast('反馈提交失败，请稍后重试','error');
    });
  }

  // === Mode switching ===
  function switchToTextMode(){isTextMode=true;els.avatarMode.classList.add('hidden');els.textMode.classList.remove('hidden');}
  function switchToAvatarMode(){isTextMode=false;els.textMode.classList.add('hidden');els.avatarMode.classList.remove('hidden');}

  // === Room join ===
  function showJoinOverlay(){els.roomJoinOverlay.classList.remove('hidden');}
  function hideJoinOverlay(){els.roomJoinOverlay.classList.add('hidden');}

  function handleJoinRoom(){
    var code=(els.roomCodeInput.value||'').trim();
    if(!code){showJoinError('请输入同行码，或点击“先自己逛逛”');return;}
    els.roomJoinBtn.disabled=true;els.roomJoinBtn.textContent='加入中...';
    els.roomJoinError.classList.add('hidden');
    api.post('/rooms/'+code+'/join',{}).then(function(r){
      if(r.ok){roomId=code;isSoloMode=false;state.set('roomId',roomId);hideJoinOverlay();ui.toast('加入成功！','success');startRoomMode();addMsg('system','你已加入同行小队');}
      else{var msg=(r.error&&r.error.message)||'加入失败';if(r.error&&r.error.status===404)msg='同行码不存在';showJoinError(msg);els.roomJoinBtn.disabled=false;els.roomJoinBtn.textContent='加入同行小队';}
    });
  }
  function showJoinError(msg){els.roomJoinError.textContent=msg;els.roomJoinError.classList.remove('hidden');}

  function startSoloMode(){
    stopRoomMode();
    roomId=null;isSoloMode=true;members=[];
    state.remove('roomId');
    if(els.roomJoinError)els.roomJoinError.classList.add('hidden');
    if(els.roomJoinBtn){els.roomJoinBtn.disabled=false;els.roomJoinBtn.textContent='加入同行小队';}
    hideJoinOverlay();
    renderMemberList();
    updateDigitalHumanState('idle');
    if(els.avatarStatusLabel)els.avatarStatusLabel.textContent='独自导览';
    if(els.spotChip){els.spotChip.classList.remove('hidden');}
    if(els.spotChipName)els.spotChipName.textContent='独自游览';
    if(els.narrationText)els.narrationText.textContent='已进入独自导览。你可以直接询问景点和路线，无需加入同行小队。';
    loadRouteData();
    if(!messages.length)addMsg('system','已进入独自导览，可直接提问或播放讲解');
    ui.toast('已进入独自导览', 'success');
  }

  // === Room mode ===
  function startRoomMode(){
    stopRoomMode();
    isSoloMode=false;
    fetchRoomMembers();fetchAvatarState();loadRouteData();fetchRoomMessages();
    roomPollTimer=setInterval(fetchRoomMembers,A.config.POLL_INTERVAL_ROOM);
    avatarPollTimer=setInterval(fetchAvatarState,A.config.POLL_INTERVAL_AVATAR);
  }

  function stopRoomMode(){
    if(roomPollTimer)clearInterval(roomPollTimer);
    if(avatarPollTimer)clearInterval(avatarPollTimer);
    roomPollTimer=null;avatarPollTimer=null;
  }

  function loadRouteData(){
    api.get('/routes').then(function(r){
      if(r.ok&&r.data&&r.data.routes&&r.data.routes.length){
        var route=null;
        if(roomRouteId)route=r.data.routes.find(function(item){return item.routeId===roomRouteId;});
        route=route||r.data.routes[0];
        routeSpots=route.spotIds||[];
        if(!currentSpotId&&routeSpots.length){
          currentSpotId=routeSpots[0];
          state.set('currentSpotId',currentSpotId);
          fetchSpotInfo();
        }
        updateRouteProgress();
      }
    });
    // Also try to get spot details
    if(currentSpotId) fetchSpotInfo();
  }

  function updateRouteProgress(){
    if(!routeSpots.length) return;
    var bar=document.getElementById('route-progress-bar');
    if(bar) bar.classList.remove('hidden');
    var idx=routeSpots.indexOf(currentSpotId);
    if(idx>=0) routeIndex=idx+1;
    var pct=routeSpots.length?Math.round(routeIndex/routeSpots.length*100):0;
    var fill=document.getElementById('route-progress-fill');
    if(fill) fill.style.width=pct+'%';
    var txt=document.getElementById('route-progress-text');
    if(txt) txt.textContent=routeIndex+'/'+routeSpots.length;
    var pills=document.getElementById('route-spots-pills');
    if(pills){
      pills.innerHTML=routeSpots.map(function(s,i){
        var isCurrent=s===currentSpotId;
        return '<span class="px-2 py-0.5 rounded-full text-[9px] '+(isCurrent?'bg-brand-accent text-white':'bg-[#F5F5F2] text-text-secondary')+'">'+ui.escapeHtml(s)+'</span>';
      }).join('');
    }
  }

  function fetchSpotInfo(){
    if(!currentSpotId) return;
    api.get('/spots/'+currentSpotId).then(function(r){
      var card=document.getElementById('spot-info-card');
      if(!card) return;
      card.classList.remove('hidden');
      if(r.ok&&r.data){
        document.getElementById('spot-info-name').textContent=r.data.spotName||currentSpotId;
        document.getElementById('spot-info-desc').textContent=r.data.description||'暂无简介';
      }
    });
  }

  function fetchRoomMembers(){
    if(!roomId||roomRequestPending)return;
    roomRequestPending=true;
    api.get('/rooms/'+roomId).then(function(r){
      if(r.ok&&r.data){
        members=r.data.members||[];
        var prevSpot=currentSpotId;
        currentSpotId=r.data.currentSpot;
        roomRouteId=r.data.routeId||roomRouteId;
        if(roomRouteId)state.set('routeId',roomRouteId);
        renderMemberList();
        if(currentSpotId!==prevSpot){updateRouteProgress();fetchSpotInfo();}
      }else if(r.error&&r.error.status===403){
        stopRoomMode();
        state.clearBusinessContext();
        roomId=null;
        showJoinOverlay();
        ui.toast('无权限访问该房间，请重新加入','warning');
      }
    }).finally(function(){roomRequestPending=false;});
  }

  function fetchAvatarState(){
    if(!roomId||avatarRequestPending)return;
    avatarRequestPending=true;
    api.get('/rooms/'+roomId+'/avatar-state').then(function(r){
      if(!r.ok||!r.data)return;
      var d=r.data,status=d.aiStatus||'idle';
      if(status!==lastAvatarStatus){lastAvatarStatus=status;updateDigitalHumanState(status);}
      if(els.avatarStatusLabel){var labels={idle:'待命中',listening:'聆听中',speaking:'讲解中',thinking:'思考中',paused:'已暂停',resuming:'续讲中',explaining:'讲解中',answering:'回答中'};els.avatarStatusLabel.textContent=labels[status]||status;}
      // Update narration text
      if(d.text&&els.narrationText)els.narrationText.textContent=d.text;
      if(status==='paused'){
        if(els.ttsPlayer&&!els.ttsPlayer.paused)els.ttsPlayer.pause();
        roomNarrationPaused=true;
      }else if(d.audioUrl&&d.narrationId){
        if(d.narrationId!==lastNarrationId){
          lastNarrationId=d.narrationId;
          roomNarrationPaused=false;
          playRoomNarration(d);
          addMsg('status','领队已开始新的景点讲解');
        }else if(roomNarrationPaused&&els.ttsPlayer){
          roomNarrationPaused=false;
          els.ttsPlayer.play().catch(function(){
            addMsg('system','浏览器阻止了自动续播，请等待团长重新开始讲解');
          });
        }
      }
      // Update spot chip
      if(currentSpotId&&els.spotChip){els.spotChip.classList.remove('hidden');els.spotChipName.textContent=currentSpotId;}
    }).finally(function(){avatarRequestPending=false;});
  }

  function fetchRoomMessages(){
    if(!roomId)return;
    api.get('/rooms/'+roomId+'/messages?limit=100').then(function(r){
      if(!r.ok||!r.data||!Array.isArray(r.data.messages))return;
      messages=r.data.messages.map(function(m){
        var role=m.type==='ai'?'ai':(m.type==='broadcast'?'system':(m.userId===userId?'user':'ai'));
        return{role:role,text:(m.type==='broadcast'?'【团长广播】':'')+m.content};
      });
      renderMessages();
    });
  }

  function updateDigitalHumanState(status){
    // Update CSS avatar via data-status attribute
    if(els.avatarContainer) els.avatarContainer.setAttribute('data-status', status);
    // Also keep body class for backward compatibility
    if(els.pageBody){
      els.pageBody.className=els.pageBody.className.replace(/state-\w+/g,'');
      els.pageBody.classList.add('state-'+status);
    }
  }

  function renderMemberList(){
    if(!els.memberListContainer)return;
    if(isSoloMode&&!roomId){
      els.memberListContainer.innerHTML='<div class="flex items-center gap-3 p-3 border border-brand-border rounded-xl bg-white"><div class="size-10 rounded-full border border-brand-border bg-surface-container flex items-center justify-center"><span class="material-icons text-[18px]">person</span></div><div><div class="text-sm font-medium">独自导览中</div><div class="text-xs text-text-secondary mt-0.5">未加入公共房间，问答不会广播给团队</div></div></div>';
      return;
    }
    if(!members.length){els.memberListContainer.innerHTML=comp.emptyState('group','暂无成员');return;}
    var h='';
    members.forEach(function(m){
      var init=(m.userName||'?').charAt(0).toUpperCase(),isSelf=m.userId===userId;
      h+='<div class="flex items-center gap-3 p-3 border border-brand-border rounded-xl bg-white"><div class="size-10 rounded-full border border-brand-border bg-surface-container flex items-center justify-center font-bold text-sm">'+ui.escapeHtml(init)+'</div><div><div class="text-sm font-medium">'+ui.escapeHtml(m.userName||'游客')+(isSelf?' <span class="text-on-surface-variant font-normal">(你)</span>':'')+'</div></div></div>';
    });
    els.memberListContainer.innerHTML=h;
  }

  // === Public chat ===
  function sendPublicQuestion(text,inputMode,asrConfidence){
    if(text && typeof text !== 'string') text='';
    text=text||(els.publicChatInput?els.publicChatInput.value.trim():'');
    if(!text)return;
    inputMode=inputMode==='voice'?'voice':'text';
    asrConfidence=typeof asrConfidence==='number'?asrConfidence:null;
    if(els.publicChatInput)els.publicChatInput.value='';
    addMsg('user',text);

    if(!roomId||isSoloMode){
      sendSoloQuestion(text,inputMode,asrConfidence);
      return;
    }

    // Check if this is a private question
    var isPrivate=detectPrivateQuestion(text);
    if(isPrivate){addMsg('decision','这类问题将转到私人服务，不在公共频道显示具体内容');}
    showTyping();

    api.post('/ai/public-question',{
      roomId:roomId,
      userId:userId,
      question:text,
      needAudio:true,
      voice:selectedVoice,
      inputMode:inputMode,
      asrConfidence:asrConfidence
    }).then(function(r){
      removeTyping();
      if(r.ok&&r.data){
        addMsg('ai',r.data.answer||'');
        playTTS(r.data.audioUrl);
        if(r.data.resumeText&&els.narrationText)els.narrationText.textContent=r.data.resumeText;
        if(r.data.avatarState){
          var s=r.data.avatarState.aiStatus||'explaining';
          var labels={'idle':'待命中','listening':'聆听中','speaking':'讲解中','thinking':'思考中','resuming':'续讲中','answering':'回答中'};
          if(r.data.avatarState.action==='answering') addMsg('status',labels.answering||'回答中');
          else if(s==='resuming') addMsg('status',labels.resuming||'续讲中');
        }
      }
      else{addMsg('system','发送失败: '+(r.error&&r.error.message||'网络错误'));}
    });
  }

  function sendSoloQuestion(text,inputMode,asrConfidence){
    var isPrivate=detectPrivateQuestion(text);
    if(isPrivate)addMsg('decision','独自导览时，你的提问只对你可见；如需领队协助，请加入同行小队后联系对方');
    showTyping();
    api.post('/ai/solo-question',{
      userId:userId,
      question:text,
      currentSpotId:currentSpotId||routeSpots[0]||'lingshan_dazhaobi',
      needAudio:true,
      voice:selectedVoice,
      inputMode:inputMode==='voice'?'voice':'text',
      asrConfidence:typeof asrConfidence==='number'?asrConfidence:null
    }).then(function(r){
      removeTyping();
      if(r.ok&&r.data){
        addMsg('ai',r.data.answer||'');
        if(els.narrationText)els.narrationText.textContent=r.data.answer||'';
        playTTS(r.data.audioUrl);
      }else{
        addMsg('system','暂时无法回答，请稍后再试');
      }
    }).catch(function(){
      removeTyping();
      addMsg('system','问答服务暂时无法连接，请稍后再试');
    });
  }

  function setSelectedVoice(voice,notify){
    var supported=['guide_female','xiaomei','guide_male','xiaowei'];
    selectedVoice=supported.indexOf(voice)!==-1?voice:'guide_female';
    state.set('narrationVoice',selectedVoice);
    syncVoiceSelectors();
    applyVoiceAvatar(selectedVoice);
    if(notify)ui.toast('讲解音色和数字人形象已切换，下次语音生效','success');
  }

  function applyVoiceAvatar(voice){
    if(!A.avatarVoices)return;
    var image=els.avatarContainer&&els.avatarContainer.querySelector('img');
    A.avatarVoices.apply(voice,image,els.avatarContainer);
  }

  function syncVoiceSelectors(){
    if(els.visitorVoice)els.visitorVoice.value=selectedVoice;
    if(els.roomVoiceSelect)els.roomVoiceSelect.value=selectedVoice;
  }

  function detectPrivateQuestion(text){
    var privateKeywords=['厕所','洗手间','累','休息','不舒服','走不动','迷路','离队','自己走','提前走','喝水','饿','手机没电','生病','肚子','疼','厕所'];
    return privateKeywords.some(function(k){return text.indexOf(k)!==-1;});
  }

  function addMsg(role,text){messages.push({role:role,text:text});renderMessages();}
  function renderMessages(){
    if(!els.publicChatArea)return;
    var h='<div id="narration-banner" class="bg-[#FDF6F1] border border-[#E07B3C]/15 rounded-lg p-3 text-xs leading-relaxed msg-in"><div class="flex items-center gap-1.5 text-brand-accent font-medium mb-1"><span class="material-icons text-[14px]">volume_up</span> 导游讲解</div><p id="narration-text">'+(currentSpotId?'当前景点：'+ui.escapeHtml(currentSpotId):'等待讲解开始...')+'</p></div>';
    messages.forEach(function(m){
      if(m.role==='system')h+='<div class="text-center msg-in"><span class="text-[10px] text-[#A0A0A0] bg-[#F5F5F2] px-2 py-0.5 rounded-full">'+ui.escapeHtml(m.text)+'</span></div>';
      else if(m.role==='decision')h+='<div class="msg-in"><div class="bg-[#FFF8F0] border border-[#E07B3C]/25 rounded-lg px-3 py-2 text-[10px] text-[#E07B3C] flex items-center gap-1.5"><span class="material-icons text-[14px]">psychology</span>'+ui.escapeHtml(m.text)+'</div></div>';
      else if(m.role==='status')h+='<div class="text-center msg-in"><span class="text-[10px] text-[#E07B3C] bg-[#FDF6F1] px-2 py-0.5 rounded-full flex items-center gap-1 mx-auto w-fit"><span class="w-1 h-1 rounded-full bg-[#E07B3C]"></span>'+ui.escapeHtml(m.text)+'</span></div>';
      else if(m.role==='user')h+='<div class="flex justify-end msg-in"><div class="max-w-[80%] bg-white border border-brand-border rounded-xl rounded-br-sm px-3 py-2 text-xs">'+ui.escapeHtml(m.text)+'</div></div>';
      else h+='<div class="flex msg-in"><div class="max-w-[85%] bg-[#F5F5F2] rounded-xl rounded-bl-sm px-3 py-2 text-xs border-l-2 border-brand-accent">'+ui.escapeHtml(m.text)+'</div></div>';
    });
    els.publicChatArea.innerHTML=h;
    els.narrationText=document.getElementById('narration-text');
    setTimeout(function(){els.publicChatArea.scrollTop=els.publicChatArea.scrollHeight;},50);
  }
  function showTyping(){
    var el=document.createElement('div');el.id='typing-indicator';el.className='flex msg-in';
    el.innerHTML='<div class="bg-[#F5F5F2] rounded-xl rounded-bl-sm px-3 py-2 border-l-2 border-brand-accent"><span class="text-xs text-[#A0A0A0]">正在整理回答</span><span class="dot-anim" style="color:#E07B3C"> <span>.</span><span>.</span><span>.</span></span></div>';
    els.publicChatArea.appendChild(el);els.publicChatArea.scrollTop=els.publicChatArea.scrollHeight;
  }
  function removeTyping(){var el=document.getElementById('typing-indicator');if(el)el.remove();}

  // === TTS playback ===
  function playRoomNarration(data){
    if(!data||!data.text){playTTS(data&&data.audioUrl);return;}
    api.post('/audio/tts',{text:data.text,voice:selectedVoice,speed:avatarSpeed,audioFormat:'mp3'}).then(function(r){
      if(r.ok&&r.data&&r.data.audioUrl)playTTS(r.data.audioUrl);
      else playTTS(data.audioUrl);
    }).catch(function(){playTTS(data.audioUrl);});
  }

  function playTTS(audioUrl){
    if(!audioUrl||!els.ttsPlayer)return;
    var fullUrl=audioUrl.startsWith('/')?audioUrl:A.config.API_BASE.replace('/api','')+'/'+audioUrl;
    els.ttsPlayer.src=fullUrl;
    els.ttsPlayer.play().catch(function(){});
  }

  // === Voice input ===
  var mediaRecorder=null,audioChunks=[],audioBlob=null;

  function initSpeechRecognition(){
    var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR)return;
    recognition=new SR();recognition.lang='zh-CN';recognition.interimResults=false;recognition.continuous=false;
    recognition.onresult=function(e){
      var result=e.results[0][0],text=result.transcript;
      if(text){
        if(els.publicChatInput)els.publicChatInput.value=text;
        sendPublicQuestion(text,'voice',Number.isFinite(result.confidence)?result.confidence:null);
      }
    };
    recognition.onerror=function(e){
      isRecording=false;updateVoiceBtn();
      if(e.error!=='aborted'&&e.error!=='no-speech')ui.toast('没有听清，请再说一次','warning');
    };
    recognition.onend=function(){isRecording=false;updateVoiceBtn();};
  }

  function toggleRecording(){
    if(isRecording){stopMediaRecording();return;}
    if(recognition){
      try{
        recognition.start();
        isRecording=true;updateVoiceBtn();
        ui.toast('请开始说话','info');
      }catch(e){
        isRecording=false;updateVoiceBtn();
      }
      return;
    }
    startMediaRecording();
  }

  function startMediaRecording(){
    if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){
      ui.toast('当前浏览器无法使用麦克风，请改用文字提问','warning');
      return;
    }
    navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){
      mediaRecorder=new MediaRecorder(stream,{mimeType:'audio/webm;codecs=opus'});
      audioChunks=[];
      mediaRecorder.ondataavailable=function(e){if(e.data.size>0)audioChunks.push(e.data);};
      mediaRecorder.onstop=function(){
        stream.getTracks().forEach(function(t){t.stop();});
        audioBlob=new Blob(audioChunks,{type:'audio/webm'});
        processAudioBlob(audioBlob);
      };
      mediaRecorder.start();
      isRecording=true;updateVoiceBtn();
      recSec=0;recTimer=setInterval(function(){recSec++;},1000);
      ui.toast('正在录音，再点一次结束','info');
    }).catch(function(){
      ui.toast('无法访问麦克风，请检查浏览器权限','error');
    });
  }

  function stopMediaRecording(){
    if(recTimer){clearInterval(recTimer);recTimer=null;}
    if(mediaRecorder&&mediaRecorder.state==='recording'){mediaRecorder.stop();return;}
    if(recognition){recognition.stop();}
    isRecording=false;updateVoiceBtn();
  }

  function processAudioBlob(blob){
    isRecording=false;updateVoiceBtn();
    if(!roomId||isSoloMode){
      ui.toast('当前浏览器无法直接识别录音，请使用文字提问','warning');
      return;
    }
    ui.toast('正在识别语音','info');

    // Step 1: Upload audio file
    var fd=new FormData();
    fd.append('file',blob,'recording.webm');
    fd.append('roomId',roomId);
    fd.append('userId',userId);
    fd.append('channel','public');

    api.upload('/audio/upload',fd).then(function(uploadR){
      if(uploadR.ok&&uploadR.data&&uploadR.data.audioUrl){
        var audioUrl = uploadR.data.audioUrl;
        // Step 2: Send to voice-question with the audio URL
        api.post('/ai/public-voice-question',{
          roomId: roomId, userId: userId, channel: 'public',
          audioUrl: audioUrl, audioFormat: 'webm', voice: selectedVoice
        }).then(function(r){
          if(r.ok&&r.data){
            if(r.data.asrText){addMsg('system','你说：'+r.data.asrText);}
            if(r.data.answer){addMsg('ai',r.data.answer);playTTS(r.data.audioUrl);}
            if(r.data.resumeText&&els.narrationText)els.narrationText.textContent=r.data.resumeText;
          } else {
            ui.toast('语音识别失败，请用文字','warning');
          }
        });
      } else {
        ui.toast('音频上传失败，请用文字输入','warning');
      }
    });
  }

  function updateVoiceBtn(){
    if(!els.btnVoice)return;
    var label=els.btnVoice.querySelector('span:last-child');
    if(isRecording){
      els.btnVoice.style.background='#FEE2E2';
      els.btnVoice.querySelector('.material-icons').textContent='mic_off';
      els.btnVoice.querySelector('.material-icons').style.color='#EF4444';
      if(label)label.textContent='点击结束';
    }else{
      els.btnVoice.style.background='';
      els.btnVoice.querySelector('.material-icons').textContent='mic';
      els.btnVoice.querySelector('.material-icons').style.color='';
      if(label)label.textContent='点击说话';
    }
  }

  // === Function menu ===
  function handleFunction(type){
    els.functionOverlay.classList.add('hidden');
    if(type==='knowledge'){
      var knowledgeSpotId=currentSpotId||routeSpots[0]||'lingshan_dazhaobi';
      showResult('景点资料','<div class="text-sm text-text-secondary">正在读取当前景点资料...</div>');
      api.get('/spots/'+knowledgeSpotId).then(function(r){
        if(r.ok&&r.data){
          showResult('景点资料',renderKnowledgeResult(r.data));
          return;
        }
        showResult('景点资料','<div class="border rounded-lg p-4 text-sm text-text-secondary">景点资料暂时无法获取，请稍后重试。</div>');
      }).catch(function(){
        showResult('景点资料','<div class="border rounded-lg p-4 text-sm text-text-secondary">景点资料暂时无法获取，请稍后重试。</div>');
      });
    }
    if(type==='map'){
      api.get('/map/scenic-areas/current').then(function(r){
        var h='<p class="text-sm mb-1 font-medium">灵山胜境周边</p>';
        h+='<p class="text-xs text-text-secondary mb-3">附近的参观地点与便民服务</p>';
        if(r.ok&&r.data&&r.data.pois){
          r.data.pois.slice(0,8).forEach(function(s){
            var location=s.address||s.district||'位于灵山胜境周边';
            h+='<div class="border rounded-lg p-3 mb-2"><div class="flex items-center gap-2">'+
              '<span class="material-icons text-brand-accent text-[18px]">location_on</span>'+
              '<span class="text-sm">'+ui.escapeHtml(s.name||'附近地点')+'</span></div>'+
              '<div class="text-xs text-text-secondary mt-1 ml-7">'+ui.escapeHtml(location)+'</div></div>';
          });
          (r.data.relatedScenicAreas||[]).forEach(function(area){
            h+='<div class="border border-dashed rounded-lg p-3 mt-3"><div class="text-xs text-text-secondary">独立景区，不加入灵山路线</div>'+
              '<div class="text-sm mt-1">'+ui.escapeHtml(area.scenicAreaName)+'</div></div>';
          });
        }else{
          h+='<p class="text-xs text-red-600">附近信息暂时无法获取，请稍后重试。</p>';
        }
        showResult('附近景点',h);
      });
    }
    if(type==='assistant') router.withParams('ai-assistant',roomId?{roomId:roomId}:{});
  }

  function renderKnowledgeResult(data){
    var name=data.spotName||data.name||data.spotId||'当前景点';
    var h='<div class="space-y-sm">';
    h+='<div class="border rounded-xl p-4 bg-[#FAFAF7]"><div class="text-xs text-text-secondary">当前景点</div><div class="text-lg font-medium mt-1">'+ui.escapeHtml(name)+'</div>';
    if(data.scenicAreaName)h+='<div class="text-xs text-text-secondary mt-1">'+ui.escapeHtml(data.scenicAreaName+(data.district?' · '+data.district:''))+'</div>';
    if(data.description)h+='<p class="text-sm leading-relaxed mt-3">'+ui.escapeHtml(data.description)+'</p>';
    h+='</div>';
    var chunks=Array.isArray(data.chunks)?data.chunks:[];
    if(chunks.length){
      h+='<div class="text-xs font-medium mt-4 mb-2">相关资料 '+chunks.length+' 条</div>';
      chunks.forEach(function(chunk){
        h+='<article class="border rounded-lg p-3 mb-2"><div class="text-sm font-medium">'+ui.escapeHtml(chunk.title||'景点资料')+'</div>';
        if(chunk.source)h+='<div class="text-[10px] text-text-secondary mt-1">来源：'+ui.escapeHtml(chunk.source)+'</div>';
        h+='<p class="text-xs leading-relaxed mt-2">'+ui.escapeHtml(chunk.content||'暂无正文')+'</p></article>';
      });
    }else{
      h+='<div class="border border-dashed rounded-lg p-4 mt-3 text-xs text-text-secondary">暂时没有该景点的详细介绍，已先展示路线中的基础信息。</div>';
    }
    h+='</div>';
    return h;
  }

  function showResult(title,content){
    var modal=document.getElementById('fn-result-modal');
    if(modal){
      document.getElementById('fn-result-title').textContent=title;
      document.getElementById('fn-result-body').innerHTML=content;
      modal.classList.remove('hidden');
    }
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
